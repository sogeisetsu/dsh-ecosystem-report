# -*- coding: utf-8 -*-
"""生成 report.html：DeepSeek Harness @deepseek-ai 包调研报告（v4 重构版）"""
import json, re, datetime

rows = json.load(open('../rows.json'))
by = {r['name']: r for r in rows}
act = json.load(open('../activation.json'))
STD = set(act['presets']['standard.patch.yml'])
NPM = json.load(open('../npm_pkgs.json'))
CLOSURE = set(json.load(open('../closure.json'))['closure'])

INST_ST = ('active', 'runtime', 'preset', 'installed', 'optional', 'profile')
n_total = len(rows)
n_inst = len([r for r in rows if r['status'] in INST_ST])
n_act = len([r for r in rows if r['status'] in ('active', 'runtime') or (r['status'] == 'preset' and r['name'] in STD)])
n_profile = len([r for r in rows if r['status'] == 'profile'])
n_off = len([r for r in rows if r['status'] in ('installed', 'optional', 'profile') or (r['status'] == 'preset' and r['name'] not in STD)])
n_out = n_total - n_inst
n_ondemand = len([r for r in rows if r['status'] == 'ondemand'])
n_opt_off = len([r for r in rows if r['status'] == 'optional_off'])
n_retired = len([r for r in rows if r['status'] == 'retired'])
n_noentry = len([r for r in rows if r['status'] == 'none'])
n_base = len([r for r in rows if r['status'] == 'active'])
n_runtime = len([r for r in rows if r['status'] == 'runtime'])
n_preset = len([r for r in rows if r['status'] == 'preset'])
n_preset_std = len([r for r in rows if r['status'] == 'preset' and r['name'] in STD])
n_preset_other = n_preset - n_preset_std
n_lib = len([r for r in rows if r['status'] == 'installed'])
n_opt = len([r for r in rows if r['status'] == 'optional'])

GH = 'https://github.com/deepseek-ai/deepseek-harness'
GHP = GH + '/blob/master/'

TYPE_CLS = {'Bundle': 'tp-bundle', 'Preset': 'tp-preset', '框架': 'tp-frame', 'CLI': 'tp-cli', 'Plugin': 'tp-plugin',
            'Skill': 'tp-skill', 'MCP': 'tp-mcp', '其他': 'tp-other', '开发工具': 'tp-dev'}

def gh_link(name):
    r = by.get(name)
    if r and r.get('path'):
        return GHP + r['path']
    if name.startswith('libreoffice-kit'):
        return 'https://github.com/deepseek-ai/dsh-libreoffice-kit'
    if name.startswith('node-addon'):
        return GH + '/tree/master/native/system'
    return GH + '/tree/master/packages'

def td(label, html, cls=''):
    c = f' class="{cls}"' if cls else ''
    return f'<td data-l="{label}"{c}>{html}</td>'

def esc(s):
    return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

# ---------------- 数据块 ----------------
profiles = [('web', 'dsh --profile web', 'dsh-base + dsh-web-app', '默认入口，浏览器 UI'),
            ('headless', 'dsh --profile headless "task"', 'dsh-base + dsh-headless', '一次性任务，适合脚本与 CI'),
            ('acp', 'dsh --profile acp', 'dsh-base + dsh-acp-app', '被支持 ACP 的编辑器/客户端驱动'),
            ('sdk', 'dsh --profile sdk', 'dsh-base + dsh-sdk-app', 'stdio JSON-RPC 对外提供运行时'),
            ('sdk-minimal', 'dsh --profile sdk-minimal', 'dsh-sdk-minimal', '最小组合：单模型 + 本地持久化')]
presets = [('standard', 1, 28, '默认预设。完整工具面：文件、命令、计划、子智能体、联网、工作流'),
           ('ptc', 2, 29, '在 standard 基础上改用 PTC 程序化工具执行器'),
           ('minimal', 3, 9, '最小工具面：bash / pwsh 持久终端 + 文件工具，无联网与子智能体'),
           ('cordis', 4, 29, '面向改造 Harness 自身，额外提供 dsh-tool-cordis 运行时自省')]

STATES = [
    ('1a', '已激活 · 组合层', 'tp-plugin', '命中 dsh-base 或 dsh-web-app 的插件行，正在加载', '有', '是', '无需操作', n_base),
    ('1b', '已激活 · 运行时', 'tp-frame', '运行时基座与 profile 入口（dsh、cordis、dsh-base、dsh-web-app 等），由 app-boot 直接装载', '有', '是', '无需操作', n_runtime),
    ('1c', '已激活 · 预设', 'tp-preset', f'仅在 Agent 预设中声明，共 {n_preset} 个，其中 {n_preset_std} 个属默认 standard', '有', '是', '保持默认预设', n_preset_std),
    ('2a', '随包未启用 · 可选 bundle', 'tp-other', '官方可选 bundle：已落盘，开关未打开', '有', '否', '插件页开启，无需重新下载', n_opt),
    ('2b', '随包未启用 · 库或内部件', 'tp-other', '无独立开关，由使用方加载（如 libreoffice-kit 由 office-to-pdf 调用）', '有', '否', '无需操作', n_lib),
    ('2c', '随包未启用 · 仅非默认预设', 'tp-other', f'只在 minimal / cordis 等非默认预设中声明，共 {n_preset_other} 个', '有', '否', '切换预设', n_preset_other),
    ('3a', '官方按需 · 未落盘', 'tp-mcp', 'ON_DEMAND_BUNDLES：未随包，插件页提供官方入口', '无', '否', '插件页一键安装', n_ondemand),
    ('3b', '官方可选 · 未落盘', 'tp-mcp', '官方可选但当前版本未随包（dsh-cua-bundle）', '无', '否', '开启时才下载', n_opt_off),
    ('3c', '无官方入口 · 未落盘', 'tp-other', '示例、测试夹具、内部散件、平台二进制', '无', '否', '自行 npm 安装，通常不必装', n_noentry),
    ('—', '已下架', 'tp-other', '曾随包，已列入 RETIRED_BUNDLES，加载时被移除', '无', '否', '无需安装', n_retired),
]

TIERS = [
 ('must', '必装', '基础工作流依赖，且均已默认落盘并激活。本层含义是不得卸载或禁用。',
  [('dsh', 'CLI 入口，所有 profile 由此启动', 'README'),
   ('dsh-base', 'base 层组合包，提供 provider、工具与服务的共享内核', 'PROFILE_TEMPLATES'),
   ('dsh-web-app', 'Web profile 组合层，95 个服务端与客户端插件', 'PROFILE_TEMPLATES'),
   ('dsh-tool-fs', 'read / write / edit / apply_patch，所有代码改动的唯一通道', 'tool-catalog.md'),
   ('dsh-tool-fs-search', 'glob / grep，内置 ripgrep', 'tool-catalog.md'),
   ('dsh-tool-bash', '执行测试、安装依赖、git 操作', 'tool-catalog.md'),
   ('dsh-tool-subagent + dsh-subagent-fork-in-process', '任务拆分与并行执行', 'tool-catalog.md'),
   ('dsh-tool-web + dsh-web-deepseek-api', '联网搜索与抓取，默认接 DeepSeek Search / Fetch API', '提交记录'),
   ('dsh-tool-todo', '任务清单，维持长任务目标', 'tool-catalog.md'),
   ('dsh-skill + dsh-skill-filesystem', 'Skill 基础设施与本地加载器', 'dsh-base patch'),
   ('dsh-plugin-manager', '插件管理器本体，受 PROTECTED_PLUGINS 保护', 'PROTECTED_PLUGINS'),
   ('dsh-permission-presets', '只读 / 工作区可写 / 完全访问三档权限', 'config-catalog.md')]),
 ('rec', '推荐', '显著提升体验，成本仅为开启开关。均属状态 2a，已随包落盘。',
  [('dsh-experimental-terminal-bundle', '持久终端面板，Agent 与用户共享同一 PTY', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-session-search', '跨会话历史检索', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-session-titles-bundle', '自动生成会话标题', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-auto-review', '提交前自动评审 diff', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-badge-skill-bundle', 'Skill 编写范式示例', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-ralph-bundle', 'Ralph 循环，对同一目标反复迭代', 'OPTIONAL_BUNDLES'),
   ('dsh-tool-schedule + dsh-schedule', '定时与延迟提醒', 'tool-catalog.md')]),
 ('scene', '场景选装', '仅在对应工作流下产生价值，不影响日常使用。',
  [('dsh-skill-office', 'Office Skill：Word / PowerPoint / Excel 工作流。随包落盘，Web 入口默认不加载（只在 sdk 入口的插件行中启用）', 'dsh-sdk-app cordis.patch.yml'),
   ('dsh-mcp-client', 'MCP 客户端，接入外部 MCP 服务端时启用；MCP 资源工具已默认激活', '依赖存在，无插件行'),
   ('dsh-subagent-claude-code / dsh-subagent-codex', '将 Claude Code / Codex 作为子智能体，属官方按需包', 'ON_DEMAND_BUNDLES'),
   ('dsh-experimental-plugin-market-bundle', '插件市场 Discover 页，需接入第三方索引', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-liveshare', '多人共享同一会话', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-voice-input-bundle', '语音输入', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-cot-translation-bundle', '思维链翻译', 'OPTIONAL_BUNDLES'),
   ('dsh-cua-bundle / dsh-computer-use', 'Computer Use，GUI 自动化；当前版本未随包', 'OPTIONAL_BUNDLES'),
   ('dsh-web-search-exa / dsh-web-search-perplexity', '替换搜索供应商，需自备密钥', 'dsh-web 提供方'),
   ('dsh-experimental-agent-team-profile', '智能体团队，分工与汇总', 'OPTIONAL_BUNDLES'),
   ('libreoffice-kit', 'Office 转 PDF 引擎，由 dsh-office-to-pdf 调用', 'dsh-web-app 依赖'),
   ('dsh-experimental-forge-bundle', '长任务工程化，实验性', 'OPTIONAL_BUNDLES')]),
 ('no', '暂不建议', '维护不足、功能重复或仅在特定环境下有意义。',
  [('dsh-experimental-schedule-bundle', '已列入 RETIRED_BUNDLES，加载时自动移除', 'RETIRED_BUNDLES'),
   ('dsh-agent-presets', '早期实现，已被 dsh-agent-preset 与 preset-registry 取代（0.0.1-rc.1，2026-08-10 后未更新）', 'npm 元数据'),
   ('dsh-experimental-agent-team / tool-agent-team / client-ui-agent-team', '与 agent-team-profile 重叠，且未进入可选清单', 'bundle 清单'),
   ('dsh-acp-demo / agent-spine-demo / sdk-jsonrpc-demo / *-testkit / loader-smoke', '示例与测试夹具，非终端用户功能', '包描述'),
   ('dsh-subprocess-e2b / dsh-fs-e2b / dsh-e2b', '依赖 E2B 外部服务与密钥', '包描述'),
   ('dsh-sandbox-ssh / dsh-subprocess-ssh / dsh-fs-ssh', '远端 POSIX 场景专用，配置成本高（0.1.6-alpha.1）', 'npm 版本'),
   ('dsh-win32-process / node-addon-system / node-addon-landlock-run', '平台原生原语，由沙箱层间接调用', '包描述'),
   ('dsh-client-ui-deepseek-model-label-1017 等内部件', '无独立使用价值，随 UI 组合升级', 'npm 下载量')]),
]
TIER_CLS = {'must': 't-must', 'rec': 't-rec', 'scene': 't-scene', 'no': 't-no'}

# ---------- 合并后的社区包清单（第三方包总览 + 外部清单核对）----------
# (推荐值, 包名, 显示名, 仓库, 场景, 版本·日期, 星, 周下载(排序用), 周下载展示, 推荐出处, 说明, 核验标签)
RES = [
 (5, 'dshmarket', 'DSH Market', 'dsh-market/dsh-market', '插件发现', '1.73.15 · 11-07', '11k ★', 308046, '308,046',
  '无官方表态', '在 UI 内浏览、安装、升级社区插件；其余社区包的前置入口。', ''),
 (5, 'dsh-context', 'dsh-context', 'bowenliang123/dsh-context', '上下文', '0.82.2 · 11-07', '4.5k ★', 144773, '144,773',
  '负责人崔添翼 X 点赞（媒体转述）', '上下文构成、Token 趋势、缓存命中与子智能体网络，含 <code>/context</code> 命令；与官方 compaction 功能有重叠，别两边都调。', ''),
 (4, '@liustack/modlens', 'ModLens', 'liustack/modlens', '视觉', '3.27.2 · 10-23', '4.8k ★', 86518, '86,518',
  '无官方表态', '给纯文本模型加视觉能力，依赖外部 CLI 与登录态；与 vision-toolkit 二选一。', ''),
 (4, 'dsh-better-sidebar', 'DSH Better Sidebar', 'omdsh-dev/DSH-better-sidebar', '界面', '0.30.1 · 11-05', '5.0k ★', 78109, '78,109',
  '负责人崔添翼 X 推荐（媒体转述）', '文件树、编辑器、变更、任务合一；与官方 <code>sidebar-*</code> 插件功能重叠，大版本升级需跟随。', ''),
 (4, '@deepseek-harness-tui/dsh-tui', 'dsh-TUI', 'ccch1mneyyy/dsh-TUI', '界面', '0.19.0 · 11-06', '7.1k ★', 21210, '21,210',
  '社区口碑（未见官方表态）', '全屏终端 TUI，SSH / 键盘党不必开浏览器；需 Node ≥ 22.19，与 Web 是两套入口。', ''),
 (4, 'dsh-univer-office', 'Univer Office', 'dream-num/dsh-univer-office', '办公', '0.4.0 · 11-02', '683 ★', 18732, '18,732',
  '无官方表态', '图形化预览、创建、编辑与导出，自带协作 Gateway 与 View；一站式办公的首选。', ''),
 (3, 'dsh-at-file', 'dsh-at-file', 'FSMargoo/dsh-at-file', '输入体验', '0.6.3 · 08-19', '563 ★', 41797, '41,797',
  '无官方表态', 'Codex 风格 <code>@路径</code> 引用。<b>已过时</b>：官方新版已内置 <code>@file</code> 与 <code>@session</code> 引用（<code>dsh-client-ui-reference</code> 等默认加载），作者在 README 中也声明「新装请用官方实现，本插件只为存量环境保留」。', '已过时'),
 (3, 'dsh-excel-chat', 'Excel Chat', 'hccccc01333/dsh-excel-chat', '办公', '0.43.0 · 10-15', '12 ★', 1954, '1,954',
  '无官方表态', 'Excel 对话式读写与清洗，重点在公式校验与单元格级 diff，防止 AI 改坏表格。', ''),
 (3, 'dsh-web-search-free', 'Web Search Free', 'MochiNek0/dsh-web-search-free', '搜索', '1.9.1 · 11-01', '62 ★', 1881, '1,881',
  '无官方表态', '把官方 <code>deepseek-official</code> 通道换成多引擎 + 自动 fallback（TinyFish / SearXNG / Tavily / Exa / Firecrawl），需自备 Key。', ''),
 (2, 'dsh-agent-enhancer', 'Agent Enhancer', 'rebornace/dsh-agent-enhancer', '输入体验', '0.3.6 · 11-07', '1 ★', 1476, '1,476',
  '无官方表态', '会话增强工具箱，含提示词增强；与 <code>dsh-composer-enhance</code> 定位重叠，二选一。', ''),
 (2, 'dsh-composer-enhance', 'Composer Enhance', 'HeShen-1/dsh-composer-enhance', '输入体验', '0.3.1', '0 ★', 0, '—',
  '无官方表态', 'composer 里的 ✨ 按钮：读会话上下文、只追问真实歧义、原地改写并列出改动。npm 未发布，只能从仓库安装；npm 侧同类是 <code>dsh-prompt-enhance</code>（34 ★ / 2,673 次/周）。', 'npm 未发布'),
 (2, 'simple-email-mcp', 'Simple Email MCP', 'mexican75/simple-email-mcp', '邮箱', '—', '4 ★', 0, '—',
  '无官方表态', '多账户 IMAP/SMTP，配置写在 <code>accounts.json</code>，用 pip 安装；属 MCP 服务端，需先启用 <code>dsh-mcp-client</code>。', 'npm 未发布'),
 (2, 'dsh-llm-opencode-go', 'OpenCode Go Adapter', 'a2580vb/dsh-llm-opencode-go', '模型接入', '0.2.3 · 10-30', '1 ★', 485, '485',
  '无官方表态', '把 OpenCode Go 接成原生模型提供商，含协议转换与流式输出；同赛道 <code>dsh-opencode-go</code>（271 ★ / 2,696 次/周）更活跃。', ''),
 (2, 'dsh-mcp-lazy', 'MCP Lazy（wings1848）', 'wings1848/dsh-mcp-lazy', '搜索 / 上下文', '0.4.1 · 10-03', '11 ★', 267, '267',
  '无官方表态', '懒加载 MCP 网关：用一个代理工具替代成百上千个工具定义，省上下文；与 <code>@sutong12/dsh-mcp-lazy</code> 是两个作者的不同项目。', ''),
 (2, 'dsh-opencode-go-pool', 'OpenCode Go Pool', 'whitelonng/dsh-opencode-go-pool', '模型接入', '0.1.10', '3 ★', 0, '—',
  '无官方表态', '多 Key 池 + 额度耗尽自动切换 + 用量面板；npm 未发布，GitHub 上至少 4 个同名仓库，认准作者。', 'npm 未发布'),
 (2, '@anionex/dsh-vision-toolkit', 'Vision Toolkit', 'Anionex/dsh-vision-toolkit', '视觉', '0.1.49 · 11-06', '931 ★', 2911, '2,911',
  '无官方表态', '截图问答、OCR、元素定位；同名 fork 至少 4 个（<code>@mengruo/</code>、<code>@dsh-external/</code>、<code>@junjian.work/</code>），认准作者。', ''),
 (1, '@sutong12/dsh-mcp-lazy', 'MCP Lazy（wishesl）', 'wishesl/dsh-mcp-lazy', '搜索 / 上下文', '0.13.0 · 10-04', '0 ★', 138, '138',
  '无官方表态', '与 <code>dsh-mcp-lazy</code> 是两个作者的独立实现，版本线、仓库、发布节奏都不同，按需二选一。', ''),
 (1, 'dsh-mcp-skill-manager', 'MCP & Skill Manager', 'chihy525/dsh-mcp-skill-manager', '管理面板', '0.1.0 · 08-30', '1 ★', 79, '79',
  '无官方表态', '在设置页管理 MCP 与 Skill；8 月底后未更新，同功能看 <code>@michengai/dsh-skills-manager</code>（499 ★ / 51,226 次/周）。', ''),
 (1, 'dsh-harness-pilot', 'Harness Pilot', 'Lawrence7y/dsh-harness-pilot', '进阶集成', '0.2.0', '1 ★', 0, '—',
  '无官方表态', '把 claude / codex / pi / MiMo 作为子代理派发任务；包名 <code>@dsh-external/dsh-harness-pilot</code> 且 <code>private: true</code>，npm 不可安装。', 'npm 未发布'),
 (1, 'dsh-agent-preset-router', 'Agent Preset Router', 'CTWCTW9999/dsh-agent-preset-router', '进阶集成', '0.1.0', '0 ★', 0, '—',
  '无官方表态', 'Auto Mode：用 flash 模型预判新会话该用哪个预设，执行前让用户确认；npm 未发布。', 'npm 未发布'),
 (4, 'EverOS', 'EverOS 记忆引擎', 'EverMind-AI/EverOS', '记忆与知识沉淀', '1.5.1 · 10-22', '14k ★', 0, '—',
  '外部选型清单', '独立记忆运行时（PyPI 分发，npm 无包）：Markdown 真相源 + SQLite + LanceDB，本地优先、可手改、反思演化；需 Python 3.12+、uv、一个 LLM Key 与本地 8000 端口。', ''),
 (3, '@everos-ai/dsh-plugin', 'EverOS DSH 插件', 'EverMind-AI/plugins', '记忆与知识沉淀', '0.1.0 · 09-16', '9 ★', 120, '120',
  '外部选型清单', 'EverOS 的 DSH 插件入口；<code>@evermind-ai/dsh-plugin</code> 是流传的另一写法，npm 实际包名为前者。', ''),
 (3, 'dsh-simple-memory', 'Simple Memory', 'a903067276-rgb/dsh-simple-memory', '记忆与知识沉淀', '—', '1 ★', 0, '—',
  '外部选型清单', '轻量分层 Markdown 记忆，按会话注入索引而非全文，手动可控；npm 未见同名包，仅 GitHub 分发，同名仓库另有 3 个。', ''),
 (3, 'dsh-flymemory', 'FlyMemory', 'aujurd22/dsh-flymemory', '记忆', '1.9.0 · 11-08', '3 ★', 844, '844',
  '外部选型清单', '全本地记忆，自带 find_conflicts / supersede / consolidate / cleanup，无外部 LLM 依赖。', ''),
 (2, '@kai232/dsh-rag', 'DSH RAG', 'imkelt/DSH-RAG', '记忆', '0.1.2 · 08-24', '2 ★', 107, '107',
  '外部选型清单', '本地文档库检索，把项目文档接入问答链路。', ''),
 (3, '@goodandready/dsh-cron', 'DSH Cron', 'GooDAnDReaDY/dsh-cron', '调度', '0.3.42 · 11-07', '13 ★', 4403, '4,403',
  '外部选型清单', '无人值守后台调度，补内置 schedule 缺的多通道推送、重试心跳、成本护栏与执行历史。', ''),
 (2, 'dsh-wb-cron', 'WB Cron', 'miseryrua/dsh-wb-cron', '定时与任务调度', '—', '1 ★', 0, '—',
  '外部选型清单', '零依赖本地 cron 替代：cron / 固定间隔 / 一次性三种调度，到点在 Web 会话执行；npm 未见同名包。', ''),
 (2, 'dsh-sidebar', 'DSH Sidebar', 'auggie246/dsh-sidebar', '界面', '0.8.4 · 10-03', '0 ★', 257, '257',
  '外部选型清单', 'Git 密集型侧栏，与 <code>dsh-better-sidebar</code> 二选一。', ''),
 (4, '@fffangchenghao/dsh-web-search', 'Web Search', 'fangchenghao/dsh-web-search', '搜索', '0.24.2 · 11-02', '4 ★', 1744, '1,744',
  '外部选型清单', '免 Key 的 8 引擎搜索，跨引擎 RRF、公开 benchmark、单工具 8 动作，接管内置 <code>web_search</code>。', ''),
 (4, '@feiyang666/dsh-vault', 'DSH Vault', 'feiyang-dev/dsh-vault', '备份', '1.6.0 · 11-01', '4 ★', 399, '399',
  '外部选型清单', '一键备份 / 恢复 + 疑似清空告警，补官方缺失的备份能力。', ''),
 (1, 'github:RedMaple96/dsh-plugin-safety', 'Plugin Safety', 'RedMaple96/dsh-plugin-safety', '安全', '—', '0 ★', 0, '—',
  '外部选型清单', '市场安装前静态扫描并弹审查报告，补审批与沙箱管不到插件代码本身的空白。', ''),
 (2, '@jeweis/dsh-sync', 'DSH Sync', 'jeweis/dsh-sync', '同步', '0.11.0 · 10-18', '0 ★', 165, '165',
  '外部选型清单', '多机配置同步。', ''),
 (2, 'dsh-plugin-tool-guard', 'Tool Guard', 'zhaoxuejie/dsh-plugin-tool-guard', '安全', '1.0.0 · 09-08', '0 ★', 53, '53',
  '外部选型清单', '危险命令护栏，拦截破坏性 shell 与文件操作。', ''),
 (4, '@guowenzhang/dsh-mcp-manager', 'MCP Manager（guowenzhang）', 'zhang-guo-wen/dsh-mcp-manager', 'MCP', '1.7.1 · 11-05', '4 ★', 863, '863',
  '外部选型清单', '设置页增删改 / 启停 MCP、按需加载、工具过滤与 token 成本估算，含 Dynamic insert（可替代 <code>dsh-mcp-lazy</code>）。', ''),
 (2, 'nekojackie/dsh-mcp-manager', 'MCP Manager（nekojackie）', 'nekojackie/dsh-mcp-manager', 'MCP', '—', '1 ★', 0, '—',
  '外部选型清单', '面向 OAuth 远端 MCP 的 manager 实现，与 <code>@guowenzhang</code> 版是不同项目。', ''),
 (2, 'dsh-mcp-studio', 'MCP Studio', 'functy23/dsh-mcp-studio', 'MCP', '1.0.6 · 10-03', '32 ★', 535, '535',
  '外部选型清单', 'MCP 诊断与 Claude Desktop 配置导入。', ''),
 (3, 'dsh-plugin-tool-management', 'Tool Management', 'ouli-1242/dsh-plugin-tool-management', '管理', '0.22.3 · 11-07', '43 ★', 2351, '2,351',
  '外部选型清单', '跨场景统一开关记忆 / 技能 / 提示词，一个包覆盖多个管理面。', ''),
 (2, '@studyzy/dsh-lazy-tools', 'Lazy Tools', 'studyzy/dsh-lazy-tools', 'MCP 工具的渐进披露', '0.0.1 · 10-09', '3 ★', 57, '57',
  '外部选型清单', '零配置的 MCP 工具懒加载替代，无 measure 脚本要求；社区常写作 <code>dsh-lazy-tools</code>，npm 实际包名带 scope。', ''),
 (4, 'dsh-skills-manager-plus', 'Skills Manager Plus', 'appthin/dsh-skills-manager-plus', '技能', '0.2.3 · 11-08', '3 ★', 330, '330',
  '外部选型清单', '技能查看、启停、编辑、删除、新增、<code>/commands</code>、zip 导入与中文界面。', ''),
 (2, 'dsh-skill-studio', 'Skill Studio', 'zhengjy01/dsh-skill-studio', '技能', '0.3.1 · 09-29', '3 ★', 307, '307',
  '外部选型清单', '技能管理替代实现。', ''),
 (1, 'github:Wonderow666/dsh-computer-use', 'Computer Use（第三方）', 'Wonderow666/dsh-computer-use', '桌面控制', '—', '0 ★', 0, '—',
  '外部选型清单', 'Windows GUI 桌面控制；与官方 <code>@deepseek-ai/dsh-computer-use</code> 同名但为第三方实现。', ''),
 (3, 'dsh-folderead', 'FolderRead', 'nipheryang/dsh-folderead', '文件', '0.2.0 · 10-27', '0 ★', 102, '102',
  '外部选型清单', '纯文件浏览编辑，不捆绑终端与 Git，适合轻量文件操作。', ''),
 (3, '@daxu8972/dsh-file-manager', 'File Manager', '', '文件与系统操作', '0.1.0 · 08-29', '—', 12, '12',
  '外部选型清单', 'VSCode 风格独立文件管理器，提供 <code>file_*</code> 模型工具；npm 元数据无 repository 字段，GitHub 仓库未定位。', ''),
 (4, 'dsh-memory-fortress', 'Memory Fortress', 'linshuangb347/dsh-memory-fortress', '记忆', '1.0.0 · 09-08', '2 ★', 243, '243',
  '外部选型清单', 'DSH 原生侧功能较完整的记忆方案：分层记忆 + 知识图谱。', ''),
 (4, '@michengai/dsh-automation', 'DSH Automation（MichengAI）', 'MichengAI/dsh-automation', '定时与任务调度', '1.0.20 · 11-07', '40 ★', 19640, '19,640',
  '外部选型清单', '独立运行完整编码任务：每次触发在全新 root Agent + Session 中执行，带权限边界与可审计运行历史；另有 titanwings（104★）、cofy-x（0★）同名实现。', ''),
 (3, 'dsh-schedule-tasks', 'Schedule Tasks', 'uluckystar/dsh-schedule-tasks', '定时与任务调度', '—', '2 ★', 0, '—',
  '外部选型清单', '标准 5 段式 cron + shell / 通知触发 + Web 侧边栏，不涉及 Agent 会话编排；npm 未见同名包。', ''),
 (4, 'dsh-search-router', 'Search Router', 'XGrin/dsh-search-router', '搜索与上下文', '—', '2 ★', 0, '—',
  '外部选型清单', '路由器式搜索：统一包装 Exa / Tavily / Brave / SearXNG / DuckDuckGo / DeepSeek 后端，支持切换与失败回退；npm 未见同名包。', ''),
 (3, '@liustack/modsearch', 'ModSearch', 'liustack/modsearch', '搜索与上下文', '5.10.12 · 11-07', '957 ★', 19323, '19,323',
  '外部选型清单', '默认走 Firecrawl 免 Key 通道，每月 1,000 免费 credits，装上即用，支持网页搜索与单页抓取；社区常写作 <code>modsearch</code>，裸名是 2015 年的同名旧包，勿混。', ''),
 (3, 'dsh-hydrasearch', 'HydraSearch', 'dgagf111/dsh-hydrasearch', '搜索与上下文', '—', '0 ★', 0, '—',
  '外部选型清单', '极简双后端：TinyFish 完全免费仅限速率 + AnySearch 每天 1,000 次，匿名可用；npm 未见同名包。', ''),
 (5, 'billion-context', 'Billion Context', 'ranxianglei/billion-context', '上下文', '0.1.213 · 11-07', '4.8k ★', 848207, '848,207',
  '外部选型清单', '提供 compress / decompress / search_context，由模型按需压缩旧上下文；不关心诊断时只装它即可。', ''),
 (4, 'cc-safety-net', 'CC Safety Net', 'kenryu42/cc-safety-net', '安全', '2.7.5 · 11-08', '2k ★', 47384, '47,384',
  '外部选型清单', '工具执行前拦截破坏性 Git / 文件系统命令与敏感文件访问，安全前置守卫。', ''),
 (4, '@xiaoyuyu6420/dsh-backup', 'DSH Backup', 'xiaoyuyu6420/dsh-backup', '安全与备份', '0.14.2 · 10-30', '39 ★', 1336, '1,336',
  '外部选型清单', '<code>~/.dsh</code> 一键备份 / 恢复 / 迁移，带升级前快照与换机迁移；社区常写作 <code>dsh-backup</code>，npm 实际包名带 scope。', ''),
 (3, '@wildusk/dsh-backup', 'Backup（wildusk）', 'usertoandy/dsh-backup', '备份', '0.1.4 · 09-16', '0 ★', 28, '28',
  '外部选型清单', '轻量备份，只做时间戳 tar.gz 归档。', ''),
 (4, 'dsh-mcp-manager', 'MCP Manager（SQY Bundle）', 'sanqiuyef/SQY-DSH-PLUGIN', 'MCP', '—', '0 ★', 0, '—',
  '外部选型清单', 'SQY-DSH-PLUGIN bundle 成员：设置页清单、启停、编辑、连接健康度、就地重连、探测归因、导入导出，运行时即时生效。', ''),
 (3, 'dsh-mcp-manage', 'MCP Manage', 'null119/dsh-mcp-manage', 'MCP 服务器管理', '1.1.0 · 08-17', '23 ★', 125, '125',
  '外部选型清单', '把 MCP 服务器收进设置面板「一台一行」，一键启停 + 会话级懒启动，省掉常驻工具 token。', ''),
 (4, '@duke-dsh-plugins/dsh-memory-manager', 'Memory Manager（社区独立版）', 'MoonlitDropOfBlood/dsh-memory-manager', '记忆管理', '1.4.4 · 11-04', '8 ★', 548, '548',
  '外部选型清单', '跨后端统一管理：全局 + 项目级 <code>memory_*</code> 工具、写去重提示、别名并条、写入脱敏、运行审计；SQY-DSH-PLUGIN bundle 内另有同名组件。', ''),
 (4, 'dsh-mcp-gateway', 'MCP Gateway（SQY Bundle）', 'sanqiuyef/SQY-DSH-PLUGIN', 'MCP', '—', '0 ★', 0, '—',
  '外部选型清单', 'SQY bundle 成员：<code>mcp_catalog</code> / <code>mcp_search</code> / <code>mcp_describe</code> 渐进披露，不隐藏原有工具。', ''),
 (3, 'dsh-mcp-lens', 'MCP Lens', 'labmimors/dsh-mcp-lens', 'MCP', '0.1.0-rc.9 · 08-15', '12 ★', 305, '305',
  '外部选型清单', '更激进的渐进披露：两个固定 schema 背后挂上千工具，适合超大型远程目录。', ''),
 (4, 'dsh-skill-manager', 'Skill Manager（SQY Bundle）', 'sanqiuyef/SQY-DSH-PLUGIN', '技能', '—', '0 ★', 0, '—',
  '外部选型清单', 'SQY bundle 成员：技能根扫描、<code>_disabled</code> 启停、三态调用策略、批量操作、调用账本、本地技能包导入。', ''),
 (4, '@michengai/dsh-skills-manager', 'Skills Manager（MichengAI）', 'MichengAI/dsh-skills-manager', '技能', '1.3.0 · 11-08', '506 ★', 50872, '50,872',
  '外部选型清单', '可视化 Skills 页面、GitHub 安装、预览更新与备份回退。', ''),
 (3, 'dsh-project-skills-mng', 'Project Skills Mng', 'MT3166/dsh-project-skills-mng', '技能管理', '—', '0 ★', 0, '—',
  '外部选型清单', '右侧栏浏览、编辑与管理项目级 / 全局技能，不叠加调用账本与安装来源追踪；npm 未见同名包。', ''),
 (2, 'changan0617/dsh-plugin-market', 'Plugin Market（轻量）', 'changan0617/dsh-plugin-market', '市场', '—', '0 ★', 0, '—',
  '外部选型清单', '只做一件事：设置侧边栏加一个 Plugin Market 按钮，新标签页打开社区市场。', ''),
 (3, 'dsh-plugin-hub', 'Plugin Hub（SQY Bundle）', 'sanqiuyef/SQY-DSH-PLUGIN', '插件市场与插件管理', '—', '0 ★', 0, '—',
  '外部选型清单', 'SQY bundle 成员：集成插件市场 + 插件管理，额外支持版本回滚与故障诊断。', ''),
 (2, '@zfdx123/dsh-atelier', 'DSH Atelier', 'zfdx123/dsh-atelier', '集成包', '1.0.17 · 10-31', '0 ★', 132, '132',
  '外部选型清单', '社区 bundle，含 <code>dsh-mcp-manager</code>、<code>dsh-skills-manager</code>、<code>dsh-memery</code> 等 7 个插件；与 SQY bundle 功能重叠但维护者不同。', ''),
 (2, '@sophiadata-ai/dsh-mcp-skill-manager', 'MCP & Skill Manager（SophiaData）', 'gtk96/dsh-mcp-skill-manager', '管理', '0.10.1 · 11-06', '0 ★', 431, '431',
  '外部选型清单', 'MCP + 技能二合一管理，与 SQY bundle 无归属关系，按包名区分。', ''),
 (3, '@sheep233_/dsh-web-search-free', 'Web Search Free（sheep233_）', 'sheep-programmer/dsh-web-search-free', '搜索与上下文', '0.3.1 · 08-29', '11 ★', 141, '141',
  '外部选型清单', '注册 Parallel + Exa 双免费后端，匿名免 Key，可一键切回官方付费搜索；接管内置 <code>web_search</code>。', ''),
 (3, '@js2hou/dsh-mcp-manager', 'MCP Manager（js2hou）', 'js2hou/dsh-mcp-manager', 'MCP 服务器管理', '0.1.6 · 10-18', '26 ★', 295, '295',
  '外部选型清单', 'MCP 可视化管理：查看已装 / 已启用服务器，设置页启停与编辑；与 <code>@guowenzhang</code>、<code>nekojackie</code> 版同名不同实现。', ''),
 (2, '@yilinxiao/dsh-mcp-lazy', 'MCP Lazy（yilinxiao）', 'leaforbook/dsh-mcp-lazy', 'MCP 工具的渐进披露', '0.5.1 · 08-20', '7 ★', 245, '245',
  '外部选型清单', 'MCP 懒加载 + 动态工具加载 + Tool Router；server 仅在被用到时连接，空闲自动断开，工具列表缓存磁盘。', ''),
]

RES.sort(key=lambda r: (-r[0], -r[7]))
n_res = len(RES)

SCENE_ORDER = [
    '文件与系统操作',
    '记忆与知识沉淀',
    '定时与任务调度',
    '侧边工作台（侧栏工作台）',
    '搜索与上下文',
    '安全与备份',
    'MCP 服务器管理',
    '记忆管理',
    'MCP 工具的渐进披露',
    '技能管理',
    '插件市场与插件管理',
    '其他',
]

SCENE_MAP = {
    'dshmarket': '插件市场与插件管理',
    'dsh-context': '搜索与上下文',
    '@liustack/modlens': '其他',
    'dsh-better-sidebar': '侧边工作台（侧栏工作台）',
    '@deepseek-harness-tui/dsh-tui': '其他',
    'dsh-univer-office': '其他',
    'dsh-at-file': '其他',
    'dsh-excel-chat': '其他',
    'dsh-web-search-free': '搜索与上下文',
    'dsh-agent-enhancer': '其他',
    'dsh-composer-enhance': '其他',
    'simple-email-mcp': '其他',
    'dsh-llm-opencode-go': '其他',
    'dsh-mcp-lazy': 'MCP 工具的渐进披露',
    'dsh-opencode-go-pool': '其他',
    '@anionex/dsh-vision-toolkit': '其他',
    '@sutong12/dsh-mcp-lazy': 'MCP 工具的渐进披露',
    'dsh-mcp-skill-manager': 'MCP 服务器管理',
    'dsh-harness-pilot': '其他',
    'dsh-agent-preset-router': '其他',
    'EverOS': '记忆与知识沉淀',
    '@everos-ai/dsh-plugin': '记忆与知识沉淀',
    'dsh-simple-memory': '记忆与知识沉淀',
    'dsh-flymemory': '记忆与知识沉淀',
    '@kai232/dsh-rag': '记忆与知识沉淀',
    '@goodandready/dsh-cron': '定时与任务调度',
    'dsh-wb-cron': '定时与任务调度',
    'dsh-sidebar': '侧边工作台（侧栏工作台）',
    '@fffangchenghao/dsh-web-search': '搜索与上下文',
    '@feiyang666/dsh-vault': '安全与备份',
    'github:RedMaple96/dsh-plugin-safety': '安全与备份',
    '@jeweis/dsh-sync': '安全与备份',
    'dsh-plugin-tool-guard': '安全与备份',
    '@guowenzhang/dsh-mcp-manager': 'MCP 服务器管理',
    'nekojackie/dsh-mcp-manager': 'MCP 服务器管理',
    'dsh-mcp-studio': 'MCP 服务器管理',
    'dsh-plugin-tool-management': '记忆管理',
    '@studyzy/dsh-lazy-tools': 'MCP 工具的渐进披露',
    'dsh-skills-manager-plus': '技能管理',
    'dsh-skill-studio': '技能管理',
    'github:Wonderow666/dsh-computer-use': '文件与系统操作',
    'dsh-folderead': '文件与系统操作',
    '@daxu8972/dsh-file-manager': '文件与系统操作',
    'dsh-memory-fortress': '记忆与知识沉淀',
    '@michengai/dsh-automation': '定时与任务调度',
    'dsh-schedule-tasks': '定时与任务调度',
    'dsh-search-router': '搜索与上下文',
    '@liustack/modsearch': '搜索与上下文',
    'dsh-hydrasearch': '搜索与上下文',
    'billion-context': '搜索与上下文',
    'cc-safety-net': '安全与备份',
    '@xiaoyuyu6420/dsh-backup': '安全与备份',
    '@wildusk/dsh-backup': '安全与备份',
    'dsh-mcp-manager': 'MCP 服务器管理',
    'dsh-mcp-manage': 'MCP 服务器管理',
    '@duke-dsh-plugins/dsh-memory-manager': '记忆管理',
    'dsh-mcp-gateway': 'MCP 工具的渐进披露',
    'dsh-mcp-lens': 'MCP 工具的渐进披露',
    'dsh-skill-manager': '技能管理',
    '@michengai/dsh-skills-manager': '技能管理',
    'dsh-project-skills-mng': '技能管理',
    'changan0617/dsh-plugin-market': '插件市场与插件管理',
    'dsh-plugin-hub': '插件市场与插件管理',
    '@zfdx123/dsh-atelier': '插件市场与插件管理',
    '@sophiadata-ai/dsh-mcp-skill-manager': 'MCP 服务器管理',
    '@sheep233_/dsh-web-search-free': '搜索与上下文',
    '@js2hou/dsh-mcp-manager': 'MCP 服务器管理',
    '@yilinxiao/dsh-mcp-lazy': 'MCP 工具的渐进披露',
}

scene_counts = {}
for _r in RES:
    _sc = SCENE_MAP.get(_r[1], '其他')
    scene_counts[_sc] = scene_counts.get(_sc, 0) + 1
scene_options = ''.join(
    '<option value="%s">%s（%d）</option>' % (sc, sc, scene_counts[sc])
    for sc in SCENE_ORDER if scene_counts.get(sc))

SCENE_JS = r'''
(function(){
  var sel=document.getElementById('sceneSel');
  if(!sel)return;
  var rows=[].slice.call(document.querySelectorAll('.res-tbl tbody tr'));
  var cnt=document.getElementById('sceneCnt');
  sel.addEventListener('change',function(){
    var v=this.value,shown=0;
    rows.forEach(function(r){
      var ok=(!v)||(r.getAttribute('data-scene')===v);
      r.style.display=ok?'':'none';
      if(ok)shown++;
    });
    cnt.textContent='显示 '+shown+' / '+rows.length;
  });
})();
'''


def stars_html(n):
    filled = '★' * n
    empty = '★' * (5 - n)
    return f'<span class="rec" title="推荐值 {n}/5">{filled}<i>{empty}</i></span>'

def res_rows():
    out = []
    for rec, name, disp, repo, _scene, ver, st, wkn, wk, origin, note, tag in RES:
        scene = SCENE_MAP.get(name, '其他')
        namecell = f'<code>{name}</code><div class="sub">{disp}'
        if repo and not repo.startswith('（'):
            namecell += f' · {repo}'
        namecell += '</div>'
        if tag:
            cls = {'已在包内': 't-rec', '已过时': 't-no2'}.get(tag, 't-no')
            namecell += f'<div style="margin-top:3px"><span class="tag {cls}">{tag}</span></div>'
        out.append(f'<tr data-scene="{scene}">'
            + td('推荐值', f'{stars_html(rec)}<span class="recn">{rec}</span>', 'c')
            + td('包', namecell)
            + td('场景', scene, 'sub')
            + td('版本 · 日期', ver, 'sub nowrap')
            + td('星 / 周下载', f'{st} / {wk}', 'sub nowrap')
            + td('推荐出处', origin, 'sub')
            + td('说明', note, 'sub') + '</tr>')
    return ''.join(out)

res_html = res_rows()

NAME_FIX = [
 ('dsh-market', 'dshmarket', 'npm 上不存在 dsh-market；@dsh-market/plugin、/core、/schema 为其拆包'),
 ('DSH-better-sidebar', 'dsh-better-sidebar', 'npm 包名全小写，带 DSH- 前缀的写法查不到（仓库名反而叫 DSH-better-sidebar）'),
 ('dsh-vision-toolkit', '@anionex/dsh-vision-toolkit', '裸名不存在；另有 @mengruo/、@dsh-external/、@junjian.work/ 三个 fork'),
 ('dsh-composer-enhance', '（npm 未发布）', '仓库 HeShen-1/dsh-composer-enhance 的 package.json 中 name 同名，但未发布到 registry'),
 ('dsh-composer-enhancer', '（已废弃，改用 dsh-agent-enhancer）', '作者标记 deprecated，弃用说明为 renamed to dsh-agent-enhancer'),
 ('dsh-mcp-manager（裸名）', '按作者与 bundle 归属区分', '同名至少有 @guowenzhang/、nekojackie/、@zhengjunyao/、hyqhyq3/ 四个独立实现，以及 SQY-DSH-PLUGIN bundle 内的同名插件'),
 ('@zfdx123/dsh-atelier', '（独立 bundle，非 SQY）', '内含 dsh-mcp-manager、dsh-skills-manager、dsh-memery 等 7 个插件，与 SQY-DSH-PLUGIN 功能重叠但维护者不同'),
]

UNVERIFIED = [
 ('社区包的实际运行表现', '功能描述取自各包 README 与 npm description，本报告未逐包安装；兼容性、插件冲突与性能开销没有实测数据'),
 ('社区包与宿主的版本匹配', '多数包只声明宽松的 dsh peer 范围，能否在 0.2.2-rc.1 上正常加载，需安装后逐个验证'),
]

namefix_rows = ''.join(
    '<tr>' + td('常见写法', f'<code>{a}</code>') + td('实际包名', f'<code>{b}</code>')
    + td('说明', c, 'sub') + '</tr>' for a, b, c in NAME_FIX)

unv_rows = ''.join('<tr>' + td('项目', a) + td('现状', b, 'sub') + '</tr>' for a, b in UNVERIFIED)


prof_rows = ''.join(
    '<tr>' + td('profile', f'<code>{x[0]}</code>') + td('启动命令', f'<code>{esc(x[1])}</code>')
    + td('bundle 组合', x[2]) + td('用途', x[3]) + '</tr>' for x in profiles)

preset_rows = ''.join(
    '<tr>' + td('预设', f'<code>{x[0]}</code>') + td('order', x[1], 'c')
    + td('成员包数', x[2], 'c') + td('差异', x[3]) + '</tr>' for x in presets)

STATE_DEFS = [
    dict(k='1a', cls='s-active', name='已激活 · 组合层', n=n_base, desc='命中 dsh-base 或 dsh-web-app 的插件行，随启动加载'),
    dict(k='1b', cls='s-runtime', name='已激活 · 运行时', n=n_runtime, desc='运行时基座与 profile 入口，由 app-boot 直接装载'),
    dict(k='1c', cls='s-preset', name='已激活 · 预设', n=n_preset_std, desc=f'由 Agent 预设声明并落在默认 standard 内；预设声明共 {n_preset} 个，另 {n_preset_other} 个见 2c'),
    dict(k='2a', cls='s-opt', name='随包未启用 · 可选 bundle', n=n_opt, desc='官方可选组合包，已落盘；插件页开启即生效，不会重新下载'),
    dict(k='2b', cls='s-inst', name='随包未启用 · 库或内部件', n=n_lib, desc='没有独立开关，由上层调用时才加载，如 libreoffice-kit 由 office-to-pdf 调用'),
    dict(k='2c', cls='s-preset', name='随包未启用 · 仅其他预设或入口', n=n_preset_other + n_profile, desc='只在 minimal / cordis 预设，或 sdk / headless / acp 入口的插件行中声明；Web 默认入口不加载'),
    dict(k='3a', cls='s-out', name='官方按需 · 未落盘', n=n_ondemand, desc='ON_DEMAND_BUNDLES 中的公开包，插件页「发现 / 更多」一键安装'),
    dict(k='3b', cls='s-out', name='官方可选 · 未落盘', n=n_opt_off, desc='官方可选但当前版本未随包（dsh-cua-bundle），开启时才下载'),
    dict(k='3c', cls='s-out', name='无官方入口 · 未落盘', n=n_noentry, desc='示例、测试夹具、内部散件与平台二进制，只能自行 npm 安装，通常没有加载路径'),
    dict(k='—', cls='s-ret', name='已下架', n=n_retired, desc='已列入 RETIRED_BUNDLES，即使旧安装里存在，加载时也会被移除'),
]

legend_html = ''.join(
    f'<div class="it"><span class="tag {d["cls"]}"><i class="cd2">{d["k"]}</i>{d["name"]}</span>'
    f'<span class="tx">{d["desc"]}<b class="n">{d["n"]} 个</b></span></div>'
    for d in STATE_DEFS)

# ---- 安装建议：按状态代码渲染徽章 ----
import re as _re
_TOK = _re.compile(r'dsh(?:-[a-z0-9-]+)?|libreoffice-kit[a-z0-9-]*|node-addon-[a-z0-9-]+')
PCODE = {d['k']: (d['cls'], d['name']) for d in STATE_DEFS}

def badge_py(code):
    cls, name = PCODE.get(code, ('s-out', '未核实'))
    return f'<span class="tag {cls}"><i class="cd2">{code}</i>{name}</span>'

def codes_of(name):
    r = by.get(name)
    return [r['code']] if r and r.get('code') else ['3c']

def pills_for(label):
    seen = []
    for t in _TOK.findall(label):
        if t in by:
            for c in codes_of(t):
                if c not in seen:
                    seen.append(c)
    if not seen:
        return badge_py('3c')
    return ''.join(badge_py(c) for c in seen)

tier_html = ''
for key, tname, tdesc, items in TIERS:
    body = ''
    for it in items:
        body += ('<tr>' + td('包', f'<code>{it[0]}</code>')
                 + td('当前状态', pills_for(it[0]))
                 + td('理由', it[1]) + td('证据', it[2], 'muted') + '</tr>')
    tier_html += (f'<div class="card tier {TIER_CLS[key]}">'
        f'<h3><span class="tag {TIER_CLS[key]}">{tname}</span> <span class="sub">{tdesc}</span></h3>'
        f'<div class="scroll"><table class="mini tier-tbl">'
        f'<colgroup><col style="width:25%"><col style="width:14%"><col style="width:40%"><col style="width:21%"></colgroup>'
        f'<thead><tr><th>包</th><th>当前状态</th><th>理由</th><th>证据</th></tr></thead>'
        f'<tbody>{body}</tbody></table></div></div>')

def leaf_html(d):
    return (f'<details class="tn lf" open>'
            f'<summary><span class="tag {d["cls"]}"><i class="cd2">{d["k"]}</i>{d["name"]}</span>'
            f'<span class="num">{d["n"]} 个</span></summary>'
            f'<div class="tb"><div class="ld">{d["desc"]}</div></div></details>')

LEAF = {d['k']: leaf_html(d) for d in STATE_DEFS}
leaf_1a = LEAF['1a']; leaf_1b = LEAF['1b']; leaf_1c = LEAF['1c']
leaf_2a = LEAF['2a']; leaf_2b = LEAF['2b']; leaf_2c = LEAF['2c']
leaf_3a = LEAF['3a']; leaf_3b = LEAF['3b']; leaf_3c = LEAF['3c']; leaf_ret = LEAF['—']

CSS = '''
:root{
  --bg:#f4f5f7; --panel:#fff; --panel2:#fafbfc; --panel3:#f6f7f9; --hover:#fcfcfd; --codebg:#f2f3f6;
  --ink:#181b21; --ink2:#3d434d; --muted:#646b78; --line:#e3e5ea; --line2:#eef0f4;
  --accent:#2456d6; --ok:#157347; --warn:#9a5b00; --bad:#b02a2a;
  --hl-bg:#f3f6ff; --hl-line:#d6e0fb; --wn-bg:#fffaf0; --wn-line:#f3e0be;
  --shadow:0 1px 2px rgba(16,24,40,.04); --hoverink:#12307a;
  color-scheme:light;
}
:root[data-theme="dark"]{
  --bg:#0e1218; --panel:#151b23; --panel2:#1a212b; --panel3:#232b36; --hover:#1b232e; --codebg:#1e2630;
  --ink:#e6eaf0; --ink2:#bcc5d2; --muted:#8d97a7; --line:#2a333f; --line2:#232b36;
  --accent:#7aa2ff; --ok:#4ec98a; --warn:#dfa34d; --bad:#ef7f7f;
  --hl-bg:#151d2e; --hl-line:#2b3c5c; --wn-bg:#241c11; --wn-line:#4e3b1c;
  --shadow:0 1px 2px rgba(0,0,0,.4); --hoverink:#a9c2ff;
  color-scheme:dark;
}
*{box-sizing:border-box}
html{scrollbar-gutter:stable}
html,body{margin:0;padding:0}
body{background:var(--bg);color:var(--ink);
  font:15px/1.72 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  -webkit-text-size-adjust:100%}
.wrap{width:100%;max-width:1120px;margin:0 auto;padding:0 24px}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
code{font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--codebg);border:1px solid var(--line2);
  border-radius:4px;padding:1px 5px;word-break:break-word}
h1,h2,h3,h4{margin:0;font-weight:650;letter-spacing:-.01em}
p{margin:0 0 10px}
ul,ol{margin:8px 0 10px;padding-left:22px}
li{margin:3px 0}
.muted{color:var(--muted)}
.sub{color:var(--muted);font-size:12.5px;line-height:1.55}
.c{text-align:center}
.num{font-variant-numeric:tabular-nums}
.wide{table-layout:fixed}
.res-tbl{table-layout:fixed;width:100%}
.res-tbl td{word-break:break-word}
.res-tbl td.nowrap{white-space:normal}
.res-tbl th.c{text-align:center}
.rec{letter-spacing:1px;font-size:12.5px;color:#f0a020;white-space:nowrap}
.rec i{color:#e3e6eb;font-style:normal}
.recn{display:inline-block;margin-left:9px;font-size:11px;color:#9aa1ad;vertical-align:1px}
.nowrap{white-space:nowrap}

/* header */
.hdr{background:var(--panel);border-bottom:1px solid var(--line);padding:34px 0 26px;margin-bottom:0}
.hdr .eyebrow{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0}
.hdr-top{display:flex;align-items:center;justify-content:space-between;gap:16px;margin:0 0 8px}
.theme-seg{flex:0 0 auto;display:inline-flex;align-items:center;gap:2px;padding:3px;border:1px solid var(--line);
  border-radius:999px;background:var(--panel2);box-shadow:var(--shadow)}
.theme-seg button{font:inherit;font-size:12px;line-height:1;padding:5px 10px;border:0;border-radius:999px;
  background:transparent;color:var(--muted);cursor:pointer;display:inline-flex;align-items:center;gap:4px;
  white-space:nowrap;transition:background .15s,color .15s}
.theme-seg button:hover{color:var(--ink);background:var(--panel3)}
.theme-seg button:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.theme-seg button[aria-pressed="true"]{background:var(--panel);color:var(--ink);box-shadow:var(--shadow)}
.theme-seg .ic{font-size:12.5px;line-height:1;font-style:normal}
:root[data-theme="dark"] .theme-seg button[aria-pressed="true"]{background:#313d4c;color:#fff}
.hdr-actions{display:flex;align-items:center;gap:8px}
.ghbtn{display:inline-flex;align-items:center;gap:6px;font-size:12px;line-height:1;padding:6px 11px;
  border:1px solid var(--line);border-radius:999px;background:var(--panel2);color:var(--ink2);
  text-decoration:none;box-shadow:var(--shadow);white-space:nowrap;
  transition:background .15s,color .15s,border-color .15s}
.ghbtn:hover{background:var(--panel3);color:var(--ink);border-color:var(--muted);text-decoration:none}
.ghbtn:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.ghbtn svg{width:15px;height:15px;display:block;fill:currentColor}
.hdr h1{font-size:27px;line-height:1.3;margin:0 0 12px}
.hdr .lead{font-size:15.5px;color:var(--ink2);max-width:900px;margin:0 0 16px}
.meta{display:flex;flex-wrap:wrap;gap:6px 22px;font-size:12.5px;color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:20px 0 0}
.kpi{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:11px 13px}
.kpi b{display:block;font-size:22px;line-height:1.25;font-variant-numeric:tabular-nums}
.kpi span{font-size:12px;color:var(--muted)}
.kpi.hl{background:var(--hl-bg);border-color:var(--hl-line)}

/* tabs */
.tabsbar{position:sticky;top:0;z-index:30;background:var(--bg);border-bottom:1px solid var(--line)}
.tabs{display:flex;gap:2px;overflow-x:auto;padding:8px 0;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tabs a{flex:0 0 auto;font-size:13.5px;color:var(--muted);background:none;border:1px solid transparent;
  border-radius:8px;padding:7px 12px;white-space:nowrap;text-decoration:none}
.tabs a:hover{color:var(--ink);background:var(--panel);text-decoration:none}
.tabs a.cur{background:var(--panel);border-color:var(--line);color:var(--ink);font-weight:600;
  box-shadow:var(--shadow)}

/* sections */
main{padding:26px 0 60px}
section.sec{scroll-margin-top:66px;margin:0 0 34px}
section.sec>h2.sec-t{font-size:19px;margin:0 0 4px;padding:0 2px}
section.sec>p.sec-d{color:var(--muted);font-size:13px;margin:0 2px 14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px 22px;margin:0 0 16px}
.card>h2{font-size:17px;margin:0 0 6px}
.card>h2+.hint{color:var(--muted);font-size:13px;margin:0 0 14px}
.card h3{font-size:14.5px;margin:18px 0 8px}
.card h3:first-child{margin-top:0}
.lead2{font-size:14.5px;color:var(--ink2)}

/* legends / notes */
.note{border:1px solid var(--line);background:var(--panel2);border-radius:10px;padding:12px 14px;font-size:13.5px;color:var(--ink2)}
.twocol{display:grid;grid-template-columns:1fr 1fr;gap:10px 24px;margin:10px 0}
.twocol>div{border-left:2px solid var(--line2);padding-left:11px}
.twocol h4{margin:0 0 4px;font-size:12.5px;font-weight:650;color:var(--ink)}
.twocol p{margin:0;font-size:12.5px;line-height:1.65;color:var(--ink2)}
.note.info{background:var(--hl-bg);border-color:var(--hl-line)}
.note.warn{background:var(--wn-bg);border-color:var(--wn-line)}
.note b{color:var(--ink)}
.tree{border:1px solid var(--line);border-radius:10px;padding:14px 16px;background:var(--panel2);font-size:13.5px}
.tree .q{font-weight:650;margin:12px 0 4px}
.tree .q:first-child{margin-top:0}
.tree .br{margin:2px 0;padding-left:12px;border-left:2px solid var(--line);color:var(--ink2)}
.tree .l2{margin-left:20px}
.tree .l3{margin-left:40px}
.tree .l4{margin-left:64px}
.tbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 12px}
.btn{font:inherit;font-size:12.5px;padding:5px 11px;border:1px solid var(--line);border-radius:8px;background:var(--panel);
  color:var(--ink2);cursor:pointer}
.btn:hover{background:var(--panel3);color:var(--ink)}
.btn:active{background:var(--panel3)}
.dtree{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:14px 18px;font-size:13.5px}
.tn{margin:0}
.tn>summary{list-style:none;cursor:pointer;display:block;padding:5px 0;font-weight:650;color:var(--ink)}
.tn>summary::-webkit-details-marker{display:none}
.tn>summary:before{content:"▸";display:inline-block;width:16px;color:#8b93a1;font-size:13px;
  transition:transform .15s;transform-origin:center}
.tn[open]>summary:before{transform:rotate(90deg)}
.tn>summary:hover{color:var(--hoverink)}
.tn>.tb{margin:2px 0 2px 7px;border-left:2px solid var(--line);padding-left:16px}
.tn>.tb>.tn:last-child,.tn>.tb>.bline:last-child{margin-bottom:4px}
.dtree .qn{display:inline-block;margin-right:8px;padding:0 7px;border-radius:5px;background:var(--panel3);
  color:var(--ink2);font-size:11.5px;font-weight:600;line-height:1.8;vertical-align:1px}
.dtree .bl{display:inline-block;min-width:52px;margin-right:8px;font-weight:650}
.dtree .bl.yes{color:#157347}.dtree .bl.no{color:#9a5b00}
.dtree .sepc{color:var(--muted);margin:0 4px}
.bline{color:var(--ink2);margin:4px 0 8px;font-weight:400}
.grp{color:var(--ink2);margin:10px 0 2px;font-weight:400;max-width:860px}
.grp:first-child{margin-top:2px}
.tn.lf{margin:6px 0;max-width:690px}
.tn.lf>summary{display:flex;align-items:center;gap:8px}
.tn.lf>summary .num{margin-left:auto;color:var(--muted);font-variant-numeric:tabular-nums;font-weight:650;font-size:12.5px}
.tn.lf>.tb{border-left:0;padding-left:20px;margin:0 0 2px}
.tn.gr>summary{font-weight:600}
.leaf{margin:8px 0;max-width:860px}
.leaf .lh{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.leaf .lh b{font-weight:600}
.leaf .meta{font-size:11px;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:0 7px;line-height:1.7}
.leaf .num{margin-left:auto;color:var(--muted);font-variant-numeric:tabular-nums;font-weight:650;font-size:12.5px}
.leaf .ld{color:var(--ink2);font-size:12.5px;margin:2px 0 0 2px}
.tree code.k{font-size:11px;padding:0 4px;background:#eceef2;border-color:#e0e3e9;color:#3f4753}

/* tags */
.legend{display:flex;flex-wrap:wrap;gap:10px 22px;font-size:12.5px;color:var(--muted)}
.legend .lg{display:inline-flex;align-items:center;gap:6px}

h2.sec{font-size:16px;margin:26px 2px 10px;color:var(--ink)}
.cd2{font:10.5px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-style:normal;opacity:.72;
  margin-right:4px;letter-spacing:0}
.tag{display:inline-block;font-size:11.5px;line-height:1.55;padding:1px 7px;border-radius:999px;border:1px solid;
  white-space:nowrap;background:var(--panel);color:var(--muted)}
.tp-bundle{color:#5b31c9;border-color:#dcd2fb;background:#f6f3ff}
.tp-preset{color:#6d34c4;border-color:#e4d7fb;background:#faf6ff}
.tp-frame{color:#1f4ec4;border-color:#d3ddfa;background:#f3f6ff}
.tp-cli{color:#fff;border-color:#181b21;background:#181b21}
.tp-plugin{color:#0d6b62;border-color:#b7e6df;background:#f0fbf9}
.tp-skill{color:#157347;border-color:#c3e8d3;background:#f2fbf6}
.tp-mcp{color:#a5500b;border-color:#f6dcc0;background:#fff8f1}
.tp-other{color:#5b6472;border-color:#e3e5ea;background:#fafbfc}
.tp-dev{color:#8a6100;border-color:#f0e2b6;background:#fdfaef}
.s-active{color:#157347;border-color:#c3e8d3;background:#f2fbf6}
.s-runtime{color:#0d6b62;border-color:#b7e6df;background:#f0fbf9}
.s-preset{color:#1f4ec4;border-color:#d3ddfa;background:#f3f6ff}
.s-opt{color:#9a5b00;border-color:#f3e0be;background:#fffaf0}
.s-inst{color:#5b6472;border-color:#e3e5ea;background:#fafbfc}
.s-out{color:#5b6472;border-color:#d9dde5;background:#fbfcfd;border-style:dashed}
.s-ret{color:#b02a2a;border-color:#f0cccc;background:#fef6f6}
.t-must{border-left:3px solid #b02a2a}
.t-rec{border-left:3px solid #157347}
.t-scene{border-left:3px solid #2456d6}
.t-no{border-left:3px solid #9aa1ad}
.tag.t-must{color:#b02a2a;border-color:#f0cccc;background:#fef6f6}
.tag.t-rec{color:#157347;border-color:#c3e8d3;background:#f2fbf6}
.tag.t-scene{color:#2456d6;border-color:#d3ddfa;background:#f3f6ff}
.tag.t-no{color:#5b6472;border-color:#e3e5ea;background:#fafbfc}
.t-ok{color:#157347;border-color:#c3e8d3;background:#f2fbf6}
.t-off{color:#9a5b00;border-color:#f3e0be;background:#fffaf0}
.t-need{color:#2456d6;border-color:#d3ddfa;background:#f3f6ff}
.t-no2{color:#b02a2a;border-color:#f0cccc;background:#fef6f6}
.t-mix{color:#5b6472;border-color:#e3e5ea;background:#fafbfc}
.t-unk{color:#9a5b00;border-color:#f3e0be;background:#fffaf0}

/* ---- dark palette ---- */
:root[data-theme="dark"] .rec i{color:#2e3743}
:root[data-theme="dark"] .recn{color:#7f8999}
:root[data-theme="dark"] .tn>summary:before{color:#6f7a8b}
:root[data-theme="dark"] .dtree .bl.yes{color:#4ec98a}
:root[data-theme="dark"] .dtree .bl.no{color:#dfa34d}
:root[data-theme="dark"] .tree code.k{background:#212a35;border-color:#2c3644;color:#c6cfdd}
:root[data-theme="dark"] .tp-bundle{color:#bda8ff;border-color:#3c2f68;background:#1e1830}
:root[data-theme="dark"] .tp-preset{color:#c9adff;border-color:#442f6d;background:#211a35}
:root[data-theme="dark"] .tp-frame{color:#96b7ff;border-color:#2e4168;background:#141d2e}
:root[data-theme="dark"] .tp-cli{color:#0e1218;border-color:#c7d1de;background:#c7d1de}
:root[data-theme="dark"] .tp-plugin{color:#5fd6c8;border-color:#1f534d;background:#0f2725}
:root[data-theme="dark"] .tp-skill{color:#6fdc9b;border-color:#25593a;background:#10261b}
:root[data-theme="dark"] .tp-mcp{color:#e9a86a;border-color:#5c3e20;background:#2a1d11}
:root[data-theme="dark"] .tp-other{color:#9aa6b6;border-color:#2c3441;background:#1a212b}
:root[data-theme="dark"] .tp-dev{color:#d7b45f;border-color:#544219;background:#271f10}
:root[data-theme="dark"] .s-active{color:#6fdc9b;border-color:#25593a;background:#10261b}
:root[data-theme="dark"] .s-runtime{color:#5fd6c8;border-color:#1f534d;background:#0f2725}
:root[data-theme="dark"] .s-preset{color:#96b7ff;border-color:#2e4168;background:#141d2e}
:root[data-theme="dark"] .s-opt{color:#dfa94f;border-color:#5b441d;background:#241c11}
:root[data-theme="dark"] .s-inst{color:#9aa6b6;border-color:#2c3441;background:#1a212b}
:root[data-theme="dark"] .s-out{color:#8d97a7;border-color:#343d4a;background:#141a22}
:root[data-theme="dark"] .s-ret{color:#ef9090;border-color:#5c2626;background:#2a1515}
:root[data-theme="dark"] .tag.t-must{color:#ef9090;border-color:#5c2626;background:#2a1515}
:root[data-theme="dark"] .tag.t-rec{color:#6fdc9b;border-color:#25593a;background:#10261b}
:root[data-theme="dark"] .tag.t-scene{color:#96b7ff;border-color:#2e4168;background:#141d2e}
:root[data-theme="dark"] .tag.t-no{color:#9aa6b6;border-color:#2c3441;background:#1a212b}
:root[data-theme="dark"] .t-ok{color:#6fdc9b;border-color:#25593a;background:#10261b}
:root[data-theme="dark"] .t-off{color:#dfa94f;border-color:#5b441d;background:#241c11}
:root[data-theme="dark"] .t-need{color:#96b7ff;border-color:#2e4168;background:#141d2e}
:root[data-theme="dark"] .t-no2{color:#ef9090;border-color:#5c2626;background:#2a1515}
:root[data-theme="dark"] .t-mix{color:#9aa6b6;border-color:#2c3441;background:#1a212b}
:root[data-theme="dark"] .t-unk{color:#dfa94f;border-color:#5b441d;background:#241c11}
:root[data-theme="dark"] .kpi.hl b{color:#a9c2ff}
.stleg{border:1px solid var(--line);border-radius:10px;background:var(--panel2);margin:0 0 14px;padding:0 14px}
.stleg>summary{cursor:pointer;font-size:13px;font-weight:600;padding:10px 0;list-style:none;display:flex;
  align-items:center;gap:8px;color:var(--ink)}
.stleg>summary::-webkit-details-marker{display:none}
.stleg>summary:before{content:"▸";color:var(--muted);font-size:11px;transition:transform .15s}
.stleg[open]>summary:before{transform:rotate(90deg)}
.stleg>summary .hint2{font-weight:400;color:var(--muted);font-size:12px}
.stleg .grid{display:grid;grid-template-columns:1fr;gap:7px;padding:0 0 14px}
.stleg .it{display:grid;grid-template-columns:auto 1fr;gap:4px 10px;align-items:baseline;font-size:12.5px;color:var(--ink2)}
.stleg .it .n{font-weight:600;color:var(--muted);margin-left:8px;font-variant-numeric:tabular-nums}
@media (max-width:760px){
  .theme-seg .lb{display:none}
  .theme-seg button{padding:6px 8px}
  .res-tbl{display:block;table-layout:auto;width:100%}
  .res-tbl thead{display:none}
  .res-tbl tbody,.res-tbl tr{display:block}
  .res-tbl tr{border:1px solid var(--line);border-radius:10px;padding:9px 11px;margin:0 0 8px;background:var(--panel)}
  .res-tbl td{display:block;border:0;padding:2px 0;text-align:left}
  .res-tbl td[data-l]:before{content:attr(data-l) "：";color:var(--muted);font-size:11.5px}
  .stleg .grid{grid-template-columns:1fr;grid-auto-flow:row;grid-template-rows:none}
  .stleg .it{grid-template-columns:1fr}
  .stleg .it .tag{justify-self:start}
  .twocol{grid-template-columns:1fr;gap:8px}
}

/* tables */
.scroll{overflow:auto;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
.scroll.tall{max-height:70vh}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:9px 11px;border-bottom:1px solid var(--line2);vertical-align:top}
th{background:var(--panel2);color:var(--muted);font-weight:600;font-size:12px;letter-spacing:.01em}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--hover)}
.scroll.tall th{position:sticky;top:0;z-index:2;box-shadow:inset 0 -1px 0 var(--line)}
table.mini{font-size:13px}
table.mini td{padding:8px 10px}
table.mini code{font-size:12px}
th.sortable{cursor:pointer;user-select:none}
th.sortable:hover{color:var(--ink)}
th .ar{opacity:.4;font-size:10px}

/* toolbar */
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 12px}
.bar select,.bar input{font:inherit;font-size:13px;padding:6px 9px;border:1px solid var(--line);border-radius:8px;
  background:var(--panel);color:var(--ink);min-width:0}
.bar input[type=search]{flex:1 1 200px}
.bar .cnt{font-size:12.5px;color:var(--muted);margin-left:auto;white-space:nowrap}

/* misc */
.pkg{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px;font-weight:600;
  word-break:break-word}
.pkg+.lnk{margin-top:2px}
.lnk a{font-size:11.5px;color:var(--muted)}
.lnk a:hover{color:var(--accent)}
.ok{color:var(--ok)}.no{color:var(--bad)}
footer{border-top:1px solid var(--line);padding:18px 0 40px;color:var(--muted);font-size:12.5px}

/* 回到顶部 */
.totop{position:fixed;right:24px;bottom:24px;z-index:40;width:42px;height:42px;display:inline-flex;
  align-items:center;justify-content:center;border:1px solid var(--line);border-radius:50%;
  background:var(--panel);color:var(--ink2);cursor:pointer;box-shadow:0 2px 10px rgba(16,24,40,.12);
  opacity:0;visibility:hidden;transform:translateY(8px);
  transition:opacity .18s,transform .18s,visibility .18s,background .15s,color .15s,border-color .15s}
.totop.show{opacity:1;visibility:visible;transform:none}
.totop:hover{background:var(--panel2);color:var(--ink);border-color:var(--muted)}
.totop:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.totop svg{width:17px;height:17px;display:block}
:root[data-theme="dark"] .totop{box-shadow:0 2px 12px rgba(0,0,0,.55)}

@media (max-width:980px){
  .kpis{grid-template-columns:repeat(3,1fr)}
  .hdr h1{font-size:23px}
}
@media (max-width:720px){
  .wrap{padding:0 14px}
  .hdr{padding:24px 0 18px}
  .hdr h1{font-size:20px}
  .hdr .lead{font-size:14px}
  .ghbtn span{display:none}
  .ghbtn{padding:6px 8px}
  .kpis{grid-template-columns:repeat(2,1fr);gap:8px}
  .kpi b{font-size:18px}
  .card{padding:15px 14px}
  .scroll{border:0;background:transparent;overflow:visible}
  .scroll.tall{max-height:none}
  table{font-size:13px}
  table thead{display:none}
  table tbody tr{display:block;background:var(--panel);border:1px solid var(--line);border-radius:10px;
    padding:10px 12px;margin-bottom:8px}
  table tbody td{display:block;border:0;padding:2px 0;text-align:left!important}
  table tbody td[data-l]:before{content:attr(data-l)"：";color:var(--muted);font-size:11.5px}
  .tree .l3{margin-left:20px}
  .dtree{padding:12px 12px}
  .tn>.tb{margin-left:4px;padding-left:9px}
  .tn.lf>.tb{padding-left:14px}
  .dtree .bl{min-width:44px}
  .leaf .num{margin-left:0}
  .leaf .ld{font-size:12px}
  .totop{right:14px;bottom:14px;width:38px;height:38px}
}
'''

# 首屏前置：在样式生效前定好主题，避免闪白
THEME_BOOT = '''<script>(function(){try{
var m=localStorage.getItem("dsh-theme")||"auto";
var d=m==="dark"||(m==="auto"&&window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches);
document.documentElement.setAttribute("data-theme",d?"dark":"light");
}catch(e){}})();</script>'''

JS = r'''
const ROWS = __ROWS__;
const TYPE_CLS = {"Bundle":"tp-bundle","Preset":"tp-preset","框架":"tp-frame","CLI":"tp-cli","Plugin":"tp-plugin",
  "Skill":"tp-skill","MCP":"tp-mcp","其他":"tp-other","开发工具":"tp-dev"};
const CODE = {
  "1a":["s-active","已激活 · 组合层"],
  "1b":["s-runtime","已激活 · 运行时"],
  "1c":["s-preset","已激活 · 预设"],
  "2a":["s-opt","随包未启用 · 可选 bundle"],
  "2b":["s-inst","随包未启用 · 库或内部件"],
  "2c":["s-preset","随包未启用 · 仅非默认预设"],
  "3a":["s-out","官方按需 · 未落盘"],
  "3b":["s-out","官方可选 · 未落盘"],
  "3c":["s-out","无官方入口 · 未落盘"],
  "\u2014":["s-ret","已下架"]
};
const CODE_ORDER = ["1a","1b","1c","2a","2b","2c","3a","3b","3c","\u2014"];
const GH = "https://github.com/deepseek-ai/deepseek-harness";

function e(s){return String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}
function num(n){return n==null?'<span class="muted">—</span>':n.toLocaleString();}
function repoLink(r){
  if(r.path) return '<a href="'+GH+'/blob/master/'+r.path+'" target="_blank" rel="noopener">源码</a>';
  if(r.name.indexOf("libreoffice-kit")===0) return '<a href="https://github.com/deepseek-ai/dsh-libreoffice-kit" target="_blank" rel="noopener">仓库</a>';
  if(r.name.indexOf("node-addon")===0) return '<a href="'+GH+'/tree/master/native/system" target="_blank" rel="noopener">仓库</a>';
  return '<a href="'+GH+'/tree/master/packages" target="_blank" rel="noopener">仓库</a>';
}
function badge(code){
  const m=CODE[code]||["s-out","未核实"];
  return '<span class="tag '+m[0]+'"><i class="cd2">'+e(code)+'</i>'+e(m[1])+'</span>';
}
function tags(r){ return '<span title="'+e(r.statusLabel)+'">'+badge(r.code)+'</span>'; }
function rowDefault(r){
  return '<tr><td><span class="pkg">'+e(r.name)+'</span><div class="lnk">'+
    '<a href="https://www.npmjs.com/package/'+r.pkg+'" target="_blank" rel="noopener">npm</a> · '+repoLink(r)+'</div></td>'+
    '<td><span class="tag '+(TYPE_CLS[r.type]||'tp-other')+'">'+e(r.type)+'</span></td>'+
    '<td>'+tags(r)+'<div class="sub">'+e(r.ev)+'</div></td></tr>';
}
function rowAll(r){
  return '<tr><td><span class="pkg">'+e(r.name)+'</span><div class="lnk">'+
    '<a href="https://www.npmjs.com/package/'+r.pkg+'" target="_blank" rel="noopener">npm</a> · '+repoLink(r)+'</div></td>'+
    '<td data-l="类型"><span class="tag '+(TYPE_CLS[r.type]||'tp-other')+'">'+e(r.type)+'</span></td>'+
    '<td data-l="方向"><span class="tag tp-other">'+e(r.dir)+'</span></td>'+
    '<td data-l="用途">'+e(r.purpose)+(r.desc?'<div class="sub">'+e(r.desc)+'</div>':'')+'</td>'+
    '<td data-l="版本" class="sub nowrap"><code>'+e(r.version)+'</code><br>'+e(r.date)+'<br>'+e(r.maint)+'</td>'+
    '<td data-l="默认状态">'+tags(r)+'</td>'+
    '<td data-l="周下载" class="c num">'+num(r.weekly)+'</td></tr>';
}
function build(root, opts){
  const S={type:"",dir:"",status:"",q:"",key:"name",dirn:1};
  const body=root.querySelector("[data-rows]");
  const cnt=root.querySelector("[data-cnt]");
  const fType=root.querySelector('[data-f="type"]');
  const fDir=root.querySelector('[data-f="dir"]');
  const fSt=root.querySelector('[data-f="status"]');
  const fQ=root.querySelector('[data-f="q"]');
  const base=ROWS.filter(opts.filter||(()=>true));
  if(fType) [...new Set(base.map(r=>r.type))].sort().forEach(v=>fType.add(new Option(v,v)));
  if(fDir) [...new Set(base.map(r=>r.dir))].sort().forEach(v=>fDir.add(new Option(v,v)));
  if(fSt){
    const cnts={};base.forEach(r=>cnts[r.code]=(cnts[r.code]||0)+1);
    CODE_ORDER.filter(k=>cnts[k]).forEach(k=>fSt.add(new Option(k+" "+CODE[k][1]+"（"+cnts[k]+"）",k)));
  }
  function render(){
    let list=base.slice();
    if(S.type) list=list.filter(r=>r.type===S.type);
    if(S.dir) list=list.filter(r=>r.dir===S.dir);
    if(S.status) list=list.filter(r=>r.code===S.status);
    if(S.q){const q=S.q.toLowerCase();list=list.filter(r=>(r.name+" "+r.purpose+" "+r.desc+" "+r.dir).toLowerCase().includes(q));}
    list.sort((a,b)=>{
      let x=a[S.key],y=b[S.key];
      if(S.key==="weekly"){x=x==null?-1:x;y=y==null?-1:y;return (x-y)*S.dirn;}
      if(S.key==="date") return (x<y?-1:x>y?1:0)*S.dirn;
      return String(x).localeCompare(String(y),"zh")*S.dirn;
    });
    body.innerHTML=list.map(opts.mode==="all"?rowAll:rowDefault).join("");
    if(cnt) cnt.textContent="显示 "+list.length+" / "+base.length+" 条";
  }
  root.querySelectorAll("th.sortable").forEach(th=>{
    th.addEventListener("click",()=>{
      const k=th.dataset.k;
      if(S.key===k) S.dirn=-S.dirn; else {S.key=k;S.dirn=1;}
      root.querySelectorAll("th.sortable .ar").forEach(a=>a.textContent="");
      const ar=th.querySelector(".ar"); if(ar) ar.textContent=S.dirn>0?" ▲":" ▼";
      render();
    });
  });
  [fType,fDir,fSt].forEach(el=>{if(el)el.addEventListener("change",()=>{
    S.type=fType?fType.value:"";S.dir=fDir?fDir.value:"";S.status=fSt?fSt.value:"";render();});});
  if(fQ) fQ.addEventListener("input",()=>{S.q=fQ.value;render();});
  render();
}

const links=[...document.querySelectorAll(".tabs a")];
const secs=links.map(a=>document.querySelector(a.getAttribute("href")));
const spy=()=>{
  const y=window.scrollY+120;
  let idx=0;
  secs.forEach((s_,i)=>{if(s_&&s_.offsetTop<=y) idx=i;});
  links.forEach((a,i)=>a.classList.toggle("cur",i===idx));
};
window.addEventListener("scroll",spy,{passive:true});
spy();

document.querySelectorAll(".tbar .btn").forEach(btn=>{
  btn.addEventListener("click",()=>{
    const open=btn.dataset.act==="expand";
    document.querySelectorAll("#dtree details").forEach(d=>{d.open=open;});
  });
});

const d1=document.getElementById("wrap-default");
if(d1) build(d1,{mode:"default",filter:r=>["active","runtime","preset","installed","optional","profile"].indexOf(r.status)>=0});
const d2=document.getElementById("wrap-all");
if(d2) build(d2,{mode:"all"});

/* ---------------- 主题：自动 / 亮色 / 暗色（三选一） ---------------- */
(function(){
  var KEY="dsh-theme";
  var seg=document.getElementById("themeSeg");
  var btns=seg?[].slice.call(seg.querySelectorAll("button")):[];
  var mq=window.matchMedia?window.matchMedia("(prefers-color-scheme: dark)"):null;
  var mode="auto";
  try{mode=localStorage.getItem(KEY)||"auto";}catch(e){}
  if(mode!=="light"&&mode!=="dark")mode="auto";
  function paint(){
    var dark=(mode==="dark")||(mode==="auto"&&mq&&mq.matches);
    document.documentElement.setAttribute("data-theme",dark?"dark":"light");
    btns.forEach(function(b){
      var on=b.dataset.mode===mode;
      b.setAttribute("aria-pressed",on?"true":"false");
      b.classList.toggle("on",on);
    });
  }
  btns.forEach(function(b){
    b.addEventListener("click",function(){
      mode=b.dataset.mode;
      try{localStorage.setItem(KEY,mode);}catch(e){}
      paint();
    });
  });
  if(mq){
    var on=function(){if(mode==="auto")paint();};
    if(mq.addEventListener)mq.addEventListener("change",on);
    else if(mq.addListener)mq.addListener(on);
  }
  paint();
})();

/* ---------------- 回到顶部 ---------------- */
(function(){
  var b=document.getElementById("toTop");
  if(!b) return;
  var on=false;
  function upd(){
    var y=window.pageYOffset||document.documentElement.scrollTop||0;
    var show=y>560;
    if(show!==on){on=show;b.classList.toggle("show",show);}
  }
  window.addEventListener("scroll",upd,{passive:true});
  window.addEventListener("resize",upd,{passive:true});
  upd();
  b.addEventListener("click",function(){
    var rm=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({top:0,behavior:rm?"auto":"smooth"});
  });
})();
'''

HTML = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>@deepseek-ai 官方包调研报告 · DeepSeek Harness</title>
{THEME_BOOT}
<style>{CSS}</style>
</head>
<body>
<header class="hdr"><div class="wrap">
  <div class="hdr-top">
    <p class="eyebrow">DeepSeek Harness · npm 生态</p>
    <div class="hdr-actions">
      <a class="ghbtn" href="https://github.com/sogeisetsu/dsh-ecosystem-report" target="_blank" rel="noopener noreferrer" aria-label="在 GitHub 查看仓库" title="在 GitHub 查看仓库">
        <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/></svg><span>GitHub</span>
      </a>
      <div class="theme-seg" id="themeSeg" role="group" aria-label="主题模式">
      <button type="button" data-mode="auto" aria-pressed="true" title="跟随系统设置"><i class="ic">◐</i><span class="lb">自动</span></button>
      <button type="button" data-mode="light" aria-pressed="false" title="只用亮色"><i class="ic">☀</i><span class="lb">亮色</span></button>
      <button type="button" data-mode="dark" aria-pressed="false" title="只用暗色"><i class="ic">☾</i><span class="lb">暗色</span></button>
      </div>
    </div>
  </div>
  <h1>@deepseek-ai 官方包全景调研</h1>
  <p class="lead">截至 2026-11-08，npm <code>@deepseek-ai</code> 作用域共有 <b>{n_total}</b> 个公开包，全部服务于 DeepSeek Harness（dsh）。执行一次 <code>npx @deepseek-ai/dsh web</code> 会在磁盘上落下 <b>{n_inst}</b> 个包，其中 <b>{n_act}</b> 个默认加载、<b>{n_off}</b> 个已落盘但未启用；余下 <b>{n_out}</b> 个不在依赖闭包内，需另行获取。</p>
  <div class="meta">
    <span>检索日期：2026-11-08</span>
    <span>数据抓取：npm registry、GitHub、官方文档</span>
    <span>统计口径：<code>@deepseek-ai/</code> 前缀精确匹配，共 {n_total} 个</span>
    <span>判定依据：依赖闭包递归展开 + 包内 cordis.patch.yml</span>
  </div>
  <div class="kpis">
    <div class="kpi hl"><b>{n_total}</b><span>作用域内包总数</span></div>
    <div class="kpi"><b>{n_inst}</b><span>随 dsh 落盘</span></div>
    <div class="kpi"><b>{n_act}</b><span>默认加载</span></div>
    <div class="kpi"><b>{n_off}</b><span>已落盘未启用</span></div>
    <div class="kpi"><b>{n_out}</b><span>不在闭包内</span></div>
  </div>
</div></header>

<nav class="tabsbar"><div class="wrap"><div class="tabs">
  <a href="#s-overview" class="cur">概览</a>
  <a href="#s-default">默认安装清单</a>
  <a href="#s-all">全量分类</a>
  <a href="#s-advice">安装建议</a>
  <a href="#s-community">社区与推荐</a>
  <a href="#s-method">方法与局限</a>
</div></div></nav>

<main class="wrap">

<!-- ================= 概览 ================= -->
<section class="sec" id="s-overview">
  <div class="card">
    <h2>结论摘要</h2>
    <ol class="lead2">
      <li><b>生态高度集中。</b>{n_total} 个包中，{n_inst} 个由 <code>@deepseek-ai/dsh</code> 及其 bundle 的依赖闭包一次性带入，用户无需逐个安装。</li>
      <li><b>落盘不等于启用。</b>{n_inst} 个已落盘包中只有 {n_act} 个默认加载，{n_off} 个处于"在磁盘上但未加载"状态。</li>
      <li><b>未加载分三种原因。</b>官方可选 bundle（{n_opt} 个，开关即用）、库与内部件（{n_lib} 个，由使用方加载）、仅其他预设或入口声明（{n_preset_other + n_profile} 个）。</li>
      <li><b>不在闭包内的 {n_out} 个包用途有限。</b>其中 {n_ondemand} 个为官方按需包，{n_opt_off} 个为官方可选但未随包，其余 {n_noentry} 个无官方入口。</li>
      <li><b>两个易误判点：</b>Office Skill（<code>dsh-skill-office</code>）与 MCP 客户端（<code>dsh-mcp-client</code>）都随包落盘，但 Web 入口默认不加载：前者只在 sdk 入口的插件行里启用，后者需在插件页或配置中挂载。</li>
      <li><b>外部清单要逐个核对。</b>第三方整理的 19 项社区增强清单里，5 项在 npm 查不到（只在 GitHub）、1 项已废弃、1 项是官方随包件（不属社区，未列入社区表），剩下 12 项能按包名安装（其中 2 项要先写对实际包名）。合并后的清单见「社区与推荐 → 社区包精选」。</li>
    </ol>
  </div>

  <div class="card">
    <h2>判定路径与状态定义</h2>
    <p class="hint">按三步判断任意一个包：先看作用域，再看有没有装到磁盘，最后看装完是否加载。走到最末一层就是它的状态。点击任一层标题可单独折叠，下方按钮可整体展开或递归折叠。</p>
    <div class="tbar">
      <button type="button" class="btn" data-act="expand">全部展开</button>
      <button type="button" class="btn" data-act="collapse">全部折叠</button>
      <span class="sub">每一层都可单独折叠，可一直收到最末级的状态条目</span>
    </div>
    <div class="dtree" id="dtree">

      <details class="tn" open>
        <summary><span class="qn">第 1 步</span>它是否在 <code>@deepseek-ai</code> 作用域下？</summary>
        <div class="tb">
          <div class="bline"><b class="bl no">不在</b>社区包，不计入 {n_total} 个，需自行安装（见「社区与推荐」）</div>
          <details class="tn" open>
            <summary><b class="bl yes">在</b>共 {n_total} 个，继续判断 <span class="sepc">→</span> <span class="qn">第 2 步</span>它是否随 <code>dsh</code> 一起装到磁盘？</summary>
            <div class="tb">
              <details class="tn" open>
                <summary><b class="bl no">没装</b>{n_out} 个 <span class="sepc">→</span> <span class="qn">追问</span>官方给不给安装入口？</summary>
                <div class="tb">
                  <details class="tn gr" open>
                    <summary><b class="bl yes">有入口</b>{n_ondemand + n_opt_off} 个，可以一键安装</summary>
                    <div class="tb">{leaf_3a}{leaf_3b}</div>
                  </details>
                  <details class="tn gr" open>
                    <summary><b class="bl no">没入口</b>{n_noentry + n_retired} 个，只能自行 npm 安装</summary>
                    <div class="tb">{leaf_3c}{leaf_ret}</div>
                  </details>
                </div>
              </details>
              <details class="tn" open>
                <summary><b class="bl yes">装了</b>{n_inst} 个 <span class="sepc">→</span> <span class="qn">第 3 步</span>装完之后，它默认会加载吗？</summary>
                <div class="tb">
                  <details class="tn gr" open>
                    <summary><b class="bl yes">会加载</b>{n_act} 个</summary>
                    <div class="tb">{leaf_1a}{leaf_1b}{leaf_1c}</div>
                  </details>
                  <details class="tn gr" open>
                    <summary><b class="bl no">不加载</b>{n_off} 个，按原因分三种</summary>
                    <div class="tb">{leaf_2a}{leaf_2b}{leaf_2c}</div>
                  </details>
                </div>
              </details>
            </div>
          </details>
        </div>
      </details>

    </div>
    <p class="sub" style="margin:12px 0 0">{n_total} = {n_inst}（落盘）+ {n_out}（未落盘）；{n_inst} = {n_act}（加载）+ {n_off}（未启用）。</p>
  </div>

  <div class="card">
    <h2>Profile 模板：不同入口加载不同组合</h2>
    <div class="scroll"><table class="mini">
      <thead><tr><th style="width:12%">profile</th><th style="width:26%">启动命令</th><th style="width:32%">bundle 组合</th><th style="width:30%">用途</th></tr></thead>
      <tbody>{prof_rows}</tbody></table></div>
    <p class="sub" style="margin:10px 0 0">来源：<code>@deepseek-ai/dsh-official-bundles</code> 的 <code>PROFILE_TEMPLATES</code> 常量（npm 包 <code>lib/index.js</code>）；命令见 <code>apps/cli/README.md</code>。</p>
    <div class="note" style="margin-top:10px">
      <b>另有 <code>desktop</code> profile 不在上表内。</b>它由 Electron 桌面端独占，位于 <code>$DSH_HOME/profiles/desktop</code>，运行时就是「Electron 外壳 + 完整 Web 应用」，CLI 拒绝启动或查看它。<b>但「复用 Web 模板」只指 bundle 清单，不代表与 <code>web</code> profile 共享状态：</b>
      <div class="twocol">
        <div>
          <h4>复用的是模板</h4>
          <p>新建 desktop profile 时按 Web 模板生成 bundle 列表（<code>dsh-base</code> + <code>dsh-web-app</code>），此后两者可各自增删只属于自己的插件。</p>
        </div>
        <div>
          <h4>状态完全独立</h4>
          <p>可执行包、插件激活、lockfile 与 <code>node_modules</code> 互不共享。<code>web</code> profile 里装的插件，在 desktop profile 里看不到，反之亦然。</p>
        </div>
      </div>
      <p style="margin:0 0 6px">给 desktop 装插件：先启动一次桌面端完成 profile 初始化，退出后执行 <code>dsh plugin --profile desktop add &lt;包名&gt;</code>，再打开桌面端生效。桌面端另带 Office Skill 运行时（<code>runtime/office-skills</code>）。</p>
      <p class="sub" style="margin:0">依据：<code>apps/desktop/README.md</code> 的状态归属表 —— CLI 与 Desktop 共享 <code>$DSH_HOME</code> 下的产品数据，但「never executable packages, plugin activation, lockfiles, or <code>node_modules</code>」。</p>
    </div>
  </div>

  <div class="card">
    <h2>Agent 预设：第二层开关</h2>
    <div class="scroll"><table class="mini">
      <thead><tr><th style="width:12%">预设</th><th style="width:8%" class="c">order</th><th style="width:10%" class="c">成员包数</th><th style="width:70%">差异</th></tr></thead>
      <tbody>{preset_rows}</tbody></table></div>
    <p class="sub" style="margin:10px 0 0">来源：<code>@deepseek-ai/dsh-web-app@0.2.2-rc.1</code> 内的 <code>presets/*.patch.yml</code>；<code>order: 1</code> 的 standard 为默认。</p>
  </div>
</section>

<!-- ================= 默认安装清单 ================= -->
<section class="sec" id="s-default">
  <h2 class="sec-t">默认安装清单</h2>
  <p class="sec-d">随 dsh 落盘的 {n_inst} 个包，以及它们是否在加载。</p>
  <div class="card" id="wrap-default">
    <h2>状态明细</h2>
    <p class="hint">范围为随 <code>dsh</code> 落盘的包。<b>已激活</b>=正在加载；<b>随包·未启用</b>=在磁盘上但未加载。各状态的含义见「全量分类」中的状态说明，悬停标签可查看完整判定文案。</p>
    <div class="bar">
      <select data-f="status"><option value="">全部状态</option></select>
      <input type="search" data-f="q" placeholder="搜索包名">
      <span class="cnt" data-cnt></span>
    </div>
    <div class="scroll tall"><table>
      <thead><tr><th style="width:34%">包名</th><th style="width:12%">类型</th><th style="width:54%">状态与依据</th></tr></thead>
      <tbody data-rows></tbody></table></div>
  </div>
</section>

<!-- ================= 全量分类 ================= -->
<section class="sec" id="s-all">
  <h2 class="sec-t">全量分类</h2>
  <p class="sec-d">作用域内 {n_total} 个包的类型、方向、状态与下载量。</p>
  <div class="card">
    <h2>分类方法</h2>
    <p class="hint">类型按包的职责划分，一包只归一类；方向按主要用途划分，一包只归一个主方向。</p>
    <div class="legend">
      <span class="lg"><span class="tag tp-cli">CLI</span>命令入口</span>
      <span class="lg"><span class="tag tp-bundle">Bundle</span>官方组合包</span>
      <span class="lg"><span class="tag tp-preset">Preset</span>预设声明</span>
      <span class="lg"><span class="tag tp-frame">框架</span>接缝与协议</span>
      <span class="lg"><span class="tag tp-plugin">Plugin</span>可装卸插件</span>
      <span class="lg"><span class="tag tp-skill">Skill</span>技能</span>
      <span class="lg"><span class="tag tp-mcp">MCP</span>客户端与资源</span>
      <span class="lg"><span class="tag tp-other">其他</span>库与杂项</span>
      <span class="lg"><span class="tag tp-dev">开发工具</span>测试与示例</span>
    </div>
  </div>
  <div class="card" id="wrap-all">
    <h2>包清单与筛选</h2>
    <details class="stleg" open>
      <summary>状态说明<span class="hint2">下拉菜单 9 个选项对应下列 10 类（预设与随包未启用各按原因拆为两类），末尾为当前数量</span></summary>
      <div class="grid">{legend_html}</div>
    </details>
    <div class="bar">
      <select data-f="type"><option value="">全部类型</option></select>
      <select data-f="dir"><option value="">全部方向</option></select>
      <select data-f="status"><option value="">全部状态</option></select>
      <input type="search" data-f="q" placeholder="搜索包名、用途或描述">
      <span class="cnt" data-cnt></span>
    </div>
    <div class="scroll tall"><table>
      <thead><tr>
        <th class="sortable" data-k="name" style="width:22%">包名 <span class="ar"></span></th>
        <th class="sortable" data-k="type" style="width:8%">类型 <span class="ar"></span></th>
        <th class="sortable" data-k="dir" style="width:8%">方向 <span class="ar"></span></th>
        <th style="width:28%">用途</th>
        <th class="sortable" data-k="date" style="width:14%">版本与发布 <span class="ar"></span></th>
        <th class="sortable" data-k="status" style="width:13%">状态 <span class="ar"></span></th>
        <th class="sortable" data-k="weekly" style="width:7%" class="c">周下载 <span class="ar"></span></th>
      </tr></thead>
      <tbody data-rows></tbody></table></div>
    <p class="sub" style="margin:10px 0 0">下载量为 registry 搜索接口的滚动 7 天快照（2026-11-08 抓取）。破折号表示接口未返回该包数据，不代表为 0。该生态整包安装会拉取完整闭包，多数包下载量处于同一量级，不宜作为热度指标。</p>
  </div>
</section>

<!-- ================= 安装建议 ================= -->
<section class="sec" id="s-advice">
  <h2 class="sec-t">安装建议</h2>
  <p class="sec-d">按当前状态与能力缺口分层，官方包与社区包分列。</p>
  <h2 class="sec">一、官方包建议</h2>
  {tier_html}

  <div class="card">
    <h2>执行顺序</h2>
    <ol class="lead2">
      <li>最小可用：<code>npx @deepseek-ai/dsh web</code> → 填写 DeepSeek API Key → 选择工作区。</li>
      <li>长期使用：开启 <code>terminal-bundle</code>、<code>session-search</code>、<code>session-titles</code>；接受自动评审再加 <code>auto-review</code>。</li>
      <li>文档处理：开启 <code>dsh-skill-office</code>（已落盘，默认未启用）。</li>
      <li>外部工具接入：配置 <code>dsh-mcp-client</code>，挂载 MCP 服务端。</li>
      <li>跨 Agent 协作：安装 <code>dsh-subagent-claude-code</code> 或 <code>dsh-subagent-codex</code>（官方按需包）。</li>
    </ol>
    <div class="note info" style="margin-top:12px">
      <b>社区安装组合</b>（三种起步路线）：
      <ul class="lead2" style="margin:6px 0 0">
        <li><b>极简起步（只补硬伤）</b>：<code>dsh-better-sidebar</code> + <code>dsh-simple-memory</code> + <code>cc-safety-net</code> + <code>@wildusk/dsh-backup</code>。</li>
        <li><b>搜索零成本</b>：在极简起步上把搜索换成 <code>@liustack/modsearch</code>，或 <code>@sheep233_/dsh-web-search-free</code>（Parallel + Exa 双免费后端）。</li>
        <li><b>全面托管</b>：SQY-DSH-PLUGIN 四件套 + <code>dshmarket</code> + <code>EverOS</code> + <code>@michengai/dsh-automation</code>。</li>
        <li><b>避免踩坑</b>：不装重复的「插件管理插件」；记忆管理只在需要跨后端统一视图时装；MCP 工具少于 10 个时不上渐进披露。</li>
      </ul>
    </div>
  </div>

  <h2 class="sec">二、社区包补充建议</h2>
  <div class="card">
    <p class="lead2">以下为第三方包，<b>不属于官方范畴，无兼容承诺</b>。入选条件：近 7 天有发版、周下载不低于 2 万或星数不低于 900、补足官方未覆盖的能力。</p>
    <p class="sub" style="margin:0 0 10px">本表是「社区包精选」按门槛筛出的<b>安装决策子集</b>：近 7 天有发版，且周下载不低于 2 万或星数不低于 900，并补足官方未覆盖的能力；定位列写明具体补的是哪一处原生短板。完整资料（推荐值、出处、说明）见「社区与推荐 → 社区包精选」。</p>
    <div class="scroll"><table class="mini">
      <thead><tr><th style="width:7%">优先级</th><th style="width:22%">包</th><th style="width:14%">仓库</th><th style="width:11%">版本</th><th style="width:7%" class="c">星</th><th style="width:9%" class="c">周下载</th><th style="width:30%">定位</th></tr></thead>
      <tbody>
        <tr><td data-l="优先级"><span class="tag t-rec">首选</span></td><td data-l="包"><code>dshmarket</code></td><td data-l="仓库" class="sub">dsh-market/dsh-market</td><td data-l="版本" class="sub">1.73.15</td><td data-l="星" class="c">11k</td><td data-l="周下载" class="c">308,046</td><td data-l="定位">补原生无插件市场：提供发现、比较与安装入口</td></tr>
        <tr><td data-l="优先级"><span class="tag t-rec">首选</span></td><td data-l="包"><code>dsh-context</code></td><td data-l="仓库" class="sub">bowenliang123/dsh-context</td><td data-l="版本" class="sub">0.82.2</td><td data-l="星" class="c">4.5k</td><td data-l="周下载" class="c">144,773</td><td data-l="定位">补原生上下文不可见：Token 构成、缓存命中与子代理开销可视化</td></tr>
        <tr><td data-l="优先级"><span class="tag t-scene">可选</span></td><td data-l="包"><code>dsh-better-sidebar</code></td><td data-l="仓库" class="sub">omdsh-dev/DSH-better-sidebar</td><td data-l="版本" class="sub">0.30.1</td><td data-l="星" class="c">5.0k</td><td data-l="周下载" class="c">78,109</td><td data-l="定位">补原生侧栏只有基础预览：文件树、编辑器、变更与任务整合</td></tr>
        <tr><td data-l="优先级"><span class="tag t-scene">可选</span></td><td data-l="包"><code>@liustack/modlens</code></td><td data-l="仓库" class="sub">liustack/modlens</td><td data-l="版本" class="sub">3.27.2</td><td data-l="星" class="c">4.8k</td><td data-l="周下载" class="c">86,518</td><td data-l="定位">补原生纯文本无视觉：截图问答与界面元素定位，依赖外部 CLI</td></tr>
        <tr><td data-l="优先级"><span class="tag t-scene">可选</span></td><td data-l="包"><code>@anionex/dsh-vision-toolkit</code></td><td data-l="仓库" class="sub">Anionex/dsh-vision-toolkit</td><td data-l="版本" class="sub">0.1.49</td><td data-l="星" class="c">931</td><td data-l="周下载" class="c">2,911</td><td data-l="定位">补原生无视觉：OCR 与图像问答；与 ModLens 二选一</td></tr>
        <tr><td data-l="优先级"><span class="tag t-no2">已过时</span></td><td data-l="包"><code>dsh-at-file</code></td><td data-l="仓库" class="sub">FSMargoo/dsh-at-file</td><td data-l="版本" class="sub">0.6.3</td><td data-l="星" class="c">563</td><td data-l="周下载" class="c">41,797</td><td data-l="定位">原生已内置 <code>@file</code> 与 <code>@session</code> 引用，无需再装；作者也建议新装改用官方实现</td></tr>
        <tr><td data-l="优先级"><span class="tag t-scene">可选</span></td><td data-l="包"><code>@deepseek-harness-tui/dsh-tui</code></td><td data-l="仓库" class="sub">ccch1mneyyy/dsh-TUI</td><td data-l="版本" class="sub">0.19.0</td><td data-l="星" class="c">7.1k</td><td data-l="周下载" class="c">21,210</td><td data-l="定位">补原生只有 Web 入口：提供全屏终端 TUI，需 Node 22.19 及以上</td></tr>
        <tr><td data-l="优先级"><span class="tag t-rec">首选</span></td><td data-l="包"><code>billion-context</code></td><td data-l="仓库" class="sub">ranxianglei/billion-context</td><td data-l="版本" class="sub">0.1.213</td><td data-l="星" class="c">4.8k</td><td data-l="周下载" class="c">848,207</td><td data-l="定位">补原生仅自动 compaction：可按需压缩旧上下文</td></tr>
        <tr><td data-l="优先级"><span class="tag t-rec">首选</span></td><td data-l="包"><code>cc-safety-net</code></td><td data-l="仓库" class="sub">kenryu42/cc-safety-net</td><td data-l="版本" class="sub">2.7.5</td><td data-l="星" class="c">2k</td><td data-l="周下载" class="c">47,384</td><td data-l="定位">补原生沙箱管不到插件代码：执行前拦截破坏性命令与敏感文件访问</td></tr>
        <tr><td data-l="优先级"><span class="tag t-scene">可选</span></td><td data-l="包"><code>@michengai/dsh-skills-manager</code></td><td data-l="仓库" class="sub">MichengAI/dsh-skills-manager</td><td data-l="版本" class="sub">1.3.0</td><td data-l="星" class="c">506</td><td data-l="周下载" class="c">50,872</td><td data-l="定位">补原生技能无管理 UI：可视化启停、编辑、安装与备份回退</td></tr>
      </tbody></table></div>
    <p class="sub" style="margin:10px 0 0">星数取自 shields.io 接口，2026-11-08 抓取。DSH 处于 developer preview，社区插件随版本迭代失效属常态。</p>
  </div>
</section>

<!-- ================= 社区与官方推荐 ================= -->
<section class="sec" id="s-community">
  <h2 class="sec-t">社区与推荐</h2>
  <p class="sec-d">从社区里筛出的第三方包，按用途与推荐值排序；不是社区生态的完整清单。安装建议节的「社区包补充建议」是本表按过线门槛筛出的子集，另附安装优先级。</p>
  <div class="card">
    <h2>社区包精选</h2>
    <p class="hint">这 {n_res} 项是<b>从社区里挑出来的精选</b>，不是社区包的完整清单——npm 上带 <code>dsh</code> 关键词的第三方包数量远多于此。收录以社区选型清单中出现的插件为界，含 npm 未发布、仅 GitHub 分发与 bundle 内组件；数据缺失以「—」标注，不作推测。它们均不在 <code>@deepseek-ai</code> 作用域内，不计入 {n_total} 个官方包统计。数据为 2026-11-08 实测：npm registry 取版本与发布日期，shields.io 取仓库星数，<code>downloads/point</code> 取近 7 天下载量；npm 查不到的直接到 GitHub 找同名仓库。</p>
    <p class="hint"><b>推荐值口径</b>：<b>5</b> 日常必装（周下载 ≥ 10 万、星数 ≥ 4k，且本周有发版）；<b>4</b> 强烈推荐（单一场景显著提升，或补官方明确不做的能力）；<b>3</b> 值得一试（场景明确，但受众窄、久未更新或有配置成本）；<b>2</b> 尝鲜（体量小、需额外依赖）；<b>1</b> 仅记录（0–1 星、npm 未发布或已有更优替代）。标注「外部选型清单」的条目按清单中的推荐强度定级，不完全由星数与下载量决定。</p>
    <div class="bar" style="margin:0 0 10px">
      <label for="sceneSel" class="sub">场景</label>
      <select id="sceneSel"><option value="">全部（{n_res}）</option>{scene_options}</select>
      <span class="cnt" id="sceneCnt">显示 {n_res} / {n_res}</span>
    </div>
    <div class="scroll tall"><table class="wide res-tbl">
      <colgroup><col style="width:10%"><col style="width:21%"><col style="width:13%"><col style="width:11%"><col style="width:12%"><col style="width:11%"><col style="width:22%"></colgroup>
      <thead><tr><th class="c">推荐值</th><th>包 / 仓库</th><th>场景</th><th>版本 · 日期</th><th>星 / 周下载</th><th>推荐出处</th><th>说明</th></tr></thead>
      <tbody>{res_html}</tbody></table></div>

    <p class="sub" style="margin:10px 0 0">推荐出处标注「媒体转述」者，无一手链接；「无官方表态」表示未找到官方或项目负责人的公开推荐；「外部选型清单」表示来自第三方能力面对照清单。</p>
    <p class="sub" style="margin:6px 0 0"><span class="tag t-no2">已过时</span> 表示该能力<b>已被官方内置取代</b>，或作者已声明停止维护：新装不要选它，直接用官方实现或替代方案；存量环境里它可能还能跑。</p>
  </div>

  <div class="card">
    <h2>包名对照</h2>
    <p class="hint">社区流传的部分名称在 npm 上并不存在，或同名实现分属不同作者与 bundle，安装前需核对实际包名。</p>
    <div class="scroll"><table class="mini">
      <thead><tr><th style="width:24%">常见写法</th><th style="width:30%">实际包名</th><th style="width:46%">说明</th></tr></thead>
      <tbody>{namefix_rows}</tbody></table></div>
  </div>

  <div class="card">
    <h2>生态规模参考</h2>
    <ul class="lead2">
      <li>官方包 {n_total} 个；社区插件目录 <code>dsh-plugin-catalog</code> 自称收录 9,305 条，周下载 111,822。</li>
      <li><code>dsh</code> 本体：GitHub 276k 星、34k fork；npm 周下载 826,814、月下载 2,287,267。</li>
      <li>GitHub <code>dsh-plugin</code> topic 下已有 PicGo、WeKnora、reactive-resume 等成熟项目挂标签接入。</li>
      <li>社区 bundle 方面，<code>SQY-DSH-PLUGIN</code>（sanqiuyef 维护，MIT，经 <code>dsh.bundle.patch</code> 安装）一次带入 <code>dsh-mcp-manager</code>、<code>dsh-memory-manager</code>、<code>dsh-mcp-gateway</code>、<code>dsh-skill-manager</code>、<code>dsh-plugin-hub</code> 五个组件；名称相近但归属不同的还有 <code>@zfdx123/dsh-atelier</code> 与 <code>@sophiadata-ai/dsh-mcp-skill-manager</code>。</li>
    </ul>
  </div>
</section>

<!-- ================= 方法与局限 ================= -->
<section class="sec" id="s-method">
  <h2 class="sec-t">方法与局限</h2>
  <p class="sec-d">数据来源、统计口径与未核实事项。</p>
  <div class="card">
    <h2>数据来源</h2>
    <div class="scroll"><table class="mini">
      <tbody>
        <tr><td data-l="项目" style="width:18%">包清单</td><td>npm registry <code>/-/v1/search</code> 多关键词翻页，按 <code>@deepseek-ai/</code> 前缀过滤，得 {n_total} 个；与官方 5 个 profile 模板、base/web 插件行、依赖闭包、可选与按需清单逐一比对，无遗漏</td></tr>
        <tr><td data-l="项目">依赖闭包</td><td>对 422 个包逐个获取 packument，按最高版本取 <code>dependencies</code>，从 7 个 profile 入口递归展开</td></tr>
        <tr><td data-l="项目">安装与激活</td><td><code>dsh@0.2.2-rc.1</code>、<code>dsh-base</code>、<code>dsh-web-app</code>、<code>dsh-sdk-app</code>、<code>dsh-headless</code>、<code>dsh-acp-app</code>、<code>dsh-sdk-minimal</code> 的 <code>package.json</code> 与包内 <code>cordis.patch.yml</code>、<code>presets/*.patch.yml</code>（npm tarball 解包直读）</td></tr>
        <tr><td data-l="项目">清单常量</td><td><code>@deepseek-ai/dsh-official-bundles</code> 的 <code>lib/index.js</code>：PROFILE_TEMPLATES、OPTIONAL_BUNDLES、ON_DEMAND_BUNDLES、RETIRED_BUNDLES、PROTECTED_PLUGINS</td></tr>
        <tr><td data-l="项目">下载量</td><td>registry 搜索接口的 <code>downloads.weekly / monthly</code> 快照</td></tr>
        <tr><td data-l="项目">文档</td><td>仓库 <code>docs/tool-catalog.md</code>（工具清单，自动生成）、<code>docs/config-catalog.md</code>（配置项与源码路径）、根 <code>README.md</code></td></tr>
        <tr><td data-l="项目">GitHub</td><td>组织仓库列表与 shields.io 星数接口（REST API 匿名限流）</td></tr>
      </tbody></table></div>
  </div>

  <div class="card">
    <h2>未核实项</h2>
    <p class="hint">以下两项需要实际安装、运行才能判断，本报告未作推测。</p>
    <div class="scroll"><table class="mini">
      <thead><tr><th style="width:32%">项目</th><th style="width:68%">现状</th></tr></thead>
      <tbody>{unv_rows}</tbody></table></div>
  </div>

  <div class="card">
    <h2>已知限制</h2>
    <ul class="lead2">
      <li><b>开发者预览。</b>仓库 README 明确标注 <i>developer preview</i> 且存在破坏性变更；核心包多停留在 <code>0.x</code>，大量包自 2026-08-10 后未再发布。</li>
      <li><b>版本节奏不一致。</b><code>dsh@0.2.2-rc.1</code> 依赖 <code>dsh-official-bundles@0.2.2-rc.1</code>，但后者 npm 的 latest 标签仍指向 <code>0.2.2-alpha.2</code>；同批包中 rc 与 alpha 混布。</li>
      <li><b>默认值与文档存在差异。</b><code>dsh-fs-observation-policy</code> 在 tool-catalog 中注明发布配置未启用该行。</li>
      <li><b>可选 bundle 多标注实验性。</b>{n_opt} 个可选 bundle 多数带 <code>dsh-experimental-</code> 前缀，稳定性低于 base 层。</li>
      <li><b>原生依赖按平台分发。</b><code>libreoffice-kit-*</code>、<code>node-addon-system-*</code>、<code>node-addon-landlock-run-*</code> 各有 5 至 6 个平台子包，升级需同步。</li>
    </ul>
  </div>
</section>

</main>

<footer><div class="wrap">
本报告数据抓取自 npm registry、GitHub 与官方文档，检索日期 2026-11-08。未核实字段以"—"或文字标注，不作推测填充。社区内容与官方内容分节呈现，官方统计口径为 <code>@deepseek-ai</code> 作用域内的 {n_total} 个包。
</div></footer>

<button id="toTop" class="totop" type="button" aria-label="回到顶部" title="回到顶部">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5"/><path d="M5 12l7-7 7 7"/></svg>
</button>

<script>{JS.replace('__ROWS__', json.dumps(rows, ensure_ascii=False))}</script>
<script>{SCENE_JS}</script>
</body>
</html>'''

open('../report.html', 'w', encoding='utf-8').write(HTML)
print('written', len(HTML))
