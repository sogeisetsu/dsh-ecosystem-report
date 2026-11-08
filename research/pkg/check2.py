import json, urllib.request

rows = {x['name']: x['status'] for x in json.load(open('../rows.json'))}
for n in ['dsh-fs-local', 'dsh-terminal', 'dsh-terminal-bash',
          'dsh-tool-bash-persistent', 'dsh-tool-pwsh-persistent']:
    print(n, rows.get(n))

d = json.load(urllib.request.urlopen(urllib.request.Request(
    'https://registry.npmjs.org/dsh-at-file', headers={'User-Agent': 'v'}), timeout=25))
lv = d['dist-tags']['latest']
v = d['versions'][lv]
print('homepage', v.get('homepage'))
print('repo', v.get('repository'))
readme = (d.get('readme') or '')
print('readme head', readme[:400].replace('\n', ' '))
