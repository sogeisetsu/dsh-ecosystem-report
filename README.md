# DSH 生态调研报告

对 npm [`@deepseek-ai`](https://www.npmjs.com/org/deepseek-ai) 作用域（DeepSeek Harness，简称 **dsh**）的一次全景梳理：官方包怎么分类、装完到底加载了什么，以及第三方社区插件里哪些值得装。

交付物是单文件 HTML：**[`deepseek-harness-npm-report.html`](deepseek-harness-npm-report.html)**，无外部 CDN、无图片、无字体请求，双击即可离线阅读。

**在线预览**：<https://sogeisetsu.github.io/dsh-ecosystem-report/>

## 报告包含什么

| 分节 | 内容 |
|---|---|
| 概览 | 结论摘要、判定路径与状态定义、Profile 模板、Agent 预设 |
| 默认安装清单 | 随包落盘的官方包状态明细 |
| 全量分类 | 422 个官方包的分类方法与可筛选清单 |
| 安装建议 | 官方包分层建议、执行顺序、社区包补充建议 |
| 社区与推荐 | 65 个社区插件（按 11 个场景分组，可筛选）、包名对照、生态规模 |
| 方法与局限 | 数据来源、未核实项、已知限制 |

核心口径：

```
422 总数 = 308 落盘 + 114 未落盘
308 = 205 已激活 + 103 随包未启用
103 = 2a 可选 bundle 15 + 2b 库/内部件 76 + 2c 仅其他预设或入口 12
114 = 3a 官方按需 2 + 3b 官方可选未随包 1 + 3c 无官方入口 110 + 已下架 1
```

状态代码：`1a` 组合层 / `1b` 运行时 / `1c` 预设 / `2a` 可选 bundle / `2b` 库或内部件 / `2c` 仅其他预设或入口 / `3a` 官方按需 / `3b` 官方可选未随包 / `3c` 无官方入口 / `—` 已下架。

## 快速开始

```bash
git clone https://github.com/sogeisetsu/dsh-ecosystem-report.git
cd dsh-ecosystem-report
# 用浏览器打开
open deepseek-harness-npm-report.html      # macOS
start deepseek-harness-npm-report.html     # Windows
```

## 重新生成

报告是脚本生成的，不要直接改 HTML。

```bash
cd research/pkg
python build_v2.py                          # 读 ../rows.json，输出 ../report.html
cp ../report.html ../../deepseek-harness-npm-report.html
```

- Python 3.9+，仅标准库，无第三方依赖。
- 脚本用相对路径 `../rows.json` / `../report.html`，必须在 `research/pkg` 下执行。

## 目录结构

```
deepseek-harness-npm-report.html   交付件（生成物，勿手改）
AGENTS.md                          给后续 AI agent 的项目说明
research/
  rows.json                        422 个官方包的分类数据（生成报告的唯一数据源）
  *.json / *.md / *.ts             抓取的元数据、文档与源码存档
  pkg/
    build_v2.py                    报告生成脚本
    act_full.py / closure.py 等    历史抓取与分析脚本
.workbuddy/                        客户端数据，不入库
```

## 数据来源

| 数据 | 来源 |
|---|---|
| 包清单、版本、发布日期 | `registry.npmjs.org`（`/-/v1/search`、单包 packument） |
| 周下载量 | `api.npmjs.org/downloads/point/last-week` |
| GitHub 星数 | `img.shields.io/github/stars/<owner>/<repo>.json` |
| 安装与激活关系 | 包内 `cordis.patch.yml`、`presets/*.patch.yml`、`@deepseek-ai/dsh-official-bundles` 的 `lib/index.js` 常量 |

数据抓取日期：**2026-11-08**。npm 数据变动频繁，重新生成前请先确认口径仍然成立。

## 免责声明

- dsh 处于 developer preview，存在破坏性变更；社区插件随版本迭代失效属常态。
- 社区包的星数、下载量、版本为抓取时快照，查不到的字段标 `—`，不作推测。
- 本仓库与 DeepSeek 官方无关，仅为第三方调研。

## License

报告文本与脚本采用 MIT 许可。报告引用的包名、版本、星数等数据版权归各项目作者所有。
