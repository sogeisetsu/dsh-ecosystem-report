import json, os, re

names = [l.strip().replace('@deepseek-ai/', '') for l in open('../names.txt') if l.strip()]
PRE = {'alpha': 1, 'beta': 2, 'rc': 3, '': 4}

def vkey(v):
    m = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-([a-z]+)\.?(\d*))?', v)
    if not m:
        return ((0, 0, 0), (0, 0))
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    pre = m.group(4) or ''
    num = int(m.group(5) or 0)
    return ((major, minor, patch), (PRE.get(pre, 0), num))

def pick(vers):
    try:
        return max([v for v in vers if not v.startswith('0.0.0')], key=vkey)
    except ValueError:
        return None

def meta(n):
    p = f'../meta/{n}.json'
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None

deps, chosen = {}, {}
for n in names:
    d = meta(n)
    if not d:
        continue
    v = pick(list(d.get('versions', {}).keys()))
    chosen[n] = v
    dd = (d['versions'][v].get('dependencies') or {}) if v else {}
    deps[n] = sorted(k.replace('@deepseek-ai/', '') for k in dd if k.startswith('@deepseek-ai/'))

roots = ['dsh', 'dsh-base', 'dsh-web-app', 'dsh-headless', 'dsh-sdk-app', 'dsh-acp-app', 'dsh-sdk-minimal']
seen, stack = set(), list(roots)
while stack:
    n = stack.pop()
    if n in seen:
        continue
    seen.add(n)
    for d in deps.get(n, []):
        if d not in seen:
            stack.append(d)

print('closure', len(seen), '| outside', len([n for n in names if n not in seen]))
json.dump({'closure': sorted(seen), 'deps': deps, 'chosen': chosen}, open('../closure.json', 'w'), indent=1)
for k in ['libreoffice-kit', 'dsh-office-to-pdf', 'node-addon-system', 'node-addon-require-builtin',
          'dsh-subagent-claude-code', 'dsh-subagent-codex', 'dsh-cua-bundle', 'dsh-computer-use']:
    print(f'{k:35s} closure={k in seen!s:5s} ver={chosen.get(k)} deps={len(deps.get(k, []))}')
