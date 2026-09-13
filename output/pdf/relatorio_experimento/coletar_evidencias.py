"""Read-only measurement of the historical experiment; writes report evidence only."""
from pathlib import Path
import collections
import datetime as dt
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
THREAD = '01a08ca4-18ea-7160-95a0-e1e805620720'
SESSION = Path.home()/'.codex/sessions/2026/09/10'/f'rollout-2026-09-10T15-45-59-{THREAD}.jsonl'
END = '2026-09-13T04:04:06.100Z'
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
files = git('ls-tree', '-r', '--name-only', '-z', 'v1.0.0').decode().split('\0')[:-1]
groups = collections.defaultdict(lambda: dict(files=0, physical_lines=0, nonblank_lines=0))
inventory = []
for name in files:
    if Path(name).suffix not in {'.py', '.cpp', '.c', '.h', '.sh'}:
        continue
    raw = git('show', 'v1.0.0:'+name)
    lines = raw.decode().splitlines()
    group = name.split('/')[0]
    counts = dict(files=1, physical_lines=len(lines), nonblank_lines=sum(bool(s.strip()) for s in lines))
    for key, value in counts.items():
        groups[group][key] += value
    inventory.append(dict(path=name, sha256=hashlib.sha256(raw).hexdigest(), **counts))
users, goals, contexts, calls = [], [], collections.Counter(), collections.Counter()
goal_ids = set()
session_lines = []
for lineno, line in enumerate(SESSION.open(), 1):
    d = json.loads(line)
    p = d['payload']
    if d['timestamp'] > END:
        continue
    item = p.get('item', {})
    if item.get('type') == 'UserMessage':
        users.append(dict(line=lineno, timestamp_utc=d['timestamp'], text=' '.join(x.get('text','') for x in item['content'])))
    if d['type'] == 'turn_context':
        contexts[(p.get('model'), p.get('effort'))] += 1
    if p.get('type') == 'thread_goal_updated':
        goals.append(dict(line=lineno, timestamp_utc=d['timestamp'], goal=p['goal']))
    if p.get('type') == 'custom_tool_call' and 'update_goal(' in p.get('input',''):
        goal_ids.add(p.get('call_id'))
    if p.get('type') == 'custom_tool_call_output' and p.get('call_id') in goal_ids:
        for block in p.get('output', []):
            try:
                result = json.loads(block.get('text',''))
            except (ValueError, TypeError):
                continue
            if isinstance(result, dict) and 'goal' in result:
                goals.append(dict(line=lineno, timestamp_utc=d['timestamp'], **result))
    if p.get('type') == 'function_call':
        calls[p.get('name')] += 1
final = [x['goal'] for x in goals if x['goal']['status']=='complete'][-1]
subagents = []
for path in (Path.home()/'.codex/sessions/2026/09').glob('*/*.jsonl'):
    with path.open() as stream:
        try:
            meta = json.loads(next(stream))['payload']
        except (ValueError, StopIteration, KeyError):
            continue
        source = meta.get('source')
        if not isinstance(source, dict):
            continue
        spawn = source.get('subagent', {}).get('thread_spawn', {})
        if spawn.get('parent_thread_id') != THREAD:
            continue
        counts = collections.Counter()
        for line in stream:
            record = json.loads(line)
            if record['type'] == 'turn_context' and record['timestamp'] <= END:
                q = record['payload']
                counts[(q.get('model'),q.get('effort'))] += 1
        subagents.append(dict(session_file=path.name, sha256=sha(path), source=spawn,
            model_contexts=[dict(model=m,effort=e,records=n) for (m,e),n in counts.items()]))
sources = ['docs/literatura/protocolo_busca.md','docs/literatura/decisao_recorte.md',
 'docs/revisao_cientifica_1.md','docs/auditoria_final.md','docs/reproducao.md',
 'docs/c12_errata_v0110.md','docs/dados_sinteticos.md','docs/dados_publicos.md',
 'project_status.json','results/C13/c07_current_execution.json',
 'results/C13/bibliography_audit.json']
evidence = dict(revision=git('rev-parse','v1.0.0^{commit}').decode().strip(),
 tracked_files=len(files), code_groups=dict(groups), code_inventory=inventory,
 measurement='Physical splitlines and nonblank lines in Git v1.0.0; includes comments, archived code and copies. No deduplication.',
 thread_id=THREAD, session_sha256=sha(SESSION), user_messages=users, subagents=subagents,
 model_contexts=[dict(model=m,effort=e,records=n) for (m,e),n in contexts.items()],
 goal_events=goals, goal_final=final,
 goal_calendar_seconds=final['updatedAt']-final['createdAt'],
 first_request_to_completion_seconds=final['updatedAt']-1789066025,
 direct_function_calls=dict(calls),
 tags=git('tag','--merged','v1.0.0').decode().splitlines(),
 commits=git('log','--reverse','--format=%h %aI %s','v1.0.0').decode().splitlines(),
 source_hashes={p:sha(ROOT/p) for p in sources})
clarification = OUT/'esclarecimento_gemini.json'
if clarification.exists():
    evidence['subsequent_user_clarification'] = json.loads(clarification.read_text())
post_goal = OUT/'complementos_pos_goal.json'
if post_goal.exists():
    evidence['post_goal_complements'] = json.loads(post_goal.read_text())
(OUT/'evidencias.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in evidence.items() if k in ['code_groups','tracked_files','goal_final','goal_calendar_seconds','model_contexts']},ensure_ascii=False,indent=2))
