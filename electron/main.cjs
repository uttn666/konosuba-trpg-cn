// 素晴TRPG · 非官方中文规则书 — 桌面端入口（Electron）
// 非盈利 · 仅供学习交流 · 详见 NOTICE.md
const { app, BrowserWindow, shell, Menu } = require('electron')
const path = require('node:path')

const APP_FILE = path.join(__dirname, '..', 'dist', 'index.html')

function createWindow(hash) {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 960,
    minHeight: 620,
    backgroundColor: '#fdf6e3',
    title: '素晴TRPG · 非官方中文规则书',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  })
  win.setMenuBarVisibility(false)
  if (hash) win.loadFile(APP_FILE, { hash })
  else win.loadFile(APP_FILE)

  // 角色创建助手 → 新窗口；外部链接 → 系统浏览器
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.includes('#wizard')) { createWindow('wizard'); return { action: 'deny' } }
    if (/^https?:/i.test(url)) { shell.openExternal(url); return { action: 'deny' } }
    return { action: 'allow' }
  })
  win.webContents.on('will-navigate', (e, url) => {
    if (!url.startsWith('file://')) { e.preventDefault(); shell.openExternal(url) }
  })
  return win
}

app.whenReady().then(() => {
  Menu.setApplicationMenu(null)
  createWindow()
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow() })
})
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
