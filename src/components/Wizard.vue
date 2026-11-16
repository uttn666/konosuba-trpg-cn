<script setup>
import { ref, computed, watch } from 'vue'
import { ABILS, ABIL_ZH, RACE_BASE, ALLOC_POINTS, abilFinal, abilBonus, LIFESTYLES, resolveEquip, num } from '../character.js'
import skillsData from '../data/skills.json'
import homebrewData from '../data/skills_homebrew.json'
import classesData from '../data/classes.json'
import itemsData from '../data/items.json'
import lifepath from '../data/lifepath.json'

const props = defineProps({ ch: Object, stats: Object })
const emit = defineEmits(['finish'])

const KIND_LABEL = { racial: '种族', class: '职业', advanced: '上位职业', general: '通用', spell: '法术', passive: '被动', homebrew: 'AR2E 扩展' }
const STEPS = ['① 概念', '② 种族', '③ 职业', '④ 生命轨迹', '⑤ 技能', '⑥ 属性值', '⑦ 装备', '⑧ 细节']
const step = ref(Math.min(8, Math.max(1, parseInt(localStorage.getItem('kt-wiz-step')) || 1)))
watch(step, v => { try { localStorage.setItem('kt-wiz-step', v) } catch (e) {} })
const RACES = Object.keys(RACE_BASE)
function raceSkillCount(r) {
  const all = skillsData.filter(s => s.kind === 'racial' && s.cls === r)
  const off = all.filter(s => s.src === 'official').length
  const rest = all.length - off
  return rest ? `种族技能 ${off} 官方 + ${rest} 进阶规则书` : `种族技能 ${off}`
}
const starterClasses = classesData.filter(c => !c.advanced)
const advancedClasses = classesData.filter(c => c.advanced)
// 转职规则（p241/p244）：上位职业自动带出基础职业；冒险者可从任意职业学习
const baseOf = (name) => { const c = classesData.find(x => x.name === name); return c && c.base ? c.base : '' }
function learnerClasses() {
  const set = new Set()
  if (props.ch.cls) set.add(props.ch.cls)
  if (props.ch.prevCls) set.add(props.ch.prevCls)
  const b = baseOf(props.ch.cls) || baseOf(props.ch.prevCls)
  if (b) set.add(b)
  return set
}

/* AR2E 扩展技能分类映射（与技能库一致） */
const HB_RACE = ['转生者', '原住民', '红魔族', '魔王军']
const HB_GENERAL = ['通用', '通用技能', '专注', '信仰']
function hbCat(s) {
  if (HB_RACE.includes(s.cls)) return 'racial'
  if (HB_GENERAL.includes(s.cls)) return 'general'
  if (s.cls === '基础魔法') return 'spell'
  return 'class'
}

/* ④ 生命轨迹 */
const ORIGIN_KEY = { 转生者: 'reinc', 原住民: 'native', 红魔族: 'crimson' }
function rollPath(kind) {
  const key = kind === 'origin' ? (ORIGIN_KEY[props.ch.race] || 'native') : kind === 'circum' ? 'circum' : 'goal'
  const table = lifepath.find(t => t.key === key)
  const d1 = 1 + Math.floor(Math.random() * 6), d2 = 1 + Math.floor(Math.random() * 6)
  const v = d1 * 10 + d2
  const hit = table.entries.find(e => v >= e.lo && v <= e.hi)
  if (!hit) return
  const map = { origin: ['origin', 'originDesc'], circum: ['circum', 'circumDesc'], goal: ['goal', 'goalDesc'] }
  const [f, fd] = map[kind]
  props.ch.lifepath[f] = hit.name
  props.ch.lifepath[fd] = hit.desc
  rollInfo.value = { kind, d1, d2, v, name: hit.name }
}
const rollInfo = ref(null)
const originTable = computed(() => lifepath.find(t => t.key === (ORIGIN_KEY[props.ch.race] || 'native')))
const circumTable = computed(() => lifepath.find(t => t.key === 'circum'))
const goalTable = computed(() => lifepath.find(t => t.key === 'goal'))

/* ⑤ 技能（卡片 + 上限） */
const skTab = ref('class')
const skillDetail = ref(null)
const includeHb = ref(localStorage.getItem('kt-wiz-hb') !== '0')
watch(includeHb, v => { try { localStorage.setItem('kt-wiz-hb', v ? '1' : '0') } catch (e) {} })
const skillSearch = ref('')
function dedupe(list) {
  const seen = new Set()
  return list.filter(s => { const k = s.name + '|' + s.cls; if (seen.has(k)) return false; seen.add(k); return true })
}
const pickable = computed(() => {
  const hb = homebrewData
  let list
  if (skTab.value === 'racial') {
    list = [...skillsData.filter(s => s.kind === 'racial' && s.cls === props.ch.race),
            ...(includeHb.value ? hb.filter(s => hbCat(s) === 'racial' && s.cls === props.ch.race) : [])]
  } else if (skTab.value === 'class') {
    if (props.ch.cls === '冒险者') {
      // 冒险者：可学习任意职业（含上位）的技能（p133；上位/敌技能需GM许可）
      list = [...skillsData.filter(s => s.kind === 'class' || s.kind === 'advanced'),
              ...(includeHb.value ? hb.filter(s => hbCat(s) === 'class' && !HB_RACE.includes(s.cls) && !HB_GENERAL.includes(s.cls)) : [])]
    } else {
      const mine = learnerClasses()
      list = [...skillsData.filter(s => (s.kind === 'class' || s.kind === 'advanced') && mine.has(s.cls)),
              ...(includeHb.value ? hb.filter(s => hbCat(s) === 'class' && mine.has(s.cls)) : [])]
    }
  } else if (skTab.value === 'general') {
    list = [...skillsData.filter(s => s.kind === 'general'),
            ...(includeHb.value ? hb.filter(s => hbCat(s) === 'general') : [])]
  } else {
    list = [...skillsData.filter(s => s.kind === 'spell' || s.kind === 'passive'),
            ...(includeHb.value ? hb.filter(s => hbCat(s) === 'spell') : [])]
  }
  list = dedupe(list)
  const q = skillSearch.value.trim().toLowerCase()
  if (q) list = list.filter(s => (s.name + (s.effect || '')).toLowerCase().includes(q))
  return list
})
const isPicked = s => props.ch.skills.some(x => x.name === s.name && x.cls === s.cls)
function addSkill(s) {
  if (isPicked(s)) return
  props.ch.skills.push({ ...s, sl: 1 })
}
function removeSkill(i) { props.ch.skills.splice(i, 1) }
const racialCount = computed(() => props.ch.skills.filter(s => s.kind === 'racial').length)
const generalCount = computed(() => props.ch.skills.filter(s => s.kind === 'general').length)
const clsSkills = computed(() => props.ch.skills.filter(s => s.kind === 'class' || s.kind === 'advanced'))
const slCount = computed(() => clsSkills.value.reduce((a, s) => a + (parseInt(s.sl) || 1), 0))
const LIMITS = { racial: 1, clsSL: 5, clsSingle: 2, general: 2 }
const limitRows = computed(() => [
  { t: '种族技能', v: racialCount.value, max: LIMITS.racial, ok: racialCount.value <= LIMITS.racial },
  { t: '职业技能 SL 合计', v: slCount.value, max: LIMITS.clsSL, ok: slCount.value <= LIMITS.clsSL },
  { t: '职业技能单项 SL', v: Math.max(0, ...clsSkills.value.map(s => parseInt(s.sl) || 1)), max: LIMITS.clsSingle, ok: clsSkills.value.every(s => (parseInt(s.sl) || 1) <= LIMITS.clsSingle) },
  { t: '通用技能', v: generalCount.value, max: LIMITS.general, ok: generalCount.value <= LIMITS.general },
])
const skillViolations = computed(() => limitRows.value.filter(r => !r.ok).map(r => `${r.t}：${r.v}（上限 ${r.max}）`))

/* ⑥ 属性值（自动计算 + 种族技能快速应用） */
const allocLeft = computed(() => ALLOC_POINTS - ABILS.reduce((a, k) => a + (props.ch.abil[k].alloc || 0), 0))
function bump(a, d) {
  const m = props.ch.abil[a]
  const base = (RACE_BASE[props.ch.race] || {})[a] || 0
  const next = (m.alloc || 0) + d
  if (next < 0) return
  if (base + (m.raceMod || 0) + next + (m.misc || 0) > 13) return
  if (d > 0 && allocLeft.value <= 0) return
  m.alloc = next
}
const hasTalent = computed(() => props.ch.skills.some(s => s.name.includes('多才多艺')))
const hasSpecialize = computed(() => props.ch.skills.some(s => s.name.includes('能力特化')))
const talentPicks = ref(['', '', ''])
const specPlus = ref(''), specMinus = ref('')
function applyRacialMods() {
  ABILS.forEach(a => { props.ch.abil[a].raceMod = 0 })
  if (hasTalent.value) talentPicks.value.filter(Boolean).forEach(a => { props.ch.abil[a].raceMod = 1 })
  if (hasSpecialize.value) {
    if (specPlus.value) props.ch.abil[specPlus.value].raceMod = 4
    if (specMinus.value) props.ch.abil[specMinus.value].raceMod = (props.ch.abil[specMinus.value].raceMod || 0) - 1
  }
}
function clearRacialMods() {
  ABILS.forEach(a => { props.ch.abil[a].raceMod = 0 })
  talentPicks.value = ['', '', '']; specPlus.value = ''; specMinus.value = ''
}

/* ⑦ 装备（数值 + 价格 + 预算） */
const SLOT_CATS = {
  rightHand: ['weapons', 'shields'], leftHand: ['weapons', 'shields'],
  head: ['armor'], body: ['armor'], other: ['armor'], accessory: ['accessories'],
}
const slotDefs = [['rightHand', '右手'], ['leftHand', '左手'], ['head', '头部'], ['body', '身体'], ['other', '其他防具'], ['accessory', '饰品']]
const STAT_COLS = {
  weapons: ['重量', '命中', '攻击力', '行动', '射程', '价格'],
  shields: ['重量', '物防', '魔防', '行动', '价格'],
  armor: ['重量', '闪避', '物防', '魔防', '移动', '价格'],
  accessories: ['价格', '效果'],
}
function catRows(cat) {
  return (itemsData[cat] || []).flatMap(t => t.rows.map(r => {
    const f = {}
    t.headers.forEach((h, i) => { f[h] = r.cells[i] ?? '' })
    const price = num(f['价格'])
    return { name: r.name, cat, headers: t.headers, cells: r.cells, price: price == null ? 0 : price, note: r.note || '' }
  }))
}
const eqOpen = ref('')
const eqSearch = ref('')
function slotOptions(slot) {
  let list = SLOT_CATS[slot].flatMap(c => catRows(c))
  if (eqSearch.value.trim()) {
    const q = eqSearch.value.trim().toLowerCase()
    list = list.filter(o => o.name.toLowerCase().includes(q))
  }
  return list
}
function pickSlot(slot, opt) {
  if (!opt) { props.ch.equip[slot] = null; eqOpen.value = ''; return }
  props.ch.equip[slot] = resolveEquip(opt.name, opt.cat, itemsData)
  props.ch.equip[slot].price = opt.price
  eqOpen.value = ''
}
function cellVal(o, col) { const i = o.headers.indexOf(col); return i >= 0 ? (o.cells[i] || '—') : '—' }
const equippedList = computed(() => Object.values(props.ch.equip || {}).filter(Boolean))
// 价格兜底：旧存档无 price 字段时回落到 f.price / 装备表反查
function priceOf(e) {
  if (!e) return 0
  if (e.price != null) return e.price
  const p = num(e.f && e.f.price)
  if (p != null) return p
  const row = catRows(e.cat || 'weapons').find(o => o.name === e.name)
  return row ? row.price : 0
}
const eqTotalPrice = computed(() => equippedList.value.reduce((a, e) => a + priceOf(e), 0))
const money = computed(() => parseInt(props.ch.money) || 0)
const eqOver = computed(() => eqTotalPrice.value > money.value)
const carryCap = computed(() => props.stats.final.STR || 0)
const carryOver = computed(() => (props.stats.em.weight || 0) > carryCap.value)

/* 步骤守卫 + 提示弹窗 */
const warnMsg = ref('')
function warn(t) { warnMsg.value = t }
function stepBlockReason() {
  if (step.value === 5 && skillViolations.value.length) return '技能超出创建上限：\n' + skillViolations.value.join('\n') + '\n\n请调整后再继续。'
  if (step.value === 7 && carryOver.value) return `超出负重：
装备总重 ${props.stats.em.weight} > 基础力量值 ${carryCap.value}（负重上限 p123）。

请更换更轻的装备后再继续。`
  if (step.value === 7 && eqOver.value) return `资金不足（没钱了）：\n装备总价 ${eqTotalPrice.value} KE，现金 ${money.value} KE，超出 ${eqTotalPrice.value - money.value} KE。\n\n请减少装备、降低价格或调整金钱后再继续。`
  return ''
}
function nextStep() {
  const r = stepBlockReason()
  if (r) { warn(r); return }
  if (step.value < 8) step.value++
}
function prevStep() { if (step.value > 1) step.value-- }

/* ⑧ 细节 + 官方规则检查清单 */
const equipPrice = computed(() => props.stats.em.price || 0)
const wizChecks = computed(() => {
  const over = ABILS.filter(a => abilFinal(props.ch, a) > 13)
  return [
    { ok: slCount.value === 5, need: true, t: '职业技能 SL 合计 ' + slCount.value + ' / 5（官方：升级前共 5 级）' },
    { ok: clsSkills.value.every(s2 => (parseInt(s2.sl) || 1) <= 2), need: true, t: '职业技能单项 SL ≤ 2' },
    { ok: racialCount.value === 1, need: true, t: '种族技能 ' + racialCount.value + ' / 1 个（时机：创建）' },
    { ok: generalCount.value === 2, need: true, t: '通用技能 ' + generalCount.value + ' / 2 个（1 级）' },
    { ok: over.length === 0, need: true, t: '基础属性值均 ≤ 13' + (over.length ? '（超出：' + over.join('/') + '）' : '') },
    { ok: allocLeft.value === 0, need: false, t: '5 点属性分配' + (allocLeft.value ? '剩 ' + allocLeft.value + ' 点未用' : '已用完') },
    { ok: equipPrice.value <= money.value, need: false, t: '装备总价 ' + equipPrice.value + ' KE / 现金 ' + money.value + ' KE' },
    { ok: !carryOver.value, need: true, t: '负重 ' + (props.stats.em.weight || 0) + ' / 基础力量值 ' + carryCap.value },
  ]
})
function finish() {
  const r = stepBlockReason()
  if (r) { warn(r); return }
  if (wizChecks.value.some(c => !c.ok && c.need)) { warn('还有未完成的规则项（见⑧检查清单），请先修正。'); return }
  emit('finish')
}
</script>

<template>
  <div class="kt-wizard">
    <div class="kt-steps">
      <button v-for="(s, i) in STEPS" :key="s" :class="{ 'is-cur': step === i + 1 }" @click="step = i + 1">{{ s }}</button>
      <span class="kt-wiz-tip">官方顺序：先选技能、后定属性值（创建上限 13）</span>
    </div>
    <div class="kt-livestat">
      <div class="kt-ls-item"><span>HP</span><b>{{ stats.hpMax ?? '—' }}</b></div>
      <div class="kt-ls-item"><span>MP</span><b>{{ stats.mpMax ?? '—' }}</b></div>
      <div class="kt-ls-item"><span>命中</span><b>{{ stats.hit >= 0 ? '+' : '' }}{{ stats.hit }}</b></div>
      <div class="kt-ls-item"><span>闪避</span><b>{{ stats.dodge >= 0 ? '+' : '' }}{{ stats.dodge }}</b></div>
      <div class="kt-ls-item"><span>物防</span><b>{{ stats.pd }}</b></div>
      <div class="kt-ls-item"><span>魔防</span><b>{{ stats.md }}</b></div>
      <div class="kt-ls-item"><span>行动</span><b>{{ stats.act }}</b></div>
      <div class="kt-ls-item"><span>移动</span><b>{{ stats.move }}</b></div>
      <div class="kt-ls-item" :class="{ over: carryOver }"><span>负重</span><b>{{ stats.em.weight }}<i>/{{ carryCap }}</i></b></div>
    </div>

    <!-- ① 概念 -->
    <div v-if="step === 1" class="kt-step-pane">
      <div class="kt-form-grid">
        <label>角色名称<input class="kt-input" v-model="ch.meta.name" placeholder="例如：佐藤和真"></label>
        <label>玩家名称<input class="kt-input" v-model="ch.meta.player"></label>
        <label>年龄<input class="kt-input" v-model="ch.meta.age"></label>
        <label>性别<input class="kt-input" v-model="ch.meta.gender"></label>
        <label>角色等级<input class="kt-input" type="number" min="1" v-model.number="ch.meta.level"></label>
        <label>已用经验点数<input class="kt-input" v-model="ch.meta.expUsed"></label>
      </div>
    </div>

    <!-- ② 种族 -->
    <div v-if="step === 2" class="kt-step-pane">
      <div class="kt-race-cards">
        <button v-for="r in RACES" :key="r" class="kt-racecard" :class="{ 'is-on': ch.race === r }" @click="ch.race = r">
          <strong>{{ r }}</strong>
          <div class="kt-race-abils">
            <span v-for="a in ABILS" :key="a" :title="ABIL_ZH[a]"><b>{{ ABIL_ZH[a][0] }}</b><span class="kt-num">{{ RACE_BASE[r][a] }}</span></span>
          </div>
          <em>{{ raceSkillCount(r) }}</em>
          <p class="kt-race-desc">{{ r === '转生者' ? '来自异世界的灵魂，可从3种「转生恩赐」中择一，创建时可选带「时机：创建」的技能。' : r === '原住民' ? '这个世界的一般居民，含精灵、矮人等亚人。可选3项基础属性值+1。' : '生来魔力强大的人族分支。能力特化：智力+4、其他某项-1。' }}</p>
        </button>
      </div>
      <p v-if="!ch.race" class="kt-placeholder">← 选择一个种族以继续</p>
    </div>

    <!-- ③ 职业（12 初始 + 4 上位） -->
    <div v-if="step === 3" class="kt-step-pane">
      <div class="kt-flabel">初始职业（12）</div>
      <div class="kt-cls-cards">
        <button v-for="c in starterClasses" :key="c.name" class="kt-racecard" :class="{ 'is-on': ch.cls === c.name }" @click="ch.cls = c.name; ch.prevCls = ''">
          <strong>{{ c.name }}</strong>
          <span class="kt-num kt-cls-mod">{{ ABILS.map(a => (c[a] ? `${ABIL_ZH[a]}+${c[a]}` : '')).filter(Boolean).join(' ') || '无修正' }}</span>
          <em>HP {{ c.hp0 }}（+{{ c.hpGain }}/级）· MP {{ c.mp0 }}（+{{ c.mpGain }}/级）· 装备需求：{{ c.equip }}</em>
        </button>
      </div>
      <div class="kt-flabel" style="margin-top:14px">上位职业（4）· 需 CL10 后通过转职获得（p242-244）</div>
      <div class="kt-cls-cards">
        <button v-for="c in advancedClasses" :key="c.name" class="kt-racecard kt-advcard" :class="{ 'is-on': ch.cls === c.name }" @click="ch.cls = c.name">
          <strong>{{ c.name }} <span class="kt-badge kt-badge-red">上位</span></strong>
          <span class="kt-num kt-cls-mod">前置：{{ c.base }} · {{ ABILS.map(a => (c[a] ? `${ABIL_ZH[a]}+${c[a]}` : '')).filter(Boolean).join(' ') }}</span>
          <em>HP成长+{{ c.hpGain }} · MP成长+{{ c.mpGain }}</em>
          <p class="kt-race-desc">可继续学习 {{ c.base }} 的技能（p244）。仅 {{ c.base }} 可转职为此职业。</p>
        </button>
      </div>
      <div v-if="ch.cls && !advancedClasses.some(c => c.name === ch.cls)" class="kt-form-grid" style="margin-top:12px">
        <label>转职前职业（可选）
          <select class="kt-select" v-model="ch.prevCls">
            <option value="">— 无转职历史 —</option>
            <option v-for="c in starterClasses" :key="c.name" :value="c.name" :disabled="c.name === ch.cls">{{ c.name }}</option>
          </select>
        </label>
      </div>
      <p v-if="!ch.cls" class="kt-placeholder">← 选择一个职业</p>
      <p v-else class="kt-sub" style="margin-top:6px">转职规则：转职后可同时学习原职业与新职业的技能（p241）。冒险者可从任意职业学习技能，创建时必须取得「额外祝福」（p133）。</p>
    </div>

    <!-- ④ 生命轨迹 -->
    <div v-if="step === 4" class="kt-step-pane">
      <p class="kt-sub" style="margin-bottom:10px">出身表随种族自动切换；RoC = 掷骰或自选。{{ ch.race ? '' : '（建议先在②选择种族）' }}</p>
      <div v-for="k in ['origin', 'circum', 'goal']" :key="k" class="kt-lp-row">
        <div class="kt-lp-head">
          <strong>{{ k === 'origin' ? '出身' + (originTable ? '（' + originTable.title + '）' : '') : k === 'circum' ? '境遇' : '目标' }}</strong>
          <button class="kt-btn" @click="rollPath(k)">🎲 掷 d66</button>
        </div>
        <input class="kt-input" v-model="ch.lifepath[k === 'origin' ? 'origin' : k === 'circum' ? 'circum' : 'goal']" placeholder="条目名（可掷骰或手填）">
        <textarea class="kt-input" rows="2" v-model="ch.lifepath[k === 'origin' ? 'originDesc' : k === 'circum' ? 'circumDesc' : 'goalDesc']" placeholder="说明（可留空）"></textarea>
      </div>
      <div v-if="rollInfo" class="kt-roll-result">🎲 {{ rollInfo.d1 }} + {{ rollInfo.d2 }} = d66 [{{ rollInfo.v }}] → <strong>{{ rollInfo.name }}</strong></div>
    </div>

    <!-- ⑤ 技能（卡片） -->
    <div v-if="step === 5" class="kt-step-pane">
      <div class="kt-skillpick">
        <div class="kt-pick-left">
          <div class="kt-sub" v-if="skTab === 'class'" style="margin-bottom:6px">
            可学职业：{{ ch.cls === '冒险者' ? '全部职业（冒险者特殊规则 p133）' : [...learnerClasses()].join(' / ') || '（先选职业）' }}
          </div>
          <div class="kt-tabs">
            <button class="kt-tab" :class="{ 'is-on': skTab === 'racial' }" @click="skTab = 'racial'">种族技能</button>
            <button class="kt-tab" :class="{ 'is-on': skTab === 'class' }" @click="skTab = 'class'">职业技能</button>
            <button class="kt-tab" :class="{ 'is-on': skTab === 'general' }" @click="skTab = 'general'">通用技能</button>
            <button class="kt-tab" :class="{ 'is-on': skTab === 'spell' }" @click="skTab = 'spell'">法术/被动</button>
          </div>
          <div class="kt-sktools">
            <input class="kt-input" v-model="skillSearch" placeholder="搜索技能名 / 效果关键词…">
            <label class="kt-check kt-check-sm"><input type="checkbox" v-model="includeHb">含 AR2E 扩展</label>
            <span class="kt-count">可选 {{ pickable.length }} 条</span>
          </div>
          <div class="kt-skgrid">
            <div v-for="s in pickable" :key="s.name + s.cls" class="kt-skcard" :class="{ 'is-picked': isPicked(s) }">
              <div class="kt-skcard-head" @click="skillDetail = s">
                <strong>{{ s.name }}</strong>
                <span class="kt-badge kt-badge-blue">{{ s.cls }}</span>
                <span v-if="s.src === 'ar2e'" class="kt-badge kt-badge-gold">AR2E</span>
              </div>
              <div class="kt-skgrid-stats">
                <span>{{ s.timing || '—' }}</span><span>{{ s.cost && s.cost !== '-' ? s.cost + 'MP' : '—' }}</span><span>SL{{ s.maxSL || '—' }}</span>
              </div>
              <div class="kt-skcard-eff">{{ s.effect }}</div>
              <div class="kt-skcard-foot">
                <button class="kt-btn kt-mini" @click.stop="isPicked(s) ? removeSkill(ch.skills.findIndex(x => x.name === s.name && x.cls === s.cls)) : addSkill(s)">
                  {{ isPicked(s) ? '✕ 移除' : '＋ 选择' }}
                </button>
                <button class="kt-btn kt-mini" @click.stop="skillDetail = s">详情</button>
              </div>
            </div>
            <p v-if="!pickable.length" class="kt-placeholder">该分类下没有可选技能（先完成②种族 / ③职业）</p>
          </div>
        </div>
        <div class="kt-pick-right">
          <div class="kt-flabel">已选技能（{{ ch.skills.length }}）</div>
          <div class="kt-pick-chosen">
            <div v-for="(s, i) in ch.skills" :key="s.name + i" class="kt-pick-row">
              <span class="kt-pick-name">{{ s.name }}</span>
              <span class="kt-pick-meta">{{ s.cls }}</span>
              <input class="kt-input kt-sl-input" type="number" min="1" :max="parseInt(s.maxSL) || 5" v-model.number="s.sl" title="SL">
              <button class="kt-btn kt-mini" @click="removeSkill(i)">✕</button>
            </div>
            <p v-if="!ch.skills.length" class="kt-placeholder">从左侧卡片点「＋ 选择」加入</p>
          </div>
          <div class="kt-limits">
            <div v-for="r in limitRows" :key="r.t" class="kt-limitrow" :class="r.ok ? 'ok' : 'bad'">
              <span>{{ r.ok ? '✓' : '✗' }} {{ r.t }}</span>
              <b class="kt-num">{{ r.v }} / {{ r.max }}</b>
            </div>
            <div v-if="skillViolations.length" class="kt-limitwarn">超出上限，无法进入下一步：{{ skillViolations.join('；') }}</div>
          </div>
        </div>
      </div>

      <!-- 技能详情弹窗 -->
      <div v-if="skillDetail" class="kt-skmodal-backdrop" @click.self="skillDetail = null">
        <div class="kt-skmodal">
          <div class="kt-skmodal-head">
            <div><h3>{{ skillDetail.name }}</h3><span v-if="skillDetail.nameEn" class="kt-en">{{ skillDetail.nameEn }}</span></div>
            <button class="kt-btn" @click="skillDetail = null">✕</button>
          </div>
          <dl class="kt-dl">
            <dt>分类</dt><dd>{{ skillDetail.cls }}（{{ KIND_LABEL[skillDetail.kind] || skillDetail.kind }}）</dd>
            <dt>时机</dt><dd>{{ skillDetail.timing || '—' }}</dd>
            <dt>判定</dt><dd>{{ skillDetail.check || '—' }}</dd>
            <dt>对象 / 射程</dt><dd>{{ skillDetail.target || '—' }} / {{ skillDetail.range || '—' }}</dd>
            <dt>消耗 / 最大SL</dt><dd>{{ skillDetail.cost || '—' }} / {{ skillDetail.maxSL || '—' }}</dd>
            <template v-if="skillDetail.usage"><dt>使用条件</dt><dd>{{ skillDetail.usage }}</dd></template>
            <dt>参照</dt><dd>{{ skillDetail.ref || '—' }}</dd>
          </dl>
          <p style="font-size:13px">{{ skillDetail.effect }}</p>
          <div v-if="skillDetail.fixNote" class="kt-gm-note">修正记录：{{ skillDetail.fixNote }}</div>
          <div class="kt-rel" style="margin-top:10px">
            <button class="kt-btn kt-btn-primary" :disabled="isPicked(skillDetail)" @click="addSkill(skillDetail); skillDetail = null">{{ isPicked(skillDetail) ? '已选择' : '＋ 选择此技能' }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ⑥ 属性值（自动计算） -->
    <div v-if="step === 6" class="kt-step-pane">
      <p class="kt-sub" style="margin-bottom:8px">最终值 = 种族基础值 + 种族技能修正 + 分配（剩余 <strong>{{ allocLeft }}</strong> 点）+ 其他；加成 = 最终值 ÷ 3 向下取整（自动计算）。单项 ≤ 13。</p>
      <table class="kt-table kt-abiltab">
        <thead><tr><th>属性</th><th>基础值</th><th>种族技能修正</th><th>分配</th><th>其他</th><th>最终</th><th>加成(÷3)</th></tr></thead>
        <tbody>
          <tr v-for="a in ABILS" :key="a">
            <td><strong>{{ ABIL_ZH[a] }}</strong> <span style="opacity:.5">{{ a }}</span></td>
            <td class="kt-num">{{ (RACE_BASE[ch.race] || {})[a] ?? '—' }}</td>
            <td><input class="kt-input kt-num-in" type="number" v-model.number="ch.abil[a].raceMod"></td>
            <td class="kt-num">
              <button class="kt-btn kt-mini" @click="bump(a, -1)">−</button>
              {{ ch.abil[a].alloc || 0 }}
              <button class="kt-btn kt-mini" @click="bump(a, 1)">＋</button>
            </td>
            <td><input class="kt-input kt-num-in" type="number" v-model.number="ch.abil[a].misc"></td>
            <td class="kt-num"><strong>{{ abilFinal(ch, a) }}</strong><span v-if="abilFinal(ch, a) > 13" style="color:var(--kt-red)"> ⚠超13</span></td>
            <td class="kt-num"><strong>+{{ abilBonus(ch, a) }}</strong></td>
          </tr>
        </tbody>
      </table>
      <div v-if="hasTalent || hasSpecialize" class="kt-limits" style="margin-top:10px">
        <div class="kt-flabel">种族技能自动应用（写入「种族技能修正」列）</div>
        <div v-if="hasTalent" class="kt-rowline">
          <span>多才多艺：选择 3 项属性各 +1</span>
          <select v-for="i in 3" :key="'t' + i" class="kt-select kt-mini-sel" v-model="talentPicks[i - 1]">
            <option value="">—</option>
            <option v-for="a in ABILS" :key="a" :value="a">{{ ABIL_ZH[a] }}</option>
          </select>
        </div>
        <div v-if="hasSpecialize" class="kt-rowline">
          <span>能力特化：一项 +4，另一项 −1</span>
          <select class="kt-select kt-mini-sel" v-model="specPlus"><option value="">+4 →</option><option v-for="a in ABILS" :key="a" :value="a">{{ ABIL_ZH[a] }}</option></select>
          <select class="kt-select kt-mini-sel" v-model="specMinus"><option value="">−1 →</option><option v-for="a in ABILS" :key="a" :value="a">{{ ABIL_ZH[a] }}</option></select>
        </div>
        <div class="kt-rel" style="margin-top:6px">
          <button class="kt-btn kt-btn-primary" @click="applyRacialMods">应用</button>
          <button class="kt-btn" @click="clearRacialMods">清除</button>
        </div>
      </div>
    </div>

    <!-- ⑦ 装备（数值 + 价格 + 预算） -->
    <div v-if="step === 7" class="kt-step-pane">
      <p class="kt-sub" style="margin-bottom:8px">初始资金 500 KE（kiloeris = 1000 厄里斯）。点击槽位展开选择器，表中列出各项数值与价格。</p>
      <div class="kt-eqslots">
        <div v-for="[slot, label] in slotDefs" :key="slot" class="kt-eqslot">
          <div class="kt-flabel">{{ label }}</div>
          <button class="kt-eqbtn" :class="{ 'is-open': eqOpen === slot, 'is-empty': !ch.equip[slot] }" @click="eqOpen = (eqOpen === slot ? '' : slot); eqSearch = ''">
            <template v-if="ch.equip[slot]">
              <strong>{{ ch.equip[slot].name }}</strong>
              <span class="kt-eqvals kt-num">
                <span v-if="ch.equip[slot].f.pd">物防{{ ch.equip[slot].f.pd }}</span>
                <span v-if="ch.equip[slot].f.md">魔防{{ ch.equip[slot].f.md }}</span>
                <span v-if="ch.equip[slot].f.atk">攻{{ ch.equip[slot].f.atk }}</span>
                <span v-if="ch.equip[slot].f.hit">命中{{ ch.equip[slot].f.hit }}</span>
                <span v-if="ch.equip[slot].f.act">行动{{ ch.equip[slot].f.act }}</span>
                <span v-if="ch.equip[slot].f.weight">重{{ ch.equip[slot].f.weight }}</span>
                <b>{{ priceOf(ch.equip[slot]) }} KE</b>
              </span>
            </template>
            <span v-else>— 点击选择 —</span>
          </button>
          <div v-if="eqOpen === slot" class="kt-eqpanel">
            <div class="kt-eqpanel-head">
              <input class="kt-input" v-model="eqSearch" placeholder="搜索名称…">
              <button class="kt-btn kt-mini" @click="pickSlot(slot, null)">清空</button>
              <button class="kt-btn kt-mini" @click="eqOpen = ''">关闭</button>
            </div>
            <div class="kt-eqtable-wrap">
              <table class="kt-table kt-eqtable">
                <thead><tr><th>名称</th><th v-for="c in STAT_COLS[SLOT_CATS[slot][0]]" :key="c">{{ c }}</th></tr></thead>
                <tbody>
                  <tr v-for="o in slotOptions(slot)" :key="o.name + o.cat" @click="pickSlot(slot, o)" style="cursor:pointer">
                    <td><strong>{{ o.name }}</strong><div v-if="o.note" class="kt-fixnote">{{ o.note }}</div></td>
                    <td v-for="c in STAT_COLS[SLOT_CATS[slot][0]]" :key="c" class="kt-num">{{ cellVal(o, c) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      <div class="kt-calc-out" :class="{ 'kt-over': eqOver }" style="margin-top:10px">
        装备汇总：命中 {{ stats.em.hit >= 0 ? '+' : '' }}{{ stats.em.hit }} · 攻击力 +{{ stats.em.atk }} · 物防 +{{ stats.em.pd }} · 魔防 +{{ stats.em.md }} · 行动 {{ stats.em.act >= 0 ? '+' : '' }}{{ stats.em.act }} · 重量 {{ stats.em.weight }}
        <br>装备总价 <strong>{{ eqTotalPrice }} KE</strong> / 现金 <strong>{{ money }} KE</strong> · 负重 <strong>{{ stats.em.weight }}</strong> / 上限 <strong>{{ carryCap }}</strong>（基础力量值）
        <span v-if="eqOver" style="color:var(--kt-red); font-weight:600"> ⚠ 超出 {{ eqTotalPrice - money }} KE，无法进入下一步</span>
        <span v-if="carryOver" style="color:var(--kt-red); font-weight:600"> ⚠ 超出负重 {{ stats.em.weight - carryCap }}，无法进入下一步</span>
      </div>
      <div class="kt-form-grid" style="margin-top:10px">
        <label>生活方式
          <select class="kt-select" v-model="ch.lifestyle">
            <option value="">— 未定 —</option>
            <option v-for="l in LIFESTYLES" :key="l" :value="l">{{ l }}</option>
          </select>
        </label>
        <label>金钱（KE）<input class="kt-input" type="number" v-model.number="ch.money"></label>
      </div>
      <div class="kt-flabel" style="margin-top:12px">所持物品</div>
      <div class="kt-form-grid">
        <input v-for="i in 6" :key="i" class="kt-input" v-model="ch.items[i - 1]" :placeholder="'物品 ' + i">
      </div>
    </div>

    <!-- ⑧ 细节 -->
    <div v-if="step === 8" class="kt-step-pane">
      <div class="kt-form-grid">
        <label>身高<input class="kt-input" v-model="ch.appearance.height"></label>
        <label>发色<input class="kt-input" v-model="ch.appearance.hair"></label>
        <label>眼色<input class="kt-input" v-model="ch.appearance.eyes"></label>
        <label>发型<input class="kt-input" v-model="ch.appearance.hairstyle"></label>
        <label>肤色<input class="kt-input" v-model="ch.appearance.skin"></label>
        <label>祝福值<input class="kt-input" v-model="ch.blessing" placeholder="通常为 5"></label>
        <label>祝福使用次数<input class="kt-input" v-model="ch.blessingUses"></label>
      </div>
      <div class="kt-form-grid" style="margin-top:10px">
        <label>作弊能力（开挂）名称<input class="kt-input" v-model="ch.cheat.name" placeholder="如：死亡回归（见作弊能力页）"></label>
      </div>
      <label class="kt-flabel" style="display:block;margin-top:8px">作弊效果</label>
      <textarea class="kt-input" rows="3" v-model="ch.cheat.effect"></textarea>
      <div class="kt-checklist">
        <div class="kt-flabel">创建检查（官方构筑规则 p121-124）</div>
        <div v-for="(c, i) in wizChecks" :key="i" class="kt-checkrow" :class="c.ok ? 'ok' : (c.need ? 'bad' : 'warn')">
          <b>{{ c.ok ? '✓' : (c.need ? '✗' : '…') }}</b> {{ c.t }}
        </div>
      </div>
      <div class="kt-rel" style="margin-top:14px">
        <button class="kt-btn kt-btn-primary" @click="finish">🖨 生成 A4 角色卡（打印 / 存 PDF）</button>
      </div>
    </div>

    <div class="kt-rel" style="margin-top:12px">
      <button class="kt-btn" :disabled="step <= 1" @click="prevStep">← 上一步</button>
      <button class="kt-btn" :disabled="step >= 8" @click="nextStep">下一步 →</button>
    </div>

    <!-- 提示弹窗（超限 / 没钱） -->
    <div v-if="warnMsg" class="kt-skmodal-backdrop" @click.self="warnMsg = ''">
      <div class="kt-skmodal kt-warnmodal">
        <div class="kt-skmodal-head"><h3>⚠ 无法继续</h3><button class="kt-btn" @click="warnMsg = ''">✕</button></div>
        <p style="white-space:pre-line; font-size:13.5px">{{ warnMsg }}</p>
        <div class="kt-rel" style="margin-top:12px"><button class="kt-btn kt-btn-primary" @click="warnMsg = ''">知道了</button></div>
      </div>
    </div>
  </div>
</template>
