import json, urllib.request, os
from concurrent.futures import ThreadPoolExecutor

names = [l.strip() for l in open('../names.txt') if l.strip()]
os.makedirs('../meta', exist_ok=True)

def fetch(n):
    short = n.replace('@deepseek-ai/', '')
    path = f'../meta/{short}.json'
    if os.path.exists(path) and os.path.getsize(path) > 200:
        return short, 'cached'
    u = f'https://registry.npmjs.org/@deepseek-ai%2F{short}'
    for _ in range(3):
        try:
            req = urllib.request.Request(u, headers={'Accept': 'application/vnd.npm.install-v1+json',
                                                     'User-Agent': 'dsh-survey'})
            data = urllib.request.urlopen(req, timeout=25).read()
            if len(data) > 100:
                open(path, 'wb').write(data)
                return short, 'ok'
        except Exception as e:
            err = str(e)[:40]
    return short, 'fail'

with ThreadPoolExecutor(max_workers=8) as ex:
    res = list(ex.map(fetch, names))
from collections import Counter
print(Counter(r[1] for r in res))
print('fails:', [r[0] for r in res if r[1] == 'fail'][:20])
