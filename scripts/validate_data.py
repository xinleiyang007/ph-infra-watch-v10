"""Fail deploy if required data schema or frontend files are corrupted."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def run(root=ROOT):
    root=Path(root)
    for filename,key in [('projects.json','projects'),('companies.json','companies'),('media_leads.json','leads'),('media_status.json','sources'),('translation_status.json',None)]:
        content=json.loads((root/'data'/filename).read_text(encoding='utf-8'))
        if key and (key not in content or not isinstance(content[key],list)):raise ValueError(f'Invalid {filename}: {key}')
    projects=json.loads((root/'data/projects.json').read_text(encoding='utf8'))['projects']
    if len({p['id'] for p in projects})!=len(projects):raise ValueError('Duplicate project IDs')
    for name in ['index.html','assets/app.js','assets/style.css']:
        if (root/name).stat().st_size<1000:raise ValueError('Missing or empty '+name)
    print('V10 deployment data validated:',len(projects),'projects')
if __name__=='__main__':run()
