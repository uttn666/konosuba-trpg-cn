# -*- coding: utf-8 -*-
"""
素晴TRPG规则书 数据管道 v1
来源: scripts/sources/sections.json (旧HTML 116节, 中文, 大部分经6代理核对)
输出: src/data/*.json (结构化数据, 构建时由 Vite 内联)
核对确认的错误以 FIX_* 常量显式修正(可审计), 而非手改数据。
"""
import json, os, re
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'scripts', 'sources', 'sections.json')
OUT = os.path.join(ROOT, 'src', 'data')

with open(SRC, encoding='utf-8') as f:
    SECTIONS = json.load(f)
SEC = {s['i']: s for s in SECTIONS}

# ---------- HTML 工具 ----------
def cell_text(c):
    t = re.sub(r'<br\s*/?>', ' ', c)
    t = re.sub(r'<[^>]+>', '', t)
    t = t.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#x27;', "'")
    return re.sub(r'\s+', ' ', t).strip()

def tables_of(i):
    """返回 [(heading, rows)] —— heading 为该表之前最近的 h4/h5 文本"""
    content = SEC[i]['content']
    parts = re.split(r'(<h[45][^>]*>.*?</h[45]>)', content, flags=re.S)
    out, heading = [], ''
    for p in parts:
        m = re.match(r'<h[45][^>]*>(.*?)</h[45]>', p, flags=re.S)
        if m:
            heading = cell_text(m.group(1)); continue
        for t in re.findall(r'<table[^>]*>(.*?)</table>', p, flags=re.S):
            rows = []
            for r in re.findall(r'<tr[^>]*>(.*?)</tr>', t, flags=re.S):
                cells = [cell_text(c) for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', r, flags=re.S)]
                rows.append(cells)
            if rows:
                out.append((heading, rows))
    return out

def clean_heading(h):
    return re.sub(r'（[^）]*）$', '', h or '').strip()

def split_name_en(s):
    """'哥布林 Goblin' -> ('哥布林','Goblin'); '治愈术（Heal）' -> ('治愈术','Heal')"""
    m = re.match(r'^(.*?)（([^（）]+)）$', s)
    if m: return m.group(1).strip(), m.group(2).strip()
    m = re.match(r'^([\u4e00-\u9fff（）·、]+?)\s*([A-Za-z][A-Za-z0-9\'\- ]*)$', s)
    if m: return m.group(1).strip(), m.group(2).strip()
    return s, ''

def norm_en(s):
    return re.sub(r'\s+', '', s or '').lower()

def clean_cls(t):
    """'十字军（Crusader）——战士进阶' -> '十字军'；'祭司法术一览表' -> '祭司'"""
    t = re.sub(r'——.*$', '', t or '')
    t = re.sub(r'（[^）]*）', '', t)
    t = re.sub(r'(法术一览|被动技能一览|技能一览|法术表|法术|被动技能|一览|表)$', '', t.strip())
    return t.strip()

# ---------- 表头名 → 字段映射 ----------
HDR_MAP = {'技能名': 'name', '法术名': 'name', '名称': 'name', '时机': 'timing', '判定': 'check',
           '对象': 'target', '射程': 'range', '范围': 'range', '消耗': 'cost', '最大SL': 'maxSL',
           '使用条件': 'usage', '效果': 'effect', '效果概要': 'effect'}

def map_fields(rows):
    """按表头行把数据行映射为字段 dict；返回 (headers_map, [dict])"""
    if not rows: return None, []
    hdr = rows[0]
    fmap = [HDR_MAP.get(h.strip(), '') for h in hdr]
    if not fmap or fmap.count('name') != 1: return None, []
    out = []
    for r in rows[1:]:
        if len(r) < 2 or not r[0]: continue
        obj = {}
        for k, v in zip(fmap, (r + [''] * len(fmap))[:len(fmap)]):
            if k: obj[k] = v
        if obj.get('name') in (None, '', '技能名', '法术名', '名称'): continue
        out.append(obj)
    return fmap, out

# ---------- 核对修正 (来源: 核对报告.md, 已确认项) ----------
SPELL_FIXES = {
    '神圣守卫':   {'effect': '目标受到的伤害变为0。仅祭司可用，每剧本1次。', 'fix': '旧版误作「每场景1次」，官方 once per scenario (p146)'},
    '魔力升华':   {'effect': '仅法师。魔法攻击目标变单体*，伤害+CL×10。每剧本1次。', 'fix': '旧版误作「每场景1次」，官方 once per scenario (p155)'},
    '延长咏唱':   {'cls': '大法师', 'fix': '大法师技能被旧版误置于法师表 (p176)'},
    '高阶圣盾':   {'check': '自动成功', 'cost': '4', 'fix': '旧版判定栏错填时机、漏4MP消耗 (p179)'},
    '祈祷技能':   {'effect': '祭司/大祭司技能的所有判定+1d6。', 'fix': '旧版误作「法术的判定」，官方为 skills (p180)'},
    '圣典术':     {'effect': '仅影响祭司/大祭司技能。主要动作造成的HP恢复或攻击伤害+精神值，持续到主流程结束。', 'fix': '旧版范围收窄为「法术」(p180)'},
}
ITEM_FIXES = {
    '巴斯莱剑':   {'note': '可投掷', 'fix': '备注漏「可投掷」(p190)'},
    '圆盾':       {'note': '职业限制含盗贼', 'fix': '旧版漏盗贼职业限制 (p194)'},
    '提灯':       {'note': '持续到剧本结束', 'fix': 'scenario误译为场景 (p197)'},
    '马厩生活':   {'note': '最大值不会低于1；持续到剧本结束', 'fix': '漏限制与持续期 (p198)'},
}
MP_FIX = {  # 单体敌人MP (旧版整列缺失, 官方 p281-290)
    'GiantToad': 22, 'EarthGolem': 0, 'GoblinLeader': 38, 'ZombieMaker': 36,
    'FireDrake': 65, 'One-PunchBear': 58, 'Slime': 62, 'Scarosaurus': 73,
    'Manticore': 65, 'NewbieKiller': 63, 'Griffin': 114, 'KingToad': 92,
}
MP_FIX_N = {norm_en(k): v for k, v in MP_FIX.items()}  # 归一化大小写/空格
APPLY_FIX_LOG = []

def apply_fix(obj, fixes, name):
    if name in fixes:
        f = dict(fixes[name])
        note = f.pop('fix', '')
        for k, v in f.items():
            obj[k] = v
        if note:
            obj['fixNote'] = (obj.get('fixNote', '') + '；' if obj.get('fixNote') else '') + note
            APPLY_FIX_LOG.append({'name': name, 'fix': note})

# ---------- 1. rulebook.json (阅读视图原始内容, 图片路径指向 public/img) ----------
rulebook = [{'i': s['i'], 'ch': s['chapter'], 'chTitle': s['chapterTitle'],
             'title': s['title'], 'id': s['id'],
             'html': s['content'].replace('images/', 'img/')} for s in SECTIONS]

# ---------- 2. 生命轨迹表 [32] ----------
lifepath = []
for heading, rows in tables_of(32):
    h = clean_heading(heading)
    key = {'转生者出身表': 'reinc', '原住民出身表': 'native', '红魔族出身表': 'crimson',
           '境遇表': 'circum', '目标表': 'goal'}.get(h)
    if not key: continue
    entries = []
    for r in rows:
        if len(r) < 3 or r[0] in ('d66', ''): continue
        rng = r[0]
        m = re.match(r'^(\d+)~(\d+)$', rng)
        if m: lo, hi = int(m.group(1)), int(m.group(2))
        elif rng.isdigit() and len(rng) <= 2: lo = hi = int(rng)
        else: continue
        entries.append({'lo': lo, 'hi': hi, 'name': r[1], 'desc': r[2]})
    if entries:
        lifepath.append({'key': key, 'title': h, 'entries': entries})

# ---------- 3. 技能 ----------
skills = []

def add_skills(rows, cls, kind):
    _, objs = map_fields(rows)
    for obj in objs:
        obj['name'], en = split_name_en(obj['name'])
        obj['nameEn'] = en
        obj['cls'] = cls
        obj['kind'] = kind
        obj['src'] = 'official'
        obj['ref'] = ''
        obj.setdefault('timing', '')
        obj.setdefault('check', '')
        obj.setdefault('target', '')
        obj.setdefault('range', '')
        obj.setdefault('cost', '')
        obj.setdefault('maxSL', '')
        obj.setdefault('usage', '')
        obj.setdefault('effect', '')
        skills.append(obj)

# 3a. 种族技能 [43]（表内以种族基础值信息行分隔）
r43 = tables_of(43)[0][1]
hdr = r43[0]
fmap43 = [HDR_MAP.get(h.strip(), '') for h in hdr]
cur_race = ''
for r in r43[1:]:
    if not r or not r[0] or r[0] == '技能名': continue
    if any('基础能力值' in c for c in r):
        cur_race = r[0]
        continue
    if len(r) < 9: continue
    obj = {}
    for k, v in zip(fmap43, (r + [''] * len(fmap43))[:len(fmap43)]):
        if k: obj[k] = v
    if not obj.get('name') or obj['name'] == '技能名': continue
    obj['name'], en = split_name_en(obj['name'])
    obj['nameEn'] = en
    obj['cls'] = cur_race
    obj['kind'] = 'racial'
    obj['src'] = 'official'
    obj['ref'] = ''
    for k in ('timing', 'check', 'target', 'range', 'cost', 'maxSL', 'usage', 'effect'):
        obj.setdefault(k, '')
    skills.append(obj)

# 3b. 职业技能 [45]-[61]
for i in range(45, 62):
    cls = clean_cls(SEC[i]['title'])
    kind = 'advanced' if i >= 58 else 'class'
    for heading, rows in tables_of(i):
        add_skills(rows, cls, kind)

# 3c. 通用技能 [111]（完整版, 已核对80行）
for heading, rows in tables_of(111):
    add_skills(rows, '通用', 'general')

# 3d. 法术/被动 [90]（按标题分组）
for heading, rows in tables_of(90):
    h = heading or ''
    if not rows or not rows[0]: continue
    kind = 'spell' if ('法术' in h or '基础魔法' in h) else 'passive'
    cls = clean_cls(h) or '法术'
    _, objs = map_fields(rows)
    for obj in objs:
        obj['name'], en = split_name_en(obj['name'])
        obj['nameEn'] = en
        obj['cls'] = cls
        obj['kind'] = kind
        obj['src'] = 'official'
        obj['ref'] = ''
        for k in ('timing', 'check', 'target', 'range', 'cost', 'maxSL', 'usage', 'effect'):
            obj.setdefault(k, '')
        skills.append(obj)

# 3e. 核对修正
for s in skills:
    apply_fix(s, SPELL_FIXES, s['name'])

# 3e2. 官方表内混排的来源尾标行（旧HTML把少量AR2E技能混进职业表）
TAG_SRC = {'AR2E扩展': 'ar2e', 'AR2E勘误': 'ar2e', '进阶规则书': 'ar2e', 'AR2E遗产职业': 'legacy', 'Watson': 'home', 'Haru': 'home'}
for s2 in skills:
    m2 = re.search(r'\[([^\[\]]+)\]\s*$', s2['effect'])
    if m2 and m2.group(1) in TAG_SRC:
        s2['src'] = TAG_SRC[m2.group(1)]
        s2['srcTag'] = m2.group(1)
        s2['effect'] = re.sub(r'\s*\[[^\[\]]+\]\s*$', '', s2['effect'])
        APPLY_FIX_LOG.append({'name': s2['name'], 'fix': f'来源标签修正: {m2.group(1)}'})

# 3f. ref 映射（xlsx 英文名 → PageRef）
REFS = {}
for fn in ('Race_Skill_List_English.json', 'Classes_Skill_List_English.json', 'General_Skill_List_English.json'):
    try:
        rows = json.load(open(os.path.join(ROOT, 'scripts', 'sources', 'xlsx', fn), encoding='utf-8'))
        for r in rows:
            if len(r) >= 11 and r[0] and r[10]:
                REFS[norm_en(str(r[0]))] = str(r[10])
    except Exception as e:
        print('ref map skip', fn, e)
def ref_fuzzy(en):
    if not en: return None
    key = norm_en(en)
    if key in REFS: return REFS[key]
    # 去掉 Spell/Skill/Magic 后缀再比对；或前缀互含（≥4字符）
    for suf in ('spell', 'skill', 'magic'):
        if key.endswith(suf): key = key[:-len(suf)]
    if key in REFS: return REFS[key]
    for name, ref in REFS.items():
        base = name
        for suf in ('spell', 'skill', 'magic'):
            if base.endswith(suf): base = base[:-len(suf)]
        if len(key) >= 4 and (base.startswith(key) or key.startswith(base)):
            return ref
    return None
for s in skills:
    if not s['ref'] and s.get('nameEn'):
        ref = ref_fuzzy(s['nameEn'])
        if ref: s['ref'] = ref

# ---------- 3.5 职业修正表 [44]（起始HP/MP/成长/属性修正/装备限制） ----------
ABILS = ['STR', 'DEX', 'AGI', 'INT', 'PER', 'MND', 'LUK']
classes = []
for heading, rows in tables_of(44):
    if not rows or not rows[0] or '职业' not in rows[0][0]: continue
    adv = '起始HP' not in rows[0]
    for r in rows[1:]:
        if not r[0]: continue
        if not adv:  # 起始职业：职业|7属性|起始HP|起始MP|HP成长|MP成长|装备限制
            if len(r) < 13: continue
            c = {'name': clean_cls(r[0]), 'advanced': False, 'equip': r[12]}
            for k, v in zip(ABILS, r[1:8]): c[k] = 0 if v in ('—', '-', '') else int(v)
            c['hp0'], c['mp0'] = int(r[8]), int(r[9])
            c['hpGain'] = int(re.sub(r'[+＋]', '', r[10]) or 0)
            c['mpGain'] = int(re.sub(r'[+＋]', '', r[11]) or 0)
        else:  # 进阶职业：进阶职业|7属性|HP成长|MP成长|前置职业
            if len(r) < 11: continue
            c = {'name': clean_cls(r[0]), 'advanced': True, 'equip': '', 'base': clean_cls(r[10])}
            for k, v in zip(ABILS, r[1:8]): c[k] = 0 if v in ('—', '-', '') else int(v)
            c['hp0'] = c['mp0'] = 0
            c['hpGain'] = int(re.sub(r'[+＋]', '', r[8]) or 0)
            c['mpGain'] = int(re.sub(r'[+＋]', '', r[9]) or 0)
        classes.append(c)

ADV_EQUIP = {'十字军': '战士', '大祭司': '祭司', '大法师': '法师', '刺客': '盗贼'}
for c in classes:
    if c['advanced'] and not c.get('equip'):
        c['equip'] = ADV_EQUIP.get(c['name'], '')
        APPLY_FIX_LOG.append({'name': c['name'], 'fix': '补进阶职业装备限制（原书p120）'})
    if c['name'] == '刺客':
        c['note'] = 'MP成长原书正文+14、附录+4，两处不一致；本表取正文+14'

# ---------- 4. AR2E 扩展技能 [62] ----------
homebrew = []
for heading, rows in tables_of(62):
    if not rows or not rows[0] or len(rows[0]) < 9: continue
    cls = clean_heading(heading).replace('扩展技能', '').strip()
    _, objs = map_fields(rows)
    for obj in objs:
        m = re.search(r'\[([^\[\]]+)\]\s*$', obj.get('effect', ''))
        obj['srcTag'] = m.group(1) if m else ''
        obj['effect'] = re.sub(r'\s*\[[^\[\]]+\]\s*$', '', obj.get('effect', ''))
        obj['nameEn'] = ''
        obj['cls'] = cls
        obj['kind'] = 'homebrew'
        obj['src'] = 'ar2e'
        obj['ref'] = 'AR2E'
        for k in ('timing', 'check', 'target', 'range', 'cost', 'maxSL', 'usage'):
            obj.setdefault(k, '')
        homebrew.append(obj)


# ---------- 4.5 第二轮技能复核修正（2026-11-09 双代理报告） ----------
def _find(lst, cls, name):
    return [x for x in lst if x.get('cls') == cls and x.get('name') == name]

# a) ref 元数据修正（必须在 Advanced Rules Book 归类之前，避免误伤官方法术）
REF_FIX = {'闪光术': '148', '抗魔术': '144', '爆裂魔法': '176', '造土术': '170', '冰冻术': '171'}
for x in skills:
    if x['name'] in REF_FIX: x['ref'] = REF_FIX[x['name']]

# b) 进阶规则书内容 src 归类：xlsx 标记 Advanced Rules Book 的行
for x in skills:
    if x.get('ref') == 'Advanced Rules Book':
        x['src'] = 'ar2e'; x['srcTag'] = '进阶规则书'
#    以及旧HTML混入进阶规则书内容的行（按当前数组区间，共78行）
for _i in list(range(4, 11)) + list(range(15, 22)) + list(range(28, 45)) + list(range(66, 72)) + list(range(200, 239)) + list(range(246, 261)):
    if _i < len(skills) and skills[_i].get('src') == 'official':
        skills[_i]['src'] = 'ar2e'; skills[_i]['srcTag'] = '进阶规则书'
        APPLY_FIX_LOG.append({'name': skills[_i]['name'], 'fix': '来源改标：进阶规则书（主PDF无此技能）'})

# c) 效果文本修正（官方原文回填）
SKILL_EFFECT_FIXES = {
    ('战士', '防御专注'): dict(effect='回避判定 +1d6；所有主要动作判定 −1d6。以次要动作解除，或持续到场景结束。', fixNote='旧版效果为骑士「守护」文案串入，已按原书p141回填'),
    ('战士', '下劈'): dict(effect='近战攻击伤害 + 力量值，持续到你的主流程结束。', fixNote='旧版效果整段错置，已按原书p141回填'),
    ('战士', '追击'): dict(src='official', srcTag='', timing='伤害掷骰前', effect='武器攻击的伤害掷骰前使用，该次伤害 +(SL×2)d6。', fixNote='上轮误标AR2E；实为官方Follow-Up（原书p142）'),
    ('战士', '诱饵'): dict(effect='命中判定对抗。若你获胜，目标陷入激怒：对激怒者以外的目标进行主要动作判定时 −2d6。', fixNote='旧版将激怒误作威压并加戏，已修正'),
    ('祭司', '圣盾'): dict(effect='目标受到的伤害 −(SL)d6。多个圣盾同时生效时，由目标选择承受哪个效果。', fixNote='删误入的「与掩护同时使用」，补多重圣盾规则'),
    ('祭司', '驱散亡灵'): dict(effect='CL+SL 以下的不死族陷入 K.O 或死亡（你选择）。', fixNote='移除杜撰的暴击条目'),
    ('符文骑士', '武器符文'): dict(effect='目标武器攻击伤害 +(SL)×2，持续到场景结束。', fixNote='移除杜撰的暴击条目'),
    ('符文骑士', '防具符文'): dict(effect='目标物理防御 +(SL)×2、魔法防御 +SL，持续到场景结束。', fixNote='移除杜撰的暴击条目'),
    ('大祭司', '神圣驱亡'): dict(effect='需已学 3 级驱散亡灵。对不死族目标：若其等级 ≤ CL+SL+3，死亡或 K.O（你选择）；否则造成 (SL+1)d6+20 贯穿伤害。', fixNote='补前置、阈值+3与兜底伤害分支（原书p180）'),
    ('弓箭手', '影缚之术'): dict(cost='3', effect='远程攻击。目标因该攻击失去至少 1 HP 时，其回避判定 −1d6，持续到回合结束。', fixNote='消耗5→3；效果为回避−1d6而非失衡（原书p163）'),
    ('弓箭手', '弓术'): dict(src='ar2e', srcTag='进阶规则书'),
}
for (cls, name), fx in SKILL_EFFECT_FIXES.items():
    for x in _find(skills, cls, name):
        note = fx.pop('fixNote', '')
        x.update(fx)
        if note:
            x['fixNote'] = (x.get('fixNote', '') + '；' if x.get('fixNote') else '') + note
            APPLY_FIX_LOG.append({'name': name, 'fix': note})

# d) 小补丁：横扫暴击 / 高阶圣盾 / 神圣之光 / 复活spent / 异世界生意II / 告白技能
for x in _find(skills, '战士', '横扫'):
    if '暴击' not in x['effect']: x['effect'] += '暴击：追加骰子。'
for x in skills:
    if x['name'] == '高阶圣盾' and x.get('kind') == 'passive':
        x['timing'] = '圣盾术'
        if '同时使用' not in x['effect']: x['effect'] = '与圣盾术同时使用。' + x['effect']
    if x['name'] == '神圣之光' and x.get('kind') == 'class':
        x['effect'] = x['effect'].replace('主要行动的', '')
    if x['name'] == '复活' and x.get('kind') == 'class':
        x['effect'] = x['effect'].replace('已行动状态', '消耗状态')
    if x['name'] == '异世界生意' and 'II' in (x.get('nameEn') or ''):
        x['name'] = '异世界生意II'
    if x['name'] == '告白技能':
        x['effect'] = x['effect'].replace('倾诉情感或秘密以获得宣泄的技能。', '')

# e) 弓箭手：删虚构技能、补官方缺失技能（原书p163共3技能）
skills[:] = [x for x in skills if not (x.get('cls') == '弓箭手' and x.get('name') == '幸运射击')]
APPLY_FIX_LOG.append({'name': '幸运射击', 'fix': '删除：官方无此技能（旧HTML臆造）'})
for add in [
    dict(name='狙击技能', nameEn='Sniping Skill', cls='弓箭手', kind='class', src='official', ref='p163',
         timing='次要动作', check='自动成功', target='自身', range='—', cost='5', maxSL='1', usage='—',
         effect='你的远程攻击伤害 + 幸运值。'),
    dict(name='先见', nameEn='Foresight', cls='弓箭手', kind='class', src='official', ref='p163',
         timing='移动动作', check='自动成功', target='自身', range='—', cost='3', maxSL='5', usage='—',
         effect='你的远程攻击伤害 +SL×3，且不受黑暗状态修正。'),
]:
    skills.append(add)
    APPLY_FIX_LOG.append({'name': add['name'], 'fix': '补官方缺失技能（原书p163）'})

# f) 盗贼·陷阱解除：恢复官方技能，遗产版移入扩展库
for x in skills:
    if x.get('cls') == '盗贼' and x.get('name') == '陷阱解除':
        legacy = dict(x)
        legacy.update(src='legacy', srcTag='AR2E遗产职业', kind='homebrew', ref='AR2E')
        homebrew.append(legacy)
        x.update(name='陷阱解除技能', nameEn='Trap Disarm Skill', src='official', srcTag='', kind='class',
                 timing='被动', check='—', target='自身', range='—', cost='—', maxSL='1', usage='—',
                 effect='解除陷阱的全部判定 +1d6。', ref='p162',
                 fixNote='旧版误用遗产版文本，已恢复官方技能（原书p162）；遗产版移入AR2E扩展库')
        APPLY_FIX_LOG.append({'name': '陷阱解除技能', 'fix': '恢复官方版；遗产版移入扩展库'})
        break

# g) 基础魔法（法术版）字段照抄通用版
_gen = {x['name']: x for x in skills if x.get('kind') == 'general'}
for x in skills:
    if x.get('cls') == '基础魔法' and x.get('kind') == 'spell':
        g = _gen.get(x['name'])
        if g:
            for k in ('target', 'range', 'maxSL', 'timing', 'check', 'cost', 'usage'):
                if not x.get(k): x[k] = g.get(k, '')

# h) homebrew：移除误入库的道具表（契约妖精8/灵武器10/奥秘卡26 + 表头3 = 47行）
def _hb_garbage(h):
    c = (h.get('check') or '').strip()
    t = (h.get('timing') or '').strip()
    if h.get('name') == '命名': return True
    import re as _re
    if _re.fullmatch(r'\d+(\.\d+)?', c): return True
    if c in ('Type', 'Level', 'Weight', 'Effects'): return True
    if t in ('C. Fae', 'SprWeap', '奥秘'): return True
    if c.startswith('Effect:'): return True
    return False
_n0 = len(homebrew)
homebrew[:] = [h for h in homebrew if not _hb_garbage(h)]
APPLY_FIX_LOG.append({'name': '(homebrew)', 'fix': '移除误入库的道具表 %d 行（契约妖精/灵武器/奥秘卡）' % (_n0 - len(homebrew))})

# i) homebrew：强风×2 效果错配、两处截断
for h in homebrew:
    if h['name'] == '强风' and '术士' in (h.get('cls') or ''):
        if '准备' in (h.get('timing') or ''):
            h['effect'] = '风属性魔法攻击的伤害 +5，持续到回合结束。'; h['fixNote'] = '效果错配修正（Overwind）'
        elif (h.get('timing') or '') == '被动':
            h['effect'] = '风属性法术的魔法攻击命中判定暴击时，该攻击伤害额外 +3d6。'; h['fixNote'] = '效果错配修正（Strong Wind）'
    if h['name'] == '尖刺射击' and (h.get('effect') or '').rstrip().endswith('+1'):
        h['effect'] += 'd6；掷出2个6则+2d6）。持续到本主要阶段结束。'
    if h['name'] == '强化标记' and (h.get('effect') or '').rstrip().endswith('另一个'):
        h['effect'] += '次要动作。'

# ---------- 5. 敌人 [98] ----------
enemies = []
for heading, rows in tables_of(98):
    if not rows or '敌人名' not in rows[0][0]: continue
    for r in rows[1:]:
        if len(r) < 9 or not r[0]: continue
        name, en = split_name_en(r[0])
        e = {'name': name, 'nameEn': en, 'type': r[1], 'level': r[2], 'hp': r[3],
             'defense': r[4], 'check': r[5], 'attack': r[6], 'actMove': r[7], 'skills': r[8],
             'mp': None, 'mob': 'Mob' in r[2]}
        if norm_en(en) in MP_FIX_N:
            e['mp'] = MP_FIX_N[norm_en(en)]
            e['fixNote'] = '旧版MP缺失，已按原书p281-290回填'
            APPLY_FIX_LOG.append({'name': name, 'fix': f'MP={e["mp"]} (原书回填)'})
        if norm_en(en) == 'kingtoad' and '特殊物理抗性' not in e['skills']:
            e['skills'] += ', 特殊物理抗性:徒手/钝器 Lv5'
            e['fixNote'] = (e.get('fixNote') or '') + '；补漏「特殊物理抗性:徒手/钝器 Lv5」(原书p285)'
            APPLY_FIX_LOG.append({'name': name, 'fix': '补漏特殊物理抗性技能'})
        if norm_en(en) == 'zombie' and '抗性:毒' in e['skills']:
            e['skills'] = e['skills'].replace('抗性:毒', '').strip().rstrip(',').strip()
            e['fixNote'] = (e.get('fixNote') or '') + '；移除串行的「抗性:毒」(属幽灵)'
            APPLY_FIX_LOG.append({'name': name, 'fix': '移除串行的抗性:毒'})
        enemies.append(e)

# ---------- 6. 物品 [69]-[75] ----------
ITEM_SECS = {69: 'weapons', 70: 'armor', 71: 'consumables', 72: 'shields', 73: 'accessories', 74: 'tools', 75: 'lifestyles'}
items = {}
for i, cat in ITEM_SECS.items():
    tlist = []
    for heading, rows in tables_of(i):
        if not rows or not rows[0] or len(rows[0]) < 2: continue
        data = []
        for r in rows[1:]:
            if len(r) < 2 or not r[0]: continue
            it = {'cells': r, 'note': '', 'nameEn': ''}
            it['name'], it['nameEn'] = split_name_en(r[0])
            apply_fix(it, ITEM_FIXES, it['name'])
            data.append(it)
        if data:
            tlist.append({'heading': clean_heading(heading), 'headers': rows[0], 'rows': data})
    items[cat] = tlist


# ---------- 6.5 物品 cells 修正（第二轮） ----------
ITEM_CELL_FIXES = {
    'shields': {'圆盾': {8: '战士、祭司、盗贼'}},
    'tools': {'提灯': {3: '持续到剧本结束'}},
}
for _cat, _fx in ITEM_CELL_FIXES.items():
    for _t in items.get(_cat, []):
        for _r in _t['rows']:
            if _r['name'] in _fx:
                for _idx, _val in _fx[_r['name']].items():
                    if _idx < len(_r['cells']):
                        _r['cells'][_idx] = _val
                APPLY_FIX_LOG.append({'name': _r['name'], 'fix': 'cells 字段修正'})

# ---------- 7. 陷阱 [101]（数值列来自旧表, 效果列整列修正） ----------
TRAP_EFFECTS = {
    '水池':   '目标陷入游泳状态，需通过力量判定DL10，失败则失去剩余移动。不影响飞行状态角色。(p294)',
    '锁A':    '目标变为「不可开」。仅拆除此陷阱才能打开（HP 20、物防/魔防 10）。(p294)',
    '落穴':   '敏捷判定DL13，失败者坠入洞中受到2d6贯穿伤害。(p294)',
    '尖刺板': '敏捷判定DL14，失败者受到3d6+10物理伤害。(p295)',
    '锁B':    '需特定钥匙或满足特定条件才能解除，无法直接撬开。(p295)',
    '酸液湖': '受到5点HP损失，且每次清理流程再受5点HP损失。(p295)',
    '爆裂陷阱': '范围内所有目标进行幸运判定DL13，失败者受到2d6+10物理伤害。(p295)',
}
traps = []
for heading, rows in tables_of(101):
    if not rows or not rows[0]: continue
    if clean_heading(heading) != '陷阱列表' and not any('探测值' in h for h in rows[0]): continue
    if not any('探测值' in h for h in rows[0]): continue
    eff_idx = rows[0].index('效果') if '效果' in rows[0] else len(rows[0]) - 1
    for r in rows[1:]:
        if len(r) < 5 or not r[0]: continue
        nm = re.sub(r'\s*（.*?）\s*$', '', r[0]).strip()
        nm_key = nm.replace(' ', '')
        t = {'headers': rows[0], 'cells': r, 'name': nm, 'effect': r[eff_idx] if eff_idx < len(r) else '', 'fixNote': ''}
        for k, eff in TRAP_EFFECTS.items():
            if k in nm_key:
                t['effect'] = eff
                t['cells'] = t['cells'][:eff_idx] + [eff]
                t['fixNote'] = '旧版效果列整列错置，已按原书p294-295回填'
                APPLY_FIX_LOG.append({'name': nm, 'fix': '效果列回填'})
                break
        traps.append(t)

# ---------- 8. 作弊能力 [94]（块级原文） ----------
cheats = {'html': SEC[94]['content']}

# ---------- 输出 ----------
os.makedirs(OUT, exist_ok=True)
def dump(name, obj):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
    print(f'  {name:24s} {os.path.getsize(os.path.join(OUT, name)) / 1024:8.1f} KB')

dump('rulebook.json', rulebook)
dump('lifepath.json', lifepath)
dump('classes.json', classes)
dump('skills.json', skills)
dump('skills_homebrew.json', homebrew)
dump('enemies.json', enemies)
dump('items.json', items)
dump('traps.json', traps)
dump('cheats.json', cheats)
manifest = {
    'dataVersion': str(date.today()),
    'source': '旧HTML sections.json (经6代理核对) + 核对报告修正',
    'counts': {'rulebook': len(rulebook), 'skills': len(skills), 'homebrew': len(homebrew),
               'enemies': len(enemies), 'traps': len(traps),
               'lifepath': sum(len(t['entries']) for t in lifepath)},
    'fixesApplied': len(APPLY_FIX_LOG),
}
dump('manifest.json', manifest)
_seen = set(); _dedup = []
for _f in APPLY_FIX_LOG:
    _k = _f['name'] + '|' + _f['fix']
    if _k not in _seen:
        _seen.add(_k); _dedup.append(_f)
APPLY_FIX_LOG[:] = _dedup
with open(os.path.join(ROOT, 'scripts', 'fix_log.json'), 'w', encoding='utf-8') as f:
    json.dump(APPLY_FIX_LOG, f, ensure_ascii=False, indent=1)
print(f'\nfixes applied: {len(APPLY_FIX_LOG)} (scripts/fix_log.json)')
print('skills by kind:', {k: sum(1 for s in skills if s['kind'] == k) for k in ('racial', 'class', 'advanced', 'general', 'spell', 'passive')})
