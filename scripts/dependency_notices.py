"""Record actual installed dependency metadata without inventing licenses."""
from pathlib import Path
from importlib import metadata
import json,sys

root=Path(__file__).resolve().parents[1]
records=[]
for line in (root/'requirements.lock.txt').read_text().splitlines():
    if '==' not in line:continue
    name,version=line.split('==',1);dist=metadata.distribution(name);m=dist.metadata
    assert dist.version==version,(name,version,dist.version)
    license=m.get('License-Expression') or m.get('License') or '; '.join(c for c in m.get_all('Classifier',[]) if c.startswith('License ::'))
    if not license:license='Not declared in installed metadata; inspect upstream terms.'
    if len(license)>180:license='License text present in installed metadata; inspect upstream distribution.'
    license=' '.join(license.split())
    records.append({'package':name,'version':version,'declared_license':license,
                    'project_urls':m.get_all('Project-URL',[]) or ([m['Home-page']] if m.get('Home-page') else [])})
out=root/'results'/'submission';out.mkdir(parents=True,exist_ok=True)
(out/'dependency_notices.json').write_text(json.dumps(records,indent=2),encoding='utf-8',newline='\n')
lines=['# Third-party dependency notices','',
 'Inventory from the verified clean environment and locked packages. This records metadata supplied by dependencies; it does not relicense them or the supplied dataset. Installed dependency source/binaries are not bundled in the public source snapshot. Consult each upstream distribution for its complete applicable terms.','',
 '| Package | Locked version | License metadata |','|---|---|---|']
for r in records:lines.append(f'| {r["package"]} | {r["version"]} | {r["declared_license"].replace("|","/")} |')
lines+=['','Team-authored source license: not specified. No source or dataset license has been invented. See `docs/LICENSING_AND_DATA.md`.','']
(root/'THIRD_PARTY_NOTICES.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
print(f'Recorded installed metadata for {len(records)} locked packages.')
