"""Audit citation closure and integrity of catalogued local reading copies.

Checks metadata presence, not the factual accuracy of every bibliographic field
or the scientific support for each citing sentence.
"""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
bib = root / 'latex/referencias/referencias.bib'
bcf = root / 'tmp/latex/dissertacao/dissertacao.bcf'
catalog = root / 'literature/catalog.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
matches = list(re.finditer(r'(?ms)^@(\w+)\{([^,]+),(.*?)(?=^@|\Z)', bib.read_text()))
entries = {m[2]: (m[1], m[3]) for m in matches}
assert len(entries) == len(matches), 'Duplicate bibliography keys'
cited = sorted({n.text for n in ET.parse(bcf).iter() if n.tag.endswith('}citekey')})
assert set(cited) <= entries.keys(), 'Citations without bibliography entries'
for key in cited:
    kind, body = entries[key]
    fields = set(re.findall(r'^\s*(\w+)\s*=', body, re.M))
    assert {'author', 'title'} <= fields, key
    assert fields & {'date', 'year'}, key
    if kind == 'article':
        assert fields & {'journal', 'journaltitle'}, key
        assert {'volume', 'pages'} <= fields, key
    if 'url' in fields:
        assert 'urldate' in fields, key
papers = json.loads(catalog.read_text())['papers']
verified = []
for paper in papers:
    if paper['key'] not in cited:
        continue
    path = root / paper['local_path']
    assert path.is_file(), str(path)
    assert sha(path) == paper['sha256'], str(path)
    assert path.stat().st_size == paper['size_bytes'], str(path)
    verified.append(dict(key=paper['key'], path=paper['local_path'], sha256=paper['sha256']))
missing_access_date = [k for k in cited if re.search(r'^\s*url\s*=', entries[k][1], re.M)
    and not re.search(r'^\s*urldate\s*=', entries[k][1], re.M)]
report = dict(passed=True, scope=__doc__, cited_entries=len(cited),
    bibliography_entries=len(entries), verified_reading_copies=verified,
    cited_outside_paper_catalog=sorted(set(cited)-{p['key'] for p in papers}),
    records_with_url_without_access_date=missing_access_date,
    pagination_correction=dict(key='vehtari2021', pages='667--718',
        source='https://research.aalto.fi/fi/publications/rank-normalization-folding-and-localization-an-improved-r-hat-for/'),
    inputs={str(p.relative_to(root)):sha(p) for p in (bib, bcf, catalog)},
    source_sha256=sha(Path(__file__)))
(root / 'results/C13/bibliography_audit.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('verified_reading_copies','inputs','scope')}, indent=2))
