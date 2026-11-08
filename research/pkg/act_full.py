import re, json, glob, os

def names(path):
    s = open(path, encoding='utf-8').read()
    out = set()
    for n in re.findall(r"name:\s*'([^']+)'", s):
        if n.startswith('@deepseek-ai/'):
            out.add(n.split('/tools')[0].replace('@deepseek-ai/', ''))
    return out

base = names('dsh-base/package/cordis.patch.yml')
web = names('dsh-web-app/package/cordis.patch.yml')
sdk = names('dsh-sdk-app/package/cordis.patch.yml')
headless = names('dsh-headless/package/cordis.patch.yml')
acp = names('dsh-acp-app/package/cordis.patch.yml')

presets = {}
for f in glob.glob('dsh-web-app/package/presets/*.yml'):
    presets[os.path.basename(f)] = names(f)

web_active = base | web
other_profiles = (sdk | headless | acp)
profile_only = sorted((sdk | headless | acp) - web_active)
print('base', len(base), 'web', len(web), 'web_active', len(web_active))
print('sdk', len(sdk), 'headless', len(headless), 'acp', len(acp))
print('\nprofile-only packages:', len(profile_only))
for p in profile_only:
    where = [k for k, v in (('sdk', sdk), ('headless', headless), ('acp', acp)) if p in v]
    print('  ', p, where)

preset_only = set()
for k, v in presets.items():
    preset_only |= v
preset_only -= web_active
print('\npreset-only (not in web patch):', sorted(preset_only))

json.dump({'base': sorted(base), 'web': sorted(web), 'sdk': sorted(sdk), 'headless': sorted(headless),
           'acp': sorted(acp), 'profile_only': profile_only,
           'presets': {k: sorted(v) for k, v in presets.items()}},
          open('../activation_full.json', 'w'), indent=1, ensure_ascii=False)
