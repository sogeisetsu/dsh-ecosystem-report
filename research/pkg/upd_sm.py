import json
import re

s = open('sm/package/cordis.patch.yml', encoding='utf-8').read()
names = re.findall(r"name:\s*'([^']+)'", s)
pkgs = sorted({n.split('/tools')[0].replace('@deepseek-ai/', '') for n in names if n.startswith('@deepseek-ai/')})
print('pkgs', len(pkgs))

p = '../activation_full.json'
a = json.load(open(p))
add = set(pkgs) - set(a['base']) - set(a['web'])
before = set(a['profile_only'])
a['profile_only'] = sorted(before | add)
json.dump(a, open(p, 'w'), ensure_ascii=False, indent=1)
print('added', sorted(add - before))
print('profile_only', len(a['profile_only']))
