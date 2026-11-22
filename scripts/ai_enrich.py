#!/usr/bin/env python3
"""Optional Gemini API enrichment of RSS *headlines and short excerpts only*.
Configure GEMINI_API_KEY as GitHub Actions secret; never commit it or send it to browser.
Unverified candidate: the model is explicitly told not to infer project facts absent from the source.
"""
import json,os,sys,re,time
from pathlib import Path
from urllib.request import Request,urlopen
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]

def enrich(root=ROOT,request=None,limit=25):
    root=Path(root); p=root/'data/media_leads.json'
    data=json.loads(p.read_text(encoding='utf-8'))
    key=os.getenv('GEMINI_API_KEY','').strip()
    model=os.getenv('GEMINI_MODEL','gemini-2.5-flash-lite').strip()
    status={'schema_version':'ai-enrichment-10.0','generated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'mode':'gemini' if key else 'disabled_no_key','model':model if key else None,'processed':0,'errors':0,
            'notice':'Only source headline and short RSS excerpt are available; never treat AI summary as verified project evidence.'}
    if not key:
        (root/'data/ai_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('AI enrichment optional: GEMINI_API_KEY not configured; skipped safely')
        return status
    endpoint=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    request=request or _http_request
    for r in data.get('leads',[]):
        if status['processed']>=limit:break
        if r.get('ai_summary_status')=='gemini':continue
        title=r.get('title',''); excerpt=r.get('summary_excerpt','')
        if not title:continue
        prompt=("Return only a JSON object with keys title_zh, summary_zh, summary_en. "
                "Translate the supplied title into fluent Simplified Chinese while preserving company, place and numeric values. "
                "Summarize in 1-2 sentences each language using ONLY the supplied title and RSS excerpt. "
                "Do not claim to have read a full article. Do not invent investor, contractor, capacity, bidding status or location. "
                "If excerpt is missing, state only what the title supports. No Markdown.\n"
                +json.dumps({'title':title[:240],'rss_excerpt':excerpt[:500]},ensure_ascii=False))
        payload={'contents':[{'parts':[{'text':prompt}]}], 'generationConfig':{'responseMimeType':'application/json','temperature':0.1,'maxOutputTokens':360}}
        try:
            raw=request(endpoint,payload,key)
            output=raw['candidates'][0]['content']['parts'][0]['text']
            obj=json.loads(output)
            if not isinstance(obj,dict) or not obj.get('summary_zh') or not obj.get('summary_en'):raise ValueError('missing summary fields')
            for field in ('title_zh','summary_zh','summary_en'):
                value=obj.get(field)
                if isinstance(value,str) and value.strip():r[field]=value.strip()[:750]
            r['ai_summary_status']='gemini';r['ai_model']=model
            if r.get('title_zh'):r['translation_status']='machine';r['translation_engine']='Gemini'
            status['processed']+=1
        except Exception as e:
            status['errors']+=1
            print('WARN AI enrichment for one record:',type(e).__name__,str(e)[:120],file=sys.stderr)
            if status['errors']>=4:break
        time.sleep(.3)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (root/'data/ai_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('AI enrichment status:',status)
    return status

def _http_request(endpoint,payload,key):
    req=Request(endpoint,data=json.dumps(payload).encode('utf-8'),method='POST',headers={'Content-Type':'application/json','x-goog-api-key':key})
    with urlopen(req,timeout=26) as r:
        return json.load(r)
if __name__=='__main__':enrich()
