// 角色模型与官方公式计算（公式来源均为核对过的规则书数据）
import { reactive, computed } from 'vue'

export const ABILS = ['STR', 'DEX', 'AGI', 'INT', 'PER', 'MND', 'LUK']
export const ABIL_ZH = { STR: '力量', DEX: '灵巧', AGI: '敏捷', INT: '智力', PER: '感知', MND: '精神', LUK: '幸运' }
// 种族基础值（已核对：旧HTML[43] 与英文PDF p132-136 一致）
export const RACE_BASE = {
  转生者: { STR: 8, DEX: 9, AGI: 8, INT: 9, PER: 8, MND: 7, LUK: 8 },
  原住民: { STR: 9, DEX: 8, AGI: 8, INT: 8, PER: 8, MND: 8, LUK: 8 },
  红魔族: { STR: 7, DEX: 8, AGI: 8, INT: 10, PER: 7, MND: 10, LUK: 7 },
}
export const LIFESTYLES = ['马厩生活', '野营生活', '普通生活', '舒适生活', '奢侈生活']
export const ALLOC_POINTS = 5

export function newCharacter() {
  return reactive({
    meta: { name: '', player: '', age: '', gender: '', expUsed: '', level: 1 },
    race: '', cls: '', prevCls: '',
    appearance: { height: '', hair: '', eyes: '', hairstyle: '', skin: '' },
    abil: Object.fromEntries(ABILS.map(a => [a, { raceMod: 0, alloc: 0, misc: 0 }])),
    skills: [], // {...skill, sl}
    equip: { rightHand: null, leftHand: null, head: null, body: null, other: null, accessory: null },
    items: ['', '', '', '', '', ''], money: 500,
    lifepath: { origin: '', originDesc: '', circum: '', circumDesc: '', goal: '', goalDesc: '' },
    cheat: { name: '', effect: '' },
    lifestyle: '',
    blessing: '', blessingUses: '',
    hpCur: '', mpCur: '',
    manual: { hit: 0, dodge: 0, pd: 0, md: 0, act: 0, move: 0 }, // 技能等其他修正（手填）
  })
}

export function abilFinal(ch, a) {
  const base = (RACE_BASE[ch.race] || {})[a] || 0
  const m = ch.abil[a]
  return base + (m.raceMod || 0) + (m.alloc || 0) + (m.misc || 0)
}
export const abilBonus = (ch, a) => Math.floor(Math.max(0, abilFinal(ch, a)) / 3)

// 数值单元格解析：'±0'→0, '+4'→4, '−1'→-1, '—'/''→null
export function num(v) {
  if (v == null) return null
  const s = String(v).trim()
  if (!s || s === '—' || s === '-') return null
  const n = s.replace(/[+＋]/g, '').replace(/[−ー]/g, '-').replace('±', '')
  const f = parseFloat(n)
  return isNaN(f) ? null : f
}

// 装备条目解析：按各类表表头名取列，返回统一字段
const FIELDS = { weight: ['重量'], hit: ['命中'], dodge: ['闪避'], atk: ['攻击力'], pd: ['物防'], md: ['魔防'], act: ['行动'], move: ['移动'], range: ['射程'], price: ['价格'], effect: ['效果'] }
export function resolveEquip(name, cat, items) {
  const tables = (items[cat] || [])
  let cells = null, headers = null, note = ''
  for (const t of tables) {
    const row = t.rows.find(r => r.name === name)
    if (row) { cells = row.cells; headers = t.headers; note = row.note || ''; break }
  }
  const f = { weight: '', hit: '', dodge: '', atk: '', pd: '', md: '', act: '', move: '', range: '', price: '', effect: '' }
  if (!cells) return { name, cat, f }
  const col = names => { for (const n of names) { const i = headers.findIndex(h => h.includes(n)); if (i >= 0 && cells[i] != null && cells[i] !== '') return cells[i] } return '' }
  for (const [k, names] of Object.entries(FIELDS)) f[k] = col(names)
  if (note) f.effect = (f.effect ? f.effect + ' ' : '') + note
  return { name, cat, f }
}

// 装备加值汇总（读取已解析的字段）
export function equipMods(ch) {
  const out = { hit: 0, atk: 0, dodge: 0, pd: 0, md: 0, act: 0, move: 0, weight: 0, price: 0, effects: [] }
  for (const e of Object.values(ch.equip)) {
    if (!e || !e.f) continue
    for (const k of ['hit', 'atk', 'dodge', 'pd', 'md', 'act', 'move', 'weight', 'price']) {
      const n = num(e.f[k]); if (n != null) out[k] += n
    }
    if (e.f.effect) out.effects.push(e.f.effect)
  }
  return out
}

export function makeStats(ch, classes, items) {
  return computed(() => {
    const c = classes.find(x => x.name === ch.cls)
    const lv = Math.max(1, parseInt(ch.meta.level) || 1)
    const em = equipMods(ch)
    // 官方公式（p118-124）：能力值 = 属性加成(÷3) + 职业修正
    const bonus = Object.fromEntries(ABILS.map(a => [a, abilBonus(ch, a)]))
    const final = Object.fromEntries(ABILS.map(a => [a, abilFinal(ch, a)]))
    const ab = Object.fromEntries(ABILS.map(a => [a, bonus[a] + (c ? (c[a] || 0) : 0)]))
    // 最大HP = 基础力量值 + 职业起始HP + HP成长×(CL−1)（p118/p242）
    // 最大MP = 基础精神值 + 职业起始MP + MP成长×(CL−1)
    const hpMax = c && !c.advanced ? ab.STR + c.hp0 + c.hpGain * (lv - 1) : null
    const mpMax = c && !c.advanced ? ab.MND + c.mp0 + c.mpGain * (lv - 1) : null
    return {
      cls: c, lv, em, bonus, final, ab, hpMax, mpMax,
      hit: ab.DEX + em.hit + (ch.manual.hit || 0),
      dodge: ab.AGI + em.dodge + (ch.manual.dodge || 0),
      pd: em.pd + (ch.manual.pd || 0),
      md: em.md + (ch.manual.md || 0),
      act: ab.AGI + ab.PER + em.act + (ch.manual.act || 0),
      move: ab.STR + 5 + em.move + (ch.manual.move || 0),
      atk: em.atk,
    }
  })
}

// 已选技能按第2页四张表分组：蓝1种族 / 蓝2职业 / 橙通用+基础魔法 / 绿法术与其他
export function skillGroups(ch) {
  const g = { racial: [], cls: [], general: [], other: [] }
  for (const s of ch.skills) {
    if (s.kind === 'racial') g.racial.push(s)
    else if (s.kind === 'class' || s.kind === 'advanced') g.cls.push(s)
    else if (s.kind === 'general' || s.cls === '基础魔法') g.general.push(s)
    else g.other.push(s)
  }
  return g
}
