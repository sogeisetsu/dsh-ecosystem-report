# AGENTS.md

给后续 AI agent 的项目说明。改这份报告之前先读完本文。

## 1. 项目是什么

- 交付物：单文件 HTML 调研报告 `deepseek-harness-npm-report.html`（约 400 KB，无外部 CDN、无图片、无字体请求）。
- 主题：npm `@deepseek-ai` 作用域（DeepSeek Harness / dsh）的官方包分类，加第三方社区插件选型。
- **报告是生成物，不要手改 HTML**。改 `research/pkg/build_v2.py`，再重新生成。

## 2. 目录

```
deepseek-harness-npm-report.html   交付件（生成物，勿手改）
AGENTS.md                          本文件
research/
  rows.json                        422 个官方包的分类数据（build_v2.py 的数据源）
  report.html                      build_v2.py 的输出，交付件的副本
  pkg/
    build_v2.py                    唯一的报告生成脚本（约 1,350 行）
    *.py                           历史抓取/分析脚本，多数一次性，勿当依赖
    dsh-*/package/                 解包后的官方包（cordis.patch.yml、README、lib）
  *.md / *.json / *.ts             抓取的文档、元数据、源码
.workbuddy/                        客户端数据，绝对不要动
```

## 3. 构建

```bash
cd research/pkg
python build_v2.py                                  # 生成 ../report.html
cp ../report.html ../../deepseek-harness-npm-report.html
```

- 脚本用相对路径 `../rows.json`、`../report.html`，必须在 `research/pkg` 下执行。
- 生成后必须校验：`research/report.html` 与根目录交付件**逐字节一致**。

## 4. 报告结构（6 个分节）

1. 概览：结论摘要、判定路径与状态定义、Profile 模板、Agent 预设
2. 默认安装清单：状态明细
3. 全量分类：分类方法、包清单与筛选
4. 安装建议：建议的形成方式、一、官方包建议、执行顺序、二、社区包补充建议
5. 社区与推荐：社区包精选（68 行，可按场景筛选）、包名对照、生态规模参考
6. 方法与局限：数据来源、未核实项、已知限制

**默认不新增章节**：只在现有分节/卡片内补内容，不加 `<section>`、目录项或新卡片。用户明确要求时除外。

## 5. 核心口径（改数据时保持自洽）

- 422 总数 = 308 落盘 + 114 未落盘；308 = 205 已激活 + 103 随包未启用。
- 状态代码：`1a` 组合层 / `1b` 运行时 / `1c` 预设 / `2a` 可选 bundle / `2b` 库或内部件 / `2c` 仅其他预设或入口 / `3a` 官方按需 / `3b` 官方可选未随包 / `3c` 无官方入口 / `—` 已下架。
- 官方包与社区包严格分节；社区包不计入 422。

## 6. build_v2.py 关键结构

| 名称 | 作用 |
|---|---|
| `RES` | 社区包精选数据（65 行），字段 `(rec, name, disp, repo, scene, ver, stars, weekly_num, weekly_str, origin, note, tag)` |
| `SCENE_MAP` | 包名 → 11 个场景分组之一或「其他」；**改 RES 包名必须同步改这里**，否则场景掉进「其他」 |
| `SCENE_ORDER` | 12 个场景（11 组 + 其他），用于生成 `#sceneSel` 下拉 |
| `NAME_FIX` | 包名歧义对照（常见写法 → 实际包名） |
| `UNVERIFIED` | 未核实项，只保留「必须安装运行才能判断」的 |
| `CSS` / `JS` / `THEME_BOOT` / `SCENE_JS` | 独立字符串常量 |
| `HTML` | f-string 模板 |

## 7. 硬约束与踩过的坑

1. **`HTML` 是 f-string**：模板正文不能含单花括号 `{` `}`；JS 代码必须放普通字符串变量（如 `SCENE_JS`），再用 `{SCENE_JS}` 注入。
2. **精确替换**：改脚本时用唯一锚点，并断言命中次数 = 1。不要跨大段替换，历史上曾整段误删数据块。
3. **交付件一致性**：两个 HTML 必须逐字节相同。
4. **报告体**：正文不出现「你 / 我 / 我们 / 回答 / 截图 / 上一版」等对话词，用「本报告」「数据显示」。
5. **不编造数据**：查不到的星数/下载量写 `—`，并在说明列注明分发方式（npm 无包 / 仅 GitHub / bundle 内组件）。不要拿 `0` 当占位。
6. **包名以 npm 实际名为准**：清单写法可能与 npm 不同（如 `@evermind-ai` → `@everos-ai`、`modsearch` → `@liustack/modsearch`），改名或新增前先查 registry。
7. **宽表**：`<table>` 必须包在 `<div class="scroll">` 内；每个单元格带 `data-l` 供移动端堆叠；`html{scrollbar-gutter:stable}` 不能删，否则切分节会横向抖动。
8. **明暗主题**：只用 CSS 变量，不写死颜色；`<head>` 里的 `THEME_BOOT` 负责防闪白。
9. **`.workbuddy/`** 是客户端数据目录，不改、不删。
10. **临时脚本用完即删**；`research/` 只留数据与生成脚本，不留截图和草稿 HTML。

## 8. 验证清单（每次改完必做）

- 重跑 `build_v2.py`，交付件与 `research/report.html` 逐字节一致。
- `<section class="sec">` = 6，nav 链接 = 6，卡片 `<h2>` 数不变（当前 14）。
- 社区包精选 = 68 行；`#sceneSel` 选项 = 13（11 组 + 其他 + 全部）。
- headless Chrome 探针：1280 / 768 / 520 三档 `documentElement.scrollWidth == clientWidth`；筛选后可见行数与计数一致；暗色下文字可读。

### 8.1 探针模板

```bash
CHROME="C:/Program Files/Google/Chrome/Application/chrome.exe"
"$CHROME" --headless=new --disable-gpu --virtual-time-budget=1200 \
  --window-size=520,900 --dump-dom "file:///<probe.html>"
```

做法：复制交付件，在 `</body>` 前注入探针 `<script>`，把测量结果写进 `document.title`，`--dump-dom` 后用正则取 `P|{...}`。

## 9. 数据来源

- npm：`registry.npmjs.org/<pkg>`、`/-/v1/search`、`api.npmjs.org/downloads/point/last-week/<pkg>`。
- GitHub 星数：`img.shields.io/github/stars/<owner>/<repo>.json`（避开 REST 匿名限流）；仓库搜索用 `api.github.com/search/repositories`，限 10 次/分钟。
- 官方包内：`cordis.patch.yml`、`presets/*.patch.yml`、`@deepseek-ai/dsh-official-bundles` 的 `lib/index.js` 常量。
- 抓取日期 2026-11-08；数据更新时同步改报告里的日期与「数据来源」卡。

## 10. 仓库与发布

- 远程：`https://github.com/sogeisetsu/dsh-ecosystem-report`（public，`main` 分支）。
- GitHub Pages：源 = `main` 根目录 `/`，不使用 Actions。
  - 入口 <https://sogeisetsu.github.io/dsh-ecosystem-report/> 由根目录 `index.html` 做 0 秒 meta refresh 跳到报告。
  - 报告直链：`https://sogeisetsu.github.io/dsh-ecosystem-report/deepseek-harness-npm-report.html`。
  - `.nojekyll` 已提交，跳过 Jekyll 构建。
- 更新流程：改 `build_v2.py` → 重新生成 → 同步根目录交付件 → `git add -A && git commit -m "..." && git push`；Pages 随 `main` 自动重建，约 30–60 秒。
- `.gitignore` 已排除：`.workbuddy/`、`research/report.html`、所有图片、`research/meta/`、解包的 `*/package/`、`*.tgz`。

## 11. 不要做

- 不要直接编辑 `deepseek-harness-npm-report.html`。
- 不要新增分节、目录项或卡片（除非用户明确要求）。
- 不要动 `.workbuddy/`。
- 不要编造星数、下载量、版本号或发布日期。
- 不要把临时截图、草稿 HTML 留在 `research/`。
