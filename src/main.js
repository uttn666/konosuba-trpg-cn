import { createApp } from 'vue'
import App from './App.vue'
import './styles.css'

createApp(App).mount('#app')

// PWA 离线缓存（仅 http/https 环境，file:// 双击场景自动跳过）
if ('serviceWorker' in navigator && /^https?:$/.test(location.protocol)) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(() => {})
  })
}
