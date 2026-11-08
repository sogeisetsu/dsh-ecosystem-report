import json, re, glob

pk = json.load(open('../npm_pkgs.json'))
have = {k.replace('@deepseek-ai/', '') for k in pk}
act = json.load(open('../activation.json'))

refs = set()
refs |= set(act['base']) | set(act['web'])
for v in act['presets'].values():
    refs |= set(v)

# dsh dependency closure (direct)
deps = json.load(open('../dsh_meta.json'))
latest = deps['0.2.2-rc.1']['deps']
refs |= {k.replace('@deepseek-ai/', '') for k in latest}

# optional / on-demand / retired / protected lists from official-bundles
s = open('package/lib/index.js', encoding='utf-8').read()
extra = set()
for m in re.findall(r"'@deepseek-ai/([a-z0-9-]+)'", s):
    extra.add(m)
refs |= extra

missing = sorted(r for r in refs if r not in have and not r.startswith('dsh-web-app'))
print('referenced-but-unscanned:', len(missing))
print(', '.join(missing))
print()
print('total scanned', len(pk))
