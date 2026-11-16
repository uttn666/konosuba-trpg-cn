<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import rulebook from './data/rulebook.json'
import skills from './data/skills.json'
import homebrew from './data/skills_homebrew.json'
import enemies from './data/enemies.json'
import items from './data/items.json'
import traps from './data/traps.json'
import cheats from './data/cheats.json'
import classes from './data/classes.json'
import manifest from './data/manifest.json'
import Wizard from './components/Wizard.vue'
import SheetA4 from './components/SheetA4.vue'
import { newCharacter, makeStats } from './character.js'

/* ---------- 全局状态 ---------- */
const theme = ref(localStorage.getItem('kt-theme') || 'light')
const mode = ref(localStorage.getItem('kt-mode') || 'player')
const view = ref('skills')

/* ---------- 角色创建 ---------- */
const ch = newCharacter()
try { const saved = localStorage.getItem('kt-character'); if (saved) Object.assign(ch, JSON.parse(saved)) } catch (e) {}
watch(ch, () => { try { localStorage.setItem('kt-character', JSON.stringify(ch)) } catch (e) {} }, { deep: true })
const stats = makeStats(ch, classes, items)
const showPrint = ref(false)
const showAbout = ref(false)
const navOpen = ref(false)
function onKtClosePrint(){ showPrint.value = false }
function toggleTheme(){ theme.value = theme.value === 'dark' ? 'light' : 'dark'; localStorage.setItem('kt-theme', theme.value) }
function setMode(m){ mode.value = m; localStorage.setItem('kt-mode', m) }

/* ---------- 导航 ---------- */
const NAV = [
  { head: '📖 规则书', items: [
    { v: 'reader', ico: '📖', label: '规则书阅读' },
  ]},
  { head: '🗂 资料库', items: [
    { v: 'skills', ico: '📚', label: '技能库' },
    { v: 'skills', ico: '✨', label: '法术表', preset: 'spell' },
    { v: 'items', ico: '⚔️', label: '装备库' },
    { v: 'monsters', ico: '👹', label: '怪物卡' },
    { v: 'traps', ico: '⚠️', label: '陷阱与物体', gm: true },
    { v: 'cheats', ico: '🎯', label: '作弊能力' },
  ]},
  { head: '🎲 工具', items: [
    { v: 'charcreate', ico: '🎲', label: '角色创建助手' },
  ]},
  { head: '📜 模组', items: [
    { v: 'mods', ico: '🗺️', label: '全部模组' },
    { v: 'modtemplate', ico: '➕', label: '新建模组（模板）' },
  ]},
]
const activeNav = ref('skills')
const WIZARD_HASH = '#wizard'
function go(v, preset, label){
  const isSmall = window.matchMedia('(max-width: 900px)').matches
  // 角色创建助手：桌面单开新标签页；手机/平板在应用内打开
  if (v === 'charcreate' && !isSmall) {
    const url = location.pathname + location.search + WIZARD_HASH
    const w = window.open(url, '_blank')
    if (!w) { view.value = 'charcreate'; activeNav.value = label } // 弹窗被拦截时回退为当前页打开
    searchOpen.value = false
    navOpen.value = false
    return
  }
  navOpen.value = false
  // 离开创建视图时清掉 hash
  if (location.hash) { try { history.replaceState(null, '', location.pathname + location.search) } catch (e) {} }
  view.value = v
  activeNav.value = label
  if (v === 'skills' && preset === 'spell') skCat.value = 'spell'
  searchOpen.value = false
}

/* ---------- 技能库 ---------- */
const SRC_LABEL = { official: ['官方', 'kt-badge-green'], ar2e: ['AR2E 扩展', 'kt-badge-gold'], legacy: ['遗产职业', 'kt-badge-purple'], home: ['社区自制', 'kt-badge-cyan'] }
const KIND_LABEL = { racial: '种族', class: '职业', advanced: '上位职业', general: '通用', spell: '法术', passive: '被动', homebrew: 'AR2E 扩展' }
const SKILL_CATS = [
  { k: 'all', label: '全部' },
  { k: 'racial', label: '种族技能' },
  { k: 'class', label: '职业技能' },
  { k: 'advanced', label: '上位职业技能' },
  { k: 'general', label: '通用技能' },
  { k: 'spell', label: '法术' },
  { k: 'passive', label: '被动技能' },
]
// 互通职业：官方转职规则——上位职业可学习其基础职业技能（p241「转职后可同时学习原职业与新职业技能」/p244「Advanced classes can also learn skills from their base class」）。
// 注意：符文骑士等起始职业的「装备限制：战士」只是装备需求，不授予技能，故不在此表。
const CROSS_CLASS = { 十字军: ['战士'], 大祭司: ['祭司'], 大法师: ['法师'], 刺客: ['盗贼'] }
const skCat = ref('all')
const skCls = ref('')
const filters = reactive({ timing: 'all' })
const skillView = ref('cards')
// AR2E 扩展按其所属职业/种族并入对应分类（用徽章区分来源）
const RACE_CLS = ['转生者', '原住民', '红魔族', '魔王军']
const GENERAL_CLS = ['通用', '通用技能', '专注', '信仰']
function hbCat(s){
  if (RACE_CLS.includes(s.cls)) return 'racial'
  if (GENERAL_CLS.includes(s.cls)) return 'general'
  if (s.cls === '基础魔法') return 'spell'
  return 'class'
}
function poolFor(cat){
  const o = skills, h = homebrew
  if (cat === 'all') {
    const seen = new Set(); const out = []
    for (const sk of [...o, ...h]) { const k = sk.name + '|' + sk.cls; if (seen.has(k)) continue; seen.add(k); out.push(sk) }
    return out
  }
  if (cat === 'racial') return [...o.filter(s => s.kind === 'racial'), ...h.filter(s => hbCat(s) === 'racial')]
  if (cat === 'class') return [...o.filter(s => s.kind === 'class' || s.kind === 'advanced'), ...h.filter(s => hbCat(s) === 'class')]
  if (cat === 'advanced') return o.filter(s => s.kind === 'advanced')
  if (cat === 'general') return [...o.filter(s => s.kind === 'general'), ...h.filter(s => hbCat(s) === 'general')]
  if (cat === 'spell') return [...o.filter(s => s.kind === 'spell'), ...h.filter(s => hbCat(s) === 'spell')]
  if (cat === 'passive') return o.filter(s => s.kind === 'passive')
  return [...o, ...h]
}
const classChips = computed(() => [...new Set(poolFor(skCat.value).map(s => s.cls).filter(Boolean))])
const TIMINGS = ['主要动作', '主要行动', '次要动作', '伤害掷骰前', '伤害掷骰后', '判定后', '准备流程', '被动', '见效果']
const filteredSkills = computed(() => {
  let base = poolFor(skCat.value)
  if (skCls.value) {
    const extra = CROSS_CLASS[skCls.value] || []
    if (extra.length) {
      // 上位职业：并入基础职业的技能（不受当前分类池限制，按转职规则 p241/p244）
      base = [...base, ...skills.filter(s => extra.includes(s.cls) && (s.kind === 'class' || s.kind === 'advanced'))]
      const seen = new Set()
      base = base.filter(s => { const k = s.name + '|' + s.cls; if (seen.has(k)) return false; seen.add(k); return true })
    }
    base = base.filter(s => s.cls === skCls.value || extra.includes(s.cls))
  }
  if (filters.timing !== 'all') base = base.filter(s => s.timing === filters.timing)
  return base
})
function kindClass(s){ return 'kt-k-' + (s.kind || 'class') }
const drawer = ref(null)
function openDrawer(s){ drawer.value = s }

/* ---------- 怪物卡 ---------- */
const mType = ref('all')
const expanded = reactive({})
const filteredMobs = computed(() => enemies.filter(e => mType.value === 'all' || (mType.value === 'solo') !== !!e.mob))
function mobSkills(e){ return e.skills.split(/[,，]\s*/).filter(Boolean) }

/* ---------- 装备库 ---------- */
const itemTab = ref('weapons')
const ITEM_TABS = [
  ['weapons', '武器'], ['shields', '盾牌'], ['armor', '防具'],
  ['accessories', '饰品'], ['tools', '工具'], ['lifestyles', '生活方式'], ['consumables', '消耗品'],
]

/* ---------- 阅读视图 ---------- */
const chapters = (() => {
  const out = []
  for (const s of rulebook) {
    let ch = out[out.length - 1]
    if (!ch || ch.ch !== s.ch || ch.chTitle !== s.chTitle) { ch = { ch: s.ch, chTitle: s.chTitle, sections: [] }; out.push(ch) }
    ch.sections.push(s)
  }
  return out
})()
const tocOpen = ref(false)
function sameCh(a, b){ return !!a && !!b && a.ch === b.ch && a.chTitle === b.chTitle }
function chapterOf(sec){ return chapters.find(c => c.sections.some(x => x.i === sec.i)) || chapters[0] }
const anchorIdx = ref(Math.max(0, chapters.indexOf(chapterOf(rulebook.find(s => s.id === 'char-overview') || rulebook[0]))))
const renderedCount = ref(1)
const renderedChapters = computed(() => chapters.slice(anchorIdx.value, anchorIdx.value + renderedCount.value))
const renderedSections = computed(() => renderedChapters.value.flatMap(c => c.sections))
const curSec = ref(null)
const headChapter = computed(() => curSec.value ? chapterOf(curSec.value) : chapters[anchorIdx.value])
const curSecTitle = computed(() => curSec.value ? curSec.value.title : '')
function setChapter(idx){
  anchorIdx.value = Math.max(0, Math.min(chapters.length - 1, idx))
  renderedCount.value = 1
  curSec.value = null
  nextTick(() => { const m = document.querySelector('.kt-main'); if (m) m.scrollTop = 0 })
}
function pickCur(c){ setChapter(chapters.indexOf(c)) }
function gotoChapter(d){ setChapter(anchorIdx.value + d) }
function onMainScroll(){
  if (view.value !== 'reader') return
  const m = document.querySelector('.kt-main'); if (!m) return
  // 滚动接近底部 → 自动追加下一章（持续向下阅读）
  if (m.scrollTop + m.clientHeight >= m.scrollHeight - 600 && anchorIdx.value + renderedCount.value < chapters.length) renderedCount.value++
  // 当前小节跟随
  let cur = null
  for (const sec of renderedSections.value) {
    const el = document.getElementById('kt-sec-' + sec.i)
    if (el && el.getBoundingClientRect().top <= 130) cur = sec
  }
  if (!cur && renderedSections.value.length) cur = renderedSections.value[0]
  if (curSec.value !== cur) curSec.value = cur
}
async function jumpSection(c, sec){
  const idx = chapters.indexOf(c)
  if (idx < anchorIdx.value || idx >= anchorIdx.value + renderedCount.value) {
    anchorIdx.value = Math.max(0, Math.min(chapters.length - 1, idx))
    renderedCount.value = 1
    await nextTick()
  }
  tocOpen.value = false
  await nextTick()
  const el = document.getElementById('kt-sec-' + sec.i)
  const m = document.querySelector('.kt-main')
  if (el && m) m.scrollTop = el.getBoundingClientRect().top - m.getBoundingClientRect().top + m.scrollTop - 8
}

/* ---------- 角色创建 ---------- */
const step = ref(4)
const STEPS = ['① 概念', '② 种族', '③ 职业', '④ 生命轨迹', '⑤ 属性值', '⑥ 装备', '⑦ 细节']
const lpKey = ref('reinc')
const LP_TITLES = { reinc: '转生者出身表', native: '原住民出身表', crimson: '红魔族出身表', circum: '境遇表', goal: '目标表' }
const rollResult = ref(null)
function rollD66(){
  const table = lifepath.find(t => t.key === lpKey.value)
  const d1 = 1 + Math.floor(Math.random() * 6), d2 = 1 + Math.floor(Math.random() * 6)
  const v = d1 * 10 + d2
  const hit = table.entries.find(e => v >= e.lo && v <= e.hi)
  rollResult.value = { d1, d2, v, hit }
}
const abil = ref(9)
const abilBonus = computed(() => Math.floor(Math.max(0, abil.value) / 3))
const RACE_BASE = [
  ['转生者', 'kt-badge-purple', [8, 9, 8, 9, 8, 7, 8]],
  ['原住民', 'kt-badge-green', [9, 8, 8, 8, 8, 8, 8]],
  ['红魔族', 'kt-badge-gold', [7, 8, 8, 10, 7, 10, 7]],
]
const ABIL_NAMES = ['力量', '灵巧', '敏捷', '智力', '感知', '精神', '幸运']

/* ---------- 模组（import.meta.glob 自动发现，放入 mods/ 目录重新构建即收录） ---------- */
const modFiles = import.meta.glob('./data/mods/*/module.json', { eager: true })
const modsList = Object.entries(modFiles)
  .map(([, m]) => (m && m.default) ? m.default : m)
  .filter(m => m && m.id && !m.template)
  .sort((a, b) => (b.official ? 1 : 0) - (a.official ? 1 : 0))
const modSeries = ref('all')
const modSeriesList = computed(() => [...new Set(modsList.map(m => (m.meta && m.meta.series) || '其他'))])
const visibleMods = computed(() => modSeries.value === 'all' ? modsList : modsList.filter(m => ((m.meta && m.meta.series) || '其他') === modSeries.value))
const curModId = ref(modsList[0] ? modsList[0].id : '')
const curMod = computed(() => modsList.find(m => m.id === curModId.value) || modsList[0] || null)
function jp(x, d){ try { const v = JSON.parse(x); return v || d } catch (e) { return d } }
const modProgress = reactive(jp(localStorage.getItem('kt-mod-progress'), {}))
const stageOpenMap = reactive(jp(localStorage.getItem('kt-stage-open'), {}))
function stageDone(mid, i){ const a = modProgress[mid] || (modProgress[mid] = []); return !!a[i] }
function toggleStageDone(mid, i){ const a = modProgress[mid] || (modProgress[mid] = []); a[i] = !a[i]; localStorage.setItem('kt-mod-progress', JSON.stringify(modProgress)) }
function stageDoneCount(m){ return m.stages.filter((_, i) => stageDone(m.id, i)).length }
function stageIsOpen(mid, i){ const a = stageOpenMap[mid] || (stageOpenMap[mid] = []); return a[i] !== undefined ? !!a[i] : i < 2 }
function toggleStageOpen(mid, i){ const a = stageOpenMap[mid] || (stageOpenMap[mid] = []); a[i] = !stageIsOpen(mid, i); localStorage.setItem('kt-stage-open', JSON.stringify(stageOpenMap)) }
function findEnemy(name){ return enemies.find(e => e.name === name) }
function encName(b){ if (b.enemyRef) return b.enemyRef; const m = curMod.value && curMod.value.monsters[b.monster]; return m ? m.name : b.monster }
function encMeta(b){
  if (b.enemyRef) { const e = findEnemy(b.enemyRef); return e ? 'Lv' + e.level + ' · HP ' + e.hp + (e.mp != null ? ' · MP ' + e.mp : '') + ' · 防 ' + e.defense + ' · ' + e.check : '' }
  const m = curMod.value && curMod.value.monsters[b.monster]
  return m ? 'Lv' + m.level + ' · HP ' + m.hp + (m.mp != null ? ' · MP ' + m.mp : '') + ' · 防 ' + m.defense + ' · ' + m.attack : ''
}
const encExpanded = reactive({})
function toggleEnc(k, b){
  if (b.enemyRef) { view.value = 'monsters'; activeNav.value = '怪物卡' }
  else encExpanded[k] = !encExpanded[k]
}

/* ---------- 全局搜索 ---------- */
const searchOpen = ref(false)
const query = ref('')
const searchInput = ref(null)
const STATIC_RULES = [
  { g: '规则', t: '对抗判定：平局时反应方优先（反应方优先规则）', ref: 'p206', secId: 'rules-opposed' },
  { g: '规则', t: '全力移动 = 移动力 + 5 米', ref: 'p227', secId: 'combat-actions' },
  { g: '规则', t: '祝福：加骰 / 重掷判定（无「稳定伤势」用法）', ref: 'p235', secId: 'rules-blessings' },
  { g: '规则', t: '角色创建顺序：先技能 → 后属性值（上限 13）', ref: 'p121', secId: 'char-overview' },
]
const searchIndex = computed(() => {
  const out = []
  for (const s of skills) out.push({ g: '技能', t: `${s.name}${s.nameEn ? ' ' + s.nameEn : ''} — ${s.cls} ${s.cost || ''}${s.cost ? 'MP' : ''}`, ref: s.ref, v: 'skills', id: s })
  for (const s of homebrew.slice(0, 200)) out.push({ g: '扩展技能', t: `${s.name} — ${s.cls}`, ref: s.ref, v: 'skills', id: s })
  for (const e of enemies) out.push({ g: '怪物', t: `${e.name} ${e.nameEn} Lv${e.level} HP${e.hp}${e.mp != null ? ' MP' + e.mp : ''}`, ref: '', v: 'monsters', id: e })
  for (const s of rulebook) out.push({ g: '规则书', t: `${s.ch}·${s.title}`, ref: '', v: 'reader', id: s })
  out.push(...STATIC_RULES)
  return out
})
const searchResults = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return searchIndex.value.slice(0, 40)
  return searchIndex.value.filter(x => x.t.toLowerCase().includes(q)).slice(0, 40)
})
function openSearch(){ searchOpen.value = true; query.value = ''; setTimeout(() => searchInput.value && searchInput.value.focus(), 50) }
function onSearchHit(item){
  if (item.v === 'skills') { view.value = 'skills'; activeNav.value = '技能库'; drawer.value = item.id }
  else if (item.v === 'monsters') { view.value = 'monsters'; activeNav.value = '怪物卡' }
  else if (item.v === 'reader') { view.value = 'reader'; activeNav.value = '规则书阅读'; jumpSection(chapterOf(item.id), item.id) }
  searchOpen.value = false
}
function onKey(e){
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k'){ e.preventDefault(); searchOpen.value ? searchOpen.value = false : openSearch() }
  if (e.key === 'Escape'){ searchOpen.value = false; drawer.value = null; showPrint.value = false }
}
function wrapTablesIn(root){
  if (!root) return
  root.querySelectorAll('table').forEach(t => {
    const p = t.parentElement
    if (!p) return
    // 已有滚动容器/专用布局的表格不重复包裹
    if (p.closest('.kt-tblscroll, .kt-table-wrap, .kt-eqtable-wrap, .kt-scrollx, .sheet')) return
    const w = document.createElement('div')
    w.className = 'kt-tblscroll'
    p.insertBefore(w, t)
    w.appendChild(t)
  })
}
function wrapAllTables(){
  wrapTablesIn(document.getElementById('kt-main'))
}
if (typeof window !== 'undefined') {
  watch([view, anchorIdx, renderedCount], () => { nextTick(wrapAllTables) })
}

onMounted(() => {
  window.addEventListener('keydown', onKey)
  document.addEventListener('kt-close-print', onKtClosePrint)
  const m = document.querySelector('.kt-main')
  if (m) m.addEventListener('scroll', onMainScroll, { passive: true })
  if (location.hash === WIZARD_HASH) { view.value = 'charcreate'; activeNav.value = '角色创建助手' }
  nextTick(wrapAllTables)
})
onBeforeUnmount(() => { window.removeEventListener('keydown', onKey); document.removeEventListener('kt-close-print', onKtClosePrint) })

const srcBadge = s => SRC_LABEL[s.src] || SRC_LABEL.official
const fmtCost = c => (!c || c === '-' || c === '—') ? '—' : (/^\d+$/.test(c) ? c + ' MP' : c)
</script>

<template>
  <div id="kt-app" :class="{ dark: theme === 'dark', gm: mode === 'gm' }">
    <div class="kt-window">
      <header class="kt-topbar">
        <div class="kt-brand">
          <button class="kt-menu-btn" @click="navOpen = !navOpen" aria-label="菜单">☰</button>
          <span class="kt-logo">✨</span>
          <div class="kt-brand-txt"><strong>为美好的世界献上祝福！TRPG</strong><span>规则书 · {{ manifest.dataVersion }} 数据 · <b class="kt-unofficial">非官方中文版 · 学习交流用</b></span></div>
        </div>
        <button class="kt-searchbar" @click="openSearch"><span>🔍</span><span>搜索技能、装备、怪物、规则…</span><kbd>Ctrl</kbd><kbd>K</kbd></button>
        <div class="kt-top-actions">
          <div class="kt-seg" role="group" aria-label="视图模式">
            <button :class="{ 'is-on': mode === 'player' }" @click="setMode('player')">玩家</button>
            <button :class="{ 'is-on': mode === 'gm' }" @click="setMode('gm')">GM</button>
          </div>
          <button class="kt-iconbtn" @click="toggleTheme" aria-label="切换亮暗主题">{{ theme === 'dark' ? '☀️' : '🌙' }}</button>
        </div>
      </header>

      <div v-if="navOpen" class="kt-nav-backdrop" @click="navOpen = false"></div>
      <div class="kt-body">
        <nav class="kt-sidebar" :class="{ open: navOpen }" aria-label="导航">
          <div v-for="grp in NAV" :key="grp.head" class="kt-navgroup">
            <div class="kt-navhead">{{ grp.head }}</div>
            <button v-for="it in grp.items" :key="it.label" class="kt-navitem"
                    :class="{ 'is-active': activeNav === it.label, 'kt-gm-only': it.gm }" @click="go(it.v, it.preset, it.label)">
              <span class="kt-ico">{{ it.ico }}</span>{{ it.label }}
            </button>
            <div v-if="grp.head === '📜 模组'" class="kt-navslots">＋ 预留模组位<span>拖入 module.json 即可</span></div>
          </div>
        </nav>

        <main class="kt-main" id="kt-main">

          <!-- 技能库 -->
          <section v-show="view === 'skills'">
            <div class="kt-view-head">
              <div><h2>技能库</h2><p class="kt-sub">官方 {{ skills.length }} 条 + AR2E 扩展 {{ homebrew.length }} 条 · 数据已按核对报告修正</p></div>
              <div class="kt-view-tools">
                <span class="kt-count">共 {{ filteredSkills.length }} 条</span>
                <div class="kt-seg kt-seg-sm" role="group" aria-label="视图切换">
                  <button :class="{ 'is-on': skillView === 'cards' }" @click="skillView = 'cards'">卡片</button>
                  <button :class="{ 'is-on': skillView === 'table' }" @click="skillView = 'table'">表格</button>
                </div>
              </div>
            </div>
            <div class="kt-skills-layout">
              <aside class="kt-filters">
                <div class="kt-fgroup">
                  <div class="kt-flabel">分类（单选）</div>
                  <div class="kt-chips">
                    <button v-for="c in SKILL_CATS" :key="c.k" class="kt-chip kt-cat" :class="{ 'is-on': skCat === c.k }" @click="skCat = c.k">{{ c.label }}</button>
                  </div>
                </div>
                <div class="kt-fgroup">
                  <div class="kt-flabel">职业 / 种族 <span style="font-weight:400;opacity:.7">单选·再点取消</span></div>
                  <div class="kt-chips">
                    <button v-for="c in classChips" :key="c" class="kt-chip" :class="{ 'is-on': skCls === c }" @click="skCls = (skCls === c ? '' : c)">{{ c }}</button>
                  </div>
                </div>
                <div class="kt-fgroup">
                  <label class="kt-flabel" for="kt-timing">时机</label>
                  <select id="kt-timing" class="kt-select" v-model="filters.timing">
                    <option value="all">全部</option>
                    <option v-for="t in TIMINGS" :key="t" :value="t">{{ t }}</option>
                  </select>
                </div>
                <div class="kt-fgroup kt-fgroup-note">
                  徽章说明
                  <span class="kt-badge kt-badge-green">官方</span>
                  <span class="kt-badge kt-badge-gold">AR2E</span>
                  <span class="kt-badge kt-badge-red">上位职业</span>
                  <div class="kt-cross-note">上位职业（十字军/大祭司/大法师/刺客）会一并显示其基础职业技能——依据转职规则 p241「转职后可同时学习原职业与新职业技能」。起始职业的「装备需求」不授予技能。</div>
                </div>
              </aside>
              <div class="kt-results">
                <div v-if="skillView === 'cards'" class="kt-grid">
                  <button v-for="(s, i) in filteredSkills" :key="i" class="kt-skillcard" :class="kindClass(s)" @click="openDrawer(s)">
                    <span class="kt-ref">{{ s.ref || KIND_LABEL[s.kind] }}</span>
                    <span class="kt-name">{{ s.name }}</span>
                    <span v-if="s.nameEn" class="kt-en">{{ s.nameEn }}</span>
                    <span class="kt-badges">
                      <span class="kt-badge kt-badge-blue">{{ s.cls }}</span>
                      <span v-if="s.kind === 'advanced'" class="kt-badge kt-badge-red">上位职业</span>
                      <span class="kt-badge" :class="srcBadge(s)[1]">{{ srcBadge(s)[0] }}</span>
                      <span v-if="s.kind === 'spell'" class="kt-badge kt-badge-purple">法术</span>
                      <span v-if="s.fixNote" class="kt-badge kt-badge-red">已修正</span>
                    </span>
                    <span class="kt-statline"><span>时机 <b>{{ s.timing || '—' }}</b></span><span>消耗 <b>{{ fmtCost(s.cost) }}</b></span><span>SL <b>{{ s.maxSL || '—' }}</b></span></span>
                    <span class="kt-eff">{{ s.effect }}</span>
                  </button>
                </div>
                <div v-else class="kt-table-wrap">
                  <table class="kt-table">
                    <thead><tr><th>名称</th><th>分类</th><th>类别</th><th>时机</th><th>判定</th><th>对象</th><th>射程</th><th>消耗</th><th>MaxSL</th><th>来源</th><th>页码</th></tr></thead>
                    <tbody>
                      <tr v-for="(s, i) in filteredSkills" :key="i" @click="openDrawer(s)" style="cursor:pointer">
                        <td>{{ s.name }}{{ s.fixNote ? ' ⚠' : '' }}</td><td>{{ s.cls }}</td><td><span class="kt-badge" :class="s.kind === 'advanced' ? 'kt-badge-red' : 'kt-badge-blue'">{{ KIND_LABEL[s.kind] }}</span></td><td>{{ s.timing || '—' }}</td><td>{{ s.check || '—' }}</td>
                        <td>{{ s.target || '—' }}</td><td>{{ s.range || '—' }}</td><td class="kt-num">{{ fmtCost(s.cost) }}</td><td class="kt-num">{{ s.maxSL || '—' }}</td>
                        <td><span class="kt-badge" :class="srcBadge(s)[1]">{{ srcBadge(s)[0] }}</span></td><td>{{ s.ref || '—' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>

          <!-- 怪物卡 -->
          <section v-show="view === 'monsters'">
            <div class="kt-view-head">
              <div><h2>怪物卡</h2><p class="kt-sub">杂兵无 MP；{{ enemies.filter(e => !e.mob).length }} 只单体敌人 MP 已按原书 p281-290 回填</p></div>
              <div class="kt-view-tools">
                <div class="kt-seg kt-seg-sm" role="group" aria-label="类型筛选">
                  <button :class="{ 'is-on': mType === 'all' }" @click="mType = 'all'">全部</button>
                  <button :class="{ 'is-on': mType === 'solo' }" @click="mType = 'solo'">单体</button>
                  <button :class="{ 'is-on': mType === 'mob' }" @click="mType = 'mob'">杂兵</button>
                </div>
              </div>
            </div>
            <div class="kt-grid kt-grid-mob">
              <div v-for="e in filteredMobs" :key="e.name + e.nameEn" class="kt-mobcard">
                <div class="kt-mob-top">
                  <strong>{{ e.name }} <span style="opacity:.55;font-size:12px">{{ e.nameEn }}</span></strong>
                  <span class="kt-badge" :class="e.mob ? 'kt-badge-cyan' : 'kt-badge-gold'">{{ e.mob ? '杂兵' : '单体 Lv' + e.level }}</span>
                </div>
                <div class="kt-mob-stats">
                  <span>HP <b>{{ e.hp }}</b></span>
                  <span>MP <b>{{ e.mob ? '—（杂兵无MP）' : (e.mp ?? '—') }}</b></span>
                  <span>防 <b>{{ e.defense }}</b></span>
                  <span>判定 <b>{{ e.check }}</b></span>
                </div>
                <div class="kt-mob-skills"><span v-for="k in mobSkills(e).slice(0, 4)" :key="k" class="kt-chip">{{ k }}</span></div>
                <div v-if="expanded[e.name]" class="kt-mob-more">
                  <dt>攻击</dt><dd>{{ e.attack }}</dd>
                  <dt>行动/移动</dt><dd>{{ e.actMove }}</dd>
                  <dt>技能</dt><dd>{{ e.skills }}</dd>
                  <div v-if="e.fixNote" class="kt-fixnote">⚠ {{ e.fixNote }}</div>
                </div>
                <button class="kt-mob-toggle" @click="expanded[e.name] = !expanded[e.name]">{{ expanded[e.name] ? '收起 ▴' : '展开详情 ▾' }}</button>
              </div>
            </div>
          </section>

          <!-- 装备库 -->
          <section v-show="view === 'items'">
            <div class="kt-view-head">
              <div><h2>装备库</h2><p class="kt-sub">官方列表 p185-200（部分修正已标注 ⚠）</p></div>
            </div>
            <div class="kt-tabs">
              <button v-for="[k, label] in ITEM_TABS" :key="k" class="kt-tab" :class="{ 'is-on': itemTab === k }" @click="itemTab = k">{{ label }}</button>
            </div>
            <div v-for="t in items[itemTab]" :key="t.heading">
              <div v-if="items[itemTab].length > 1 || t.heading" class="kt-table-title">{{ t.heading }}</div>
              <div class="kt-table-wrap">
                <table class="kt-table">
                  <thead><tr><th v-for="h in t.headers" :key="h">{{ h }}</th><th v-if="t.rows.some(r => r.note)">备注</th></tr></thead>
                  <tbody>
                    <tr v-for="r in t.rows" :key="r.name + r.cells[1]">
                      <td v-for="(c, ci) in r.cells" :key="ci">{{ c }}</td>
                      <td v-if="t.rows.some(r2 => r2.note)">{{ r.note }}<div v-if="r.fixNote" class="kt-fixnote">⚠ {{ r.fixNote }}</div></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <!-- 陷阱 -->
          <section v-show="view === 'traps'">
            <div class="kt-view-head">
              <div><h2>陷阱与物体</h2><p class="kt-sub">七条陷阱效果已按原书 p294-295 逐条回填（修复旧版整列错置）</p></div>
            </div>
            <div class="kt-table-wrap">
              <table class="kt-table">
                <thead><tr><th>名称</th><th>类型</th><th>等级</th><th>探测</th><th>拆除</th><th>对象/射程</th><th>效果（已回填）</th></tr></thead>
                <tbody>
                  <tr v-for="t in traps" :key="t.name">
                    <td><strong>{{ t.cells[0] }}</strong></td><td>{{ t.cells[1] }}</td><td class="kt-num">{{ t.cells[3] }}</td>
                    <td class="kt-num">{{ t.cells[6] }}</td><td class="kt-num">{{ t.cells[7] }}</td><td>{{ t.cells[8] }}</td>
                    <td>{{ t.effect }}<div v-if="t.fixNote" class="kt-fixnote">⚠ {{ t.fixNote }}</div></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <!-- 作弊 -->
          <section v-show="view === 'cheats'">
            <div class="kt-view-head"><div><h2>作弊能力（Cheat）</h2><p class="kt-sub">创建角色时与 GM 商定 · 详见规则书阅读</p></div></div>
            <div class="kt-article" v-html="cheats.html"></div>
          </section>

<!-- 阅读视图：整章连续滚动 + 右侧常驻目录 -->
          <section v-show="view === 'reader'">
            <div class="kt-view-head">
              <div><h2>{{ headChapter.ch + ' · ' + headChapter.chTitle }}</h2><p class="kt-sub">连续阅读 · 已载入 {{ renderedSections.length }} 节 · 滚动到底自动载入下一章 · 当前：<strong>{{ curSecTitle || '—' }}</strong></p></div>
              <div class="kt-view-tools">
                <button class="kt-btn kt-toc-toggle" @click="tocOpen = true">☰ 目录</button>
                <button class="kt-pager" @click="gotoChapter(-1)" :disabled="anchorIdx <= 0">← 上一章</button>
                <button class="kt-pager" @click="gotoChapter(1)" :disabled="anchorIdx + renderedCount >= chapters.length">下一章 →</button>
              </div>
            </div>
            <div class="kt-reader-layout">
              <article class="kt-article kt-chapter">
                <template v-for="(c, ci) in renderedChapters" :key="c.ch + c.chTitle">
                  <h2 v-if="ci > 0 || anchorIdx > 0" class="kt-chapdiv">{{ c.ch }} · {{ c.chTitle }}</h2>
                  <div v-for="sec in c.sections" :key="sec.i" class="kt-sec" :id="'kt-sec-' + sec.i">
                    <h3 class="kt-sec-h">{{ sec.title }}</h3>
                    <div v-html="sec.html"></div>
                  </div>
                </template>
              </article>

              <aside class="kt-reader-aside" :class="{ open: tocOpen }" role="complementary" aria-label="章节目录">
                <div class="kt-aside-head">
                  <span>目录</span>
                  <button class="kt-btn kt-aside-close" @click="tocOpen = false">✕</button>
                </div>
                <div class="kt-aside-body">
                  <template v-for="c in chapters" :key="c.ch + c.chTitle">
                    <a class="kt-toc-ch" :class="{ 'is-cur': sameCh(headChapter, c) }" @click="pickCur(c)">{{ c.ch }} · {{ c.chTitle }}<span class="kt-toc-n">{{ c.sections.length }}节</span></a>
                    <template v-if="sameCh(headChapter, c)">
                      <a v-for="sec in c.sections" :key="sec.i" class="kt-toc-sec" :class="{ 'is-cur': curSec && curSec.i === sec.i }" @click="jumpSection(c, sec)">{{ sec.title }}</a>
                    </template>
                  </template>
                </div>
              </aside>
            </div>
            <div v-if="tocOpen" class="kt-toc-backdrop" @click.self="tocOpen = false"></div>
          </section>

          <!-- 角色创建助手 -->
          <section v-show="view === 'charcreate'">
            <div class="kt-view-head"><div><h2>角色创建助手</h2><p class="kt-sub">八步向导 · 遵循官方构筑顺序 · 完成后导出 A4 横版角色卡</p></div></div>
            <Wizard :ch="ch" :stats="stats" @finish="showPrint = true"/>
          </section>

<!-- 模组 -->
          <section v-show="view === 'mods'">
            <div class="kt-mod-series">
              <button class="kt-chip" :class="{ 'is-on': modSeries === 'all' }" @click="modSeries = 'all'">全部（{{ modsList.length }}）</button>
              <button v-for="sr in modSeriesList" :key="sr" class="kt-chip" :class="{ 'is-on': modSeries === sr }" @click="modSeries = sr">{{ sr }}</button>
            </div>
            <div class="kt-mod-cards">
              <button v-for="m in visibleMods" :key="m.id" class="kt-modcard" :class="{ 'is-on': curMod && curMod.id === m.id }" @click="curModId = m.id">
                <strong>{{ m.title }}</strong>
                <span class="kt-badge" :class="m.official ? 'kt-badge-green' : 'kt-badge-blue'">{{ m.official ? '官方模组' : '社区模组' }}</span>
                <span v-if="m.meta.series" class="kt-chip">{{ m.meta.series }}</span>
                <span>{{ m.meta.players }} · {{ m.meta.duration }}</span>
              </button>
              <button class="kt-modcard" @click="view = 'modtemplate'"><strong>＋ 新建模组</strong><span>复制 _template 目录即可</span></button>
              <div class="kt-modcard kt-modcard-dashed"><strong>预留模组位</strong><span>放入 src/data/mods/ 重新构建自动收录</span></div>
            </div>

            <template v-if="curMod">
              <div class="kt-view-head">
                <div>
                  <h3>{{ curMod.title }}</h3>
                  <div class="kt-meta-chips">
                    <span class="kt-badge" :class="curMod.official ? 'kt-badge-green' : 'kt-badge-blue'">{{ curMod.official ? '官方' : '自制' }}</span>
                    <span class="kt-chip">{{ curMod.meta.level }}</span>
                    <span class="kt-chip">{{ curMod.meta.players }}</span>
                    <span class="kt-chip">{{ curMod.meta.duration }}</span>
                    <span class="kt-chip">{{ curMod.meta.source }}</span>
                  </div>
                </div>
                <div class="kt-view-tools"><span class="kt-count">已完成 {{ stageDoneCount(curMod) }} / {{ curMod.stages.length }} 阶段</span></div>
              </div>
              <div v-if="curMod.pregen" class="kt-note kt-note-info"><strong>预读：</strong>{{ curMod.pregen }}</div>

              <div v-for="(st, i) in curMod.stages" :key="curMod.id + '-' + i" class="kt-stage">
                <button class="kt-stage-head" @click="toggleStageOpen(curMod.id, i)">
                  <span>{{ stageIsOpen(curMod.id, i) ? '▾' : '▸' }}</span>
                  <label class="kt-check kt-check-sm" @click.stop><input type="checkbox" :checked="stageDone(curMod.id, i)" @change="toggleStageDone(curMod.id, i)">{{ st.title }}</label>
                  <span class="kt-stage-dl">{{ st.tag }}</span>
                </button>
                <div v-show="stageIsOpen(curMod.id, i)" class="kt-stage-body">
                  <template v-for="(b, bi) in st.blocks" :key="bi">
                    <p v-if="b.type === 'text'">{{ b.text }}</p>
                    <div v-else-if="b.type === 'check'" class="kt-enc-check">{{ b.text }}</div>
                    <table v-else-if="b.type === 'table'" class="kt-table kt-xptable">
                      <thead><tr><th v-for="h in b.head" :key="h">{{ h }}</th></tr></thead>
                      <tbody><tr v-for="(r, ri) in b.rows" :key="ri"><td v-for="(c, ci) in r" :key="ci">{{ c }}</td></tr></tbody>
                    </table>
                    <div v-else-if="b.type === 'rule'" class="kt-ruleblock">
                      <div class="kt-ruleblock-title">📖 {{ b.title }}</div>
                      <div class="kt-ruleblock-text">{{ b.text }}</div>
                      <table v-if="b.table" class="kt-table kt-xptable">
                        <thead><tr><th v-for="h in b.table.head" :key="h">{{ h }}</th></tr></thead>
                        <tbody><tr v-for="(r, ri) in b.table.rows" :key="ri"><td v-for="(c, ci) in r" :key="ci">{{ c }}</td></tr></tbody>
                      </table>
                    </div>
                    <div v-else-if="b.type === 'encounter'" class="kt-encounter" @click="toggleEnc(curMod.id + '-' + i + '-' + bi, b)">
                      <strong>{{ encName(b) }} × {{ b.count }}</strong>
                      <span v-if="encMeta(b)">{{ encMeta(b) }}</span>
                      <span v-if="b.note" style="opacity:.8">{{ b.note }}</span>
                      <em>{{ b.enemyRef ? '在怪物库中查看 →' : '展开数据 ▾' }}</em>
                      <div v-if="encExpanded[curMod.id + '-' + i + '-' + bi] && b.monster" class="kt-enc-detail" @click.stop>
                        <div v-for="(skm, si) in curMod.monsters[b.monster].skills" :key="si">· {{ skm }}</div>
                        <div style="margin-top:4px"><b>战利品：</b>{{ curMod.monsters[b.monster].loot }}</div>
                        <div style="margin-top:4px;opacity:.75">{{ curMod.monsters[b.monster].abils }}</div>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </template>
          </section>

          <!-- 新建模组模板 -->
          <section v-show="view === 'modtemplate'">
            <div class="kt-view-head"><div><h2>新建模组（模板）</h2><p class="kt-sub">复制 _template 目录 → 填写 module.json → 重新构建，界面自动生成</p></div></div>
            <div class="kt-template-card">
              <pre><code>src/data/mods/my-module/
├── module.json      # 元数据：标题 / 推荐等级 / 人数 / 时长
├── stages.json      # 阶段：正文块 + encounters[]（引用 enemies.json 的 id）
├── npcs.json        # NPC 卡
└── handouts/        # 给玩家的地图与图片</code></pre>
            <p style="margin-top:8px">目录放入 <code>src/data/mods/</code> 后执行 <code>npm run build</code>，模组即被 <code>import.meta.glob</code> 自动发现并列出——无需改任何界面代码。</p>
              <div class="kt-gm-note">遭遇卡直接复用怪物卡组件：<code>{"enemyId":"berserk-bamboo-shoot","count":"1+1d3"}</code> ——数据单一出处，怪物库更新即全模组同步。</div>
            </div>
          </section>

        </main>
      </div>

      <footer class="kt-statusbar">
        <span>Vue 3 + Vite 单文件构建 · {{ manifest.source }}</span>
        <span class="kt-credit">
          内容翻译：<a href="https://space.bilibili.com/357358593" target="_blank" rel="noopener">B站 @黑白隔阂</a>
          · 非官方中文版 · 仅供学习交流，禁止商用
          · <a class="kt-license-link" @click="showAbout = true">版权与使用声明</a>
        </span>
        <span>已应用核对修正 {{ manifest.fixesApplied }} 处</span>
      </footer>
      <!-- 应用水印（不拦截点击） -->
      <div class="kt-wm" aria-hidden="true"></div>

      <!-- 技能详情（居中弹窗，点空白关闭） -->
      <div v-if="drawer" class="kt-skmodal-backdrop" @click.self="drawer = null">
        <div class="kt-skmodal" role="dialog" aria-label="技能详情">
          <div class="kt-skmodal-head">
            <div>
              <h3>{{ drawer.name }}</h3>
              <div v-if="drawer.nameEn" class="kt-en">{{ drawer.nameEn }}</div>
            </div>
            <button class="kt-btn" @click="drawer = null">✕</button>
          </div>
          <div id="kt-drawer-body">
            <span class="kt-badge" :class="srcBadge(drawer)[1]">{{ srcBadge(drawer)[0] }}</span>
            <dl class="kt-dl">
              <dt>分类</dt><dd>{{ drawer.cls }}（{{ KIND_LABEL[drawer.kind] || drawer.kind }}）</dd>
              <dt>时机</dt><dd>{{ drawer.timing || '—' }}</dd>
              <dt>判定</dt><dd>{{ drawer.check || '—' }}</dd>
              <dt>对象</dt><dd>{{ drawer.target || '—' }}</dd>
              <dt>射程</dt><dd>{{ drawer.range || '—' }}</dd>
              <dt>消耗</dt><dd>{{ fmtCost(drawer.cost) }}</dd>
              <dt>最大SL</dt><dd>{{ drawer.maxSL || '—' }}</dd>
              <template v-if="drawer.usage"><dt>使用条件</dt><dd>{{ drawer.usage }}</dd></template>
              <dt>参照</dt><dd>{{ drawer.ref || '—' }}</dd>
            </dl>
            <p style="font-size:13px">{{ drawer.effect }}</p>
            <div v-if="drawer.fixNote" class="kt-gm-note">修正记录：{{ drawer.fixNote }}</div>
            <div class="kt-rel"><button class="overlaybtn" @click="drawer = null">关闭</button></div>
          </div>
        </div>
      </div>

      <!-- 版权与使用声明 -->
      <div v-if="showAbout" class="kt-skmodal-backdrop" @click.self="showAbout = false">
        <div class="kt-skmodal" role="dialog" aria-label="版权与使用声明">
          <div class="kt-skmodal-head">
            <div><h3>版权与使用声明</h3><div class="kt-en">非官方 · 非盈利 · 仅供学习交流</div></div>
            <button class="kt-btn" @click="showAbout = false">✕</button>
          </div>
          <div class="kt-about">
            <p><b>本应用是什么</b>：《为美好的世界献上祝福！TRPG》的非官方中文规则书与车卡辅助工具，由中文 TRPG 爱好者自发制作，<b>不用于任何盈利目的</b>，仅供学习交流与中文 TRPG 社区跑团使用。</p>
            <p><b>内容翻译</b>：B站 <a href="https://space.bilibili.com/357358593" target="_blank" rel="noopener">@黑白隔阂</a>（space.bilibili.com/357358593）。原英文版来自 Yen Press 官方英译本。</p>
            <p><b>版权归属</b>：原作《この素晴らしい世界に祝福を！》© 晓夏目 / 三嶋くろね / KADOKAWA；TRPG 规则 © FAR EAST AMUSEMENT RESEARCH（F.E.A.R.）；英文版 © Yen Press。本汉化内容为粉丝翻译的衍生作品，版权归原权利人所有。</p>
            <p><b>使用限制</b>：禁止商业使用、禁止售卖；请勿用于任何盈利场景。若权利人认为本内容侵犯其权益，请联系我们，我们将立即移除相关内容。</p>
            <p><b>扩展内容</b>：AR2E（Arianrhod 2E）兼容同人技能与装备来自中文/英文社区整理（法术表.xlsx），作者标签 [Watson]、[Haru] 等已保留；相关权利归原作者所有。</p>
            <p><b>代码许可</b>：本项目代码以 MIT 协议开源；翻译文本不另行授权，仅供社区学习交流使用。</p>
          </div>
          <div class="kt-rel" style="margin-top:10px">
            <button class="kt-btn kt-btn-primary" @click="showAbout = false">知道了</button>
          </div>
        </div>
      </div>

      <!-- A4 角色卡打印 -->
      <SheetA4 v-if="showPrint" :ch="ch" :stats="stats"/>

      <!-- 全局搜索 -->
      <div v-if="searchOpen" class="kt-overlay kt-overlay-top" @click.self="searchOpen = false">
        <div class="kt-palette" role="dialog" aria-label="全局搜索">
          <div class="kt-palette-input"><span>🔍</span><input ref="searchInput" v-model="query" placeholder="驱散 / 圣盾 / 狮鹫 / 全力移动…" aria-label="搜索"><kbd>Esc</kbd></div>
          <div class="kt-palette-results" aria-live="polite">
            <template v-if="searchResults.length">
              <template v-for="(it, i) in searchResults" :key="i">
                <div v-if="i === 0 || searchResults[i - 1].g !== it.g" class="kt-sr-group">{{ it.g }}</div>
                <button class="kt-sr-item" @click="onSearchHit(it)">{{ it.t }}<span v-if="it.ref" class="kt-sr-meta">{{ it.ref }}</span></button>
              </template>
            </template>
            <div v-else class="kt-sr-empty">没有匹配结果</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
