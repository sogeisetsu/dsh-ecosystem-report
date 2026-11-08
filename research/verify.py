import json,urllib.request,urllib.parse

names = ["dsh-composer-enhance","dsh-composer-enhancer","dsh-agent-enhancer","dsh-context",
"dsh-better-sidebar","DSH-better-sidebar","dsh-at-file","dsh-market","dshmarket",
"simple-email-mcp","dsh-univer-office","dsh-excel-chat","dsh-web-search-free",
"dsh-mcp-lazy","@sutong12/dsh-mcp-lazy","dsh-llm-opencode-go","dsh-opencode-go-pool",
"dsh-harness-pilot","dsh-agent-preset-router","dsh-mcp-skill-manager",
"@deepseek-ai/dsh-skill","@deepseek-ai/dsh-skill-office"]

def get(u):
    req=urllib.request.Request(u,headers={'User-Agent':'verify','Accept':'application/json'})
    return json.load(urllib.request.urlopen(req,timeout=25))

out=[]
for n in names:
    enc=urllib.parse.quote(n,safe='')
    try:
        d=get(f"https://registry.npmjs.org/{enc}")
    except Exception as e:
        out.append((n,"ERR "+str(e)[:40],"","",""))
        continue
    if 'error' in d:
        out.append((n,"NOT FOUND","","",""))
        continue
    lv=d.get('dist-tags',{}).get('latest','?')
    t=d.get('time',{}).get(lv,'')[:10]
    v=d['versions'][lv]
    repo=v.get('repository')
    if isinstance(repo,dict): repo=repo.get('url','')
    out.append((n,lv,t,(v.get('description') or '')[:70],repo or ''))
for r in out:
    print(" | ".join(r))
json.dump(out,open("verify_out.json","w"),ensure_ascii=False,indent=1)
