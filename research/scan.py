import json,urllib.request,urllib.parse,time
names={}
queries=["@deepseek-ai","@deepseek-ai/dsh","@deepseek-ai/cordis","@deepseek-ai/skill office","@deepseek-ai/libreoffice","@deepseek-ai/mcp","@deepseek-ai/plugin","@deepseek-ai/preset","@deepseek-ai/cli"]
for q in queries:
    for frm in range(0, 1250, 250):
        url=f"https://registry.npmjs.org/-/v1/search?text={urllib.parse.quote(q)}&size=250&from={frm}"
        try:
            d=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'scan'}),timeout=30))
        except Exception as e:
            print("ERR",q,frm,e); break
        objs=d.get("objects",[])
        if not objs: break
        for o in objs:
            p=o["package"]
            if p["name"].startswith("@deepseek-ai/"):
                names[p["name"]]={"version":p.get("version"),"date":p.get("date"),"desc":p.get("description",""),
                 "links":p.get("links",{}),"monthly":o.get("downloads",{}).get("monthly")}
        time.sleep(0.2)
json.dump(names,open("npm_pkgs.json","w"),ensure_ascii=False,indent=1)
print("TOTAL",len(names))
