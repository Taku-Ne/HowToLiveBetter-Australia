"""Publication gates for a one-to-one Markdown adaptation; not professional review."""
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
GRADES = ('A', 'B', 'C', '规则')
SCOPES = ('full_page', 'abstract', 'pdf', 'upstream_citation')
FIELDS = ('成本', '说人话', '收益', '证据等级', '来源', '备注')

def chapter_path(chapter, upstream):
    return next(x['path'] for x in upstream if x['chapter'] == chapter['number'])

def validate_data(data, upstream, expected_chapters=None):
    errors=[]
    chapters=data.get('chapters',[])
    appendices=data.get('appendices',[])
    sources=data.get('sources',[])
    entries=[e for c in chapters+appendices for e in c.get('entries',[])]
    mapping=data.get('mapping',[])
    for c in chapters+appendices:
        if not isinstance(c.get('number'),int): errors.append('chapter number must be integer')
        for key in ('title','summary'):
            if not isinstance(c.get(key),str) or not c[key].strip(): errors.append(f'chapter {key} must be text')
    for e in entries:
        for key in ('id','title','jurisdiction','applies_to','action','cost','benefit','caveats','evidence_type','reviewed_on','evidence_grade'):
            if not isinstance(e.get(key),str) or not e[key].strip(): errors.append(f'{e.get("id")}: {key} must be text')
        if not isinstance(e.get('references'),str): errors.append(f'{e.get("id")}: references must be text')
        for key in ('steps','sources'):
            if not isinstance(e.get(key),list) or not all(isinstance(x,str) and x.strip() for x in e[key]): errors.append(f'{e.get("id")}: {key} must be a list of text')
        if not e.get('sources'): errors.append(f'{e.get("id")}: missing sources')
    for s in sources:
        for key in ('id','title','publisher','url','accessed_on','verification','supports'):
            if not isinstance(s.get(key),str) or not s[key].strip(): errors.append(f'{s.get("id")}: {key} must be text')
    for m in mapping:
        if not all(isinstance(m.get(k),int) for k in ('original_chapter','original_item')): errors.append('mapping coordinates must be integers')
        if not isinstance(m.get('target_ids'),list) or not all(isinstance(x,str) for x in m['target_ids']): errors.append('mapping targets must be a list of text')
    if errors: return errors
    numbers=[c['number'] for c in chapters]
    if expected_chapters is not None and numbers != list(expected_chapters): errors.append('chapter set or order does not match required release chapters')
    for label,values in [('chapter',[c['number'] for c in chapters+appendices]),('entry',[e['id'] for e in entries]),('source',[s['id'] for s in sources])]:
        errors.extend(f'duplicate {label}: {v}' for v,n in Counter(values).items() if n>1)
    source_ids={s['id'] for s in sources}
    ids={e['id'] for e in entries}
    expected={(x['chapter'],x['item']) for x in upstream}
    actual=[]
    for c in chapters:
        wanted=[f'au-{n:02d}-{i:02d}' for n,i in sorted(expected) if n==c['number']]
        if [e['id'] for e in c['entries']] != wanted: errors.append(f'chapter {c["number"]}: entry count or order differs from original')
        for i,e in enumerate(c['entries'],1):
            actual.append((c['number'],i))
            oid=f'O{c["number"]:02d}{i:02d}'
            if oid not in e['sources']: errors.append(f'{e["id"]}: missing original provenance {oid}')
    if set(actual) != expected: errors.append('original positions differ from chapter entries')
    for c in chapters+appendices:
        for e in c['entries']:
            if not e['id'].startswith(f'au-{c["number"]:02d}-'): errors.append(f'{e["id"]}: chapter mismatch')
    for e in entries:
        eid=e['id']
        if not re.fullmatch(r'au-\d{2}-\d{2}',eid): errors.append(f'invalid entry id: {eid}')
        if e['evidence_grade'] not in GRADES: errors.append(f'{eid}: invalid evidence grade')
        for sid in e['sources']:
            if sid not in source_ids: errors.append(f'{eid}: unknown source {sid}')
    for s in sources:
        u=urlparse(s['url'])
        if u.scheme not in ('http','https') or not u.netloc: errors.append(f'{s["id"]}: unsafe URL')
        if s['verification'] not in SCOPES: errors.append(f'{s["id"]}: invalid verification scope')
        if re.fullmatch(r'O\d{4}',s['id']) and s['verification']!='upstream_citation': errors.append(f'{s["id"]}: original-mediated citation cannot claim independent verification')
    for obj,key in [(e,'reviewed_on') for e in entries]+[(s,'accessed_on') for s in sources]:
        try: date.fromisoformat(obj[key])
        except (ValueError,TypeError): errors.append(f'{obj["id"]}: invalid {key}')
    seen=Counter((m['original_chapter'],m['original_item']) for m in mapping)
    for key in sorted(expected-set(seen)): errors.append(f'missing mapping {key[0]}:{key[1]}')
    for key,n in seen.items():
        if n>1: errors.append(f'duplicate mapping {key[0]}:{key[1]}')
        if key not in expected: errors.append(f'unknown original item {key[0]}:{key[1]}')
    for m in mapping:
        n,i=m['original_chapter'],m['original_item']; label=f'{n}:{i}'
        if m.get('action') not in ('adapt','reuse'): errors.append(f'{label}: invalid action; merging or omitting is not allowed')
        if not isinstance(m.get('reason'),str) or not m['reason'].strip(): errors.append(f'{label}: missing reason')
        if m['target_ids'] != [f'au-{n:02d}-{i:02d}']: errors.append(f'{label}: mapping must retain original position')
        for target in m['target_ids']:
            if target not in ids: errors.append(f'{label}: missing target {target}')
    return errors

def markdown_anchors(text):
    anchors=set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)',text))
    seen=Counter()
    clean=re.sub(r'```.*?```','',text,flags=re.S)
    for line in clean.splitlines():
        m=re.match(r'^#{1,6}\s+(.+?)\s*#*$',line)
        if not m: continue
        heading=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',m[1])
        heading=re.sub(r'<[^>]+>','',heading)
        slug=re.sub(r'[^\w\- ]','',heading.lower(),flags=re.UNICODE).replace(' ','-')
        suffix=f'-{seen[slug]}' if seen[slug] else ''
        anchors.add(slug+suffix); seen[slug]+=1
    return anchors

def validate_markdown(root, data, upstream):
    errors=[]; checked=0; anchor_cache={}
    expected_paths={chapter_path(c,upstream) for c in data['chapters']}
    actual_paths={p.relative_to(root).as_posix() for p in (root/'book').glob('*.md')}
    if actual_paths != expected_paths: errors.append('book filenames differ from original chapter inventory')
    paths=list((root/'book').glob('*.md'))+list((root/'docs').rglob('*.md'))+list(root.glob('*.md'))+[root/'sources/README.md']
    for path in paths:
        text=path.read_text(encoding='utf-8')
        for url in re.findall(r'\]\(([^)]+)\)',text):
            if url.startswith(('https://','http://','mailto:')): continue
            dest,_,fragment=unquote(url.strip('<>')).partition('#')
            target=(path.parent/dest).resolve() if dest else path
            checked+=1
            if not target.exists(): errors.append(f'{path.name}: broken local link {url}')
            elif fragment and target.is_file() and target.suffix=='.md':
                if target not in anchor_cache: anchor_cache[target]=markdown_anchors(target.read_text(encoding='utf-8'))
                if fragment not in anchor_cache[target]: errors.append(f'{path.name}: broken anchor {url}')
    for c in data['chapters']:
        path=root/chapter_path(c,upstream)
        if not path.exists(): continue
        text=path.read_text(encoding='utf-8')
        blocks=re.split(r'^### \d+\. ',text,flags=re.M)[1:]
        if len(blocks)!=len(c['entries']): errors.append(f'{path.name}: wrong rendered entry count')
        for i,block in enumerate(blocks,1):
            fields=re.findall(r'^- ([^：\n]+)：',block,flags=re.M)
            if fields!=list(FIELDS): errors.append(f'{path.name}:{i}: six fields missing or reordered')
        if '<details>' in text: errors.append(f'{path.name}: body must not hide instructions in disclosures')
    return errors,checked

def main():
    data=json.loads((ROOT/'sources/guide.json').read_text(encoding='utf-8-sig'))
    upstream=json.loads((ROOT/'sources/upstream.json').read_text(encoding='utf-8-sig'))['items']
    errors=validate_data(data,upstream,expected_chapters=range(1,32))
    if not errors:
        markdown_errors,checked=validate_markdown(ROOT,data,upstream); errors+=markdown_errors
    else: checked=0
    if errors:
        print('\n'.join(errors)); return 1
    print(f'PASS: 31 chapters; {sum(len(c["entries"]) for c in data["chapters"])} entries; {len(data["sources"])} source records; {len(upstream)} one-to-one mappings; {checked} internal links. Structural checks are not professional review.')
    return 0

if __name__=='__main__': sys.exit(main())
