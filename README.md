# 为美好的世界献上祝福！TRPG · 非官方中文规则书与车卡工具

> ⚠️ **本项目为非官方粉丝汉化，仅供学习交流与中文 TRPG 社区非盈利使用，禁止任何形式的商业使用。**
> 原作及规则版权归原权利人所有（详见下方「版权与免责声明」）。如权利人认为本内容侵权，请联系删除，我们将立即配合。

一个把《为美好的世界献上祝福！TRPG》规则书汉化内容与跑团工具整合在一起的**单文件应用**：阅读、查询、车卡、模组一站式，双击 `dist/index.html` 即可离线使用。

**内容翻译：B站 [@黑白隔阂](https://space.bilibili.com/357358593)**（space.bilibili.com/357358593）

---

## 功能

- 📖 **规则书阅读**：116 节全文、跨章连续滚动、抽屉目录、全文搜索高亮（居中弹窗）
- 📚 **技能库**：官方技能 + AR2E 扩展统一检索；分类单选（种族/职业/上位职业/通用/法术/被动）、来源徽章（官方/AR2E）、上位职业互通基础职业技能（依据转职规则）、页码参照
- ⚔️ **装备库 / 👹 怪物卡 / ⚠️ 陷阱 / 🎯 作弊能力**：分类浏览、数值表、GM 信息
- 🎲 **角色创建助手**（独立标签页）：
  - 八步向导，遵循官方构筑顺序（先技能后属性、创建上限 13）
  - 种族/职业/生命轨迹（d66 掷骰）/技能卡片（含 AR2E）/属性自动计算/装备选择（带数值与价格）/导出
  - 实时数值条、技能上限拦截、资金与负重校验、规则检查清单
- 🖨 **A4 横版角色卡导出**：两页版式（复刻社区改良版中文角色卡），打印或另存 PDF
- 📜 **模组系统**：内置官方模组「给这些竹笋的美味！」；放入 `src/data/mods/<slug>/module.json` 重新构建即可收录新模组
- 🌓 亮/暗主题 · 🖥 单文件离线运行 · 数据本地保存
- 📱 手机/平板适配（抽屉式导航与目录、触屏优化）· 🖥 Windows 桌面程序（Electron）· 📲 安卓（Capacitor / PWA）· 阅读目录右侧常驻

## 使用

### 桌面程序（Windows）

- 下载 Releases 中的 `KonosubaTRPG-CN-*-portable.exe`，双击即用（免安装，离线可用）
- 或自行构建：`npm install && npm run build:win`（产物在 `release/`；也可 `npm run desktop` 直接运行开发版）
- 说明：便携版由 Electron 打包；未做代码签名与 exe 资源编辑（需 Windows 开发者模式权限），exe 图标为默认图标，不影响使用

### 安卓（手机 / 平板）

- **方式一（推荐）**：下载 Releases 中的 APK 安装（需允许安装未知来源应用）
- **方式二（PWA，免安装）**：把 `dist/` 部署到任意静态服务器（或把 `docs/pages-workflow.example.yml` 复制到 `.github/workflows/pages.yml` 即可启用 GitHub Pages 自动部署（需 workflow 权限）），手机 Chrome 打开后菜单中选择「添加到主屏幕」，即可以类 App 方式离线使用
- **方式三（自行构建）**：安装 Android Studio（含 SDK），然后：
  ```bash
  npm install
  npm run build                 # 生成 dist
  npx cap copy android          # 同步 Web 资源
  # 用 Android Studio 打开 android/ 目录直接运行/打包
  # 或命令行：cd android && ./gradlew assembleDebug
  ```
  产物：`android/app/build/outputs/apk/debug/app-debug.apk`

### 浏览器 / 直接使用

下载 `dist/index.html`，双击打开即可（Chrome / Edge 等现代浏览器，离线可用）。

### 开发 / 构建

```bash
npm install
npm run dev      # 开发预览
npm run build    # 构建单文件 → dist/index.html
npm run data     # 重新生成 src/data（需要 Python，读取 scripts/sources/）
```

数据管道：`scripts/build_data.py` 把 `scripts/sources/`（旧版翻译 HTML 的结构化节 + 社区技能表 xlsx 导出）生成 `src/data/*.json`；所有已核对的修正记录在 `scripts/fix_log.json`（可审计）。

## 内容与来源

| 内容 | 来源 |
|---|---|
| 规则书正文 / 技能 / 装备 / 怪物 / 陷阱 / 模组 | 官方英文版规则书（Yen Press）中文翻译，经两轮逐条核对与修正 |
| 内容翻译 | B站 [@黑白隔阂](https://space.bilibili.com/357358593) |
| A4 角色卡版式 | 原英文版来自 [reddit r/KonosubaTabletop 改良自动计算角色卡](https://www.reddit.com/r/KonosubaTabletop/comments/w5z1bu/)，中文版由 B站 @黑白隔阂 制作 |
| AR2E 兼容扩展技能/装备 | 社区整理表（法术表.xlsx），作者标签 `[Watson]` `[Haru]` 等已保留 |

> 说明：仓库**不包含**官方原书 PDF 与书内插图（`public/img/` 已在 `.gitignore` 中排除），如需图片请自行从合法渠道获取。

## 版权与免责声明

- 原作《この素晴らしい世界に祝福を！》© 晓夏目 / 三嶋くろね / KADOKAWA
- TRPG 规则 © FAR EAST AMUSEMENT RESEARCH（F.E.A.R.）；英文版 © Yen Press
- 本项目为粉丝翻译的**衍生作品**，**非官方**、**非盈利**，仅供中文 TRPG 社区学习交流与跑团使用
- **禁止**：商业使用、售卖、付费墙转载、任何盈利性使用
- 翻译文本**不另行授权**（不适用本仓库的代码协议），版权归原权利人所有
- 若权利人认为本内容侵犯其权益，请通过 Issue 或仓库 owner 联系，我们将立即移除相关内容

## 许可

- **代码**（构建脚本、界面代码、数据管道）：[MIT](./LICENSE)。MIT 仅覆盖代码，不覆盖翻译文本与规则数据
- **翻译文本与规则数据**：见 [NOTICE.md](./NOTICE.md)，仅供学习交流，不随代码许可授权

## 致谢

- 原译者与中文社区整理者
- [Arianrhod 2E 兼容扩展](https://example.invalid) 的社区作者（Watson、Haru 等）
- 所有参与核对、勘误与反馈的跑团玩家

*本项目与 KADOKAWA、F.E.A.R.、Yen Press 均无关联。*
