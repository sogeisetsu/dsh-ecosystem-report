import json, re, urllib.request

# 1) package -> monorepo source path, parsed from docs/config-catalog.md
src = open('../docs_config-catalog.md', encoding='utf-8').read()
paths = {}
blocks = re.split(r'<!-- BEGIN GENERATED config-catalog:(@deepseek-ai/[a-z0-9-]+) -->', src)
for i in range(1, len(blocks), 2):
    name = blocks[i].replace('@deepseek-ai/', '')
    body = blocks[i + 1]
    m = re.search(r'`source`: \[`(packages/[^`:]+)', body)
    if m:
        p = m.group(1)
        p = re.sub(r':\d+$', '', p)
        paths[name] = p

# 2) tool-catalog paths for tool packages
tc = open('../docs_tool-catalog.md', encoding='utf-8').read()
for m in re.finditer(r'## `@deepseek-ai/([a-z0-9-]+)`\n(?:.|\n)*?Source: \[`(packages/[^`:]+)', tc):
    paths.setdefault(m.group(1), re.sub(r':\d+$', '', m.group(2)))

json.dump(paths, open('../srcpaths.json', 'w'), indent=1)
print('paths', len(paths))

# 3) bundle dependency lists
def reg(p):
    u = f"https://registry.npmjs.org/{p.replace('/', '%2F')}"
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'x'}), timeout=40))

bundles = ["@deepseek-ai/dsh", "@deepseek-ai/dsh-base", "@deepseek-ai/dsh-web-app",
           "@deepseek-ai/dsh-headless", "@deepseek-ai/dsh-sdk-app", "@deepseek-ai/dsh-acp-app",
           "@deepseek-ai/dsh-sdk-minimal"]
out = {}
for b in bundles:
    d = reg(b)
    vs = [v for v in d['versions'] if v.startswith('0.2.2-rc')]
    v = vs[-1] if vs else d['dist-tags']['latest']
    deps = d['versions'][v].get('dependencies', {})
    out[b] = {'version': v, 'deps': sorted(k.replace('@deepseek-ai/', '') for k in deps if k.startswith('@deepseek-ai/'))}
json.dump(out, open('../bundledeps.json', 'w'), indent=1)
print('bundles saved')
