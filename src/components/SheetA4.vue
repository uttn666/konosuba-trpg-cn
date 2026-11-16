<script setup>
import { computed } from 'vue'
import { ABILS, ABIL_ZH, RACE_BASE, num, skillGroups } from '../character.js'

const props = defineProps({ ch: Object, stats: Object })

const credit = '非官方中文版 · 仅供学习交流，禁止商用 · 翻译：B站 @黑白隔阂 space.bilibili.com/357358593 · 原英文版来自 reddit.com/r/KonosubaTabletop 改良版 · 原作版权 © 晓夏目/三嶋くろね/KADOKAWA · TRPG © F.E.A.R.'

/* 装备行 → 卡面各行数据（字段已在选择时解析） */
function eqRow(slot) {
  const e = props.ch.equip[slot]
  if (!e) return { name: '', weight: '', hit: '', atk: '', dodge: '', pd: '', md: '', act: '', move: '', range: '', effect: '' }
  const f = e.f || {}
  return { name: e.name, weight: f.weight, hit: f.hit, atk: f.atk, dodge: f.dodge, pd: f.pd, md: f.md, act: f.act, move: f.move, range: f.range, effect: f.effect || '' }
}
const eqRows = computed(() => ({
  rightHand: eqRow('rightHand'), leftHand: eqRow('leftHand'), head: eqRow('head'),
  body: eqRow('body'), other: eqRow('other'), accessory: eqRow('accessory'),
}))
const eqSum = computed(() => {
  const rows = Object.values(eqRows.value)
  const sum = k => rows.reduce((a, r) => a + (num(r[k]) || 0), 0)
  return { weight: sum('weight'), hit: sum('hit'), atk: sum('atk'), dodge: sum('dodge'), pd: sum('pd'), md: sum('md'), act: sum('act'), move: sum('move') }
})
const eqHasMove = true

const st = computed(() => props.stats)
const clsMod = a => { const c = st.value.cls; return c && c[a] ? c[a] : '' }

/* 第2页技能表 */
const groups = computed(() => skillGroups(props.ch))
const TABLE_ROWS = 12
function pad(list) {
  const out = [...list]
  while (out.length < TABLE_ROWS) out.push(null)
  return out.slice(0, TABLE_ROWS)
}
function trunc(t, n) { const x = String(t || '').replace(/\s+/g, ' ').trim(); return x.length > n ? x.slice(0, n) + '…' : x }
const skillCols = s => s ? [s.sl ?? 1, s.timing || '', s.check || '', s.target || '', s.range || '', s.cost || '', s.maxSL || '', trunc(s.effect, 20), s.ref || ''] : null
</script>

<template>
  <div class="kt-printwrap">
    <div class="kt-printbar no-print">
      <button class="kt-btn kt-btn-primary" onclick="window.print()">🖨 打印 / 另存 PDF（A4 横向，边距：无）</button>
      <button class="kt-btn" onclick="this.dispatchEvent(new CustomEvent('kt-close-print', {bubbles:true}))">返回向导</button>
      <span class="kt-printtip">浏览器打印对话框中请选择：纸张 A4 · 方向 横向 · 边距 无 · 勾选“背景图形”</span>
    </div>

    <!-- 第 1 页 -->
    <div class="sheet">
      <div class="saw"></div>
      <div class="s-title">
        <span class="s-t1">为美好的世界献上祝福！</span><span class="s-t2">这个</span><span class="s-t3">角色</span><span class="s-t4">表</span>
        <span class="s-trpg">TRPG</span>
      </div>
      <div class="s-body">
        <!-- 左列 -->
        <div class="s-col">
          <div class="s-namebox">
            <div class="s-namemain">
              <label>角色名称</label>
              <input class="s-in s-in-name" v-model="ch.meta.name">
              <label>玩家名称</label>
              <input class="s-in" v-model="ch.meta.player">
            </div>
            <div class="s-nameside">
              <label>年龄<input class="s-in" v-model="ch.meta.age"></label>
              <label>性别<input class="s-in" v-model="ch.meta.gender"></label>
              <label>已用经验点数<input class="s-in" v-model="ch.meta.expUsed"></label>
            </div>
          </div>
          <div class="s-racecls">
            <div class="s-box s-grow"><label>种族</label><div class="s-val">{{ ch.race }}</div></div>
            <div class="s-box s-grow"><label>职业</label><div class="s-val">{{ ch.cls }}</div></div>
            <div class="s-box s-lv"><label>角色等级</label><div class="s-val">{{ ch.meta.level }}</div></div>
          </div>
          <table class="s-tab s-abil">
            <thead><tr><th></th><th>基础<br>能力值</th><th>能力值<br>加成</th><th>职业<br>等级</th><th>技能等</th><th>能力值等</th><th>技能等</th><th>检定<br>（骰子）</th></tr></thead>
            <tbody>
              <tr v-for="(a, i) in ABILS" :key="a" :class="'s-ar' + (i % 6)">
                <th class="s-ab">{{ ABIL_ZH[a] }}</th>
                <td class="s-fill">{{ st.final[a] }}</td>
                <td class="s-fill">{{ st.bonus[a] }}</td>
                <td class="s-fill">{{ clsMod(a) }}</td>
                <td class="s-fill"></td>
                <td class="s-fill"></td>
                <td class="s-fill"></td>
                <td class="s-dice">(2d6)</td>
              </tr>
            </tbody>
          </table>
          <table class="s-tab s-equip">
            <thead><tr><th style="width:52px"></th><th>名称</th><th>重量</th><th>命中<br>修正</th><th>攻击<br>力</th><th>闪避<br>修正</th><th>物理<br>防御</th><th>魔法<br>防御</th><th>行动<br>修正</th><th>移动<br>修正</th><th>射程</th><th>效果</th></tr></thead>
            <tbody>
              <tr v-for="[slot, label] in [['rightHand','右手:'],['leftHand','左手:'],['head','头部:'],['body','身体:'],['other','其他防具:'],['accessory','饰品:']]" :key="slot">
                <th class="s-ab">{{ label }}</th>
                <td class="s-fill s-name">{{ eqRows[slot].name }}</td>
                <td class="s-fill kt-num">{{ eqRows[slot].weight }}</td>
                <td class="s-fill kt-num">{{ eqRows[slot].hit }}</td>
                <td class="s-fill kt-num">{{ eqRows[slot].atk }}</td>
                <td class="s-fill kt-num">{{ eqRows[slot].dodge }}</td>
                <td class="s-fill kt-num">{{ eqRows[slot].pd }}</td>
                <td class="s-fill kt-num">{{ eqRows[slot].md }}</td>
                <td class="s-fill kt-num">{{ eqRows[slot].act }}</td>
                <td class="s-fill kt-num">{{ eqRows[slot].move }}</td>
                <td class="s-fill">{{ eqRows[slot].range }}</td>
                <td class="s-fill s-fx">{{ eqRows[slot].effect }}</td>
              </tr>
              <tr class="s-sumrow">
                <th class="s-ab">合计:</th>
                <td></td>
                <td class="kt-num">{{ eqSum.weight }}</td>
                <td class="kt-num">{{ eqSum.hit }}</td>
                <td class="kt-num">{{ eqSum.atk }}</td>
                <td class="kt-num">{{ eqSum.dodge }}</td>
                <td class="kt-num">{{ eqSum.pd }}</td>
                <td class="kt-num">{{ eqSum.md }}</td>
                <td class="kt-num">{{ eqSum.act }}</td>
                <td class="kt-num">{{ eqSum.move }}</td>
                <td colspan="2"></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 右列 -->
        <div class="s-col">
          <div class="s-look">
            <div class="s-look-art">角色外观（角色插画等）</div>
            <div class="s-look-grid">
              <label>身高<input class="s-in" v-model="ch.appearance.height"></label>
              <label>发色<input class="s-in" v-model="ch.appearance.hair"></label>
              <label>眼色<input class="s-in" v-model="ch.appearance.eyes"></label>
              <label>发型<input class="s-in" v-model="ch.appearance.hairstyle"></label>
              <label>肤色<input class="s-in" v-model="ch.appearance.skin"></label>
            </div>
          </div>
          <table class="s-tab s-combat">
            <thead><tr><th style="width:110px">战斗判定</th><th>基础值</th><th>装备</th><th>技能/其他</th><th>骰子总数</th></tr></thead>
            <tbody>
              <tr><th class="s-ab">命中检查（灵巧）</th><td class="s-fill kt-num">{{ st.ab.DEX }}</td><td class="s-fill kt-num">{{ st.em.hit }}</td><td class="s-fill kt-num">{{ ch.manual.hit }}</td><td class="s-dice">(2d6+{{ st.hit }})</td></tr>
              <tr><th class="s-ab">攻击力</th><td class="s-fill"></td><td class="s-fill kt-num">{{ st.em.atk }}</td><td class="s-fill"></td><td class="s-dice">{{ st.atk }}</td></tr>
              <tr><th class="s-ab">闪避检查（敏捷）</th><td class="s-fill kt-num">{{ st.ab.AGI }}</td><td class="s-fill kt-num">{{ st.em.dodge }}</td><td class="s-fill kt-num">{{ ch.manual.dodge }}</td><td class="s-dice">(2d6+{{ st.dodge }})</td></tr>
              <tr><th class="s-ab">物理防御</th><td class="s-fill"></td><td class="s-fill kt-num">{{ st.em.pd }}</td><td class="s-fill kt-num">{{ ch.manual.pd }}</td><td class="s-dice">{{ st.pd }}</td></tr>
              <tr><th class="s-ab">魔法防御（感知）</th><td class="s-fill"></td><td class="s-fill kt-num">{{ st.em.md }}</td><td class="s-fill kt-num">{{ ch.manual.md }}</td><td class="s-dice">{{ st.md }}</td></tr>
              <tr><th class="s-ab">行动点数（敏捷+感知）</th><td class="s-fill kt-num">{{ st.ab.AGI }}+{{ st.ab.PER }}</td><td class="s-fill kt-num">{{ st.em.act }}</td><td class="s-fill kt-num">{{ ch.manual.act }}</td><td class="s-dice">{{ st.act }}</td></tr>
              <tr><th class="s-ab">移动力（力量+5）</th><td class="s-fill kt-num">{{ st.ab.STR }}+5</td><td class="s-fill kt-num">{{ st.em.move }}</td><td class="s-fill kt-num">{{ ch.manual.move }}</td><td class="s-dice">{{ st.move }}</td></tr>
            </tbody>
          </table>
          <table class="s-tab s-special">
            <thead><tr><th style="width:110px">特殊检定</th><th>基础值</th><th>技能</th><th>其他</th><th>骰子总数</th></tr></thead>
            <tbody>
              <tr v-for="[label, a] in [['侦测陷阱（感知）','PER'],['解除陷阱（灵巧）','DEX'],['感知威胁（感知）','PER'],['辨识敌人（智力）','INT'],['魔法检定（智力）','INT']]" :key="label">
                <th class="s-ab">{{ label }}</th><td class="s-fill kt-num">{{ st.ab[a] }}</td><td class="s-fill"></td><td class="s-fill"></td><td class="s-dice">(2d6+{{ st.bonus[a] }})</td>
              </tr>
            </tbody>
          </table>
          <div class="s-items">
            <div class="s-items-col" v-for="half in 2" :key="half">
              <div class="s-itemrow s-itemhead"><span>所持物品</span><span>重量</span></div>
              <div class="s-itemrow" v-for="i in 3" :key="i">
                <input class="s-in" v-model="ch.items[(half - 1) * 3 + i - 1]"><span class="s-w">(　)</span>
              </div>
            </div>
            <div class="s-items-foot">
              <span>可携带重量: <b class="kt-num">{{ st.final.STR }}</b></span>
              <span>金钱 <b class="kt-num">{{ ch.money }}</b> KE</span>
            </div>
          </div>
          <div class="s-vitals">
            <div class="s-vit s-vit-hp"><label>生命值 <small>最大 / 当前</small></label><b>{{ st.hpMax ?? '—' }}</b><input class="s-in" v-model="ch.hpCur"></div>
            <div class="s-vit s-vit-mp"><label>魔力值 <small>最大 / 当前</small></label><b>{{ st.mpMax ?? '—' }}</b><input class="s-in" v-model="ch.mpCur"></div>
            <div class="s-vit s-vit-bl"><label>祝福值 <small>使用次数: {{ ch.blessingUses }}</small></label><input class="s-in" v-model="ch.blessing"></div>
          </div>
          <div class="s-two">
            <div class="s-box s-lifepath">
              <label class="s-h">人生轨迹</label>
              <div class="s-lp"><label>出身</label><span class="s-val">{{ ch.lifepath.origin }}</span></div>
              <div class="s-lp"><label>境遇</label><span class="s-val">{{ ch.lifepath.circum }}</span></div>
              <div class="s-lp"><label>目标</label><span class="s-val">{{ ch.lifepath.goal }}</span></div>
            </div>
            <div class="s-box s-cheat">
              <label class="s-h">作弊（开挂）</label>
              <div class="s-lp"><label>{{ ch.cheat.name || '名称' }}</label></div>
              <div class="s-lp s-cheatfx"><span class="s-val">{{ ch.cheat.effect }}</span></div>
            </div>
            <div class="s-box s-life">
              <label class="s-h">生活方式</label>
              <div class="s-lp"><span class="s-val">{{ ch.lifestyle }}</span></div>
            </div>
          </div>
        </div>
      </div>
      <div class="s-wm">仅供学习交流 · 非官方中文版 · 翻译：B站 @黑白隔阂</div>
      <div class="s-credit">{{ credit }}</div>
    </div>

    <!-- 第 2 页：4 张技能表 -->
    <div class="sheet">
      <div class="saw"></div>
      <div class="s-p2">
        <div v-for="g in [
          ['s-blue', '技能（种族）', groups.racial],
          ['s-blue', '技能（职业）', groups.cls],
          ['s-orange', '技能（通用）', groups.general],
          ['s-green', '技能（法术与其他）', groups.other],
        ]" :key="g[1]" class="s-skillbox" :class="g[0]">
          <table class="s-tab s-skilltab">
            <colgroup><col class="c-name"><col class="c-sl"><col class="c-tm"><col class="c-ck"><col class="c-tg"><col class="c-rg"><col class="c-ct"><col class="c-mx"><col class="c-fx"><col class="c-rf"></colgroup>
            <thead><tr><th class="s-skh">技能</th><th>等级</th><th>时机</th><th>检定</th><th>目标</th><th>范围</th><th>消耗</th><th>最大<br>SL</th><th>效果</th><th>页码<br>参考</th></tr></thead>
            <tbody>
              <tr v-for="(s, i) in pad(g[2])" :key="i">
                <th class="s-ab s-skn">{{ s ? s.name : '' }}</th>
                <template v-if="s"><td v-for="(v, vi) in skillCols(s)" :key="vi" class="s-fill" :class="{ 'kt-num': vi === 0 }">{{ v }}</td></template>
                <template v-else><td v-for="vi in 9" :key="vi" class="s-fill"></td></template>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="s-wm">仅供学习交流 · 非官方中文版 · 翻译：B站 @黑白隔阂</div>
      <div class="s-credit">{{ credit }}</div>
    </div>
  </div>
</template>

<style>
/* ===== A4 横版角色卡（复刻用户现卡版式） ===== */
.kt-printwrap{position:fixed; inset:0; z-index:60; background:rgba(7,54,66,.6); overflow:auto; padding:16px;}
.kt-printbar{position:sticky; top:0; z-index:5; display:flex; gap:10px; align-items:center; padding:9px 12px; margin-bottom:12px; border-radius:10px; background:#fffdf6; box-shadow:0 2px 10px rgba(0,0,0,.25);}
.kt-printbar .kt-printtip{font-size:12px; color:#657b83;}
.sheet{width:297mm; height:210mm; margin:0 auto 8mm; background:#fff; box-shadow:0 4px 24px rgba(0,0,0,.4); padding:2.5mm 5mm; position:relative; display:flex; flex-direction:column; font-family:"Segoe UI","Microsoft YaHei",sans-serif; color:#444;}
.saw{height:3.6mm; flex:none; background:repeating-linear-gradient(135deg,#8a6d3b 0 4mm,#c9a86a 4mm 8mm); -webkit-mask:conic-gradient(from 135deg at 50% 100%, #0000 90deg, #000 0) 50%/6mm 100%; mask:conic-gradient(from 135deg at 50% 100%, #0000 90deg, #000 0) 50%/6mm 100%;}
.s-title{margin:1.2mm 0 1mm; line-height:1; white-space:nowrap;}
.s-t1{font-size:22px; font-weight:700; color:#e91e8c;}
.s-t2{font-size:20px; font-weight:700; color:#333; margin-left:4px;}
.s-t3{font-size:22px; font-weight:700; color:#1e88e5;}
.s-t4{font-size:22px; font-weight:700; color:#333;}
.s-trpg{display:inline-block; margin-left:8px; padding:1px 9px 2px; background:#1e88e5; color:#fff; font-weight:700; font-size:18px; border-radius:6px 6px 6px 0; transform:rotate(-3deg);}
.s-body{flex:1; min-height:0; display:grid; grid-template-columns:47.5% 1fr; gap:2.2mm;}
.s-col{display:flex; flex-direction:column; gap:0.9mm; min-height:0; overflow:hidden;}
.s-in{border:none; border-bottom:1px solid #bbb; background:transparent; font:inherit; font-size:11px; color:#333; width:100%; padding:0 1px;}
.s-box{border:2px solid #c9a86a; border-radius:3px; padding:0.6mm 2mm 1mm;}
.s-box label{font-size:10px; color:#8a6d3b; font-weight:600;}
.s-val{font-size:12px; color:#333; min-height:5mm;}
.s-namebox{display:flex; gap:2mm; border:2px solid #c9a86a; border-radius:3px; padding:1mm 2mm;}
.s-namemain{flex:1.4; display:flex; flex-direction:column; gap:1.6mm;}
.s-namemain label{font-size:10px; color:#8a6d3b; font-weight:600;}
.s-in-name{font-size:15px; font-weight:600;}
.s-nameside{flex:1; display:flex; flex-direction:column; gap:1.2mm; border-left:1px dashed #c9a86a; padding-left:2mm;}
.s-nameside label{display:flex; align-items:baseline; gap:2px; font-size:10px; color:#8a6d3b; font-weight:600;}
.s-racecls{display:flex; gap:2mm;}
.s-grow{flex:1;} .s-lv{width:22mm;}
.s-tab{width:100%; border-collapse:collapse; font-size:10px; table-layout:fixed;}
.s-tab th,.s-tab td{border:1.5px solid #999; padding:0.8mm 1mm; text-align:center; vertical-align:middle;}
.s-tab th{background:#f5efdf; color:#555; font-weight:600;}
.s-ab{font-weight:600; color:#333; background:#faf6ea;}
.s-fill{min-height:5mm; height:5mm;}
.s-dice{color:#666; white-space:nowrap;}
.s-abil th.s-ab{color:#c62828;}
.s-ar0 th.s-ab{color:#c62828;} .s-ar1 th.s-ab{color:#e67e22;} .s-ar2 th.s-ab{color:#27ae60;}
.s-ar3 th.s-ab{color:#2980b9;} .s-ar4 th.s-ab{color:#8e44ad;} .s-ar5 th.s-ab{color:#d81b60;}
.s-abil td{height:4mm;}
.s-equip td{height:3.5mm; font-size:9px;}
.s-equip .s-name{text-align:left;}
.s-equip .s-fx{text-align:left; font-size:8.5px;}
.s-sumrow td,.s-sumrow th{background:#faf6ea; font-weight:600;}
.s-look{border:2px solid #c9a86a; border-radius:3px; padding:0.8mm 2mm 1.2mm;}
.s-look-art{height:9mm; border:1px dashed #c9a86a; border-radius:3px; display:flex; align-items:center; justify-content:center; color:#c0b090; font-size:11px; margin-bottom:1mm;}
.s-look-grid{display:grid; grid-template-columns:1fr 1fr; gap:0.6mm 3mm;}
.s-look-grid label{display:flex; align-items:baseline; gap:3px; font-size:10px; color:#8a6d3b; font-weight:600;}
.s-combat th.s-ab{text-align:left; color:#c62828;}
.s-combat th{background:#fdeceb; border-color:#c62828;}
.s-combat td{border-color:#c62828; color:#c62828;}
.s-combat td,.s-special td{height:3.2mm; font-size:9px;}
.s-combat .s-dice{font-weight:600;}
.s-special th{background:#fdf1e0; border-color:#e67e22;}
.s-special td{border-color:#e67e22; color:#b35418;}
.s-special th.s-ab{text-align:left; color:#b35418;}
.s-items{display:grid; grid-template-columns:1fr 1fr; gap:1.2mm; border:2px solid #e0a800; border-radius:3px; padding:0.8mm 2mm 1mm;}
.s-itemrow{display:flex; align-items:baseline; gap:1.5mm; height:3.4mm; border-bottom:1px solid #e0c98a;}
.s-itemhead{font-weight:600; color:#8a6d3b; font-size:10px; border-bottom:1.5px solid #e0a800;}
.s-items-foot{grid-column:1 / -1; display:flex; justify-content:space-between; font-size:10px; color:#8a6d3b; font-weight:600; padding-top:0.8mm;}
.s-vitals{display:grid; grid-template-columns:1fr 1fr 1fr; gap:2mm;}
.s-vit{border-radius:3px; padding:0.4mm 2mm 0.8mm; border:2px solid;}
.s-vit label{font-size:10px; font-weight:700; display:block;}
.s-vit small{font-weight:400; opacity:.7;}
.s-vit b{font-size:12px;}
.s-vit .s-in{width:40%;}
.s-vit-hp{border-color:#e91e8c; color:#e91e8c;}
.s-vit-mp{border-color:#1e88e5; color:#1e88e5;}
.s-vit-bl{border-color:#c62828; color:#c62828;}
.s-two{display:grid; grid-template-columns:1.2fr 1.2fr 1fr; gap:1.6mm;}
.s-lifepath{border-color:#27ae60;} .s-lifepath .s-h,.s-lifepath label{color:#27ae60;}
.s-cheat{border-color:#8e44ad;} .s-cheat .s-h,.s-cheat label{color:#8e44ad;}
.s-h{font-size:12px; font-weight:700; display:block; margin-bottom:0.5mm;}
.s-lp{margin-bottom:0.4mm; font-size:9.5px; display:flex; gap:2px; align-items:baseline;}
.s-lp label{display:inline; flex:none;}
.s-lp .s-val{display:inline; min-height:0;} .s-lp label{font-size:9.5px; font-weight:600;}
.s-cheatfx .s-val{font-size:9px;}
.s-life{border-color:#27ae60;} .s-life .s-h{color:#27ae60;}
.s-credit{flex:none; padding-top:0.5mm; font-size:7.5px; color:#999; text-align:center; white-space:nowrap; overflow:hidden;}
.s-wm{position:absolute; inset:0; pointer-events:none; display:flex; align-items:center; justify-content:center; z-index:3; overflow:hidden;}
.s-wm::before{content:""; display:block; width:180%; height:200%; background-repeat:repeat; opacity:.075;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='420' height='220'><text x='210' y='110' font-size='15' fill='%23073642' font-family='sans-serif' text-anchor='middle' transform='rotate(-24 210 110)'>仅供学习交流 · 非官方中文版 · 翻译 B站@黑白隔阂</text></svg>");
  transform:rotate(0deg);}
.s-p2{flex:1; min-height:0; display:grid; grid-template-columns:1fr 1fr; grid-template-rows:1fr 1fr; gap:2.5mm;}
.s-skillbox{border:2px solid; border-radius:3px; padding:1.5mm; min-height:0; overflow:hidden;}
.s-blue{border-color:#1e88e5;} .s-blue .s-skh{color:#1e88e5;}
.s-orange{border-color:#e67e22;} .s-orange .s-skh{color:#e67e22;}
.s-green{border-color:#27ae60;} .s-green .s-skh{color:#27ae60;}
.s-skilltab{height:100%;}
.s-skilltab th{border-color:inherit;}
.s-skilltab td{border-color:inherit;}
.s-blue th{background:#e8f2fd; border-color:#1e88e5;} .s-blue td{border-color:#9dc9f0;}
.s-orange th{background:#fdf1e0; border-color:#e67e22;} .s-orange td{border-color:#f0b27a;}
.s-green th{background:#e9f7ee; border-color:#27ae60;} .s-green td{border-color:#93d8a8;}
.s-skilltab td{height:6.2mm; font-size:9px; text-align:left; padding:0.5mm 1mm;}
.s-skilltab th{font-size:9.5px; padding:0.5mm 1mm;}
.s-skn{text-align:left; font-size:9.5px;}

/* 技能表：固定列宽、单行省略，防止内容破坏布局 */
.s-skilltab{table-layout:fixed;}
.s-skilltab th,.s-skilltab td{white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.s-skilltab col.c-name{width:18%;} .s-skilltab col.c-sl{width:6%;} .s-skilltab col.c-tm{width:10%;}
.s-skilltab col.c-ck{width:9%;} .s-skilltab col.c-tg{width:9%;} .s-skilltab col.c-rg{width:6%;}
.s-skilltab col.c-ct{width:6%;} .s-skilltab col.c-mx{width:6%;} .s-skilltab col.c-fx{width:24%;} .s-skilltab col.c-rf{width:6%;}
.s-skilltab tbody tr{height:6.4mm;}
/* 装备表效果列同样限制为单行 */
.s-equip td{white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}

/* 斑马纹：便于阅读（打印保留） */
.s-tab tbody tr:nth-child(even) > td{background:#f4f1e8;}
.s-tab tbody tr:nth-child(even) > th.s-ab{background:#f0ecdf;}
.s-skilltab tbody tr:nth-child(even) > td{background:#f7f7f2;}
.s-skilltab tbody tr:nth-child(even) > th.s-ab{background:#faf9f4;}
@media print{ .sheet{-webkit-print-color-adjust:exact; print-color-adjust:exact;} }

/* ===== 打印 ===== */
@page{size:A4 landscape; margin:0;}
@media print{
  #kt-app{position:static !important; background:#fff !important;}
  #kt-app > .kt-window{display:none !important;}
  .kt-printwrap{position:static !important; background:#fff !important; padding:0 !important; overflow:visible !important;}
  .no-print{display:none !important;}
  .sheet{box-shadow:none !important; margin:0 !important; page-break-after:always;}
  .sheet:last-child{page-break-after:auto;}
}
</style>
