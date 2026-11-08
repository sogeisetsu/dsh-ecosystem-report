import re, glob, json

def names(f):
    s = open(f, encoding='utf-8').read()
    return re.findall(r"name:\s*'([^']+)'", s)

def pkgs(l):
    out = set()
    for n in l:
        if n.startswith('@deepseek-ai/'):
            base = n.split('/tools')[0]
            out.add(base.replace('@deepseek-ai/', ''))
    return sorted(out)

base = pkgs(names('dsh-base/package/cordis.patch.yml'))
web = pkgs(names('dsh-web-app/package/cordis.patch.yml'))
print('BASE', len(base))
print(', '.join(base))
print()
print('WEB-ONLY', len([x for x in web if x not in base]))
print(', '.join([x for x in web if x not in base]))
print()
for f in sorted(glob.glob('dsh-web-app/package/presets/*.yml')):
    p = pkgs(names(f))
    print('PRESET', f.split('/')[-1].split('\\')[-1], len(p))
    print(', '.join(p))
    print()

json.dump({'base': base, 'web': web,
           'presets': {f.split('/')[-1].split('\\')[-1]: pkgs(names(f)) for f in sorted(glob.glob('dsh-web-app/package/presets/*.yml'))}},
          open('../activation.json', 'w'), indent=1)
