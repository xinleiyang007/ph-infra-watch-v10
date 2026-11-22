#!/usr/bin/env python3
"""Extract document evidence from public PDF and XLSX files into audited document metadata.
DOES NOT modify projects.json; cannot infer contract awards or EPC from uncontrolled text.
"""
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from io import BytesIO
import json,re,hashlib,os,argparse,time
ROOT=Path(__file__).resolve().parents[1]
MATCH=re.compile(r'\b(solar|wind|storage|battery|BESS|power|photovoltaic|data center|broadband|fiber|fibre|ICT|ELV|tender|contract|substation|charging)\b',re.I)

def extract_doc(raw,fmt,max_snippets=35):
    fragments=[]
    if fmt=='pdf':
        try:import fitz
        except ImportError:raise RuntimeError('PyMuPDF package required')
        d=fitz.open(stream=raw,filetype='pdf')
        for i in range(min(len(d),8)):
            text=d[i].get_text('text')
            lines=[re.sub(r'\s+',' ',s).strip() for s in text.splitlines()]
            for line in lines:
                if 14 <= len(line)<=320 and MATCH.search(line):fragments.append({'page':i+1,'excerpt':line[:240]})
                if len(fragments)>=max_snippets:break
            if len(fragments)>=max_snippets:break
        return fragments,len(d)
    if fmt in ('xlsx','xlsm'):
        try:import openpyxl
        except ImportError:raise RuntimeError('openpyxl package required')
        w=openpyxl.load_workbook(BytesIO(raw),read_only=True,data_only=True)
        rows=0
        for s in w.worksheets[:4]:
            for row in s.iter_rows(min_row=1,max_row=400,values_only=True):
                rows+=1
                text=' | '.join(str(x) for x in row if x is not None)[:380]
                if len(text)>=10 and MATCH.search(text):fragments.append({'sheet':s.title,'row':rows,'excerpt':text[:240]})
                if len(fragments)>=max_snippets:break
            if len(fragments)>=max_snippets:break
        return fragments,rows
    raise ValueError(f'Unsupported public document extension: {fmt}')

def collect(root=ROOT,fixtures=None):
    root=Path(root);cfg=json.loads((root/'config/document_sources.json').read_text(encoding='utf-8'))
    now=datetime.now(timezone.utc).isoformat(timespec='seconds');docs=[];statuses=[]
    for source in cfg['sources']:
        if not source.get('enabled',True):continue
        record={'id':source['id'],'label':source['label'],'source_url':source['url'],'publisher':source.get('publisher',''),'format':source['format'], 'checked_at':now,'state':'error','error':'','matched_lines':0}
        try:
            if fixtures:
                ext=source['format']; raw=(Path(fixtures)/(source['id']+'.'+ext)).read_bytes()
            else:
                req=Request(source['url'],headers={'User-Agent':'PHInfraWatch/10.0 (public document metadata monitoring)','Accept':'application/pdf,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*;q=0.3'})
                with urlopen(req,timeout=20) as r: raw=r.read(12_000_001)
            if len(raw)>12_000_000:raise ValueError('Document exceeds 12MB limit')
            fragments,num=extract_doc(raw,source['format'])
            record.update(state='ok',matched_lines=len(fragments),size_bytes=len(raw),pages_or_rows=num)
            docs.append({'id':source['id'],'label':source['label'],'publisher':source.get('publisher',''),'url':source['url'],'format':source['format'], 'checked_at':now,'document_excerpts':fragments[:35], 'notice':'Quoted snippets are *unverified document extracts*, not confirmed new projects. Open source document to verify.'})
        except Exception as exc:record['error']=(str(exc) or type(exc).__name__)[:220]
        statuses.append(record)
        print(record['id'],record['state'],'lines',record['matched_lines'],record['error'])
    (root/'data/document_leads.json').write_text(json.dumps({'schema_version':'document-leads-10.0','generated_at':now,'documents':docs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (root/'data/document_status.json').write_text(json.dumps({'schema_version':'document-status-10.0','generated_at':now,'sources':statuses},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return docs,statuses
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--fixtures',type=Path);args=p.parse_args();collect(args.root,args.fixtures)
