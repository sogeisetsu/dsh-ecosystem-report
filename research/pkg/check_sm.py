import json, re

s = open('sm/package/cordis.patch.yml', encoding='utf-8').read()
names = re.findall(r"name:\s*'([^']+)'", s)
pkgs = {n.split('/tools')[0].replace('@deepseek-ai/', '') for n in names if n.startswith('@deepseek-ai/')}
print('rows', len(names), 'pkgs', len(pkgs))
a = json.load(open('../activation_full.json'))
base, web, prof = set(a['base']), set(a['web']), set(a['profile_only'])
new = sorted(pkgs - base - web)
print('not in base/web:', len(new), new)
print('new beyond profile_only:', sorted(set(new) - prof))
print('all names sample:', sorted(pkgs)[:8])
