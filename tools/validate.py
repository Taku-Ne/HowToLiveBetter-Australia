"""Structural publication gate. Passing cannot establish clinical/legal correctness."""
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

def validate_data(data, upstream, expected_chapters=None):
    errors = []
    chapters = data.get('chapters', [])
    sources = data.get('sources', [])
    entries = [e for c in chapters for e in c.get('entries', [])]
    mappings = data.get('mapping', [])
    for c in chapters:
        if not isinstance(c.get('number'),int): errors.append('chapter number must be integer')
        for key in ['title','summary']:
            if not isinstance(c.get(key),str) or not c[key].strip(): errors.append(f'chapter {key} must be text')
    for e in entries:
        for key in ['id','title','jurisdiction','applies_to','action','cost','benefit','caveats','evidence_type','reviewed_on']:
            if not isinstance(e.get(key),str) or not e[key].strip(): errors.append(f'{e.get("id")}: {key} must be text')
        for key in ['steps','sources']:
            if not isinstance(e.get(key),list) or not all(isinstance(x,str) and x.strip() for x in e[key]):
                errors.append(f'{e.get("id")}: {key} must be a list of text')
    for s in sources:
        for key in ['id','title','publisher','url','accessed_on','verification','supports']:
            if not isinstance(s.get(key),str) or not s[key].strip(): errors.append(f'{s.get("id")}: {key} must be text')
    if errors: return errors
    if expected_chapters is not None and {c['number'] for c in chapters} != set(expected_chapters):
        errors.append('chapter set does not match required release chapters')
    ids = {e.get('id') for e in entries}
    source_ids = {s.get('id') for s in sources}
    for label, values in [('chapter', [c.get('number') for c in chapters]),
                           ('entry', [e.get('id') for e in entries]),
                           ('source', [s.get('id') for s in sources])]:
        errors.extend(f'duplicate {label}: {v}' for v,n in Counter(values).items() if n>1)
    for c in chapters:
        if not c.get('title') or not c.get('entries'):
            errors.append(f'empty chapter: {c.get("number")}')
        for e in c.get('entries',[]):
            if not str(e.get('id','')).startswith(f'au-{c["number"]:02d}-'):
                errors.append(f'{e.get("id")}: chapter mismatch')
    for e in entries:
        eid = e.get('id', '?')
        for field in ['id','title','jurisdiction','applies_to','action','steps','cost','benefit',
                      'caveats','evidence_type','sources','reviewed_on']:
            if not e.get(field): errors.append(f'{eid}: missing {field}')
        for sid in e.get('sources',[]):
            if sid not in source_ids: errors.append(f'{eid}: unknown source {sid}')
        for field in ['steps','sources']:
            if not isinstance(e.get(field), list): errors.append(f'{eid}: {field} must be list')
        if not re.fullmatch(r'au-\d{2}-\d{2}',eid): errors.append(f'invalid entry id: {eid}')
    for s in sources:
        for field in ['id','title','publisher','url','accessed_on','verification','supports']:
            if not s.get(field): errors.append(f'{s.get("id")}: missing {field}')
        u = urlparse(s.get('url',''))
        if u.scheme not in ('http','https') or not u.netloc:
            errors.append(f'{s.get("id")}: unsafe URL')
        if s.get('verification') not in ('full_page','abstract','pdf'):
            errors.append(f'{s.get("id")}: invalid verification scope')
    for obj,key in [(e,'reviewed_on') for e in entries]+[(s,'accessed_on') for s in sources]:
        try: date.fromisoformat(obj.get(key,''))
        except (ValueError,TypeError): errors.append(f'{obj.get("id")}: invalid {key}')
    expected = {(int(x['chapter']),int(x['item'])) for x in upstream}
    seen = Counter((int(m['original_chapter']),int(m['original_item'])) for m in mappings)
    for key in sorted(expected-set(seen)): errors.append(f'missing mapping {key[0]}:{key[1]}')
    for key,n in seen.items():
        if n>1: errors.append(f'duplicate mapping {key[0]}:{key[1]}')
        if key not in expected: errors.append(f'unknown original item {key[0]}:{key[1]}')
    for m in mappings:
        label = f'{m["original_chapter"]}:{m["original_item"]}'
        if m.get('action') not in ('adapt','reuse','merge','omit'):
            errors.append(f'{label}: invalid action')
        if not m.get('reason'): errors.append(f'{label}: missing reason')
        if m.get('action') != 'omit' and not m.get('target_ids'):
            errors.append(f'{label}: missing mapping target')
        for target in m.get('target_ids',[]):
            if target not in ids: errors.append(f'{label}: missing target {target}')
    return errors

def main():
    data=json.loads((ROOT/'sources/guide.json').read_text(encoding='utf-8-sig'))
    upstream=json.loads((ROOT/'sources/upstream.json').read_text(encoding='utf-8-sig'))['items']
    errors=validate_data(data,upstream,expected_chapters=range(1,33))
    for path in list((ROOT/'book').glob('*.md'))+list((ROOT/'docs').glob('*.md'))+[ROOT/'README.md']:
        if not path.exists():
            errors.append(f'missing output {path.name}'); continue
        for url in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if url.startswith(('https://','http://','#','mailto:')): continue
            dest=url.split('#')[0]
            if dest and not (path.parent/dest).exists(): errors.append(f'{path.name}: broken local link {url}')
    if errors:
        print('\n'.join(errors)); return 1
    print(f'PASS: {len(data["chapters"])} chapters; {sum(len(c["entries"]) for c in data["chapters"])} entries; '
          f'{len(data["sources"])} source records; {len(upstream)} original items mapped. '
          'This is a structural check, not a claim of professional review.')
    return 0

if __name__=='__main__': sys.exit(main())
