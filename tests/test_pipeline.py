import unittest,tempfile,json,sys
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collect_news import collect, categorize, extract_items
from collect_documents import extract_doc, collect as collect_docs
from translate_news import apply_translation
from link_candidates import suggest
from ai_enrich import enrich

class WorkflowTests(unittest.TestCase):
 def test_rss_dedup_and_provenance(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'config').mkdir();(root/'data').mkdir();(root/'fixtures').mkdir()
   s=[{'id':'publisher','label':'Publisher A','publisher':'A','method':'rss','feed_url':'https://a.com/rss','home':'https://a.com'},
      {'id':'index','label':'News Index','publisher':'B','method':'google_news_search','query':'Philippines solar','home':'https://b.com'}]
   (root/'config/news_sources.json').write_text(json.dumps({'sources':s,'retention_days':90,'max_records':100,'max_items_per_source':30}))
   title='Philippines solar farm 50 MW project approved'
   for so in s:
    rss=f'<rss><channel><item><title>{title}</title><link>https://{so["id"]}.example.com/story</link><description>Construction of a solar plant in Cebu</description><pubDate>Sat, 21 Nov 2026 00:00:00 GMT</pubDate></item></channel></rss>'
    (root/'fixtures'/(so['id']+'.xml')).write_text(rss)
   original='{"projects":[{"id":"approved"}]}'
   (root/'data/projects.json').write_text(original)
   collect(root,root/'fixtures',now=datetime(2026,11,22,tzinfo=timezone.utc))
   leads=json.loads((root/'data/media_leads.json').read_text())['leads']
   self.assertEqual(len(leads),1)
   self.assertEqual(len(leads[0]['coverage']),2)
   self.assertEqual(leads[0]['review_status'],'unverified_discovery')
   self.assertEqual((root/'data/projects.json').read_text(),original)
 def test_offline_translation_toggle_data(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'data').mkdir();(root/'data/media_leads.json').write_text(json.dumps({'leads':[{'title':'A new solar power plant in Cebu','summary_excerpt':'Construction of a new energy project'}]}))
   result=apply_translation(root,lambda s:'菲律宾太阳能项目',limit=10)
   data=json.loads((root/'data/media_leads.json').read_text())
   self.assertEqual(result['translated'],1)
   self.assertEqual(data['leads'][0]['translation_status'],'machine')
   self.assertIn('菲律宾',data['leads'][0]['title_zh'])
 def test_ai_no_key_does_not_invent(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'data').mkdir();(root/'data/media_leads.json').write_text('{"leads":[{"title":"Solar project announced"}]}')
   import os
   previous=os.environ.pop('GEMINI_API_KEY',None)
   try:
    status=enrich(root)
    self.assertEqual(status['mode'],'disabled_no_key')
    self.assertNotIn('summary_zh',json.loads((root/'data/media_leads.json').read_text())['leads'][0])
   finally:
    if previous is not None:os.environ['GEMINI_API_KEY']=previous
 def test_conservative_match(self):
  projects=[{'id':'1','name':'Northern Luzon Burgos Wind Farm Project'},{'id':'2','name':'Tanauan Solar Power Plant'}]
  self.assertEqual(suggest('Northern Luzon Burgos wind farm construction starts',projects),['1'])
  self.assertEqual(suggest('New renewable project in Philippines',projects),[])
 def test_document_xlsx_extraction(self):
  import openpyxl,io
  w=openpyxl.Workbook();s=w.active;s.append(['Project','Capacity']);s.append(['Cebu solar power plant', '50 MW']);buf=io.BytesIO();w.save(buf)
  rows,count=extract_doc(buf.getvalue(),'xlsx')
  self.assertEqual(len(rows),1)
  self.assertIn('Cebu',rows[0]['excerpt'])
 def test_document_pdf_extraction(self):
  import fitz
  d=fitz.open();page=d.new_page();page.insert_text((72,72),'New Philippines solar power project 100 MW with contract');rows,count=extract_doc(d.tobytes(),'pdf')
  self.assertGreaterEqual(len(rows),1)
  self.assertEqual(count,1)

if __name__=='__main__':unittest.main()
