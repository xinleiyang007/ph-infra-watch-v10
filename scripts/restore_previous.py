#!/usr/bin/env python3
"""Best-effort persistent snapshots: use last successfully published GitHub Pages data.
Works without write access to the source branch. Never overwrite larger local seeds with empty remote data.
"""
import os, json, urllib.request, urllib.parse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=('media_leads.json','document_leads.json')

def restore(base, root=ROOT):
    if not base or not base.startswith('https://'):return []
    restored=[]
    for name in FILES:
        p=Path(root)/'data'/name
        url=base.rstrip('/')+'/data/'+urllib.parse.quote(name)
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'PHInfraWatch-V10/1.0'})
            with urllib.request.urlopen(req,timeout=9) as r:
                raw=r.read(6_000_001)
            if len(raw)>6_000_000:continue
            data=json.loads(raw)
            key='leads' if name.startswith('media') else 'documents'
            if not isinstance(data,dict) or not isinstance(data.get(key),list):continue
            old_count=len(data[key]);new_count=0
            try: new_count=len(json.loads(p.read_text(encoding='utf-8')).get(key,[]))
            except Exception:pass
            if old_count>new_count:
                p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                restored.append(f'{name}: {old_count} items')
        except Exception as ex:
            print('INFO previous snapshot not restored:',name,type(ex).__name__,str(ex)[:100])
    return restored

if __name__=='__main__':
    base=os.getenv('PAGES_BASE_URL','')
    if not base:
        repo=os.getenv('GITHUB_REPOSITORY','')
        if '/' in repo:
            owner,name=repo.split('/',1)
            base=f'https://{owner.lower()}.github.io/{name}/'
    print('Previous snapshot restore:',restore(base) if base else 'no GitHub Pages URL')
