<script setup>
import { computed } from 'vue'

const props = defineProps({ text: { type: String, default: '' } })

// 把模组正文拆成可读块：标题 / 列表 / NPC 台词 / GM 备注 / 普通段落
function parse(raw) {
  const lines = String(raw || '').replace(/\r/g, '').split('\n').map(s => s.trim()).filter(Boolean)
  const out = []
  for (const line of lines) {
    if (/^【.+?】/.test(line) && line.length < 32) {
      out.push({ kind: 'head', text: line })
    } else if (/^[·•]\s*/.test(line)) {
      out.push({ kind: 'li', text: line.replace(/^[·•]\s*/, '') })
    } else if (/^[①②③④⑤⑥⑦⑧⑨⑩]/.test(line)) {
      out.push({ kind: 'num', text: line })
    } else if (/^\d+[.、)]\s*/.test(line)) {
      out.push({ kind: 'num', text: line })
    } else if (/^[「『]/.test(line)) {
      out.push({ kind: 'quote', text: line })
    } else if (/^[（(]/.test(line)) {
      out.push({ kind: 'note', text: line })
    } else if (/^(场景|第[一二三四五六七八九十0-9]+[章节幕]|开场|中盘|高潮|结局|序章|终章|尾声|Part|Scene)\b/i.test(line) && line.length < 30) {
      out.push({ kind: 'head', text: line })
    } else {
      out.push({ kind: 'p', text: line })
    }
  }
  return out
}

function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

// 自动标注判定难度与骰子表达式，方便 DM 扫读
function rich(s) {
  let h = esc(s)
  h = h.replace(/(DC|DL)\s*:?\s*(\d+)/g, '<span class="kt-dc">$1$2</span>')
  h = h.replace(/\b(\d+)[dD](\d+)((?:[+-]\d+)?)/g, '<span class="kt-dice">$1d$2$3</span>')
  return h
}

const blocks = computed(() => parse(props.text).map(b => ({ ...b, html: rich(b.text) })))
</script>

<template>
  <div class="kt-modtext">
    <template v-for="(b, i) in blocks" :key="i">
      <h4 v-if="b.kind === 'head'" class="kt-modtext-head">{{ b.text }}</h4>
      <p v-else-if="b.kind === 'quote'" class="kt-modquote" v-html="b.html"></p>
      <p v-else-if="b.kind === 'note'" class="kt-modnote" v-html="b.html"></p>
      <p v-else-if="b.kind === 'li'" class="kt-modli" v-html="b.html"></p>
      <p v-else-if="b.kind === 'num'" class="kt-modnum" v-html="b.html"></p>
      <p v-else v-html="b.html"></p>
    </template>
  </div>
</template>
