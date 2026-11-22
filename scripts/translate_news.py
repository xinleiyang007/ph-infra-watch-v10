#!/usr/bin/env python3
"""Optional no-API-key offline English-to-Chinese machine translation for RSS headlines.
Argos model is downloaded at build time; if unavailable, mark each item untranslated.
Never represent untranslated English as Chinese. Does not translate entire copyrighted articles.
"""
import argparse, json, re, time
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]

def translator_argos():
    import argostranslate.package
    import argostranslate.translate
    langs=argostranslate.translate.get_installed_languages()
    for src in langs:
        if src.code=='en':
            target=next((x for x in langs if x.code=='zh'),None)
            if target:
                try: return src.get_translation(target).translate
                except Exception: pass
    argostranslate.package.update_package_index()
    candidates=[p for p in argostranslate.package.get_available_packages() if p.from_code=='en' and p.to_code=='zh']
    if not candidates:raise RuntimeError('Argos English→Chinese package missing from package index')
    model=candidates[0].download()
    argostranslate.package.install_from_path(model)
    langs=argostranslate.translate.get_installed_languages()
    source=next(x for x in langs if x.code=='en')
    target=next(x for x in langs if x.code=='zh')
    return source.get_translation(target).translate

def apply_translation(root=ROOT, translate=None, limit=100):
    root=Path(root);p=root/'data/media_leads.json'
    data=json.loads(p.read_text(encoding='utf-8'));rows=data.get('leads',[])
    stat={'schema_version':'translation-10.0','generated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
          'engine':'argos-en-zh' if translate is None else 'test-translator','attempted':0,'translated':0,'untranslated':0,'error':'','total':len(rows)}
    if translate is None and any(not r.get('title_zh') for r in rows):
        try:translate=translator_argos()
        except Exception as e:stat['engine']='unavailable';stat['error']=str(e)[:240]
    for r in rows:
        if r.get('title_zh') and r.get('translation_status')=='machine':continue
        if stat['attempted']>=limit or translate is None:continue
        title=r.get('title','').strip();excerpt=r.get('summary_excerpt','').strip()
        if not title:continue
        try:
            if not re.search('[A-Za-z]{3}',title):continue
            zh=translate(title)
            if not zh or zh.strip().casefold()==title.casefold() or not re.search('[\u4e00-\u9fff]',zh):continue
            r['title_zh']=zh.strip()[:350]
            if excerpt:
                zsum=translate(excerpt[:350])
                if re.search('[\u4e00-\u9fff]',zsum):r['summary_zh']=zsum.strip()[:550]
            r['translation_status']='machine';r['translation_engine']='Argos Translate';stat['translated']+=1
        except Exception as e:
            r['translation_status']='untranslated';stat['error']=(str(e) or type(e).__name__)[:200]
        stat['attempted']+=1
    stat['untranslated']=sum(not r.get('title_zh') for r in rows)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (root/'data/translation_status.json').write_text(json.dumps(stat,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Translation:',stat)
    return stat

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',default=ROOT,type=Path);parser.add_argument('--limit',default=100,type=int);args=parser.parse_args();apply_translation(args.root,limit=args.limit)
