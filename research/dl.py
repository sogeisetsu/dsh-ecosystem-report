import json,urllib.request,time
pk=json.load(open("npm_pkgs.json"))
out={}
for i,(n,meta) in enumerate(sorted(pk.items())):
    for period in ["last-month","last-week"]:
        try:
            u=f"https://api.npmjs.org/downloads/point/{period}/{n}"
            d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'x'}),timeout=20))
            out.setdefault(n,{})[period]=d.get("downloads")
        except Exception as e:
            out.setdefault(n,{})[period]=None
json.dump(out,open("downloads.json","w"),indent=1)
print("done",len(out))
