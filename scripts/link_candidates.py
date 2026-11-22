#!/usr/bin/env python3
"""Conservative project suggestion matching, never auto-edit approved project records.
Only strong descriptive name overlap is enough to suggest links. Otherwise unlinked.
"""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STOP=set('the project power solar wind energy philippines philippine and inc corp corporation company development city farm plant facility infrastructure station proposed new phase renewable data center'.split())
def words(s):return set(w for w in re.findall('[a-z0-9]+',str(s).lower()) if len(w)>3 and w not in STOP)
def suggest(headline,projects,limit=3):
    title=words(headline)
    hits=[]
    for p in projects:
        name=words(p.get('name',''))
        overlap=title & name
        if len(overlap)>=2 and len(overlap)/max(1,len(name))>=0.55:
            hits.append((len(overlap)/len(name),p['id']))
    hits.sort(reverse=True)
    return [pid for _,pid in hits[:limit]]
def run(root=ROOT):
    root=Path(root); news=root/'data/media_leads.json'
    d=json.loads(news.read_text(encoding='utf8'));projects=json.loads((root/'data/projects.json').read_text(encoding='utf8'))['projects']
    count=0
    for r in d.get('leads',[]):
        suggested=suggest(r.get('title','')+' '+r.get('summary_excerpt',''),projects)
        r['candidate_project_ids']=suggested
        r['project_link_status']='suggestion_unverified' if suggested else 'not_matched'
        count+=bool(suggested)
    news.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(f'Conservative suggestions: {count} leads with one or more *unverified* project candidates')
if __name__=='__main__':run()
