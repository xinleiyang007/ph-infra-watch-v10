from pathlib import Path
import json, subprocess
root=Path(__file__).resolve().parents[1]
assert (root/'.github/workflows/collect-and-deploy.yml').exists()
assert (root/'config/news_sources.json').exists()
assert (root/'data/projects.json').exists()
assert (root/'assets/app.js').exists()
assert 'tile.openstreetmap.org' in (root/'assets/app.js').read_text()
assert 'GEMINI_API_KEY' not in (root/'index.html').read_text()
assert 'GEMINI_API_KEY' not in (root/'assets/app.js').read_text()
assert len(json.loads((root/'data/projects.json').read_text())['projects'])==266
assert len(json.loads((root/'config/news_sources.json').read_text())['sources'])==25
assert json.loads((root/'data/media_leads.json').read_text())['leads']==[]
print('PACKAGE CHECK OK: 266 projects, 25 configured sources, empty production news seed, no client-side Gemini secret')
