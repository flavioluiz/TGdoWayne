#!/usr/bin/env python3
"""C08 lossless evidence transport. Standard library only; never runs inference.

Closed campaign roots need their completion and an explicit ROOT review. All
selected bytes are hashed before packaging, rechecked during packaging, checked
inside ZIPs and restored into a new root. Historical JSON is never rewritten.
"""
from pathlib import Path, PurePosixPath
import argparse
import contextlib
import fcntl
import gzip
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import zipfile

SCHEMA = 'C08_LOSSLESS_EVIDENCE_BUNDLE_v3'
READABLE_SCHEMAS = {SCHEMA, 'C08_LOSSLESS_EVIDENCE_BUNDLE_v2', 'C08_LOSSLESS_EVIDENCE_BUNDLE_v1'}
CAP = 90*1024**2
INVENTORY_CAP = 128*1024**2
FLAGS = {'cdf_precision_pass', 'pooled_weight_guard_pass', 'saturation_guard_pass', 'replication_pass', 'refinement_pass'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def relative(value):
    require(isinstance(value, str) and '\\' not in value and '\x00' not in value, 'Unsafe relative path')
    p = PurePosixPath(value)
    require(value == str(p) and not p.is_absolute() and p.parts and all(v not in ('', '.', '..') and ':' not in v for v in p.parts), 'Unsafe relative path')
    return p


def source(root, name):
    parts = relative(name).parts
    p = root
    for part in parts:
        p = p/part
        require(not p.is_symlink(), 'Symlink in source path: '+name)
    require(p.is_file() or p.is_dir(), 'Missing regular source: '+name)
    return p


def bound(root, descriptor):
    p = source(root, descriptor['path'])
    require(p.is_file() and sha(p) == descriptor['sha256'], 'Bound source differs: '+str(p))
    return p


@contextlib.contextmanager
def campaign_locks(root, campaigns):
    with contextlib.ExitStack() as stack:
        held = set()
        for row in sorted(campaigns, key=lambda row: row['path']):
            p = source(root,row['lock_path']) if row.get('kind')=='offline' else source(root,row['path'])/'.campaign.lock'
            require(p.is_file() and not p.is_symlink(), 'Completed campaign lock missing')
            if p in held: continue
            held.add(p)
            stream = stack.enter_context(p.open('rb'))
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise RuntimeError('Campaign still active; no archive: '+row['path']) from error
        yield


def scan(root, name):
    p = source(root, name)
    if p.is_file():
        return [name], []
    files, excluded = [], []
    for base, directories, names in os.walk(p, followlinks=False):
        for n in sorted(directories+names):
            path = Path(base)/n
            require(not path.is_symlink(), 'Symlink forbidden: '+str(path))
            require(stat.S_ISREG(path.stat().st_mode) or path.is_dir(), 'Special input forbidden')
        for n in sorted(names):
            path = Path(base)/n
            rel = path.relative_to(root).as_posix()
            require('raw' not in path.relative_to(p).parts, 'Raw has not been retired: '+rel)
            if '__pycache__' in path.parts or n in ('.campaign.lock', '.DS_Store'):
                excluded.append(rel)
            else:
                files.append(rel)
    return sorted(files), sorted(excluded)


def audit_standard_campaign(root, item, hashes):
    """Hash/identity checks only; preserves every existing numerical flag."""
    base = item['path']
    def record(name):
        return read(root/base/name)
    def digest(name):
        return hashes[base+'/'+name]['sha256']
    complete = record('campaign_complete.json'); plan = record('campaign_plan.json')
    require(digest('campaign_complete.json') == item['completion_sha256'], 'Completion changed')
    require(complete.get('schema') == 'C08_PHASE_VARIANT_COMPLETE_v1' and complete.get('status') == 'ALL_TARGET_PRODUCTS_ARCHIVED', 'Campaign not complete')
    ids = plan['all_target_ids']
    require(len(ids) == len(set(ids)) and sorted(ids) == complete['targets'], 'Duplicate/missing target IDs')
    require(complete['driver_identity'] == plan['driver_identity'] and complete['phase'] == plan['phase'] and complete['response_variant'] == plan['response_variant'], 'Campaign identity differs')
    require(plan['phase'] in ('engineering', 'main') and len(ids) == (8 if plan['phase'] == 'engineering' else 64), 'Unsupported campaign scope')
    require(complete['population_numerical_family'] == (16 if plan['phase'] == 'engineering' else 128), 'Population family differs')
    require(complete.get('no_SBC_uniformity_claim') is True and complete.get('no_publication_or_global_response_approval') is True, 'Scientific limitations missing')
    review = read(bound(root, item['root_review']))
    if plan['phase'] == 'engineering':
        require(review.get('status') == 'BOTH_VARIANTS_LIFECYCLE_NUMERICS_COMPLETE', 'Engineering ROOT review absent')
        matching = [r for r in review['rows'] if r['variant'] == plan['response_variant']]
        require(len(matching) == 1, 'ROOT review variant ambiguous')
        review = matching[0]
    else:
        require(review.get('status') == 'COMPLETE_PRODUCTS_AND_ALL_FAILURES_PRESERVED', 'Main ROOT review absent')
        wrapper = record('quantile_wrapper_complete.json')
        require(wrapper['status'] == 'ALL64_STANDARD_AND_QUANTILE_ARCHIVES_PRESERVED' and wrapper['base_complete_sha256'] == digest('campaign_complete.json'), 'Quantile completion differs')
        require(review['wrapper_complete_sha256'] == digest('quantile_wrapper_complete.json'), 'ROOT quantile completion differs')
    require(review['complete_sha256'] == item['completion_sha256'] and review['LL'] == complete['ledger'], 'ROOT review/completion mismatch')
    states = sorted(name for name in hashes if re.fullmatch(re.escape(base)+r'/state/target_\d{6}\.json', name))
    require(len(states) == len(ids), 'State count differs')
    unresolved, targets, raw_sha, checked = [], [], {}, 0
    for t in sorted(ids):
        s = record(f'state/target_{t:06d}.json')
        require(s['target'] == t and s['status'] == 'TARGET_ARCHIVED' and s['driver_identity'] == plan['driver_identity'], 'Target state differs')
        flags = s['numerical_flags']
        require(set(flags) == FLAGS and all(type(v) is bool for v in flags.values()), 'Five original boolean flags required')
        expected = 'RECORDED_NUMERICAL_CHECKS_PASSED' if all(flags.values()) else 'NUMERICALLY_UNRESOLVED'
        require(s['numerical_status'] == expected and s['no_scientific_calibration_claim'] is True, 'Numerical state contradicts flags')
        require(len(s['artifacts']) == 7 and len({a['file'] for a in s['artifacts']}) == 7, 'Seven state artifacts required')
        for a in s['artifacts']:
            relative(a['file']); require(digest(a['file']) == a['sha256'], 'State artifact SHA differs'); checked += 1
        receipt = record(f'production/archive_receipt_target_{t:06d}.json')
        released = record(f'production/released_target_{t:06d}.json')
        require(released['status'] == 'RAW_RELEASED' and released['archive_receipt_sha256'] == digest(f'production/archive_receipt_target_{t:06d}.json'), 'Raw retirement binding differs')
        require(released['raw_sha256'] == receipt['raw_sha256'], 'Raw SHA receipt differs')
        require(not set(raw_sha).intersection(receipt['raw_sha256']), 'Duplicate retired raw identity')
        raw_sha.update(receipt['raw_sha256'])
        if plan['phase'] == 'main':
            qname = f'production/quantile_archive_target_{t:06d}.json'
            q = record(qname); joint = record(f'production/quantile_release_prerequisite_target_{t:06d}.json')
            require(q['target'] == t and q['all20_retained'] is True and len(q['artifacts']) == 6, 'Quantile consumer incomplete')
            require(len({a['role'] for a in q['artifacts']}) == 6, 'Quantile roles duplicate')
            require(joint['quantile_archive_sha256'] == digest(qname) and joint['original_numerical_flags'] == flags, 'Joint release binding differs')
            require(joint['core_archive_sha256'] == digest(f'production/archive_receipt_target_{t:06d}.json'), 'Core release binding differs')
            for a in q['artifacts']:
                relative(a['file']); value = hashes[base+'/'+a['file']]
                require(value['sha256'] == a['sha256'] and value['bytes'] == a['bytes'], 'Quantile artifact differs'); checked += 1
        if not all(flags.values()): unresolved.append(t)
        targets.append({k:s[k] for k in ('target','model','datum','numerical_status','numerical_flags')})
    require(unresolved == complete['numerically_unresolved_targets'], 'Failures omitted')
    require(checked == review['artifact_hashes_verified'], 'ROOT artifact inventory differs')
    require(complete['ledger']['unclosed_reservations'] == 0, 'Unclosed reservations')
    return dict(path=base,phase=plan['phase'],variant=plan['response_variant'],scope=plan['scope'],targets=targets,
        unresolved=unresolved,retired_raw_sha256=raw_sha,completion_sha256=item['completion_sha256'],root_review=item['root_review'],
        artifact_hashes_verified=checked,original_ledger=complete['ledger'],scientific_approval_inferred=False)


def audit_replay(root,item,hashes,dependencies):
    """Transport assertions only; ROOT's completed numerical audit is required.

    Never reopens compact numeric arrays or recomputes KL/statistics. Original
    C07 proposal/checkpoint dependencies may remain in their separate bundle.
    """
    base=item['path'];prefix=str(root)+os.sep
    def entry(name):
        relative(name);key=base+'/'+name;require(key in hashes,'Replay member absent: '+key)
        return hashes[key]
    def record(name):entry(name);return read(root/base/name)
    def included_ref(ref):
        value=ref['path'];require(isinstance(value,str) and value.startswith(prefix),'Reference must use frozen repository prefix')
        name=value[len(prefix):];relative(name)
        require(name in hashes and hashes[name]['sha256']==ref['sha256'],'Transported replay artifact SHA differs')
        return name
    def dependency_ref(ref):
        value=ref['path'];require(isinstance(value,str) and value.startswith(prefix),'C07 reference prefix differs')
        name=value[len(prefix):];relative(name)
        expected=hashes.get(name) or dependencies.get(name)
        require(expected is not None and expected['sha256']==ref['sha256'],'Unlisted C07 external dependency')
    complete=record('complete.json');execution=record('replay_execution.json')
    review=read(bound(root,item['root_review']));plan=read(bound(root,item['replay_plan']))
    require(item['root_review']['path'] in hashes and item['replay_plan']['path'] in hashes,'ROOT review and replay plan must travel')
    require(review.get('schema')=='ROOT_C08_REPLAY_RESULT_REVIEW_v1' and review.get('status')=='ALL160_REPLAY_PRODUCTS_REVIEWED','Reviewed closed replay required')
    require(entry('complete.json')['sha256']==item['completion_sha256']==review['execution_complete_sha256'],'Replay completion SHA differs')
    require(complete['status']=='ALL160_MATCHED_HIGH_REPLAYS_ARCHIVED' and complete['plan_sha256']==item['replay_plan']['sha256']==review['plan_sha256'],'Replay status/plan differs')
    require(execution['identity']==complete['identity']==review['identity'] and execution['authorization_sha256']==review['authorization_sha256'],'Replay execution identity differs')
    models=['A0_CN','A_CN','B_CN','A_G','B_G'];ids=review['cohort_ids']
    require(len(ids)==32 and ids==sorted(set(ids)) and all(type(d)is int and 0<=d<500 for d in ids),'Exact original32 cohort')
    targets=[500*i+d for i in range(5) for d in ids]
    require(complete['targets']==targets==[r['target'] for r in plan['rows']] and len(targets)==160,'All160 model/data targets required')
    require(review['by_model']=={m:32 for m in models} and plan['identity']==review['original_runtime_identity'],'Cohort/model/runtime namespace differs')
    required=dict(training=0,production=41943040,other=0,total=41943040,unclosed_reservations=0)
    cross=dict(training=0,production=1048576,other=0,total=1048576,unclosed_reservations=0)
    require(complete['ledger']==review['ledger']==required and complete['optional_KL']['cross_ledger']==review['cross_ledger']==cross,'Replay/cross ledger differs')
    require(complete['optional_KL']['status']=='EIGHT_RAW_PRODUCTS_CONSUMED_FOUR_KL_PAIRS' and complete['optional_KL']['extra_replay_LL']==0 and complete['optional_KL']['additional_banks']==0,'Optional completion scope differs')
    require(review['raw_empty'] and review['endpoint_statistics_retained'] and review['all_failures_preserved'] and review['original_all3200_brackets']==[0.,1.],'ROOT preservation limitations differ')
    require(len([n for n in hashes if re.fullmatch(re.escape(base)+r'/archives/target_\d{6}\.json',n)])==160,'Exactly160 replay archives')
    require(len([n for n in hashes if re.fullmatch(re.escape(base)+r'/replicas/target_\d{6}_rep[0-3]\.json',n)])==640,'Exactly640 replay receipts')
    retired={};optional_ids=[25,26,44,48];optional_targets=[1500+d for d in optional_ids]+[2000+d for d in optional_ids]
    artifact_count=0;optional_count=0
    for index,row in enumerate(plan['rows']):
        t=row['target'];require(row['datum']==t%500 and row['scientific_model']==models[t//500],'Frozen target model mapping')
        archive=record(f'archives/target_{t:06d}.json');state=record(f'state/target_{t:06d}.json')
        require(archive['target']==t and archive['plan_sha256']==complete['plan_sha256'] and archive['status']=='REPLAY_COMPACT_PRESERVED','Replay archive mismatch')
        require(state['status']=='C08_REPLAY_TARGET_ARCHIVED' and state['target']==t and state['archive_sha256']==entry(f'archives/target_{t:06d}.json')['sha256'],'Replay state SHA differs')
        require(archive['all_failures_retained'] and archive['no_SBC_or_physical_approval'],'Replay numerical limitations missing')
        require(archive['original_files']==row['original_files'] and archive['original_receipt']==row['original_receipt'],'C07 provenance differs')
        for ref in list(row['original_files'].values())+[row['original_receipt']]:dependency_ref(ref)
        included_ref(row['cut_manifest'])
        cp=row['high_checkpoints'];require(len(cp)==4 and [c['replicate'] for c in cp]==list(range(4)),'Four original checkpoints required')
        raw={c['raw_file']:c['raw_sha256'] for c in cp};require(len(raw)==4 and not set(raw).intersection(retired) and archive['raw_sha256']==raw,'Unique original raw SHA map differs');retired.update(raw)
        for c in cp:
            receipt=record(f'replicas/target_{t:06d}_rep{c["replicate"]}.json')
            require(receipt['status']=='BIT_EXACT_HIGH_REPLAY' and receipt['target']==t and receipt['samples']==65536
                and receipt['raw_sha256']==receipt['original_raw_sha256']==c['raw_sha256'],'Replay raw receipt differs')
            require(receipt['original_rng_state_before']==c['rng_state_before'] and receipt['original_rng_state_after']==c['rng_state_after']
                and receipt['new_seed'] is False and receipt['uses_truth'] is False,'Frozen RNG/truth policy differs')
        require(len(archive['artifacts'])==3+(t in optional_targets),'All endpoint/consumer artifacts required')
        for ref in archive['artifacts']:included_ref(ref);artifact_count+=1
        if t in optional_targets:
            rec=record(f'optional_kl/receipts/target_{t:06d}.json');optional_count+=1
            require(rec['status']=='CONSUMPTION_COMPLETE' and rec['target']==t and rec['raw_sha256']==raw and rec['all_failures_retained'],'Optional consumer missing or altered')
            require(len(rec['artifacts'])==(9 if t<2000 else 2),'Optional9/2 artifacts required')
            for ref in rec['artifacts']:included_ref(ref)
    require(len(retired)==640 and optional_count==8 and artifact_count==review['counts']['archive_artifacts_verified']==488,'Replay artifact counts differ')
    for d in optional_ids:
        pair=record(f'optional_kl/pairs/datum_{d:03d}.json')
        require(pair['datum']==d and pair['clipped'] is False and pair['no_uniform_certificate'] is True,'KL limitations missing')
        included_ref(pair['AG_statistics']);included_ref(pair['BG_statistics'])
    return dict(kind='replay',path=base,scope='CLOSED_C07_HIGH_REPLAY_AND_OPTIONAL_KL_LOSSLESS_TRANSPORT',
        completion_sha256=item['completion_sha256'],root_review=item['root_review'],replay_plan=item['replay_plan'],
        targets=targets,cohort_ids=ids,by_model=review['by_model'],retired_raw_sha256=retired,
        original_ledger=required,cross_ledger=cross,original_brackets=[0.,1.],common_failure_counts=review['common_failure_counts'],
        endpoint_statistics=review['counts']['endpoint_statistics'],quantiles=3200,optional_receipts=8,KL_pairs=4,
        independent_numerical_audit_not_repeated=True,scientific_approval_inferred=False)


def audit_offline(root,item,hashes):
    """Future ROOT-consolidated analysis roots; no implicit finite PASS upgrade.

    Legacy finite/partial output is not accepted directly. ROOT must first
    provide this explicit closed-root inventory/completion/review contract.
    """
    base=item['path'];name=item['completion_file'];relative(base);relative(name)
    require(base+'/'+name in hashes,'Offline completion absent from selected inventory')
    completion=read(source(root,base+'/'+name));review=read(bound(root,item['root_review']))
    require(hashes[base+'/'+name]['sha256']==item['completion_sha256']==review.get('completion_sha256'),'Offline completion SHA differs')
    require(completion.get('schema')=='C08_OFFLINE_ROOT_COMPLETE_v1' and completion.get('status')=='ALL_SELECTED_ANALYSIS_BYTES_PRESERVED','Explicit offline consolidation required')
    require(review.get('schema')=='ROOT_C08_OFFLINE_ROOT_REVIEW_v1' and review.get('status')=='OFFLINE_ROOT_COMPLETE_REVIEWED'
        and review.get('root_path')==base and review.get('lock_path')==item['lock_path'],'ROOT offline root/lock review required')
    require(completion.get('workers_exited') is True and completion.get('all_failures_preserved') is True
        and completion.get('no_uniform_proof') is True and completion.get('identity')==review.get('identity'),'Closed offline scope/limitations required')
    # v3: a small NEW metadata root may refer to selected repository members.
    # It never adopts or rewrites a failed physical root as its completion.
    namespace=completion.get('artifact_namespace','base')
    require(namespace in ('base','repository'),'Unknown offline artifact namespace')
    require(review.get('artifact_namespace','base')==namespace,'ROOT offline namespace differs')
    artifacts=completion['artifacts']
    key='path' if namespace=='repository' else 'file'
    require(artifacts and all(key in a for a in artifacts)
        and len({a[key] for a in artifacts})==len(artifacts),'Unique offline artifacts')
    if namespace=='repository':
        require(isinstance(completion.get('identity'),str) and completion['identity'].strip(),'Explicit offline identity required')
        require(type(review.get('artifact_count')) is int,'Explicit ROOT integer artifact count required')
        rr=item['root_review'];relative(rr['path'])
        require(rr['path'] in hashes and hashes[rr['path']]['sha256']==rr['sha256'],'ROOT review absent from selected inventory')
    for a in artifacts:
        relative(a[key])
        if namespace=='repository':
            require('file' not in a,'Repository artifacts use path only; no mixed coordinate fields')
            require(type(a.get('bytes')) is int and a['bytes']>=0
                and isinstance(a.get('sha256'),str) and re.fullmatch('[0-9a-f]{64}',a['sha256']) is not None,'Explicit artifact size/SHA required')
            name=a['path']
        else:
            name=base+'/'+a['file']
        require(name in hashes,'Offline artifact absent from selected inventory: '+name)
        r=hashes[name]
        require(r['sha256']==a['sha256'] and r['bytes']==a['bytes'],'Offline artifact SHA/size differs')
    require(review.get('artifact_count')==len(artifacts),'Reviewed offline count differs')
    result=dict(kind='offline',path=base,scope=completion['scope'],completion_sha256=item['completion_sha256'],root_review=item['root_review'],
        identity=completion['identity'],artifact_count=len(artifacts),all_failures_preserved=True,scientific_approval_inferred=False)
    if namespace=='repository':result['artifact_namespace']='repository'
    return result


def audit_campaign(root,item,hashes,dependencies=None):
    kind=item.get('kind','campaign')
    if kind=='replay':return audit_replay(root,item,hashes,dependencies or {})
    if kind=='offline':return audit_offline(root,item,hashes)
    require(kind=='campaign','Unknown closed-root kind')
    return audit_standard_campaign(root,item,hashes)


def plan(selection, repository, output):
    root = Path(repository).resolve(); selection_sha = sha(selection); spec = read(selection)
    require(sha(selection) == selection_sha, 'Selection changed while reading')
    require(spec.get('schema') == 'C08_ARCHIVE_SELECTION_v1', 'Selection schema')
    require(spec.get('original_repository_prefix') == str(root), 'Historical repository prefix differs')
    campaigns = spec['campaigns']; additions = spec['include']; require(campaigns, 'Closed campaign selection required')
    with campaign_locks(root, campaigns):
        names, skipped, scans = set(), set(), {}
        for name in [r['path'] for r in campaigns]+additions:
            got, excluded = scan(root, name); scans[name] = got
            names.update(got); skipped.update(excluded)
        for row in campaigns:
            require(row['root_review']['path'] in names, 'ROOT review must be transported')
        entries = {}
        for name in sorted(names):
            require('raw' not in relative(name).parts, 'Raw arrays forbidden')
            p = source(root, name); before = p.stat(); h = sha(p); after = p.stat()
            require((before.st_size,before.st_mtime_ns) == (after.st_size,after.st_mtime_ns), 'Source changed while hashing')
            require(before.st_size < CAP-4096, 'Large input requires its separate lossless transport: '+name)
            entries[name] = dict(path=name,bytes=before.st_size,sha256=h)
        dependencies={d['path']:d for d in spec.get('external_dependencies',[])}
        audits = [audit_campaign(root,row,entries,dependencies) for row in campaigns]
        for name, old in scans.items(): require(scan(root,name)[0] == old, 'Inventory changed while planning')
    require(sha(selection) == selection_sha, 'Selection changed during planning')
    value = dict(schema='C08_FROZEN_ARCHIVE_INVENTORY_v1',selection_sha256=selection_sha,selection=spec,
        files=list(entries.values()),audits=audits,excluded_transients=sorted(skipped),total_bytes=sum(r['bytes'] for r in entries.values()),
        original_repository_prefix=str(root),external_dependencies=spec.get('external_dependencies',[]),
        raw_arrays_included=False,originals_removed=False,new_physics_calls=0,
        relocation='Restore each relative path under a NEW destination root; historical bytes/absolute strings unchanged. Prefix map is interpretive, not source rewriting.')
    write(output,value)
    return dict(status='CLOSED_C08_INVENTORY_HASHED',files=len(entries),bytes=value['total_bytes'],sha256=sha(output))


def partition(rows, cap):
    groups, current, used = [], [], 1024
    for row in rows:
        n = row['bytes']; cost = n+(n>>12)+(n>>14)+(n>>25)+1024+4*len(row['path'].encode())
        require(cost+1024 <= cap, 'Member exceeds ZIP budget')
        if current and used+cost > cap:
            groups.append(current); current,used = [],1024
        current.append(row);used+=cost
    if current: groups.append(current)
    return groups


def pack(inventory, repository, output, cap=CAP):
    require(type(cap) is int and 1024 < cap <= CAP, 'Archive cap must be at most90MiB')
    root = Path(repository).resolve(); inventory_sha = sha(inventory); frozen = read(inventory)
    require(sha(inventory) == inventory_sha, 'Inventory changed while reading')
    require(not Path(output).is_symlink(), 'Output cannot be a symlink')
    out = Path(output).resolve()
    require(frozen['schema'] == 'C08_FROZEN_ARCHIVE_INVENTORY_v1' and frozen['original_repository_prefix'] == str(root), 'Inventory identity differs')
    require(not out.exists() and out.parent.is_dir(), 'New output under an existing parent required')
    selected_roots = [source(root,r['path']) for r in frozen['selection']['campaigns']]+[source(root,n) for n in frozen['selection']['include']]
    require(all(out != p and not out.is_relative_to(p) for p in selected_roots), 'Output cannot overlap any selected input')
    rows = frozen['files']; names = [r['path'] for r in rows]
    require(len(set(names)) == len(names) and sum(r['bytes'] for r in rows) == frozen['total_bytes'], 'Frozen inventory differs')
    with campaign_locks(root,frozen['selection']['campaigns']):
        # Recheck completion/ROOT hashes and all frozen campaign bindings.
        indexed = {r['path']:r for r in rows}
        for r in rows: require(sha(source(root,r['path'])) == r['sha256'], 'Frozen source changed before packing')
        dependencies={d['path']:d for d in frozen.get('external_dependencies',[])}
        for item in frozen['selection']['campaigns']: audit_campaign(root,item,indexed,dependencies)
        with tempfile.TemporaryDirectory(prefix='.c08_pack_',dir=out.parent) as temp:
            stage = Path(temp); parts=[]
            for k, group in enumerate(partition(rows,cap)):
                name=f'evidence_part{k:03d}.zip'; dest=stage/name
                with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as archive:
                    for row in group:
                        info=zipfile.ZipInfo(row['path'],date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
                        info.create_system=3;info.external_attr=(stat.S_IFREG|0o644)<<16
                        h=hashlib.sha256();size=0
                        with source(root,row['path']).open('rb') as src, archive.open(info,'w',force_zip64=True) as dst:
                            for chunk in iter(lambda:src.read(1024**2),b''):
                                h.update(chunk);size+=len(chunk);dst.write(chunk)
                        require(h.hexdigest()==row['sha256'] and size==row['bytes'],'Source changed during packaging')
                        row['archive']=name
                require(dest.stat().st_size<=cap,'ZIP cap exceeded')
                parts.append(dict(file=name,bytes=dest.stat().st_size,sha256=sha(dest),members=len(group)))
            with (stage/'inventory.json.gz').open('xb') as dst:
                with gzip.GzipFile(fileobj=dst,mode='wb',filename='',mtime=0) as gz:
                    gz.write(json.dumps(frozen,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
            shutil.copyfile(__file__,stage/'campanha_compressao.py')
            manifest=dict(schema=SCHEMA,status='LOSSLESS_BYTES_NO_NEW_SCIENTIFIC_APPROVAL',archives=parts,
                inventory_sha256=sha(stage/'inventory.json.gz'),source_sha256=sha(stage/'campanha_compressao.py'),
                original_inventory_sha256=inventory_sha,file_count=len(rows),restored_bytes=frozen['total_bytes'],
                maximum_archive_bytes=cap,raw_arrays_included=False,originals_removed=False,
                original_repository_prefix=str(root),new_physics_calls=0)
            write(stage/'bundle.json',manifest);verify(stage)
            for name in [r['path'] for r in frozen['selection']['campaigns']]+frozen['selection']['include']:
                current,_=scan(root,name)
                expected=sorted(n for n in names if n==name or n.startswith(name+'/'))
                require(current==expected,'Input inventory changed during packaging')
            for row in rows:
                path=source(root,row['path'])
                require(path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],'Input bytes changed before publication')
            require(sha(inventory)==inventory_sha,'Frozen inventory changed before publication')
            require(not out.exists(),'Output appeared during packaging');os.rename(stage,out)
    return dict(status=manifest['status'],files=len(rows),restored_bytes=manifest['restored_bytes'],archive_bytes=sum(p['bytes'] for p in parts),parts=len(parts),bundle_sha256=sha(out/'bundle.json'))


def verify(bundle, dependency_root=None):
    bundle=Path(bundle).resolve();m=read(bundle/'bundle.json')
    require(m['schema'] in READABLE_SCHEMAS and m['status']=='LOSSLESS_BYTES_NO_NEW_SCIENTIFIC_APPROVAL','Bundle schema/status')
    require(m.get('raw_arrays_included') is False and m.get('originals_removed') is False,'Transport markers differ')
    require(type(m['maximum_archive_bytes']) is int and 0<m['maximum_archive_bytes']<=CAP,'Archive budget invalid')
    require(sha(source(bundle,'campanha_compressao.py'))==m['source_sha256'],'Transport source changed')
    require(sha(source(bundle,'inventory.json.gz'))==m['inventory_sha256'],'Inventory changed')
    with gzip.open(bundle/'inventory.json.gz','rb') as stream: raw=stream.read(INVENTORY_CAP+1)
    require(len(raw)<=INVENTORY_CAP,'Inventory memory budget exceeded');frozen=json.loads(raw)
    require(frozen['schema']=='C08_FROZEN_ARCHIVE_INVENTORY_v1','Inventory schema')
    rows=frozen['files'];expected={r['path']:r for r in rows}
    require(len(expected)==len(rows)==m['file_count'],'Duplicate members')
    for row in rows:
        require('raw' not in relative(row['path']).parts and type(row['bytes']) is int and row['bytes']>=0,'Unsafe member')
        require(re.fullmatch('[0-9a-f]{64}',row['sha256']) is not None,'Invalid digest')
    require(sum(r['bytes'] for r in rows)==m['restored_bytes']==frozen['total_bytes'],'Restored byte count differs')
    archives=m['archives'];partnames=[p['file'] for p in archives]
    require(len(partnames)==len(set(partnames)) and set(r['archive'] for r in rows)==set(partnames),'Part inventory differs')
    for desc in archives:
        require(len(relative(desc['file']).parts)==1,'Part must be flat')
        path=source(bundle,desc['file']);require(path.stat().st_size==desc['bytes']<=m['maximum_archive_bytes'] and sha(path)==desc['sha256'],'Part hash/size differs')
        selected={k:v for k,v in expected.items() if v['archive']==desc['file']}
        with zipfile.ZipFile(path) as archive:
            infos=archive.infolist();require(len(infos)==len(selected)==desc['members'] and {i.filename for i in infos}==set(selected),'ZIP members differ')
            for info in infos:
                row=selected[info.filename]
                require(not info.is_dir() and stat.S_IFMT(info.external_attr>>16)==stat.S_IFREG and info.file_size==row['bytes'],'ZIP type/size differs')
                h=hashlib.sha256();count=0
                with archive.open(info) as src:
                    for chunk in iter(lambda:src.read(1024**2),b''):
                        h.update(chunk);count+=len(chunk);require(count<=row['bytes'],'ZIP expands beyond declared size')
                require(count==row['bytes'] and h.hexdigest()==row['sha256'],'Member SHA differs')
    if dependency_root is not None:
        for d in frozen['external_dependencies']:bound(Path(dependency_root).resolve(),d)
    return m,frozen


def restore(bundle,destination,max_bytes=2*1024**3):
    require(not Path(destination).is_symlink(),'Destination cannot be a symlink')
    out=Path(destination).resolve();bundle=Path(bundle).resolve()
    require(not out.exists() and out.parent.is_dir() and not out.is_relative_to(bundle),'A new destination outside bundle is required')
    require(type(max_bytes) is int and max_bytes>0 and read(bundle/'bundle.json')['restored_bytes']<=max_bytes,'Restoration budget exceeded')
    m,frozen=verify(bundle);expected={r['path']:r for r in frozen['files']}
    with tempfile.TemporaryDirectory(prefix='.c08_restore_',dir=out.parent) as temp:
        stage=Path(temp)
        for part in m['archives']:
            with zipfile.ZipFile(bundle/part['file']) as archive:
                for info in archive.infolist():
                    path=stage.joinpath(*relative(info.filename).parts);path.parent.mkdir(parents=True,exist_ok=True)
                    with archive.open(info) as src,path.open('xb') as dst:shutil.copyfileobj(src,dst,length=1024**2)
                    require(sha(path)==expected[info.filename]['sha256'],'Restored SHA differs')
        write(stage/'C08_RELOCATION_MAP.json',dict(original_prefix=m['original_repository_prefix'],restored_prefix=str(out),
            bundle_sha256=sha(bundle/'bundle.json'),rule='New root / exact original relative path. Historical file contents are unchanged.',
            external_dependencies=frozen['external_dependencies'],does_not_authorize_execution=True))
        require(not out.exists(),'Destination appeared during restore');os.rename(stage,out)
    return dict(status='ALL_SELECTED_BYTES_RESTORED',files=m['file_count'],bytes=m['restored_bytes'],raw_arrays_restored=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('planejar');q.add_argument('--selecao',type=Path,required=True);q.add_argument('--repositorio',type=Path,required=True);q.add_argument('--saida',type=Path,required=True)
    q=sub.add_parser('empacotar');q.add_argument('--inventario',type=Path,required=True);q.add_argument('--repositorio',type=Path,required=True);q.add_argument('--saida',type=Path,required=True);q.add_argument('--max-parte-bytes',type=int,default=CAP)
    q=sub.add_parser('verificar');q.add_argument('--pacote',type=Path,required=True);q.add_argument('--dependencias',type=Path)
    q=sub.add_parser('restaurar');q.add_argument('--pacote',type=Path,required=True);q.add_argument('--destino',type=Path,required=True);q.add_argument('--max-bytes',type=int,default=2*1024**3)
    a=p.parse_args()
    if a.command=='planejar':r=plan(a.selecao,a.repositorio,a.saida)
    elif a.command=='empacotar':r=pack(a.inventario,a.repositorio,a.saida,a.max_parte_bytes)
    elif a.command=='restaurar':r=restore(a.pacote,a.destino,a.max_bytes)
    else:
        m,_=verify(a.pacote,a.dependencias);r=dict(status='ALL_ARCHIVED_BYTES_VERIFIED',files=m['file_count'],scientific_approval_inferred=False)
    print(json.dumps(r,sort_keys=True))


if __name__=='__main__':main()
