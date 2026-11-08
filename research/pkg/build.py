# -*- coding: utf-8 -*-
import json, re

pk = json.load(open('../npm_pkgs.json'))
dl = {}
act = json.load(open('../activation.json'))
bd = json.load(open('../bundledeps.json'))
paths = json.load(open('../srcpaths.json'))

def short(n):
    return n.replace('@deepseek-ai/', '')

OPTIONAL = ["dsh-personalized-recommendations", "dsh-cua-bundle", "dsh-experimental-session-search",
            "dsh-experimental-ralph-bundle", "dsh-experimental-terminal-bundle", "dsh-experimental-badge-skill-bundle",
            "dsh-experimental-session-titles-bundle", "dsh-experimental-agent-team-profile",
            "dsh-experimental-voice-input-bundle", "dsh-experimental-cot-translation-bundle",
            "dsh-experimental-auto-review", "dsh-experimental-inspector-profile", "dsh-experimental-liveshare",
            "dsh-experimental-plugin-market-bundle", "dsh-experimental-tool-worktree",
            "dsh-experimental-forge-bundle"]
ONDEMAND = ["dsh-subagent-claude-code", "dsh-subagent-codex"]
RETIRED = ["dsh-experimental-schedule-bundle"]

CLOSURE = set(json.load(open('../closure.json'))['closure'])
A = json.load(open('../activation_full.json'))
WEB_ACTIVE = set(A['base']) | set(A['web'])
PROFILE_ONLY = set(x for x in A['profile_only'] if '/' not in x) - WEB_ACTIVE
installed = set(CLOSURE)

base = set(act['base'])
web = set(act['web'])
presets = act['presets']
preset_members = {}
for p, lst in presets.items():
    for x in lst:
        preset_members.setdefault(x, []).append(p.replace('.patch.yml', ''))

RUNTIME = {'dsh', 'cordis', 'cordis-plugin-loader', 'cordis-plugin-include', 'schemastery',
           'dsh-app-boot', 'dsh-cmdline', 'dsh-official-bundles', 'dsh-home-paths', 'dsh-launch-environment',
           'dsh-base', 'dsh-web-app'}

def status(name):
    if name in RUNTIME:
        return ('runtime', '默认随包·已激活（运行时基座 / profile 入口）', 'high')
    if name in base:
        return ('active', '默认随包·已激活（base 层，所有 profile 共享）', 'high')
    if name in web:
        return ('active', '默认随包·已激活（Web profile 层）', 'high')
    if name in preset_members:
        return ('preset', '默认随包·已激活（由 Agent Preset 提供：' + '/'.join(sorted(set(preset_members[name]))) + '）', 'high')
    if name in PROFILE_ONLY:
        return ('profile', '默认随包·未激活（仅在 sdk / sdk-minimal / headless / acp 入口的插件行中加载）', 'high')
    if name in OPTIONAL:
        if name in installed:
            return ('optional', '默认随包·未激活（官方可选 bundle，插件页打开即用）', 'high')
        return ('optional_off', '未落盘·官方可选（插件页打开时才安装）', 'high')
    if name in ONDEMAND:
        return ('ondemand', '未落盘·官方按需（插件页一键安装，不随包）', 'high')
    if name in RETIRED:
        return ('retired', '已下架（RETIRED_BUNDLES，不再随包）', 'high')
    if name in installed:
        return ('installed', '默认随包·未激活（无插件行：库 / 内部件，被使用方加载）', 'mid')
    return ('none', '未落盘·无官方入口（自行 npm 安装，多数不必装）', 'high')

# ---------- curated ----------
C = {
 # 框架 / CLI
 'dsh':('CLI','基础设施','CLI 入口：profile 启动、插件管理、配置查看（npx @deepseek-ai/dsh web）'),
 'cordis':('框架','基础设施','Cordis 插件元框架本体（DSH 一切皆插件的地基，vendor 后重发到本作用域）'),
 'cosmokit':('框架','基础设施','Cordis 生态通用工具函数集'),
 'schemastery':('框架','基础设施','类型驱动的 schema 校验器（配置校验）'),
 'dsh-cmdline':('框架','基础设施','命令行参数解析与命令注册基础设施'),
 'dsh-app-boot':('框架','基础设施','应用启动胶水层：profile 加载、bundle patch 应用'),
 'dsh-official-bundles':('框架','插件管理','官方 bundle 清单数据包：profile 模板、可选/按需/下架列表、插件管理保护名单'),
 'dsh-tools':('框架','基础设施','工具注册表与执行管线（工具调用的中枢）'),
 'dsh-scope':('框架','基础设施','作用域上下文注册原语（事件与服务的隔离域）'),
 'dsh-package-manifest':('框架','基础设施','包清单与打包元数据'),
 'dsh-invariants':('框架','基础设施','体系不变量断言（内部一致性检查）'),
 'dsh-hook-protocol':('框架','开发','Hook 协议定义（跨 Agent 的生命周期钩子）'),
 'dsh-hooks-claude-code':('Plugin','开发','接入 Claude Code 钩子事件'),
 'dsh-hooks-codex':('Plugin','开发','接入 Codex 钩子事件'),
 'dsh-brand':('框架','UI','产品品牌资源与命名常量'),
 # bundle / preset
 'dsh-base':('Bundle','基础设施','基础组合包：所有 base 型 profile 的共享内核（provider + 工具 + 服务）'),
 'dsh-web-app':('Bundle','UI','Web 组合包：dsh-base + 全部 Web 服务端/客户端插件'),
 'dsh-headless':('Bundle','基础设施','无界面组合包：一次性任务执行（dsh --profile headless）'),
 'dsh-sdk-app':('Bundle','基础设施','SDK 组合包：stdio JSON-RPC 对外提供运行时'),
 'dsh-acp-app':('Bundle','基础设施','ACP 组合包：Agent Client Protocol 自动化服务'),
 'dsh-sdk-minimal':('Bundle','基础设施','最小 SDK 组合包：单模型 + JSON-RPC + 本地持久化'),
 'dsh-cua-bundle':('Bundle','浏览器','Computer-Use 组合包（可选，默认关闭）'),
 'dsh-agent-preset':('Preset','基础设施','Agent 能力组合声明（cordis YAML 形式的一层 preset）'),
 'dsh-agent-preset-registry':('Preset','基础设施','Preset 注册表与 profile 侧编辑'),
 'dsh-agent-presets':('Preset','基础设施','按会话从 preset cordis.yml 组装 Agent（早期实现）'),
 'dsh-permission-presets':('Preset','基础设施','权限预设（只读 / 工作区可写 / 完全访问）'),
 # skill
 'dsh-skill':('Skill','基础设施','Skill 提供方注册表（Skill 基础设施层）'),
 'dsh-skill-filesystem':('Skill','文件','从本地文件系统加载 Skill 的提供方'),
 'dsh-skill-office':('Skill','Office','Office Skill 内容包：Word / PowerPoint / Excel 工作流与结构校验'),
 'dsh-skill-badge':('Skill','其他','内置 badge Skill 提供方（示例/装饰性）'),
 # mcp
 'dsh-mcp-client':('MCP','模型接入','MCP 客户端：连接外部 MCP 服务端，把其工具接入 DSH'),
 'dsh-mcp-resources':('MCP','模型接入','MCP 资源工具（list/read MCP resources），随 base 激活'),
 # office
 'dsh-office-to-pdf':('Plugin','Office','Office 文档转 PDF（基于 libreoffice-kit）'),
 'libreoffice-kit':('其他','Office','预编译 LibreOfficeKit 引擎封装：转换 / 重算 / 渲染 Office 文档'),
 'libreoffice-kit-wasm':('其他','Office','LibreOfficeKit 的 WebAssembly 版（跨平台 Office→PDF）'),
 # search / web
 'dsh-web':('框架','搜索','联网能力接缝（ctx.web）：搜索与抓取的抽象层'),
 'dsh-web-search-deepseek':('Plugin','搜索','DeepSeek 搜索提供方'),
 'dsh-web-deepseek-api':('Plugin','搜索','DeepSeek Search/Fetch API 提供方（Web 设置页默认接法）'),
 'dsh-web-fetch-http':('Plugin','搜索','匿名 HTTP(S) 抓取提供方'),
 'dsh-web-search-exa':('Plugin','搜索','Exa 搜索提供方（第三方服务）'),
 'dsh-web-search-perplexity':('Plugin','搜索','Perplexity 搜索提供方（第三方服务）'),
 'dsh-tool-web':('Plugin','搜索','模型可见的 web_search / web_fetch 工具'),
 # browser / computer use
 'dsh-browser-use':('Plugin','浏览器','浏览器自动化能力接缝'),
 'dsh-computer-use':('Plugin','浏览器','桌面自动化（Computer Use）能力接缝'),
 'dsh-cua':('Plugin','浏览器','Computer Use Agent 实现'),
 'dsh-e2b':('Plugin','基础设施','E2B 远程沙箱接入'),
 'dsh-tool-lsp':('Plugin','开发','模型可见的 lsp 工具（语言服务）'),
 'dsh-lsp':('框架','开发','LSP 能力接缝'),
 'dsh-lsp-stdio':('Plugin','开发','stdio LSP 客户端实现'),
 'dsh-workspace-changes':('Plugin','Git','逐轮记录工作区文件变化（基于 git 快照）'),
 'dsh-experimental-forge-github':('Plugin','Git','GitHub 侧 forge 适配（实验）'),
 'dsh-webhook-github':('Plugin','Git','GitHub Webhook 签名校验适配器（实验）'),
 'dsh-tool-skill':('Plugin','文件','模型可见的 skill 加载工具'),
 'dsh-tool-fs':('Plugin','文件','模型可见文件工具：read / write / edit / apply_patch / read_image'),
 'dsh-tool-fs-search':('Plugin','文件','模型可见检索工具：glob / grep（内置 ripgrep）'),
 'dsh-tool-bash':('Plugin','开发','模型可见 bash 工具（含后台任务与沙箱升级）'),
 'dsh-tool-bash-persistent':('Plugin','开发','持久化 bash 工具（基于 PTY 会话）'),
 'dsh-tool-pwsh':('Plugin','开发','模型可见 PowerShell 工具'),
 'dsh-tool-pwsh-persistent':('Plugin','开发','持久化 PowerShell 工具'),
 'dsh-tool-terminal':('Plugin','开发','六个持久 PTY 终端工具'),
 'dsh-tool-subagent':('Plugin','智能体协作','模型可见的子智能体委派工具'),
 'dsh-tool-subagent-control':('Plugin','智能体协作','子智能体控制：send_message / interrupt_agent / list_agents'),
 'dsh-tool-subagent-report':('Plugin','智能体协作','子智能体回报工具'),
 'dsh-tool-workflow':('Plugin','智能体协作','运行 JavaScript 编排脚本的工作流工具'),
 'dsh-tool-todo':('Plugin','其他','todo_write 任务清单工具'),
 'dsh-tool-goal':('Plugin','其他','同会话目标管理工具'),
 'dsh-tool-jobs':('Plugin','其他','后台任务控制工具（job_output / list / kill）'),
 'dsh-tool-schedule':('Plugin','其他','定时提醒工具（after / at / fixed-rate）'),
 'dsh-tool-ask-user':('Plugin','其他','追问用户的 ask_user_question 工具'),
 'dsh-tool-present':('Plugin','文件','交付文件声明工具（把产物显式交付给用户）'),
 'dsh-tool-cordis':('Plugin','插件管理','运行时自省工具集：查看/挂载/卸载插件（cordis preset 专用）'),
 'dsh-tool-str-replace-editor':('Plugin','文件','view / create / 字面替换 / 行插入编辑器工具'),
 'dsh-tool-session-query':('Plugin','其他','会话历史检索工具'),
 'dsh-tool-working-directory':('Plugin','文件','读取与切换会话工作目录'),
 'dsh-tool-workspace-dependencies':('Plugin','开发','load_workspace_dependencies：解析内置 Python/Node 绝对路径'),
 'dsh-tool-ralph':('Plugin','智能体协作','Ralph 循环：反复开新 Agent 迭代同一目标'),
 'dsh-tool-call-timeout-policy':('Plugin','基础设施','每次工具调用的超时策略包装'),
 'dsh-tool-executor-native':('Plugin','基础设施','原生工具执行器（常规 tool call 路径）'),
 'dsh-tool-executor-ptc':('Plugin','基础设施','PTC 程序化执行器：把工具编译成可编程调用'),
 'dsh-tool-testkit':('开发工具','基础设施','工具定义与执行的测试/基准夹具'),
 'dsh-plugin-manager':('Plugin','插件管理','插件管理器（宿主侧）：安装/启用/禁用/卸载 bundle'),
 'dsh-plugin-market':('Plugin','插件管理','插件市场索引配置（Discover 页数据源）'),
 'dsh-plugin-market-index':('Plugin','插件管理','插件市场索引格式 v1 的校验与解析'),
 'dsh-plugin-detail':('Plugin','插件管理','插件详情页数据'),
 'dsh-plugin-recommendations':('Plugin','插件管理','插件推荐逻辑'),
 'dsh-personalized-recommendations':('Bundle','插件管理','个性化推荐（实验，可选 bundle）'),
 'dsh-experimental-plugin-market-bundle':('Bundle','插件管理','实验性插件市场 bundle（Discover 页，可选）'),
 'dsh-webhook':('Plugin','其他','Webhook 规则运行时：由外部事件触发新会话'),
 'dsh-llm':('框架','模型接入','模型调用接缝（ctx.llm）与路由'),
 'dsh-llm-deepseek':('Plugin','模型接入','DeepSeek 模型适配器'),
 'dsh-llm-deepseek-api-key':('Plugin','模型接入','DeepSeek API Key 认证方式'),
 'dsh-llm-deepseek-account':('Plugin','模型接入','DeepSeek 账号（OAuth）认证方式'),
 'dsh-llm-pi-ai':('Plugin','模型接入','通过 pi-ai 接入多供应商模型（OpenAI 兼容等）'),
 'dsh-llm-retry':('Plugin','模型接入','模型请求重试策略'),
 'dsh-llm-replay':('Plugin','模型接入','回放已记录的模型请求（测试/复现）'),
 'dsh-llm-mock-server':('开发工具','模型接入','模型 mock 服务端（测试用）'),
 'dsh-deepseek-account':('框架','模型接入','DeepSeek 账号能力接缝'),
 'dsh-deepseek-account-platform':('Plugin','模型接入','DeepSeek 账号平台对接'),
 'dsh-deepseek-llm-api-extensions':('Plugin','模型接入','DeepSeek API 私有扩展（推理内容等线上字段）'),
 'dsh-credentials':('框架','模型接入','凭据接缝（ctx.credentials）'),
 'dsh-credentials-local':('Plugin','模型接入','本地凭据存储实现'),
 'dsh-authorization':('框架','模型接入','授权接缝：插件自有的取凭据流程'),
 'dsh-api-gateway':('框架','基础设施','TypeRT Remote 调度与 Client API 端点'),
 'dsh-sdk-client':('框架','基础设施','驱动 DSH 运行时的 TypeScript SDK 客户端'),
 'dsh-sdk-protocol':('框架','基础设施','SDK 线上协议（NDJSON JSON-RPC）'),
 'dsh-sdk-jsonrpc-server':('Plugin','基础设施','stdio JSON-RPC 服务端插件'),
 'dsh-sdk-jsonrpc-demo':('开发工具','基础设施','SDK JSON-RPC 示例 bin'),
 'dsh-acp':('框架','基础设施','ACP（Agent Client Protocol）服务端'),
 'dsh-acp-demo':('开发工具','基础设施','ACP 示例服务端'),
 'dsh-acp-snapshot':('开发工具','基础设施','ACP 快照测试套件'),
 'dsh-agent':('框架','智能体协作','Agent 接口、注册表、事件词汇'),
 'dsh-agent-loop':('框架','智能体协作','具体 Agent 主循环插件（DSH 的心脏）'),
 'dsh-agent-loop-testkit':('开发工具','智能体协作','Agent 循环测试的前置装配'),
 'dsh-agent-instructions':('Plugin','开发','加载 AGENTS.md / CLAUDE.md 工作区指令'),
 'dsh-agent-default-model':('Plugin','模型接入','各 Agent 入口共享的默认模型选择'),
 'dsh-agent-tool-presentation':('Plugin','智能体协作','Agent 工具呈现方式选择（Code Mode / 原生）'),
 'dsh-agent-spine-demo':('开发工具','智能体协作','无 UI 的 Agent 主干示例'),
 'dsh-persona':('Plugin','智能体协作','Persona：系统提示中的角色前缀注入'),
 'dsh-system-prompt':('框架','智能体协作','系统提示装配注册表'),
 'dsh-session':('框架','基础设施','事件溯源会话存储'),
 'dsh-session-persistence':('框架','基础设施','会话持久化接缝'),
 'dsh-session-persistence-jsonl':('Plugin','基础设施','JSONL 会话持久化后端'),
 'dsh-session-persistence-sqlite':('Plugin','基础设施','SQLite 会话持久化后端'),
 'dsh-session-query':('框架','基础设施','会话查询服务契约'),
 'dsh-session-query-sqlite':('Plugin','基础设施','SQLite FTS5 会话检索后端'),
 'dsh-session-projection':('框架','基础设施','会话投影类型表与提供方'),
 'dsh-session-projection-cache':('Plugin','基础设施','持久化投影缓存'),
 'dsh-session-title':('框架','基础设施','会话标题服务与提供方注册表'),
 'dsh-session-title-llm':('Plugin','基础设施','标题生成的 LLM 策略基座'),
 'dsh-session-title-first-prompt-llm':('Plugin','基础设施','用首条用户消息生成标题'),
 'dsh-session-title-all-prompts-llm':('Plugin','基础设施','用全部用户消息生成标题'),
 'dsh-session-stats':('Plugin','基础设施','会话统计投影（轮次、时长）'),
 'dsh-session-turn-outline':('Plugin','基础设施','回合大纲投影'),
 'dsh-session-reference':('Plugin','基础设施','跨会话快照引用'),
 'dsh-session-telemetry':('框架','基础设施','遥测接缝：会话事件捕获与脱敏'),
 'dsh-session-telemetry-otel':('Plugin','基础设施','OpenTelemetry 遥测后端'),
 'dsh-session-log-deepseek':('Plugin','模型接入','DeepSeek 官方模型的增量无损会话日志扩展'),
 'dsh-session-log-export':('Plugin','文件','Web 端会话日志导出与下载对话框'),
 'dsh-session-checkpoint-policy':('Plugin','基础设施','模型请求与工具副作用前的语义检查点'),
 'dsh-session-format':('框架','基础设施','会话格式迁移机制'),
 'dsh-session-snapshot':('开发工具','基础设施','会话日志快照核心与 ACP 适配'),
 'dsh-settings':('框架','基础设施','用户设置接缝'),
 'dsh-settings-file':('Plugin','基础设施','settings.yaml 文件后端'),
 'dsh-storage':('框架','基础设施','存储中枢（ctx.storage）：命名后端注册表'),
 'dsh-storage-domain':('框架','基础设施','领域数据形态：schema 校验的 KV 域'),
 'dsh-storage-json':('Plugin','基础设施','JSON 文件 KV 后端'),
 'dsh-storage-sqlite':('Plugin','基础设施','SQLite KV 后端'),
 'dsh-fs':('框架','文件','文件系统接缝'),
 'dsh-fs-local':('Plugin','文件','本地文件系统实现'),
 'dsh-fs-sandbox':('Plugin','文件','沙箱内文件系统实现'),
 'dsh-fs-patch':('Plugin','文件','补丁式文件修改（apply_patch 支撑）'),
 'dsh-fs-ssh':('Plugin','文件','SSH 远程文件系统实现'),
 'dsh-fs-e2b':('Plugin','文件','E2B 沙箱文件系统实现'),
 'dsh-fs-observation-policy':('Plugin','文件','读后写策略（fs/* 事件门），发布配置中默认关闭'),
 'dsh-attachment':('框架','文件','附件持久化接缝'),
 'dsh-attachment-local':('Plugin','文件','DSH_HOME 内容寻址附件存储'),
 'dsh-spill':('框架','文件','溢出存储接缝（超大工具结果落盘）'),
 'dsh-spill-local':('Plugin','文件','本地溢出存储实现'),
 'dsh-spill-policy':('Plugin','文件','工具结果溢出策略'),
 'dsh-file-reference':('框架','文件','文件引用接缝'),
 'dsh-file-reference-local':('Plugin','文件','本地文件引用解析'),
 'dsh-deliverable-file-references':('Plugin','文件','交付物与文件引用关联'),
 'dsh-shell':('框架','开发','bash 执行器接缝（ctx.shell）'),
 'dsh-pwsh-local':('Plugin','开发','本地 PowerShell 执行器'),
 'dsh-pwsh-sandbox':('Plugin','开发','沙箱内 PowerShell 执行器'),
 'dsh-bash-local':('Plugin','开发','本地 bash 执行器'),
 'dsh-bash-sandbox':('Plugin','开发','沙箱内 bash 执行器'),
 'dsh-subprocess':('框架','开发','子进程接缝（进程组管理）'),
 'dsh-subprocess-local':('Plugin','开发','本地子进程实现'),
 'dsh-subprocess-ssh':('Plugin','开发','SSH 远程子进程与终端提供方'),
 'dsh-subprocess-e2b':('Plugin','开发','E2B 远程子进程实现'),
 'dsh-terminal':('框架','开发','持久 PTY 会话接缝'),
 'dsh-terminal-bash':('Plugin','开发','bash PTY 后端'),
 'dsh-sandbox':('框架','基础设施','进程沙箱接缝（ctx.sandbox）'),
 'dsh-sandbox-local':('Plugin','基础设施','本地沙箱后端：bubblewrap / Seatbelt / Windows ACL'),
 'dsh-sandbox-policy':('Plugin','基础设施','逐调用沙箱策略解析'),
 'dsh-sandbox-ssh':('Plugin','基础设施','SSH 远端 POSIX 沙箱'),
 'dsh-sandbox-windows-acl':('Plugin','基础设施','Windows ACL 写限制沙箱后端'),
 'dsh-win32-process':('其他','基础设施','Win32 进程/stdio/Job Object 原语'),
 'dsh-jobs':('框架','基础设施','后台任务接缝'),
 'dsh-jobs-local':('Plugin','基础设施','本地后台任务实现'),
 'dsh-goal':('框架','其他','目标能力接缝'),
 'dsh-goal-round-driver':('Plugin','其他','目标轮次驱动'),
 'dsh-workflow':('框架','智能体协作','工作流接缝（ctx.workflows）'),
 'dsh-workflow-ptc':('Plugin','智能体协作','在沙箱 Node PTC 运行时里编排工作流'),
 'dsh-workflow-worker-thread':('Plugin','智能体协作','worker-thread 工作流引擎'),
 'dsh-ptc-runtime':('框架','基础设施','PTC 程序化工具调用运行时'),
 'dsh-ptc-runtime-node':('Plugin','基础设施','Node 版 PTC 运行时'),
 'dsh-code-runtime':('框架','基础设施','代码执行运行时接缝'),
 'dsh-code-runtime-python':('Plugin','基础设施','Python 代码运行时'),
 'dsh-code-runtime-worker-thread':('Plugin','基础设施','worker-thread 代码运行时'),
 'dsh-subagent':('框架','智能体协作','子智能体接缝（ctx.subagents）'),
 'dsh-subagent-fork-in-process':('Plugin','智能体协作','进程内 fork 子智能体后端'),
 'dsh-subagent-spawn-in-process':('Plugin','智能体协作','进程内 spawn 子智能体后端'),
 'dsh-subagent-in-process-driver':('Plugin','智能体协作','进程内子智能体运行驱动'),
 'dsh-subagent-acp':('Plugin','智能体协作','经 ACP 驱动子进程里的子 Agent'),
 'dsh-subagent-dsh-sdk':('Plugin','智能体协作','经 SDK 运行时驱动子 Agent'),
 'dsh-subagent-claude-code':('Plugin','智能体协作','把 Claude Code 当子 Agent（官方按需安装）'),
 'dsh-subagent-codex':('Plugin','智能体协作','把 Codex 当子 Agent（官方按需安装）'),
 'dsh-token-meter':('Plugin','模型接入','可重放的 token 计量服务'),
 'dsh-compaction':('框架','模型接入','上下文压缩接缝'),
 'dsh-compaction-basic':('Plugin','模型接入','基础压缩实现'),
 'dsh-compaction-image-offload':('Plugin','模型接入','把历史图片卸载出上下文'),
 'dsh-compaction-tool-result-pruner':('Plugin','模型接入','裁剪过大的工具结果'),
 'dsh-user-approval':('框架','基础设施','用户审批接缝（一次性授权）'),
 'dsh-user-questions':('框架','基础设施','用户提问接缝'),
 'dsh-plan-mode':('Plugin','智能体协作','Plan 模式：先出计划再执行'),
 'dsh-schedule':('Plugin','其他','定时/延后/定频提醒服务'),
 'dsh-time-context':('Plugin','其他','每步注入当前时间与耗时'),
 'dsh-tmux-context':('Plugin','其他','注入 tmux pane/window 位置上下文'),
 'dsh-timeout':('框架','基础设施','零依赖超时/截止时间原语'),
 'dsh-atomic-write':('框架','基础设施','零依赖原子文件替换'),
 'dsh-home-paths':('框架','基础设施','DSH_HOME 路径约定'),
 'dsh-launch-environment':('框架','基础设施','启动环境与 .env 加载'),
 'dsh-http-proxy':('Plugin','基础设施','HTTP 代理支持'),
 'dsh-otel':('框架','基础设施','OpenTelemetry 配置接缝'),
 'dsh-output-retention':('Plugin','基础设施','输出保留策略'),
 'dsh-anonymous-user-id':('Plugin','基础设施','遥测与反馈相关的匿名用户标识'),
 'dsh-chunked-list':('框架','基础设施','分块列表数据结构'),
 'dsh-deque':('框架','基础设施','双端队列实现'),
 'dsh-repeat-tool-reminder':('Plugin','智能体协作','重复工具调用提醒'),
 'dsh-config-editor':('Plugin','基础设施','配置文件编辑能力'),
 'dsh-hmr':('Plugin','开发','配置热更新'),
 'dsh-scope':('框架','基础设施','作用域注册原语'),
 'dsh-cordis-host-runner':('Plugin','插件管理','宿主侧 cordis 运行时驱动'),
 'dsh-cordis-client-runner':('Plugin','UI','浏览器侧 cordis 运行时驱动'),
 'dsh-typert-registry':('框架','基础设施','TypeRT 运行时反射注册表'),
 'dsh-typert-loader':('框架','基础设施','Typert 贡献的加载集成'),
 'dsh-typert-protocol':('框架','基础设施','Remote 元数据与 Typert 协议'),
 'dsh-typert-generator':('开发工具','基础设施','TypeScript 分析器 + Typert 产物生成'),
 'dsh-util-crypto':('框架','基础设施','浏览器安全 UUID / 字节编码工具'),
 'dsh-util-time':('框架','基础设施','跨线边界的标准时间表述'),
 'dsh-util-values':('框架','基础设施','可重复安装的值原语'),
 'dsh-util-workspace-path':('框架','基础设施','工作区路径与展示辅助'),
 'dsh-util-code-language':('框架','基础设施','扩展名→语法高亮语言映射'),
 'dsh-util-file-drag':('框架','UI','文件拖拽传输契约'),
 'dsh-message-feedback':('Plugin','其他','消息反馈（点赞/点踩 + 备注）'),
 'dsh-message-quotes':('Plugin','其他','消息引用'),
 'dsh-action-cards':('Plugin','UI','答案下方可选操作卡片'),
 'dsh-creation-recommendations':('Plugin','其他','创作方向推荐'),
 'dsh-personalized-recommendations':('Bundle','插件管理','个性化推荐（可选 bundle）'),
 'dsh-harness-dev-context':('Plugin','开发','注入当前 checkout 与 GUI 地址等研发上下文'),
 'dsh-native-command':('框架','基础设施','原生命令通道'),
 'dsh-lazy-require':('框架','基础设施','惰性 require'),
 'dsh-remote-mock':('开发工具','基础设施','Remote 流量 mock（按端点）'),
 'dsh-loader-smoke':('开发工具','基础设施','Loader 冒烟测试'),
 'dsh-client-web':('框架','UI','Web 客户端运行时基座'),
 'dsh-client-web-react':('框架','UI','Web 客户端 React 基座'),
 'dsh-client-store':('框架','UI','客户端状态存储'),
 'dsh-client-runtime':('框架','UI','客户端运行时'),
 'dsh-client-schema-form':('框架','UI','schema 驱动表单'),
 'dsh-client-connection':('Plugin','UI','客户端与宿主连接'),
 'dsh-client-modules':('Plugin','UI','客户端模块加载'),
 'dsh-client-resources':('Plugin','UI','客户端资源提供'),
 'dsh-client-locale':('Plugin','UI','多语言'),
 'dsh-client-hmr':('Plugin','UI','客户端热更新'),
 'dsh-client-shortcuts':('Plugin','UI','快捷键'),
 'dsh-client-file-upload':('Plugin','文件','客户端文件上传'),
 'dsh-client-product-analytics':('Plugin','基础设施','产品分析埋点'),
 'dsh-client-test-runtime':('开发工具','UI','客户端测试运行时'),
 'dsh-host-webserver':('Plugin','基础设施','Web 服务端（路由/静态资源）'),
 'dsh-host-frontend-static':('Plugin','UI','前端静态资源服务'),
 'dsh-host-plugin-inventory':('Plugin','插件管理','宿主侧插件清单'),
 'dsh-host-product-telemetry-otel':('Plugin','基础设施','产品遥测 OTel 上报'),
 'dsh-host-open-in-app':('Plugin','UI','用外部编辑器打开工作区'),
 'dsh-host-directory-picker':('框架','UI','目录选择接缝'),
 'dsh-host-directory-picker-auto':('Plugin','UI','自动选择目录选择实现'),
 'dsh-host-directory-picker-browse':('Plugin','UI','网页内目录浏览选择'),
 'dsh-host-directory-picker-native':('Plugin','UI','系统原生目录选择'),
 'dsh-host-apiproxy':('Plugin','基础设施','API 反向代理'),
 'dsh-web-frontend':('框架','UI','Web 前端入口（vite 构建产物）'),
 'dsh-office-to-pdf':('Plugin','Office','Office→PDF（浏览器侧预览/导出）'),
 'dsh-plugin-package-inventory-deepseek':('Plugin','插件管理','官方包清单（DeepSeek 侧）'),
 'dsh-executor-native':('Plugin','基础设施','原生执行器'),
}

TYPE_ORDER = ['Bundle', 'Preset', '框架', 'CLI', 'Plugin', 'Skill', 'MCP', '其他', '开发工具']
DIRS = ['基础设施', '智能体协作', '文件', '开发', '模型接入', '搜索', '浏览器', '插件管理', 'UI', 'Office', 'Git', '其他']

TOK = {
 'account':'账户','action-cards':'操作卡片','agent-preset':'智能体预设','agent-team':'智能体团队','approval':'审批',
 'attachment':'附件','auto-review':'自动评审','badge-skill':'徽章 Skill','brand-official':'官方品牌','chat':'对话',
 'command':'命令','commands':'斜杠命令','compact':'上下文压缩','compaction':'上下文压缩','context-menu':'右键菜单',
 'conversation':'会话流','cordis':'插件运行时','cot-translation':'思维链翻译','creation-recommendations':'创作推荐',
 'cua':'Computer Use','deliverables':'交付物','directory-picker':'目录选择','dockkit':'停靠栏','entry-customization':'入口定制',
 'file-actions':'文件操作','file-drag':'文件拖拽','forge':'代码锻造','goal':'目标','input-trigger':'输入触发器',
 'inspector':'运行时检查器','jobs':'后台任务','layout':'布局','liveshare':'实时共享','message-feedback':'消息反馈',
 'model-selection':'模型选择','open-in-app':'外部应用打开','permission-presets':'权限预设','plan':'计划模式',
 'plugin-manager':'插件管理','plugin-market':'插件市场','plugin-recommendations':'插件推荐','primitives':'UI 基础件',
 'ralph':'Ralph 循环','reference':'引用','renderer':'渲染器','schedule':'定时任务','secret-mask':'密钥遮罩',
 'session':'会话','session-search':'会话检索','session-titles':'会话标题','settings':'设置','shortcuts':'快捷键',
 'sidebar':'侧边栏','skill':'技能','slots':'插槽','stats':'统计','subagent':'子智能体','terminal':'终端','theme':'主题',
 'tool':'工具调用展示','tool-worktree':'工作树工具','trajectory':'轨迹','user-questions':'用户提问','voice-input':'语音输入',
 'workflow-run':'工作流运行','workspace':'工作区','documentpreview':'文档预览','textpreview':'文本预览',
}

def derive(n):
    d = n.replace('dsh-', '')
    if n.startswith('dsh-client-ui-'):
        t = d.replace('client-ui-', '')
        return ('Plugin', 'UI', 'Web 客户端 UI：' + TOK.get(t, t))
    if n.startswith('dsh-client-'):
        return ('Plugin', 'UI', 'Web 客户端能力：' + TOK.get(d.replace('client-', ''), d.replace('client-', '')))
    if n.startswith('dsh-api-'):
        return ('框架', '基础设施', 'Remote API 控制器：' + d.replace('api-', ''))
    if n.startswith('dsh-experimental-'):
        t = d.replace('experimental-', '')
        kind = 'Bundle' if t.endswith('bundle') or t.endswith('profile') else 'Plugin'
        return (kind, '其他', '实验性能力：' + TOK.get(t.replace('-bundle', ''), t.replace('-bundle', '')))
    if n.startswith('dsh-tool-'):
        return ('Plugin', '其他', '模型可见工具：' + TOK.get(d.replace('tool-', ''), d.replace('tool-', '')))
    if n.startswith('dsh-skill-'):
        return ('Skill', '其他', 'Skill 提供方：' + TOK.get(d.replace('skill-', ''), d.replace('skill-', '')))
    if n.startswith('cordis-plugin-'):
        return ('框架', '基础设施', 'Cordis 官方插件：' + n.replace('cordis-plugin-', ''))
    return ('其他', '其他', '内部库：' + d)

rows = []
import datetime

STD = set(presets['standard.patch.yml'])
CODE = {'active': '1a', 'runtime': '1b', 'optional': '2a', 'installed': '2b', 'profile': '2c',
        'ondemand': '3a', 'optional_off': '3b', 'none': '3c', 'retired': '—'}

def code_of(n, st):
    if st == 'preset':
        return '1c' if n in STD else '2c'
    return CODE.get(st, '—')

def evof(n, st):
    if st == 'runtime':
        return ('dsh CLI / app-boot 运行时装载', 'runtime')
    if st == 'active':
        return ('dsh-base 或 dsh-web-app 的 cordis.patch.yml 行', 'patch')
    if st == 'preset':
        return ('dsh-web-app presets/*.patch.yml（按 Agent Preset）', 'preset')
    if st == 'optional':
        return ('dsh-official-bundles OPTIONAL_BUNDLES', 'bundles')
    if st == 'ondemand':
        return ('dsh-official-bundles ON_DEMAND_BUNDLES', 'bundles')
    if st == 'retired':
        return ('dsh-official-bundles RETIRED_BUNDLES', 'bundles')
    if st == 'installed':
        return ('dsh / dsh-base / dsh-web-app 的 dependencies', 'deps')
    return ('不在 dsh・base・web-app 依赖与任何 patch 内', 'none')

def maint(datestr):
    try:
        d = datetime.date.fromisoformat(datestr)
    except Exception:
        return ('未知', 0)
    days = (datetime.date(2026, 11, 7) - d).days
    if days <= 7:
        return ('高频更新', days)
    if days <= 30:
        return ('正常维护', days)
    if days <= 90:
        return ('低频', days)
    return ('停滞', days)

for full, meta in sorted(pk.items()):
    n = short(full)
    t = C.get(n, derive(n))
    st, label, conf = status(n)
    d = {'last-week': meta.get('weekly'), 'last-month': meta.get('monthly')}
    ev, evk = evof(n, st)
    mlabel, mdays = maint((meta.get('date') or '')[:10])
    rows.append({
        'pkg': full, 'name': n, 'type': t[0], 'dir': t[1], 'purpose': t[2],
        'desc': (meta.get('desc') or '')[:180],
        'version': meta.get('version'), 'date': (meta.get('date') or '')[:10],
        'status': st, 'code': code_of(n, st), 'statusLabel': label, 'conf': conf, 'ev': ev, 'evk': evk,
        'maint': mlabel, 'days': mdays,
        'weekly': d.get('last-week'), 'monthly': d.get('last-month'),
        'path': paths.get(n),
        'optional': n in OPTIONAL, 'ondemand': n in ONDEMAND,
    })

json.dump(rows, open('../rows.json', 'w'), ensure_ascii=False, indent=1)

from collections import Counter
print(len(rows), 'rows;', 'no-desc:', sum(1 for r in rows if not r['desc']))
print(Counter(r['type'] for r in rows))
print(Counter(r['dir'] for r in rows))
print(Counter(r['status'] for r in rows))
print('weekly known:', sum(1 for r in rows if r['weekly'] is not None))
print('paths:', sum(1 for r in rows if r['path']))
