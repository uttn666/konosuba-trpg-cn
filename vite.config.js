import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { viteSingleFile } from 'vite-plugin-singlefile'

// 构建产物为单个 dist/index.html，可双击直接打开（file://）
export default defineConfig({
  base: './',
  plugins: [vue(), viteSingleFile()],
  build: {
    // 单文件模式下禁用代码分割，图片等资源放 public/ 相对引用
    assetsInlineLimit: 100000000,
    chunkSizeWarningLimit: 100000000,
    cssCodeSplit: false,
    outDir: 'dist',
    emptyOutDir: true
  }
})
