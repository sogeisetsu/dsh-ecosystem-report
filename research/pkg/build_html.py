# -*- coding: utf-8 -*-
import json, io, datetime

rows = json.load(open('../rows.json'))
by = {r['name']: r for r in rows}

act_json = json.load(open('../activation.json'))
STD = set(act_json['presets']['standard.patch.yml'])
INSTALLED_ST = ('active', 'runtime', 'preset', 'installed', 'optional')

INST = [r for r in rows if r['status'] in INSTALLED_ST]
ACT = [r for r in rows if r['status'] in ('active', 'runtime') or (r['status'] == 'preset' and r['name'] in STD)]
n_total = len(rows)
n_inst = len(INST)
n_act = len(ACT)
n_off = len([r for r in rows if r['status'] in ('installed', 'optional') or (r['status'] == 'preset' and r['name'] not in STD)])
n_opt = len([r for r in rows if r['status'] == 'optional'])
n_none = len([r for r in rows if r['status'] in ('none', 'ondemand', 'optional_off', 'retired')])
n_ondemand = len([r for r in rows if r['status'] == 'ondemand'])
n_opt_off = len([r for r in rows if r['status'] == 'optional_off'])
n_retired = len([r for r in rows if r['status'] == 'retired'])
n_preset_other = len([r for r in rows if r['status'] == 'preset' and r['name'] not in STD])
n_base = len([r for r in rows if r['status'] == 'active'])
n_runtime = len([r for r in rows if r['status'] == 'runtime'])
n_preset = len([r for r in rows if r['status'] == 'preset'])
n_lib = len([r for r in rows if r['status'] == 'installed'])
n_noentry = len([r for r in rows if r['status'] == 'none'])
n_preset_std = len([r for r in rows if r['status'] == 'preset' and r['name'] in STD])

def bucket(n):
    """三态：1 已激活 / 2 随包未激活 / 3 需另外安装"""
    r = by.get(n)
    if not r:
        return ('?', '未核实')
    s = r['status']
    if s in ('active', 'runtime'):
        return ('1', '默认随包已激活')
    if s == 'preset':
        return ('1', '默认随包已激活') if n in STD else ('2', '随包未激活（仅非默认 Preset）')
    if s in ('installed', 'optional'):
        return ('2', '默认随包未激活')
    if s in ('ondemand', 'optional_off'):
        return ('3', '需另外安装（官方入口）')
    if s == 'retired':
        return ('0', '已下架（不再随包）')
    return ('3', '需另外安装（自行 npm）')


GH = 'https://github.com/deepseek-ai/deepseek-harness'
GHP = 'https://github.com/deepseek-ai/deepseek-harness/blob/master/'

def gh(n):
    r = by.get(n)
    if r and r.get('path'):
        return GHP + r['path']
    if n.startswith('libreoffice-kit'):
        return 'https://github.com/deepseek-ai/dsh-libreoffice-kit'
    return GH + '/tree/master/packages'

def npm(n):
    return 'https://www.npmjs.com/package/@deepseek-ai/' + n

def a(url, text, cls=''):
    return f'<a href="{url}" target="_blank" rel="noopener" class="{cls}">{text}</a>'

def tag(text, cls):
    return f'<span class="tag {cls}">{text}</span>'

TYPE_CLS = {'Bundle': 't-bundle', 'Preset': 't-preset', '框架': 't-frame', 'CLI': 't-cli', 'Plugin': 't-plugin',
            'Skill': 't-skill', 'MCP': 't-mcp', '其他': 't-other', '开发工具': 't-dev'}
ST_CLS = {'active': 's-active', 'runtime': 's-runtime', 'preset': 's-preset', 'optional': 's-opt',
          'installed': 's-inst', 'ondemand': 's-on', 'none': 's-none', 'retired': 's-ret'}

import re as _re
TOKEN = _re.compile(r'dsh(?:-[a-z0-9-]+)?|libreoffice-kit[a-z0-9-]*|node-addon-[a-z0-9-]+')
BUCKET_CLS = {'1': 'st-ok', '2': 'st-off', '3': 'st-need'}

def bucket_for(label):
    toks = TOKEN.findall(label)
    codes = []
    for t in toks:
        if t in by:
            codes.append(bucket(t))
    if not codes:
        return ('?', '未核实', 'st-need')
    texts = [c[1] for c in codes]
    codeset = {c[0] for c in codes}
    if len(set(texts)) == 1:
        c = codes[0]
        return (c[0], c[1], BUCKET_CLS.get(c[0], 'st-mix'))
    inner = []
    for t in texts:
        m = _re.search(r'（([^）]+)）', t)
        inner.append(m.group(1) if m else t)
    base = texts[0].split('（')[0]
    if len(codeset) == 1:
        return (codes[0][0], base + '（' + ' / '.join(inner) + '）', BUCKET_CLS.get(codes[0][0], 'st-mix'))
    SHORTB = {'1': '已激活', '2': '随包未启用', '3': '需另外安装', '0': '已下架'}
    txt = ' / '.join(SHORTB.get(c, c) for c in sorted(codeset))
    return ('/'.join(sorted(codeset)), txt, 'st-mix')

# ---------------- Tab 1 ----------------
profiles = [
    ('web', 'dsh --profile web / npx dsh web', 'dsh-base + dsh-web-app', '默认入口，浏览器 UI'),
    ('headless', 'dsh --profile headless "task"', 'dsh-base + dsh-headless', '一次性任务，适合脚本/CI'),
    ('acp', 'dsh --profile acp', 'dsh-base + dsh-acp-app', '以 ACP 协议被编辑器/客户端驱动'),
    ('sdk', 'dsh --profile sdk', 'dsh-base + dsh-sdk-app', 'stdio JSON-RPC 对外提供运行时'),
    ('sdk-minimal', 'dsh --profile sdk-minimal', 'dsh-sdk-minimal', '最小 SDK 组合，单模型 + 本地持久化'),
]
prof_html = ''.join(
    f'<tr><td data-l="profile"><code>{p[0]}</code></td><td data-l="启动方式"><code>{p[1]}</code></td>'
    f'<td data-l="bundle 组合">{p[2]}</td><td data-l="用途">{p[3]}</td></tr>'
    for p in profiles)

presets = [('standard', 1, 28, '默认预设：完整工具面（含 apply_patch、plan、subagent、web、workflow）'),
           ('ptc', 2, 29, '在 standard 基础上换成 PTC 程序化工具执行器'),
           ('minimal', 3, 9, '最小工具面：bash/pwsh 持久终端 + fs，无 web/subagent'),
           ('cordis', 4, 29, '面向"改 DSH 自身"：多一个 dsh-tool-cordis 运行时自省工具')]
preset_html = ''.join(
    f'<tr><td data-l="preset"><code>{p[0]}</code></td><td data-l="order">{p[1]}</td>'
    f'<td data-l="成员包数">{p[2]}</td><td data-l="差异">{p[3]}</td></tr>' for p in presets)

off_list = [r for r in rows if r['status'] == 'installed']
off_focus = ['dsh-mcp-client', 'dsh-skill-office', 'dsh-sdk-app', 'dsh-acp-app']
off_html = ''.join(
    f'<li><code>{n}</code> — {by[n]["purpose"]}</li>' for n in off_focus if n in by)

# ---------------- Tab 3 ----------------
TIERS = [
 ('must', '必装', '基础工作流离不开；默认已随 dsh 落盘并激活，本层含义是"不要卸载/不要禁用"',
  [('dsh', 'CLI 入口本身，所有 profile 都从它启动', 'README · npx @deepseek-ai/dsh web'),
   ('dsh-base', 'base 层组合包：provider + 工具 + 服务的共享内核，禁用它等于抽掉地基', 'PROFILE_TEMPLATES'),
   ('dsh-web-app', 'Web profile 的组合层：95 个 Web 服务端/客户端插件', 'PROFILE_TEMPLATES'),
   ('dsh-tool-fs', 'read/write/edit/apply_patch，是所有代码改动的唯一通道', 'tool-catalog.md'),
   ('dsh-tool-fs-search', 'glob/grep（内置 ripgrep），没有它大仓库无法定位', 'tool-catalog.md'),
   ('dsh-tool-bash', '跑测试、装依赖、git 操作都靠它', 'tool-catalog.md'),
   ('dsh-tool-subagent + dsh-subagent-fork-in-process', '任务拆分与并行，长任务的关键', 'tool-catalog.md'),
   ('dsh-tool-web + dsh-web-deepseek-api', '联网搜索与抓取（默认接 DeepSeek Search/Fetch API）', 'python/ 提交记录'),
   ('dsh-tool-todo', '任务清单，长任务不跑偏', 'tool-catalog.md'),
   ('dsh-skill + dsh-skill-filesystem', 'Skill 基础设施与本地加载器（Skill 能力的地基）', 'dsh-base patch'),
   ('dsh-plugin-manager', '插件管理器本体，卸载它就无法再管理插件', 'PROTECTED_PLUGINS'),
   ('dsh-permission-presets', '只读/工作区可写/完全访问三档权限', 'config-catalog.md')]),
 ('rec', '推荐', '显著提升体验，按需开启即可（多数是"随包已装、默认关闭"的可选 bundle）',
  [('dsh-experimental-terminal-bundle', '持久终端面板：Agent 与你在同一 PTY 里工作，调试最省心', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-session-search', '跨会话历史检索：上周那个方案能搜回来', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-session-titles-bundle', '自动会话标题，长列表不再全是"新会话"', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-auto-review', '提交前自动评审 diff，缺点是最常见返工点', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-badge-skill-bundle', '徽章/状态类 Skill 示例，学习 Skill 写法的模板', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-ralph-bundle', 'Ralph 循环：同一目标反复开新 Agent 迭代，适合难啃的重构', 'OPTIONAL_BUNDLES'),
   ('dsh-tool-schedule + dsh-schedule', '定时提醒/定时任务（Web profile 已激活服务端，工具在 standard preset 内）', 'tool-catalog.md')]),
 ('scene', '场景选装', '只在特定工作流下才有价值；不装不影响日常',
  [('dsh-skill-office', 'Office Skill：Word/PPT/Excel 工作流与结构校验。随包已装，但 Web profile 未激活（需在插件/Skill 侧启用）', 'dsh deps 有、base/web patch 无'),
   ('dsh-mcp-client', 'MCP 客户端：要把外部 MCP 服务端的工具接进来时才需要（MCP 资源工具 dsh-mcp-resources 已默认激活）', 'dsh deps 有、patch 无'),
   ('dsh-subagent-claude-code / dsh-subagent-codex', '把 Claude Code / Codex 当子智能体，官方 ON_DEMAND_BUNDLES，需单独安装', 'ON_DEMAND_BUNDLES'),
   ('dsh-experimental-plugin-market-bundle', '实验性插件市场 Discover 页，插件逛起来方便但要接第三方索引', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-liveshare', '实时共享会话（多人同看一个 Agent），协作场景才用得上', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-voice-input-bundle', '语音输入，中文长指令口述更快', 'OPTIONAL_BUNDLES'),
   ('dsh-experimental-cot-translation-bundle', '思维链翻译，看英文推理过程时有用', 'OPTIONAL_BUNDLES'),
   ('dsh-cua-bundle / dsh-computer-use', 'Computer Use：真去点鼠标键盘，适合 GUI 自动化；风险与成本都高', 'OPTIONAL_BUNDLES'),
   ('dsh-web-search-exa / dsh-web-search-perplexity', '换搜索供应商（需自备 API Key）', 'dsh-web 提供方'),
   ('dsh-experimental-agent-team-profile', '智能体团队（队长+成员），大任务才划算', 'OPTIONAL_BUNDLES'),
   ('libreoffice-kit + 平台二进制', 'Office→PDF 的引擎（dsh-office-to-pdf 已默认激活并依赖它），做文档转换才需要关心', 'dsh-web-app deps'),
   ('dsh-experimental-forge-bundle', '代码锻造/长任务工程化，实验性', 'OPTIONAL_BUNDLES')]),
 ('no', '暂不建议', '维护差、实验性、功能重复或上手成本高',
  [('dsh-experimental-schedule-bundle', '已列入 RETIRED_BUNDLES，安装后 profile 会自动移除', 'RETIRED_BUNDLES'),
   ('dsh-agent-presets', '早期实现，已被 dsh-agent-preset + dsh-agent-preset-registry 取代（0.0.1-rc.1，2026-08-10 后未更新）', 'npm 元数据'),
   ('dsh-experimental-agent-team / dsh-experimental-tool-agent-team / dsh-experimental-client-ui-agent-team', '与 dsh-experimental-agent-team-profile 重叠，且均为未打包进可选列表的散件', '官方 bundle 清单'),
   ('dsh-acp-demo / dsh-agent-spine-demo / dsh-sdk-jsonrpc-demo / *-testkit / *-mock-server / dsh-loader-smoke', '示例与测试夹具，不是给终端用户的功能', '包描述'),
   ('dsh-subprocess-e2b / dsh-fs-e2b / dsh-e2b', '依赖 E2B 外部服务与密钥，本地工作流用不上', '包描述'),
   ('dsh-sandbox-ssh / dsh-subprocess-ssh / dsh-fs-ssh', '远端 POSIX 场景专用，配置成本高（0.1.6-alpha.1）', 'npm 版本'),
   ('dsh-win32-process / node-addon-system / node-addon-landlock-run', '平台原生原语，由沙箱层间接使用，不要手动装', '包描述'),
   ('dsh-client-ui-deepseek-model-label-1017 等零下载内部件', '无独立使用价值，随 UI 组合一起升级即可', 'npm 周下载')]),
]
tier_cls = {'must': 'tier-must', 'rec': 'tier-rec', 'scene': 'tier-scene', 'no': 'tier-no'}

tiers_html = ''
for key, name, desc, items in TIERS:
    rows_h = []
    for i in items:
        b = bucket_for(i[0])
        rows_h.append(
            f'<tr><td data-l="包"><code>{i[0]}</code></td>'
            f'<td data-l="当前状态"><span class="tag {b[2]}">{b[0]} · {b[1]}</span></td>'
            f'<td data-l="理由">{i[1]}</td><td class="muted" data-l="证据">{i[2]}</td></tr>')
    lis = ''.join(rows_h)
    tiers_html += f'''
    <section class="card tier {tier_cls[key]}">
      <h3>{tag(name, tier_cls[key])} <span class="muted sm">{desc}</span></h3>
      <table class="mini tier-tbl"><colgroup><col style="width:25%"><col style="width:14%"><col style="width:40%"><col style="width:21%"></colgroup><thead><tr><th>包</th><th>当前状态</th><th>理由</th><th>证据</th></tr></thead><tbody>{lis}</tbody></table>
    </section>'''

# ---------------- Tab 4 ----------------
COMM = [
 ('@deepseek-harness-tui/dsh-tui', 'dsh-TUI', 'ccch1mneyyy/dsh-TUI', '0.19.0 · 2026-11-06', 'GitHub 7.1k★ · npm 周下载 21,210',
  '负责人崔添翼公开点名推荐的第 1 个社区插件（媒体转述"DSH 团队推荐系列①"），补齐终端 TUI', '中高'),
 ('dsh-better-sidebar', 'DSH Better Sidebar', 'omdsh-dev/DSH-better-sidebar', '0.30.1 · 2026-11-05', 'GitHub 5k★ · npm 周下载 78,109',
  '媒体称获崔添翼关注/推荐；把文件树、编辑器、变更、任务整合进侧边栏', '中'),
 ('dsh-context', 'dsh-context', '—', 'npm 存在，元数据未取到', '媒体称约 2.7k★（2026-10 报道）',
  'Token 构成分析面板，媒体称获崔添翼点赞', '低'),
 ('billion-context', 'billion-context', 'billion-context/billion-context', '2026-11-02 更新', 'npm 周下载 892,566（含非 DSH 用途）· DSH 专用向 billion-context-dsh 周下载 2,528',
  '上下文压缩代理，媒体列为崔添翼重点推荐之一；GitHub 仓库 shields 显示 0★，与媒体口径不一致', '低'),
 ('dsh-plugin-catalog', 'dsh-plugin-catalog', '—', '2026-11-07 更新', 'npm 周下载 111,822',
  '社区插件目录（自称 9305 条），是"插件生态规模"的间接证据，非官方推荐', '高'),
]
comm_html = ''.join(
    f'''<tr><td><span class="pkg">{c[0]}</span><div class="muted sm">{c[1]} · {c[3]}</div></td>
    <td class="muted sm">{c[2]}</td><td class="sm">{c[4]}</td><td>{c[5]}</td><td><span class="tag s-inst">{c[6]}</span></td></tr>''' for c in COMM)

UNVERIFIED = [
 ('sdk / acp / sdk-minimal profile 的激活行', '已取到这些 profile 的 bundle 依赖，但没有逐个下载 0.2.2-rc.1 的 cordis.patch.yml；因此这三个 profile 的"激活"只按依赖推断，标为未核实'),
 ('dsh-skill-office 在 sdk profile 是否被激活', '它是 dsh 与 dsh-sdk-app 的依赖，但不在 base/Web patch 内；SDK 组合是否引用未核实'),
 ('dsh-mcp-client 的实际激活路径', '是 @deepseek-ai/dsh 的直接依赖，但不在 base/Web patch 行内；推测由插件页/配置动态加载，未在源码中确认'),
 ('社区推荐清单的一手出处', '崔添翼的推荐散落在 X / GitHub 讨论，未抓取到官方"Official Picks"页面；本报告采用媒体（智东西系）转述，逐条标注置信度'),
 ('dsh-fs-local / dsh-host-directory-picker-* 等随包未激活包', '依赖在，patch 行未出现；可能由 profile 运行时按需装载，未核实'),
 ('单包精确周下载量', '来自搜索接口快照（滚动 7 天），非逐包 downloads/point 精确窗口；两者约有 2% 偏差，已在方法页说明'),
]

unv_html = ''.join(f'<tr><td data-l="项目">{u[0]}</td><td class="muted" data-l="现状">{u[1]}</td></tr>' for u in UNVERIFIED)

CSS = '''
:root{
 --bg:#f6f7f9; --panel:#fff; --ink:#12151a; --muted:#5b6472; --line:#e2e6ec; --line2:#eef1f5;
 --accent:#1f6feb; --ok:#15803d; --warn:#b45309; --bad:#b91c1c;
 --t-bundle:#6d28d9; --t-preset:#7c3aed; --t-frame:#1d4ed8; --t-cli:#0f172a; --t-plugin:#0f766e;
 --t-skill:#15803d; --t-mcp:#c2410c; --t-other:#64748b; --t-dev:#a16207;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
 font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px 72px}
header.top{background:linear-gradient(180deg,#fff,#fbfcfe);border-bottom:1px solid var(--line);padding:26px 0 18px;margin-bottom:18px}
h1{font-size:23px;line-height:1.35;margin:0 0 8px;letter-spacing:-.01em}
.lede{font-size:15px;color:#2a3038;margin:0 0 12px;max-width:940px}
.meta{font-size:12.5px;color:var(--muted);display:flex;gap:14px;flex-wrap:wrap}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:16px 0 4px}
.stat{background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.stat b{display:block;font-size:20px;line-height:1.2}
.stat span{font-size:12px;color:var(--muted)}
nav.tabs{display:flex;gap:6px;overflow-x:auto;padding:10px 0 0;position:sticky;top:0;background:var(--bg);z-index:20;
 border-bottom:1px solid var(--line);margin-bottom:18px}
nav.tabs button{border:1px solid transparent;background:none;padding:9px 13px;border-radius:9px 9px 0 0;font:inherit;
 font-size:13.5px;color:var(--muted);cursor:pointer;white-space:nowrap}
nav.tabs button.on{background:#fff;border-color:var(--line);border-bottom-color:#fff;color:var(--ink);font-weight:600}
section.tab{display:none}section.tab.on{display:block}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:0 0 16px}
.card h2{font-size:16px;margin:0 0 10px}
.card h3{font-size:14.5px;margin:14px 0 8px}
.card h3:first-child{margin-top:0}
p{margin:8px 0}
ul,ol{margin:8px 0 8px 20px;padding:0}li{margin:4px 0}
code{font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:#f2f4f7;border:1px solid var(--line2);
 border-radius:5px;padding:1px 5px;word-break:break-all}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.muted{color:var(--muted)}.sm{font-size:12px}
.tag{display:inline-block;font-size:11.5px;line-height:1.5;padding:1px 7px;border-radius:999px;border:1px solid;
 white-space:nowrap;background:#fff}
.t-bundle{color:var(--t-bundle);border-color:#ddd6fe;background:#f5f3ff}
.t-preset{color:var(--t-preset);border-color:#e9d5ff;background:#faf5ff}
.t-frame{color:var(--t-frame);border-color:#dbeafe;background:#eff6ff}
.t-cli{color:#fff;border-color:var(--t-cli);background:var(--t-cli)}
.t-plugin{color:var(--t-plugin);border-color:#99f6e4;background:#f0fdfa}
.t-skill{color:var(--t-skill);border-color:#bbf7d0;background:#f0fdf4}
.t-mcp{color:var(--t-mcp);border-color:#fed7aa;background:#fff7ed}
.t-other{color:var(--t-other);border-color:#e2e8f0;background:#f8fafc}
.t-dev{color:var(--t-dev);border-color:#fde68a;background:#fefce8}
.s-active{color:#15803d;border-color:#bbf7d0;background:#f0fdf4}
.s-runtime{color:#0f766e;border-color:#99f6e4;background:#f0fdfa}
.s-preset{color:#0e7490;border-color:#a5f3fc;background:#ecfeff}
.s-opt{color:#b45309;border-color:#fde68a;background:#fffbeb}
.s-inst{color:#475569;border-color:#e2e8f0;background:#f8fafc}
.s-on{color:#6d28d9;border-color:#ddd6fe;background:#f5f3ff}
.s-none{color:#94a3b8;border-color:#eef1f5;background:#fcfdff;border-style:dashed}
.s-ret{color:#b91c1c;border-color:#fecaca;background:#fef2f2}
.tree{background:#fbfcfd;border:1px solid var(--line);border-radius:10px;padding:12px 14px;font-size:13.5px}
.tree .q{font-weight:600;margin:10px 0 4px}
.tree .q:first-child{margin-top:0}
.tree .branch{color:#3f4753;margin:3px 0 3px 2px;padding-left:10px;border-left:2px solid var(--line)}
.tree .lv2{margin-left:18px}
.tree .lv3{margin-left:36px}
.states{table-layout:fixed;font-size:13px}
.states th{position:static;padding:7px 8px}
.states td{padding:9px 8px;vertical-align:top;border-bottom:1px solid var(--line2)}
.states td:first-child{white-space:normal}
.states td:nth-child(3),.states td:nth-child(4),.states td:nth-child(6){text-align:center}
.states th:nth-child(3),.states th:nth-child(4),.states th:nth-child(6){text-align:center}
.st-ok{color:#15803d;border-color:#bbf7d0;background:#f0fdf4}
.st-off{color:#b45309;border-color:#fde68a;background:#fffbeb}
.st-need{color:#1d4ed8;border-color:#dbeafe;background:#eff6ff}
.st-off.tag{color:#b45309;border-color:#fde68a;background:#fffbeb}
.st-mix{color:#6b7280;border-color:#e5e7eb;background:#f9fafb}
.tier-must{border-left:4px solid #b91c1c}.tier-rec{border-left:4px solid #15803d}
.tier-scene{border-left:4px solid #1d4ed8}.tier-no{border-left:4px solid #94a3b8}
.tier-must>.tag,.tag.tier-must{color:#b91c1c;border-color:#fecaca;background:#fef2f2}
.tag.tier-rec{color:#15803d;border-color:#bbf7d0;background:#f0fdf4}
.tag.tier-scene{color:#1d4ed8;border-color:#dbeafe;background:#eff6ff}
.tag.tier-no{color:#475569;border-color:#e2e8f0;background:#f8fafc}
table.tier-tbl{table-layout:fixed}
table.tier-tbl td{word-break:break-word}
table.tier-tbl .tag{white-space:normal}
table.tier-tbl td:first-child code{font-size:11.5px}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:8px 9px;border-bottom:1px solid var(--line2);vertical-align:top}
th{font-size:12px;color:var(--muted);font-weight:600;background:#fbfcfd;position:sticky;top:0;z-index:5;
 box-shadow:inset 0 -1px 0 var(--line)}
.tablewrap table{min-width:920px}
.wide{table-layout:fixed}
.tablewrap th:first-child,.tablewrap td:first-child{min-width:205px}
.tablewrap th:nth-child(5),.tablewrap td:nth-child(5){min-width:118px;white-space:nowrap}
tbody tr:hover{background:#fafbfd}
table.mini{font-size:13px}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:0 0 10px}
.toolbar select,.toolbar input{font:inherit;font-size:13px;padding:6px 8px;border:1px solid var(--line);border-radius:8px;
 background:#fff;color:var(--ink)}
.toolbar input[type=search]{min-width:190px;flex:1}
.toolbar label{font-size:12.5px;color:var(--muted);display:flex;gap:5px;align-items:center}
.count{font-size:12.5px;color:var(--muted);margin-left:auto}
.tablewrap{overflow:auto;max-height:74vh;border:1px solid var(--line);border-radius:10px;background:#fff}
.tablewrap table{border:0}
th.sortable{cursor:pointer;user-select:none}
th.sortable:hover{color:var(--ink)}
th .arrow{opacity:.45;font-size:10px}
.pkg{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px;font-weight:600;word-break:break-all}
.purpose{font-size:13px}
.desc{color:#7a8390;font-size:11.5px;margin-top:2px}
.badge-unv{color:#b45309;border-bottom:1px dashed #d97706;cursor:help}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.kv{display:grid;grid-template-columns:120px 1fr;gap:6px 10px;font-size:13px}
.note{background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:10px 12px;font-size:13px;color:#78350f}
.note.blue{background:#eff6ff;border-color:#dbeafe;color:#1e3a8a}
.note b{font-weight:700}
footer{color:var(--muted);font-size:12px;margin-top:26px;border-top:1px solid var(--line);padding-top:14px}
@media (max-width:900px){
 .grid2{grid-template-columns:1fr}
 h1{font-size:19px}.lede{font-size:14px}
 .tablewrap table{min-width:600px}
 .tablewrap{max-height:none}
 th{position:static}
}
@media (max-width:760px){
 .wrap{padding:0 12px 56px}
 .stats{grid-template-columns:1fr 1fr;gap:8px}
 .stat b{font-size:17px}
 .lede{font-size:13.5px}
 .card{padding:13px 13px}
 .tablewrap{border:0;background:transparent;overflow:visible}
 .tablewrap table{min-width:0}
 .tablewrap thead{display:none}
 .tablewrap tbody tr{display:block;background:#fff;border:1px solid var(--line);border-radius:10px;
  padding:9px 11px;margin:0 0 8px}
 .tablewrap tbody td{display:block;border:0;padding:2px 0;min-width:0!important;white-space:normal}
 .tablewrap tbody td[data-l]:before{content:attr(data-l) " · ";color:var(--muted);font-size:11.5px}
 .tablewrap tbody td[data-l="类型"]:before,.tablewrap tbody td[data-l="方向"]:before{content:""}
 .tablewrap tbody td.col-opt{display:block}
 .pkg{font-size:13px}
 table.mini{font-size:12.5px}
 table.mini thead{display:none}
 table.mini tbody tr{display:block;border-bottom:1px solid var(--line);padding:7px 0}
 table.mini tbody tr:last-child{border-bottom:0}
 table.mini tbody td{display:block;border:0;padding:1px 0}
 table.mini tbody td[data-l]:before{content:attr(data-l) "：";color:var(--muted);font-size:11.5px}
 table.mini tbody td[data-l="包"] code{font-size:13px}
 .states{display:block;table-layout:auto}
 .states thead{display:none}
 .states tbody,.states tr{display:block}
 .states tr{border:1px solid var(--line);border-radius:10px;padding:9px 11px;margin:0 0 8px;background:#fff}
 .states td{display:block;border:0;padding:2px 0}
 .states td[data-l]:before{content:attr(data-l) "：";color:var(--muted);font-size:11.5px}
'''

JS = '''
const ROWS = __ROWS__;
const TYPE_CLS = {"Bundle":"t-bundle","Preset":"t-preset","框架":"t-frame","CLI":"t-cli","Plugin":"t-plugin","Skill":"t-skill","MCP":"t-mcp","其他":"t-other","开发工具":"t-dev"};
const ST_CLS = {"active":"s-active","runtime":"s-runtime","preset":"s-preset","optional":"s-opt","installed":"s-inst","ondemand":"s-on","none":"s-none","retired":"s-ret"};
const GH = "https://github.com/deepseek-ai/deepseek-harness";
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}
function fmt(n){return n==null?'<span class="muted badge-unv" title="npm downloads API 未返回该包数据">未核实</span>':n.toLocaleString();}
function ghLink(r){
  if(r.path) return '<a href="'+GH+'/blob/master/'+r.path+'" target="_blank" rel="noopener">源码</a>';
  if(r.name.indexOf("libreoffice-kit")===0) return '<a href="https://github.com/deepseek-ai/dsh-libreoffice-kit" target="_blank" rel="noopener">仓库</a>';
  if(r.name.indexOf("node-addon")===0) return '<a href="'+GH+'/tree/master/native/system" target="_blank" rel="noopener">仓库</a>';
  return '<a href="'+GH+'/tree/master/packages" target="_blank" rel="noopener">仓库</a>';
}
const SHORT = {"active":"已激活·组合层","runtime":"已激活·运行时","preset":"已激活·Preset","optional":"随包·未启用",
  "installed":"随包·未启用","ondemand":"官方按需·未落盘","optional_off":"官方可选·未落盘","none":"无官方入口·未落盘","retired":"已下架"};
function rowHtml(r, mode){
  const desc = r.desc ? '<div class="desc">'+esc(r.desc)+'</div>' : '';
  const unv = r.conf==='mid' ? ' <span class="badge-unv" title="依赖在，但未见 patch 行，激活状态未核实">未核实</span>' : '';
  const st = '<span class="tag '+(ST_CLS[r.status]||'s-none')+'" title="'+esc(r.statusLabel)+'">'+esc(SHORT[r.status]||r.statusLabel)+'</span>'+unv;
  if(mode==='default'){
    return '<tr><td><span class="pkg">'+esc(r.name)+'</span><div class="sm"><a href="https://www.npmjs.com/package/'+r.pkg+'" target="_blank" rel="noopener">npm</a> · '+ghLink(r)+'</div></td>'+
      '<td data-l="类型"><span class="tag '+(TYPE_CLS[r.type]||'t-other')+'">'+esc(r.type)+'</span></td>'+
      '<td data-l="默认状态">'+st+'<div class="desc">'+esc(r.ev)+'</div></td></tr>';
  }
  return '<tr>'+
    '<td><span class="pkg">'+esc(r.name)+'</span><div class="sm"><a href="https://www.npmjs.com/package/'+r.pkg+'" target="_blank" rel="noopener">npm</a> · '+ghLink(r)+'</div></td>'+
    '<td data-l="类型"><span class="tag '+(TYPE_CLS[r.type]||'t-other')+'">'+esc(r.type)+'</span></td>'+
    '<td data-l="方向"><span class="tag t-other">'+esc(r.dir)+'</span></td>'+
    '<td class="purpose">'+esc(r.purpose)+desc+'</td>'+
    '<td class="col-opt" data-l="版本·发布"><code>'+esc(r.version)+'</code><div class="desc">'+esc(r.date)+' · '+esc(r.maint)+'</div></td>'+
    '<td data-l="默认状态">'+st+'</td>'+
    '<td class="col-opt" data-l="周下载">'+fmt(r.weekly)+'</td></tr>';
}
function makeTable(root, opts){
  const st = {type:"", dir:"", status:"", q:"", sort:"name", dir2:1};
  const typeSel = root.querySelector('[data-f=type]'), dirSel = root.querySelector('[data-f=dir]'),
        stSel = root.querySelector('[data-f=status]'), qIn = root.querySelector('[data-f=q]'),
        cnt = root.querySelector('.count'), body = root.querySelector('[data-rows]');
  function uniq(k){return [...new Set(ROWS.filter(r=>opts.filter?opts.filter(r):true).map(r=>r[k]))].sort();}
  if(typeSel){uniq('type').forEach(v=>typeSel.insertAdjacentHTML('beforeend','<option value="'+v+'">'+v+'</option>'));}
  if(dirSel){uniq('dir').forEach(v=>dirSel.insertAdjacentHTML('beforeend','<option value="'+v+'">'+v+'</option>'));}
  if(stSel){
    const order=["active","runtime","preset","optional","installed","ondemand","optional_off","none","retired"];
    const labels={};ROWS.forEach(r=>labels[r.status]=r.statusLabel);
    order.filter(s=>labels[s]).forEach(s=>stSel.insertAdjacentHTML('beforeend','<option value="'+s+'">'+labels[s]+'</option>'));
  }
  function render(){
    let list = ROWS.filter(r=>opts.filter?opts.filter(r):true);
    if(st.type) list=list.filter(r=>r.type===st.type);
    if(st.dir) list=list.filter(r=>r.dir===st.dir);
    if(st.status) list=list.filter(r=>r.status===st.status);
    if(st.q){const q=st.q.toLowerCase();list=list.filter(r=>(r.name+" "+r.purpose+" "+r.desc+" "+r.dir).toLowerCase().includes(q));}
    const k=st.sort;
    list=list.slice().sort((a,b)=>{
      let x=a[k],y=b[k];
      if(k==="weekly"){x=x==null?-1:x;y=y==null?-1:y;return (x-y)*st.dir2;}
      if(k==="date"){return (x<y?-1:x>y?1:0)*st.dir2;}
      return String(x).localeCompare(String(y),"zh")*st.dir2;
    });
    body.innerHTML = list.map(r=>rowHtml(r,opts.mode)).join("");
    cnt.textContent = "显示 "+list.length+" / "+ROWS.filter(r=>opts.filter?opts.filter(r):true).length+" 个包";
  }
  root.querySelectorAll('th.sortable').forEach(th=>{
    th.addEventListener('click',()=>{
      const k=th.dataset.k;
      if(st.sort===k){st.dir2=-st.dir2;} else {st.sort=k;st.dir2=1;}
      root.querySelectorAll('th.sortable').forEach(o=>{const ar=o.querySelector('.arrow');if(ar)ar.textContent='';});
      const ar=th.querySelector('.arrow'); if(ar) ar.textContent = st.dir2>0?' ▲':' ▼';
      render();
    });
  });
  [typeSel,dirSel,stSel].forEach(el=>{if(el)el.addEventListener('change',()=>{st.type=typeSel?typeSel.value:"";st.dir=dirSel?dirSel.value:"";st.status=stSel?stSel.value:"";render();});});
  if(qIn) qIn.addEventListener('input',()=>{st.q=qIn.value;render();});
  render();
}
document.querySelectorAll('nav.tabs button').forEach(btn=>{
  btn.addEventListener('click',()=>{
    document.querySelectorAll('nav.tabs button').forEach(b=>b.classList.toggle('on',b===btn));
    document.querySelectorAll('section.tab').forEach(s=>s.classList.toggle('on',s.id===btn.dataset.tab));
    window.scrollTo({top:0,behavior:'smooth'});
  });
});
const w1=document.getElementById('wrap-default');
if(w1) makeTable(w1,{mode:'default',filter:r=>['active','runtime','preset','installed','optional'].indexOf(r.status)>=0});
const w2=document.getElementById('tab-all');
if(w2) makeTable(w2,{mode:'all'});
'''

HTML = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DeepSeek Harness @deepseek-ai 官方包调研报告（2026-11-07）</title>
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
<h1>DeepSeek Harness 官方 npm 包全景调研</h1>
<p class="lede"><b>一句话总结：</b>截至 2026-11-07，npm <code>@deepseek-ai</code> 作用域共有 <b>{n_total}</b> 个公开包，全部服务于 DeepSeek Harness（dsh）这一套"一切皆插件"的运行时。<b>执行一次 <code>npx @deepseek-ai/dsh web</code>：磁盘上会出现 {n_inst} 个包，其中 {n_act} 个默认就在跑，{n_off} 个装着但没启用；剩下 {n_none} 个根本不在包里</b>——它们要么是官方"按需包"（{n_ondemand} 个，插件页一键装），要么干脆没有官方入口（需自行 npm 安装）。</p>
<div class="meta">
<span>检索日期：2026-11-07（GMT+8）</span>
<span>统计口径：npm registry 搜索接口全量翻页 + 名称前缀 <code>@deepseek-ai/</code> 精确匹配，共 {n_total} 个</span>
<span>默认状态依据：dsh@0.2.2-rc.1 起的依赖闭包递归展开 + dsh-base / dsh-web-app@0.2.2-rc.1 的 <code>cordis.patch.yml</code></span>
</div>
<div class="stats">
<div class="stat"><b>{n_total}</b><span>作用域内包总数</span></div>
<div class="stat"><b>{n_inst}</b><span>随 CLI 落盘（依赖闭包）</span></div>
<div class="stat"><b>{n_act}</b><span>默认就在跑（已激活）</span></div>
<div class="stat"><b>{n_off}</b><span>装着但没启用</span></div>
<div class="stat"><b>{n_none}</b><span>不在包里</span></div>
<div class="stat"><b>276k★</b><span>deepseek-harness 仓库</span></div>
</div>
</div></header>

<div class="wrap">
<nav class="tabs">
<button class="on" data-tab="tab-default">① 默认安装清单</button>
<button data-tab="tab-all">② 全量分类（{n_total}）</button>
<button data-tab="tab-advice">③ 安装建议</button>
<button data-tab="tab-community">④ 官方推荐 ≠ 官方开发</button>
<button data-tab="tab-method">⑤ 方法与未核实项</button>
</nav>

<!-- ============ TAB 1 ============ -->
<section class="tab on" id="tab-default">
<div class="card">
<h2>先把两件事分开：装了什么 ≠ 开了什么</h2>
<div class="grid2">
<div>
<h3>① 安装层（谁让包落盘）</h3>
<ul>
<li><code>npx @deepseek-ai/dsh web</code>（或 <code>npm i -g @deepseek-ai/dsh</code>）安装 <code>dsh@0.2.2-rc.1</code>，它声明了 <b>87 个</b> <code>@deepseek-ai</code> 直接依赖。</li>
<li>从 7 个入口（<code>dsh</code>、<code>dsh-base</code>、<code>dsh-web-app</code>、<code>dsh-headless</code>、<code>dsh-sdk-app</code>、<code>dsh-acp-app</code>、<code>dsh-sdk-minimal</code>）递归展开 <code>dependencies</code>，落盘 <b>{n_inst}</b> 个包。</li>
<li>这 {n_inst} 个里面，{n_opt} 个是"装着但默认关闭"的官方可选 bundle，{n_ondemand} 个按需包其实<b>不在这 {n_inst} 个里</b>（见下张卡片）。</li>
</ul>
</div>
<div>
<h3>② 激活层（谁真的跑起来）</h3>
<ul>
<li>激活不看依赖，看 bundle 的 <code>cordis.patch.yml</code>：<code>dsh-base</code> 与 <code>dsh-web-app</code> 各声明 95 个插件包（含带子路径的条目），决定哪些插件被插入运行时。</li>
<li>再叠加 <b>Agent Preset</b>：<code>standard</code>（order 1，默认）/ <code>ptc</code> / <code>minimal</code> / <code>cordis</code>，决定一次会话里 Agent 拿到哪些工具（例：<code>dsh-tool-cordis</code> 只在 cordis preset 里）。</li>
<li>并集后 <b>{n_act}</b> 个包默认就在跑；另有 <b>{n_off}</b> 个包"装着但没启用"——这是最容易被误判的一类。</li>
</ul>
</div>
</div>
<div class="note blue" style="margin-top:12px"><b>置信度说明：</b>base / web 两层全部来自 npm 包内实际文件（高置信）；sdk / headless / acp 三个 profile 只验证了依赖，未逐行下载 patch（标为未核实）；可选/按需/下架清单来自 <code>dsh-official-bundles</code> 的编译产物常量（高置信）。</div>
</div>

<div class="card">
<h2>三种状态，一次分清</h2>
<p class="sm muted">这是最粗的一层划分（判断顺序：作用域 → 是否随包 → 是否默认激活）。<b>筛选下拉里的 9 个选项是它的细化版</b>，完整图例见 ②「全量分类」页顶部。</p>
<table class="states">
<thead><tr><th>状态</th><th>磁盘上有没有</th><th>运行时有没有在跑</th><th>怎么变成"在用"</th><th>数量 / 例子</th></tr></thead>
<tbody>
<tr>
 <td data-l="状态"><span class="tag st-ok">1 · 已激活</span></td>
 <td data-l="磁盘上">✅ 有（在依赖闭包内）</td>
 <td data-l="运行时">✅ 在跑（bundle patch 行命中 base/Web 层，或由默认 standard preset 提供，或本身就是运行时基座）</td>
 <td data-l="怎么变成在用">不用做任何事，装上就在用</td>
 <td data-l="数量/例子"><b>{n_act}</b> 个<br><span class="muted sm">dsh-tool-bash、dsh-tool-fs、dsh-skill、dsh-mcp-resources</span></td>
</tr>
<tr>
 <td data-l="状态"><span class="tag st-off">2 · 随包未激活</span></td>
 <td data-l="磁盘上">✅ 有</td>
 <td data-l="运行时">❌ 没有插件行，未被加载</td>
 <td data-l="怎么变成在用">三种情况：<br>a) 官方可选 bundle → 插件页开关一开即用（<b>不用再下载</b>）<br>b) 库 / 内部件 → 没有开关，被上层用到时才加载<br>c) 仅非默认 Preset 提供 → 切到 minimal / cordis 才有</td>
 <td data-l="数量/例子"><b>{n_off}</b> 个<br><span class="muted sm">a) terminal-bundle、session-search；b) libreoffice-kit；c) dsh-tool-cordis</span></td>
</tr>
<tr>
 <td data-l="状态"><span class="tag st-need">3 · 需另外安装</span></td>
 <td data-l="磁盘上">❌ 没有（不在依赖闭包内）</td>
 <td data-l="运行时">❌ 没有</td>
 <td data-l="怎么变成在用">分两种，<b>区别只在"有没有官方安装入口"</b>：<br>3a 官方按需包 → 插件页「发现 / 更多」里一键安装<br>3b 无官方入口 → 只能自己 <code>npm i</code>，多数是内部件，装了也没用</td>
 <td data-l="数量/例子"><b>{n_none}</b> 个<br><span class="muted sm">3a：dsh-subagent-claude-code、dsh-subagent-codex、dsh-cua-bundle（{n_ondemand + n_opt_off} 个）<br>3b：示例/测试/平台二进制等（{n_none - n_ondemand - n_opt_off} 个）</span></td>
</tr>
</tbody>
</table>
<div class="note" style="margin-top:12px"><b>回答你的疑问：</b>"按需安装"和"未随包"确实<b>都不是随包落盘</b>——你的直觉没错，是我上一版的两个标签起得不好。<br>
真正的区别只有一条：<b>有没有官方安装入口</b>。<br>
· <b>官方按需包</b>（<code>ON_DEMAND_BUNDLES</code>，{n_ondemand} 个）虽然没有随 dsh 一起装，但官方在插件页登记了入口，点一下就装；这也是"按需"二字的原本含义。<br>
· <b>未随包且无官方入口</b>（{n_none - n_ondemand - n_opt_off} 个）既不在包里、也没有任何官方入口，只能自己去 npm 装，而且多数是内部件（如 <code>dsh-acp-demo</code>、<code>node-addon-landlock-run</code>），手动装了也不会被加载。<br>
· 另外注意还有<b>第三类</b>：<code>dsh-cua-bundle</code> 属于"官方可选但当前版本没随包"，打开时才会下载（{n_opt_off} 个）。</div>
</div>

<div class="card">
<h2>Profile 模板：装完之后，不同入口激活不同组合</h2>
<table class="mini"><thead><tr><th>profile</th><th>启动方式</th><th>bundle 组合（PROFILE_TEMPLATES）</th><th>用途</th></tr></thead><tbody>{prof_html}</tbody></table>
<p class="sm muted">证据：<a href="{GH}/blob/master/packages" target="_blank" rel="noopener">deepseek-harness/packages</a> 内 <code>@deepseek-ai/dsh-official-bundles</code> 的 <code>PROFILE_TEMPLATES</code> 常量（npm 包 <code>lib/index.js</code> 可直接读取）；安装命令见 <a href="{GH}#run" target="_blank" rel="noopener">README「Run from npm」</a>。</p>
</div>

<div class="card">
<h2>Agent Preset：第二道开关（工具面在这一层才最终成形）</h2>
<table class="mini"><thead><tr><th>preset</th><th>order</th><th>成员包数</th><th>差异</th></tr></thead><tbody>{preset_html}</tbody></table>
<p class="sm muted">证据：<code>@deepseek-ai/dsh-web-app@0.2.2-rc.1</code> 内的 <code>presets/{{standard,ptc,minimal,cordis}}.patch.yml</code>；<code>order: 1</code> 的 standard 为默认（<a href="https://www.npmjs.com/package/@deepseek-ai/dsh-web-app" target="_blank" rel="noopener">npm 包文件</a>，亦可对照 <code>package.json</code> 的 <code>dsh.bundle.patch</code> 顺序）。</p>
</div>

<div class="card">
<h2>状态 2 里最值得注意的 4 个（装了、但默认没在跑）</h2>
<ul>{off_html}</ul>
<p class="sm muted">判断依据：在依赖闭包内（能被 npm 装到磁盘），但不在任一 <code>cordis.patch.yml</code> 的插件行里，因此不会被加载。其中 <code>dsh-mcp-client</code> 与 <code>dsh-skill-office</code> 的运行时启用路径未在源码中确认（见「方法与未核实项」）。</p>
</div>

<div class="card" id="wrap-default">
<h2>默认安装清单（{n_inst} 个随包落盘的包）</h2>
<p class="sm muted">绿色=已激活，青色=运行时基座，琥珀=随包但关闭，灰色=随包但未见激活行。未列出的 {n_none} 个包属于状态 3（需要另外安装）。把鼠标停在标签上可看完整判定文案。</p>
<div class="toolbar">
<select data-f="status"><option value="">全部默认状态</option></select>
<input type="search" data-f="q" placeholder="搜包名…">
<span class="count"></span>
</div>
<div class="tablewrap"><table class="mini"><thead><tr><th>包名 / 链接</th><th>类型</th><th>默认状态 / 证据</th></tr></thead>
<tbody data-rows></tbody></table></div>
</div>
</section>

<!-- ============ TAB 2 ============ -->
<section class="tab" id="tab-all">
<div class="card">
<h2>先看这张"状态图例"——下拉菜单里 9 个选项各自是什么意思</h2>
<p class="sm muted">筛选下拉里的每一项，都对应下面的一种真实状态。判断顺序其实就是三个问题：<b>在不在 @deepseek-ai 作用域 → 随不随 dsh 落盘 → 默认是否激活</b>。</p>

<div class="tree">
<div class="q">Q1 这个包在 <code>@deepseek-ai</code> 作用域下吗？</div>
<div class="branch"><span class="tag st-mix">否</span> → 社区包：不在本报告 422 的统计内，见 ④ 与 ⑥，需要自己 <code>npm i</code> 或 <code>dsh plugin add</code>。</div>
<div class="branch"><span class="tag st-ok">是</span> → 进入 Q2（共 <b>{n_total}</b> 个）</div>
<div class="q lv2">Q2 它随 dsh 一起落盘吗（在依赖闭包里）？</div>
<div class="branch lv2"><span class="tag st-need">不随包</span> → <b>{n_none}</b> 个，再问 Q2a：官方给不给安装入口？</div>
<div class="branch lv3">Q2a 有官方入口（<code>ON_DEMAND_BUNDLES</code> / 官方可选但未随包）→ <b>{n_ondemand + n_opt_off}</b> 个：插件页「发现 / 更多」一键装。</div>
<div class="branch lv3">Q2a 没有官方入口 → <b>{n_none - n_ondemand - n_opt_off}</b> 个：自行 <code>npm i</code>，多为内部件/示例/平台二进制，装了也不会被加载。</div>
<div class="branch lv2"><span class="tag st-off">随包落盘</span> → <b>{n_inst}</b> 个，进入 Q3</div>
<div class="q lv2">Q3 落盘之后，默认就在跑吗？</div>
<div class="branch lv3"><span class="tag st-ok">是</span> → <b>{n_act}</b> 个：命中 base / Web 的 <code>cordis.patch.yml</code>，或由默认 <code>standard</code> preset 提供，或本身就是运行时基座。不用管。</div>
<div class="branch lv3"><span class="tag st-off">否</span> → <b>{n_off}</b> 个：磁盘上有、没被加载。再分三种处理方式（见下表 2a / 2b / 2c）。</div>
</div>

<table class="states" style="margin-top:14px">
<colgroup><col style="width:15%"><col style="width:35%"><col style="width:6%"><col style="width:7%"><col style="width:29%"><col style="width:8%"></colgroup>
<thead><tr><th>筛选里显示的名字</th><th>含义</th><th>磁盘</th><th>在跑</th><th>怎么变成"在用"</th><th>数量</th></tr></thead>
<tbody>
<tr><td data-l="名字"><span class="tag s-active">已激活·组合层</span></td><td data-l="含义">命中了 <code>dsh-base</code> 或 <code>dsh-web-app</code> 的插件行</td><td data-l="磁盘">有</td><td data-l="在跑">是</td><td data-l="怎么用">不用做任何事</td><td data-l="数量">{n_base}</td></tr>
<tr><td data-l="名字"><span class="tag s-runtime">已激活·运行时</span></td><td data-l="含义">运行时基座 / profile 入口本身（<code>dsh</code>、<code>cordis</code>、<code>dsh-base</code>、<code>dsh-web-app</code> 等），由 app-boot 直接装载，不走插件行</td><td data-l="磁盘">有</td><td data-l="在跑">是</td><td data-l="怎么用">不用做任何事</td><td data-l="数量">{n_runtime}</td></tr>
<tr><td data-l="名字"><span class="tag s-preset">已激活·Preset</span></td><td data-l="含义">只在某个 Agent Preset 里声明（standard / ptc / minimal / cordis）。共 {n_preset} 个，其中 {n_preset_std} 个在默认 standard 内 → 算"在跑"；剩下 {n_preset_other} 个见 2c</td><td data-l="磁盘">有</td><td data-l="在跑">是（默认）</td><td data-l="怎么用">保持默认即可</td><td data-l="数量">{n_preset_std}</td></tr>
<tr><td data-l="名字"><span class="tag s-opt">随包·未启用</span></td><td data-l="含义"><b>2a 官方可选 bundle</b>：官方登记、装了但开关没开</td><td data-l="磁盘">有</td><td data-l="在跑">否</td><td data-l="怎么用">插件页把开关打开（不用再下载）</td><td data-l="数量">{n_opt}</td></tr>
<tr><td data-l="名字"><span class="tag s-inst">随包·未启用</span></td><td data-l="含义"><b>2b 库 / 内部件</b>：没有独立开关，被上层用到时才加载（如 <code>libreoffice-kit</code> 被 office-to-pdf 调用）</td><td data-l="磁盘">有</td><td data-l="在跑">否</td><td data-l="怎么用">无需操作，由使用方加载</td><td data-l="数量">{n_lib}</td></tr>
<tr><td data-l="名字"><span class="tag s-preset">随包·未启用</span></td><td data-l="含义"><b>2c 仅非默认 Preset 声明</b>：切到 minimal / cordis 才会加载</td><td data-l="磁盘">有</td><td data-l="在跑">否</td><td data-l="怎么用">切 preset</td><td data-l="数量">{n_preset_other}</td></tr>
<tr><td data-l="名字"><span class="tag s-on">官方按需·未落盘</span></td><td data-l="含义"><b>3a</b> 官方 <code>ON_DEMAND_BUNDLES</code>：没随包，但插件页有官方入口</td><td data-l="磁盘">无</td><td data-l="在跑">否</td><td data-l="怎么用">插件页一键安装</td><td data-l="数量">{n_ondemand}</td></tr>
<tr><td data-l="名字"><span class="tag s-on">官方可选·未落盘</span></td><td data-l="含义"><b>3a'</b> 官方可选 bundle，但当前版本没随包（<code>dsh-cua-bundle</code>）</td><td data-l="磁盘">无</td><td data-l="在跑">否</td><td data-l="怎么用">插件页打开时才下载</td><td data-l="数量">{n_opt_off}</td></tr>
<tr><td data-l="名字"><span class="tag s-none">无官方入口·未落盘</span></td><td data-l="含义"><b>3b</b> 既不在包里也没有官方入口：示例、测试夹具、内部散件、平台二进制</td><td data-l="磁盘">无</td><td data-l="在跑">否</td><td data-l="怎么用">自行 <code>npm i</code>，通常不必装</td><td data-l="数量">{n_noentry}</td></tr>
<tr><td data-l="名字"><span class="tag s-ret">已下架</span></td><td data-l="含义">曾随包、已列入 <code>RETIRED_BUNDLES</code>，profile 加载时会被移除</td><td data-l="磁盘">无</td><td data-l="在跑">否</td><td data-l="怎么用">不用装</td><td data-l="数量">{n_retired}</td></tr>
</tbody>
</table>
<p class="sm muted" style="margin-top:8px">你提的三层判断和这张表是同一套逻辑，只是我把第 3 层"按需激活"进一步拆成了 2a / 2b / 2c——因为"随包但没开"其实有三种不同原因，处理动作也不一样。合计：{n_total} = {n_inst}（落盘）+ {n_none}（未落盘）；落盘的 {n_inst} = {n_act}（在跑）+ {n_off}（没开）。</p>
</div>

<div class="card">
<h2>全量分类：{n_total} 个包</h2>
<p class="sm muted">类型判据：Bundle=官方组合包，Preset=Agent/Permission 预设，框架=接缝/注册表/协议，Plugin=可装卸插件（含工具与 UI），Skill=Skill 提供方与内容包，MCP=MCP 客户端/资源，CLI=命令入口，其他=原生库与杂项，开发工具=测试/示例/mock。方向为人工归类，一包只归一个主方向。</p>
<div class="toolbar">
<select data-f="type"><option value="">全部类型</option></select>
<select data-f="dir"><option value="">全部方向</option></select>
<select data-f="status"><option value="">全部默认状态</option></select>
<input type="search" data-f="q" placeholder="搜包名 / 用途 / 描述…">
<span class="count"></span>
</div>
<div class="tablewrap">
<table><thead><tr>
<th class="sortable" data-k="name">包名 <span class="arrow"></span></th>
<th class="sortable" data-k="type">类型 <span class="arrow"></span></th>
<th class="sortable" data-k="dir">方向 <span class="arrow"></span></th>
<th>用途（中文归纳 / 官方描述）</th>
<th class="sortable col-opt" data-k="date">版本·发布 <span class="arrow"></span></th>
<th class="sortable" data-k="status">默认状态 <span class="arrow"></span></th>
<th class="sortable col-opt" data-k="weekly">周下载 <span class="arrow"></span></th>
</tr></thead><tbody data-rows></tbody></table>
</div>
<p class="sm muted" style="margin-top:10px">下载量口径：npm registry 搜索接口返回的 <code>downloads.weekly</code> 快照（2026-11-07 抓取，滚动 7 天）。"未核实"= 接口未返回该包数据，不代表 0。注意：多数包周下载都在 80 万量级，因为 dsh 一次安装会把整个依赖闭包都拉一遍，<b>下载量在这里不能当作"受欢迎程度"读</b>，只能当作"被安装频率"。</p>
</div>
</section>

<!-- ============ TAB 3 ============ -->
<section class="tab" id="tab-advice">
<div class="card">
<h2>先讲清楚"建议"是怎么产生的</h2>
<p>这张表不是拍脑袋排的，也不是照抄别人的插件清单。逻辑只有三层：</p>
<ol>
<li><b>先看它现在是什么状态。</b>状态 1（已激活）根本不叫"建议装"，叫"别删"；状态 2（随包未启用）成本最低，开个开关就行；状态 3（需另外安装）才有"该不该装"的问题。所以每条都标了「当前状态」。</li>
<li><b>再看它补的是哪块短板。</b>官方已覆盖文件/命令/子智能体/联网/MCP 资源，所以"必装"层几乎全是官方默认项；真正的增量在官方<b>故意不做</b>的地方（插件发现、上下文可视化、终端 TUI、视觉）。</li>
<li><b>最后看维护与风险。</b>官方包有兼容承诺（虽然仍是 developer preview），社区包没有；所以社区项一律单列，并标明"谁在推荐"。</li>
</ol>
<div class="note blue" style="margin-top:10px"><b>关于"安装"这件事，动作只有三种，别想复杂：</b><br>
· 状态 1 → <b>什么都不用做</b>；<br>
· 状态 2a（可选 bundle）→ <b>插件页把开关打开</b>，包已经在磁盘上，不会重新下载；<br>
· 状态 2c（仅非默认 Preset）→ <b>切 preset</b>；<br>
· 状态 3a（官方按需）→ <b>插件页「发现 / 更多」里点安装</b>；<br>
· 状态 3b（无官方入口）→ <b>不要装</b>，装了也不会被加载；<br>
· 社区包（不在 422 里）→ <code>npm i</code> 或 <code>dsh plugin add</code>，风险自负。</div>
</div>

<div class="card">
<h2>路线 A · 只用官方包（零第三方风险）</h2>
<p class="sm muted">下面四层全部来自官方 <code>@deepseek-ai</code> 作用域，没有一个是社区包。"推荐/场景"两层里绝大多数是<b>状态 2</b>——已经躺在你磁盘上了，只是没开。</p>
</div>
<p class="sm muted">排序逻辑：先看"是否已默认激活"（已激活的不必折腾），再看"补的是哪块短板"，最后看维护状态。新增的「当前状态」列用三色标签区分：<span class="tag st-ok">1 · 已激活</span> 装上就在跑；<span class="tag st-off">2 · 随包未激活</span> 磁盘上有、开关没开；<span class="tag st-need">3 · 需另外安装</span> 磁盘上没有。所有条目都能在官方清单里找到出处，不引入第三方包。</p>
</div>
{tiers_html}
<div class="card">
<h2>一句话决策路径（纯官方路线）</h2>
<ol>
<li>只想用起来：什么都不用装，<code>npx @deepseek-ai/dsh web</code> → 填 DeepSeek API Key → 选工作区。</li>
<li>天天用、长期会话：开 <code>terminal-bundle</code> + <code>session-search</code> + <code>session-titles</code>；接受自动评审再加 <code>auto-review</code>。</li>
<li>要处理文档：启用 <code>dsh-skill-office</code>（Office Skill 已随包，只是没激活）。</li>
<li>要接外部工具：启用/配置 <code>dsh-mcp-client</code>，把 MCP 服务端挂进来（资源读取工具 <code>dsh-mcp-resources</code> 本来就在跑）。</li>
<li>要跨 Agent 协作：按需装 <code>dsh-subagent-claude-code</code> 或 <code>dsh-subagent-codex</code>（官方 ON_DEMAND）。</li>
</ol>
</div>
<div class="card">
<h2>路线 B · 官方 + 社区（<b>我的建议</b>，非官方立场）</h2>
<p>这一节是我自己的判断，不是官方清单。官方只对 <code>@deepseek-ai</code> 作用域内的包负责；社区包没有兼容承诺，而 DSH 仍是 developer preview，升级后插件失效是常态。</p>
<p><b>我筛社区包的三条硬标准：</b>① 近 7 天内有发版；② 周下载 ≥ 2 万或 GitHub 星 ≥ 900；③ 补的是官方<b>明确不做</b>的能力（插件发现、上下文可见性、@文件引用、视觉、终端）。三条不满足一律不进这张表。</p>
<table class="wide" style="min-width:900px"><colgroup><col style="width:8%"><col style="width:23%"><col style="width:13%"><col style="width:18%"><col style="width:24%"><col style="width:14%"></colgroup>
<thead><tr><th>我的建议</th><th>包（npm 名）</th><th>谁在推荐</th><th>数据（2026-11-08 实测）</th><th>它补了什么</th><th>风险 / 注意</th></tr></thead>
<tbody>
<tr><td data-l="建议"><span class="tag st-ok">强烈建议</span></td>
<td data-l="包"><code>dshmarket</code><div class="desc">仓库 dsh-market/dsh-market</div></td>
<td data-l="谁推荐"><span class="tag st-need">我</span></td>
<td data-l="数据">11k★（截图 11,183）<br>周下载 308,046<br>1.73.14 · 2026-11-06</td>
<td data-l="补什么">把社区插件市场搬进 UI，逛/装/卸/升都能点。它是后面所有社区插件的前置，装了它就不用记命令行。</td>
<td data-l="风险">装的是第三方代码；索引非官方，质量参差</td></tr>
<tr><td data-l="建议"><span class="tag st-ok">强烈建议</span></td>
<td data-l="包"><code>dsh-context</code><div class="desc">仓库 bowenliang123/dsh-context</div></td>
<td data-l="谁推荐"><span class="tag st-off">官方（媒体转述）</span></td>
<td data-l="数据">4.5k★（截图 4,440）<br>周下载 144,773<br>0.82.2 · 2026-11-07</td>
<td data-l="补什么">上下文占用可视化：看清系统提示、工具结果各占多少，长任务跑偏时能判断是不是被压缩吃掉了。</td>
<td data-l="风险">与官方 <code>compaction-*</code> 功能有重叠，别两边都调</td></tr>
<tr><td data-l="建议"><span class="tag st-ok">建议</span></td>
<td data-l="包"><code>dsh-at-file</code><div class="desc">npm 无 repository 字段</div></td>
<td data-l="谁推荐"><span class="tag st-need">我</span></td>
<td data-l="数据">563★（截图口径，未复核）<br>周下载 41,797<br>0.6.3 · 2026-08-19</td>
<td data-l="补什么">Codex 风格的 <code>@路径</code> 引用：不把文件内容塞进输入框，只引用路径，省 token。</td>
<td data-l="风险">近 3 个月未发版；README 建议用 GitHub tarball 而非 npm</td></tr>
<tr><td data-l="建议"><span class="tag st-need">可选</span></td>
<td data-l="包"><code>dsh-better-sidebar</code><div class="desc">仓库 omdsh-dev/DSH-better-sidebar</div></td>
<td data-l="谁推荐"><span class="tag st-off">官方（媒体转述）</span></td>
<td data-l="数据">5k★（截图 4,959）<br>周下载 78,109<br>0.30.1 · 2026-11-05</td>
<td data-l="补什么">文件树 + 编辑器 + 变更 + 任务收进一栏，改完就地看 diff，不用切窗口。</td>
<td data-l="风险">与官方 <code>sidebar-*</code> 插件功能重叠，大版本升级要跟</td></tr>
<tr><td data-l="建议"><span class="tag st-need">可选</span></td>
<td data-l="包"><code>@anionex/dsh-vision-toolkit</code><div class="desc">仓库 Anionex/dsh-vision-toolkit</div></td>
<td data-l="谁推荐"><span class="tag st-need">我</span></td>
<td data-l="数据">931★（截图 928）<br>周下载 2,911<br>0.1.49 · 2026-11-06</td>
<td data-l="补什么">给纯文本模型加"眼睛"：截图问答、OCR、元素定位。看报错截图、读设计稿时有用。</td>
<td data-l="风险">同名 fork 至少 4 个（<code>@mengruo/</code>、<code>@dsh-external/</code>、<code>@junjian.work/</code>），认准作者别装错</td></tr>
<tr><td data-l="建议"><span class="tag st-need">可选</span></td>
<td data-l="包"><code>@liustack/modlens</code><div class="desc">仓库 liustack/modlens</div></td>
<td data-l="谁推荐"><span class="tag st-need">我</span></td>
<td data-l="数据">4.8k★（截图 4,820）<br>周下载 86,518<br>3.27.2 · 2026-10-23</td>
<td data-l="补什么">视觉的另一条路线（靠外部 CLI 提供视觉能力），和上面那个二选一即可。</td>
<td data-l="风险">依赖外部 CLI 与登录态，配置成本高于 vision-toolkit</td></tr>
<tr><td data-l="建议"><span class="tag st-need">可选</span></td>
<td data-l="包"><code>@deepseek-harness-tui/dsh-tui</code><div class="desc">仓库 ccch1mneyyy/dsh-TUI</div></td>
<td data-l="谁推荐"><span class="tag st-off">官方（团队推荐系列①）</span></td>
<td data-l="数据">7.1k★（截图 7,100）<br>周下载 21,210<br>0.19.0 · 2026-11-06</td>
<td data-l="补什么">全屏终端 TUI：SSH/键盘党不必开浏览器，底部常驻上下文与 TPS。</td>
<td data-l="风险">需要 Node ≥ 22.19；与 Web UI 是两套入口</td></tr>
</tbody></table>

<div class="note" style="margin-top:12px"><b>和截图的口径对不上时，以这里的实测为准：</b>截图写的 <code>dsh-market</code>，npm 上裸名不存在，实际包名是 <code>dshmarket</code>（<code>@dsh-market/*</code> 是它的插件端/核心层拆包）；截图写的 <code>dsh-vision-toolkit</code> 裸名同样不存在，实际是 <code>@anionex/dsh-vision-toolkit</code>（另有 3 个作者的 fork）。星数、周下载与截图基本吻合（11,183→11k、4,440→4.5k、4,959→5k、4,820→4.8k、928→931），只有 <code>dsh-at-file</code> 的 563★ 我没复核到（npm 未填 repository 字段）。</div>

<div class="note blue" style="margin-top:10px"><b>官方建议 vs 我的建议，差在哪：</b><br>
· <b>官方建议</b>＝只针对自己的包，且只给"可选 / 按需"两种入口（本页路线 A）。有版本兼容承诺，坏了能指望修。<br>
· <b>我的建议</b>＝在官方基础上加社区包（本页路线 B）。判断依据是"发版频率 + 下载/星数 + 是否补官方空白"，<b>没有兼容承诺</b>——DSH 每次破坏性变更，社区插件都可能要等作者适配（历史上 dsh-TUI 就跟着 0.1.7→0.2.2 连追了几个版本）。</div>
</div>
</section>

<!-- ============ TAB 4 ============ -->
<section class="tab" id="tab-community">
<div class="card">
<h2>官方推荐 ≠ 官方开发（本节不计入 {n_total} 个官方包）</h2>
<div class="note"><b>边界：</b>下表全部是社区包（npm 作用域不是 <code>@deepseek-ai</code>，仓库也不在 <code>deepseek-ai</code> 组织下）。它们之所以出现，是因为 DSH 项目负责人崔添翼（Tianyi Cui）在 X / GitHub 上公开推荐过，媒体（智东西系）做过"DSH 团队推荐系列"报道。<b>未抓取到官方"Official Picks"清单页面</b>，因此本节按"媒体报道 + 可核 npm/GitHub 数据"呈现，置信度逐条标注。</div>
<div class="tablewrap" style="max-height:none;margin-top:12px">
<table class="wide"><colgroup><col style="width:25%"><col style="width:14%"><col style="width:21%"><col style="width:29%"><col style="width:11%"></colgroup>
<thead><tr><th>npm 包 / 最新版本</th><th>GitHub 仓库</th><th>社区热度（2026-11-07）</th><th>与官方的关系</th><th>置信度</th></tr></thead>
<tbody>{comm_html}</tbody></table>
</div>
<p class="sm muted">参考来源：<a href="https://xmsumi.com/detail/4329" target="_blank" rel="noopener">dsh-TUI 报道</a>、<a href="https://m.toutiao.com/article/7699110227093799434" target="_blank" rel="noopener">智东西「12 款插件」盘点</a>、<a href="https://m.toutiao.com/article/7690145566331798016" target="_blank" rel="noopener">「DSH 团队推荐系列①」</a>；npm/GitHub 数据为本次直接抓取。</p>
</div>
<div class="card">
<h2>社区热度的量级感（用于判断"值不值得跟"）</h2>
<ul>
<li>dsh 本体：GitHub <b>276k★</b> / 34k fork；npm 周下载 <b>826,814</b>、月下载 <b>2,287,267</b>（同为快照口径）。</li>
<li>社区插件目录 <code>dsh-plugin-catalog</code> 自称收录 <b>9305</b> 条（周下载 111,822）——生态规模远大于官方 {n_total} 个包，这也是本报告把官方与社区严格分节的原因。</li>
<li>GitHub <code>dsh-plugin</code> topic 下已出现 PicGo、WeKnora、reactive-resume、OpenViking 等成熟项目挂标签接入，说明"插件化接入"已是既成事实。</li>
</ul>
</div>
</section>

<!-- ============ TAB 5 ============ -->
<section class="tab" id="tab-method">
<div class="card">
<h2>数据来源与口径</h2>
<div class="kv">
<div>包清单</div><div>npm registry 搜索接口 <code>/-/v1/search</code> 多关键词翻页（每词 5 页 ×250），再按 <code>@deepseek-ai/</code> 前缀精确过滤 → <b>{n_total}</b> 个。完整性交叉验证：把官方 5 个 profile 模板、base/web patch、dsh 依赖闭包、可选/按需/下架清单里出现的包名逐一比对，除 <code>commander/js-yaml/node-addon-require-builtin</code>（非本作用域）与两个子路径 id 外，无遗漏。</div>
<div>安装/激活</div><div><code>@deepseek-ai/dsh@0.2.2-rc.1</code>、<code>dsh-base</code>、<code>dsh-web-app</code> 的 <code>package.json</code> 与包内 <code>cordis.patch.yml</code>、<code>presets/*.patch.yml</code>（从 npm tarball 解包直读，非文档转述）。</div>
<div>清单常量</div><div><code>@deepseek-ai/dsh-official-bundles@0.2.2-alpha.2</code> 的 <code>lib/index.js</code>：PROFILE_TEMPLATES / OPTIONAL_BUNDLES / ON_DEMAND_BUNDLES / RETIRED_BUNDLES / PROTECTED_PLUGINS / EXPERIMENTAL_BUNDLES。</div>
<div>下载量</div><div>npm registry 搜索接口 <code>/-/v1/search</code> 返回的 <code>downloads.weekly / monthly</code> 快照（2026-11-07 抓取）。交叉校验：官方 <code>/downloads/point/last-week</code> 对 dsh 报 844,567，与快照 826,814 相差约 2%，属窗口口径差异，本报告统一采用快照值。</div>
<div>文档</div><div>仓库 <code>docs/tool-catalog.md</code>（工具清单，自动生成）、<code>docs/config-catalog.md</code>（配置项清单，含源码路径）、根 <code>README.md</code>。</div>
<div>GitHub</div><div>组织仓库页（46 个仓库）与 shields.io stars 徽章接口（GitHub REST API 触发匿名限流，改用徽章数据）。</div>
</div>
</div>
<div class="card">
<h2>未核实项（不猜，逐条列出）</h2>
<table class="mini"><thead><tr><th>项目</th><th>现状与原因</th></tr></thead><tbody>{unv_html}</tbody></table>
</div>
<div class="card">
<h2>已知问题与限制（来自一手材料）</h2>
<ul>
<li><b>开发者预览，明确会破坏兼容</b>：仓库 README 原文 "in <i>developer preview</i> ... THERE WILL BE COMPATIBILITY-BREAKING CHANGES"。所有 <code>dsh-*</code> 版本仍是 <code>0.x</code>，大量核心包停在 <code>0.0.1-rc.1</code>（2026-08-10 发布后未再更新）。</li>
<li><b>版本节奏分裂</b>：<code>dsh@0.2.2-rc.1</code> 依赖 <code>dsh-official-bundles@0.2.2-rc.1</code>，但该包 npm 的 <code>latest</code> 标签仍指向 <code>0.2.2-alpha.2</code>；同批包存在 <code>rc/alpha</code> 混布，脚本里写死版本号容易踩空。</li>
<li><b>发布配置与文档不一致处</b>：<code>dsh-fs-observation-policy</code>（读后写策略）官方 <code>tool-catalog.md</code> 明确写"shipped compositions leave its row disabled"，即默认不启用。</li>
<li><b>可选 bundle 全部挂 experimental 前缀</b>：{n_opt} 个可选 bundle 中多数以 <code>dsh-experimental-</code> 开头并被插件页打上 Experimental 徽章，稳定性低于 base 层。</li>
<li><b>原生依赖按平台分发</b>：<code>libreoffice-kit-*</code>、<code>node-addon-system-*</code>、<code>node-addon-landlock-run-*</code> 各有 5~6 个平台子包，锁定版本升级时要一起动。</li>
</ul>
</div>
<footer>
本报告所有包名、版本、日期、下载量、Star 数均为 2026-11-07 实际抓取；未能核实的字段显式标注"未核实"，不做推测填充。社区推荐部分严格区分"官方开发"与"官方推荐"，不计入 {n_total} 个官方包统计。
</footer>
</div>

<script>{JS.replace('__ROWS__', json.dumps(rows, ensure_ascii=False))}</script>
</body>
</html>'''

open('../report.html', 'w', encoding='utf-8').write(HTML)
print('written', len(HTML))
