#!/usr/bin/env python3
"""PH Infra Watch V10: collect short, attributed media project leads from public RSS.
No article-body scraping, no automated promotion into projects.json, no paid API.
Run `python scripts/collect_news_v9.py`; optional --fixtures DIR for offline tests.
"""
from __future__ import annotations
import argparse, hashlib, html, json, re, sys, time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode, urlparse, urlsplit, urlunsplit, parse_qsl
from urllib.request import Request, urlopen
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
UTC=timezone.utc
ATOM='{http://www.w3.org/2005/Atom}'
DC='{http://purl.org/dc/elements/1.1/}'

def iso_date(s):
    if not s:return ''
    try: d=parsedate_to_datetime(s)
    except (TypeError,ValueError,OverflowError):
        try:d=datetime.fromisoformat(s.strip().replace('Z','+00:00'))
        except (ValueError,TypeError):return ''
    if d.tzinfo is None:d=d.replace(tzinfo=UTC)
    return d.astimezone(UTC).isoformat(timespec='seconds')

class TextOnly(HTMLParser):
    def __init__(self):super().__init__();self.items=[]
    def handle_data(self,t):self.items.append(t)

def clean_text(raw):
    parser=TextOnly()
    try:parser.feed(html.unescape(raw or ''))
    except Exception:return ''
    return re.sub(r'\s+',' ',' '.join(parser.items)).strip()

def read_json(path,default):
    try:return json.loads(Path(path).read_text('utf-8'))
    except (OSError,ValueError):return default

def txt(parent,*tags):
    for tag in tags:
        n=parent.find(tag)
        if n is not None and n.text and n.text.strip():return n.text.strip()
    return ''

def extract_items(body):
    root=ET.fromstring(body)
    atom=root.tag.endswith('feed')
    for item in root.findall(ATOM+'entry') if atom else root.findall('.//item'):
        title=clean_text(txt(item, ATOM+'title' if atom else 'title'))
        link=''
        if atom:
            for node in item.findall(ATOM+'link'):
                if node.get('rel','alternate')=='alternate' and node.get('href'):link=node.get('href');break
        else:link=txt(item,'link')
        snippet=clean_text(txt(item,ATOM+'summary',ATOM+'content') if atom else txt(item,'description'))[:250]
        date=iso_date(txt(item,ATOM+'published',ATOM+'updated') if atom else txt(item,'pubDate',DC+'date'))
        origin=txt(item,'source')
        if title and link.startswith(('https://','http://')):
            yield {'title':title[:240],'url':link.strip(),'summary_excerpt':snippet,'published_at':date,'rss_publisher':origin}

# High precision: informative engineering/energy/ICT terms plus a project/action signal.
TOPICS={
 'wind':r'\bwind farm\b|\boffshore wind\b|\bwind power\b|\bwind turbine',
 'solar_ground':r'\bsolar (farm|plant|park|project|power)\b|\bphotovoltaic\b|\bPV farm\b',
 'solar_rooftop':r'\brooftop solar\b|\broof.?mounted solar\b',
 'storage':r'\bBESS\b|\bbattery energy storage\b|\bgrid battery\b',
 'ev_charging':r'\bEV charg(?:ing|er)\b|\bcharging station\b|\bcharging network\b',
 'datacenter':r'\bdata cent(?:er|re)\b|\bserver farm\b|\bhyperscale\b|\bdigital infrastructure\b',
 'elv_fiber':r'\bstructured cabling\b|\bfiber[- ]optic\b|\bfibre[- ]optic\b|\bbroadband\b|\btelecom tower\b|\bELV\b|\bCCTV\b|\bICT infrastructure\b',
 'power_other':r'\bpower (plant|project|grid|substation|transmission|facility)\b|\brenewable energy\b|\bsolar energy\b'
}
ACTION=re.compile(r'\b(project|facility|builds?|construct(?:ion|s|ed)?|commission(?:ed|ing)?|develop(?:ment|s|ed)?|invest(?:ment|s|ed)?|fund(?:ing|s|ed)?|agreement|approv(?:al|es|ed)|awards?|contract(?:or|s|ed)?|procure(?:ment)?|bid(?:ding|s)?|tender|launch(?:es|ed)?|inaugurat(?:ion|e|ed)|expand(?:s|ed|sion)?|install(?:s|ed|ation)?|upgrad(?:e|es|ed)|deploy(?:ment|s|ed)?|break(?:s|ing)? ground|energiz(?:e|ed|ation)|grid connect|permit|PPP|MW|MWh|GW|GWh|kilovolt|substation|EPC|fiber[- ]optic|broadband|cabling|datacenter)\b',re.I)
PH_LOC=re.compile(r'\b(Philippines|Philippine|Luzon|Visayas|Mindanao|Manila|Cebu|Davao|Palawan|Pampanga|Laguna|Batangas|Tarlac|Bulacan|Cavite|Negros|Iloilo|Clark|Bataan|Quezon|Pangasinan|Isabela|Ilocos|Nueva Ecija|Leyte|Bohol|Rizal|Taguig|Pasig|Makati)\b',re.I)
FOREIGN=re.compile(r'\b(United States|California|Texas|India|Australia|Japan|Indonesia|Malaysia|Vietnam|Thailand|Singapore|China|UK|Europe|Africa)\b',re.I)
REGIONS=['Metro Manila','Ilocos Norte','Ilocos Sur','Pangasinan','Nueva Ecija','Tarlac','Bulacan','Cavite','Laguna','Batangas','Quezon','Isabela','Cagayan','Pampanga','Bataan','Palawan','Iloilo','Cebu','Negros','Bohol','Leyte','Davao','Mindanao','Clark']

def categorize(text):
    cats=[k for k,rx in TOPICS.items() if re.search(rx,text,re.I)]
    if 'solar_rooftop' in cats and 'solar_ground' in cats:cats.remove('solar_ground')
    return cats

def priority(text):
    if re.search(r'\b(tender|bidding|procurement|bid invitation|requests? for proposals?|RFP|RFQ|awarded? contract|contract award)\b',text,re.I):return 3
    if re.search(r'\b(construction|groundbreaking|builds?|financing|investment|EPC|commissioning|substation)\b',text,re.I):return 2
    return 1

def normalize_title(s):return re.sub(r'[^a-z0-9\u4e00-\u9fff]+','',s.casefold())

def canonical_url(u):
    p=urlsplit(u.strip())
    qs=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=False) if not k.startswith('utm_') and k not in ('fbclid','gclid','ref','source')]
    q=urlencode(qs)
    return urlunsplit((p.scheme.lower(),p.netloc.lower().removeprefix('www.'),p.path.rstrip('/'),q,''))

def feed_address(source):
    if source['method']=='rss':return source['feed_url']
    if source['method']=='google_news_search':return 'https://news.google.com/rss/search?'+urlencode({'q':source['query'],'hl':'en-PH','gl':'PH','ceid':'PH:en'})
    raise ValueError('Unsupported feed mode: '+source['method'])

def fetch(source):
    url=feed_address(source)
    req=Request(url,headers={'User-Agent':'PHInfraWatch/10.0 (public headline RSS monitoring; contact via GitHub repo)','Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.8,*/*;q=0.5'})
    with urlopen(req,timeout=13) as r:body=r.read(2_000_001)
    if len(body)>2_000_000:raise ValueError('feed larger than 2MB limit')
    return body

def collect(root=ROOT,fixtures=None,now=None,dry_run=False):
    now=now or datetime.now(UTC)
    root=Path(root)
    cfg=read_json(root/'config/news_sources.json',{})
    if not cfg.get('sources'):raise ValueError('Missing config/news_sources.json sources[]')
    existing=read_json(root/'data/media_leads.json',{})
    cache={r['id']:r for r in existing.get('leads',[]) if isinstance(r,dict) and r.get('id')}
    stamp=now.isoformat(timespec='seconds')
    cutoff=now-timedelta(days=int(cfg.get('retention_days',120)))
    results=[];seen=set();stats=[];new_count=0
    for source in cfg['sources']:
        start=time.monotonic()
        stat={'id':source['id'],'label':source['label'],'publisher':source.get('publisher',''), 'group':source.get('group','media'), 'method':source['method'],'state':'error','checked_at':stamp,'fetched':0,'relevant':0,'added':0,'error':'','home':source.get('home','')}
        try:
            if fixtures is not None:
                body=(Path(fixtures)/(source['id']+'.xml')).read_bytes()
            else:body=fetch(source)
            rows=list(extract_items(body))[:int(cfg.get('max_items_per_source',45))]
            stat['fetched']=len(rows)
            published_dates=[iso_date(r.get('published_at')) for r in rows]
            published_dates=[d for d in published_dates if d]
            stat['latest_article_published_at']=max(published_dates) if published_dates else ''
            for r in rows:
                blob=r['title']+' '+r['summary_excerpt']
                categories=categorize(blob)
                if not categories or not ACTION.search(blob):continue
                if FOREIGN.search(blob) and not PH_LOC.search(blob):continue
                pub_date=iso_date(r['published_at'])
                if pub_date:
                    try:
                        d=datetime.fromisoformat(pub_date)
                        if d < cutoff or d > now+timedelta(days=2):continue
                    except ValueError:pass
                stat['relevant']+=1
                titlekey=normalize_title(r['title'])
                uri=canonical_url(r['url'])
                # Same article discovered via direct RSS and index: merge by exact normalized title.
                id_=hashlib.sha256(titlekey.encode()).hexdigest()[:20]
                p=priority(blob)
                regions=[x for x in REGIONS if x.lower() in blob.lower()][:3]
                if id_ not in cache:
                    cache[id_]={'id':id_,'title':r['title'],'url':r['url'],'publisher':source['publisher'],'source_label':source['label'],
                                 'source_method':source['method'],'source_group':source.get('group','media'),
                                 'published_at':pub_date,'first_seen_at':stamp,'summary_excerpt':r['summary_excerpt'],
                                 'categories':categories,'priority':p,'location_hints':regions,'review_status':'unverified_discovery',
                                 'coverage':[{'source_id':source['id'],'publisher':source['publisher'],'method':source['method'],'url':r['url']}],
                                 'url_is_index':('news.google.com' in urlsplit(r['url']).netloc),
                                 'location_check':'location_hint' if PH_LOC.search(blob) else 'requires_review'}
                    new_count+=1;stat['added']+=1
                else:
                    record=cache[id_]
                    record['priority']=max(int(record.get('priority',1)),p)
                    record['categories']=list(dict.fromkeys(record.get('categories',[])+categories))
                    record.setdefault('coverage',[])
                    if not any(c['source_id']==source['id'] for c in record['coverage']):
                        record['coverage'].append({'source_id':source['id'],'publisher':source['publisher'],'method':source['method'],'url':r['url']})
                    if source['method']=='rss' and record.get('url_is_index'):
                        record.update(url=r['url'],url_is_index=False,source_method='rss',publisher=source['publisher'])
                    if not record.get('published_at') and pub_date:record['published_at']=pub_date
            stat['state']='ok'
        except Exception as exc:
            stat['error']=(str(exc) or exc.__class__.__name__)[:180]
        stat['elapsed_ms']=int((time.monotonic()-start)*1000)
        stats.append(stat)
        print(f"{stat['state']:5} {source['id']:23} found={stat['fetched']:3} relevant={stat['relevant']:3} +{stat['added']:3} {stat['error']}")
    leads=[]
    for x in cache.values():
        d=iso_date(x.get('published_at') or x.get('first_seen_at'))
        if d:
            try:
                if datetime.fromisoformat(d)<cutoff:continue
            except ValueError:pass
        leads.append(x)
    leads.sort(key=lambda r:r.get('published_at') or r.get('first_seen_at') or '',reverse=True)
    leads=leads[:int(cfg.get('max_records',1800))]
    ok=sum(s['state']=='ok' for s in stats)
    result={'schema_version':'media-leads-10.0','generated_at':stamp,'data_notice':'Automated article-discovery candidates only. Not confirmed projects, contracts, investors or contractors. Short headline/excerpt with links; direct RSS and third-party news index identified separately.', 'leads':leads}
    status={'schema_version':'media-status-10.0','generated_at':stamp,'successful_sources':ok,'configured_sources':len(stats),'new_records':new_count,'stored_records':len(leads),'sources':stats,
            'history_notice':'每次采集前从上一成功发布的 Pages JSON 恢复历史（若访问可用）；不自动向 main 提交，不保证完整历史。建议定期下载归档。'}
    if not dry_run:
        (root/'data').mkdir(parents=True,exist_ok=True)
        (root/'data/media_leads.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
        (root/'data/media_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(f'Complete: {ok}/{len(stats)} sources responded; {len(leads)} matching leads; +{new_count} new; no changes to projects.json')
    return 0 # offline and partial failures should not prevent release; status reports errors

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--fixtures',type=Path);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    return collect(a.root,a.fixtures,dry_run=a.dry_run)
if __name__=='__main__':sys.exit(main())
