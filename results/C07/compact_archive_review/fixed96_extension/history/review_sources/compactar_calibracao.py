#!/usr/bin/env python3
"""Lossless post-completion bundles; preserves numerical failures, never deletes inputs.

Only Python's standard library is required. This is an integrity/transport tool,
not a posterior validator or a calibration decision. Paths inside ZIPs restore
under campaign/ and supplements/. Raw retirement remains the driver's task.
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
import sys
import tempfile
import zipfile

SCHEMA = 'C07_COMPACT_CAMPAIGN_v1'
MAX_ARCHIVE_BYTES = 90 * 1024**2
TARGET_RE = re.compile(r'(?:^|_)target_(\d{6})(?=[_.]|$)')
NUMERICAL_STATES = {'RECORDED_NUMERICAL_CHECKS_PASSED', 'NUMERICALLY_UNRESOLVED'}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    with Path(path).open() as stream:
        return json.load(stream)


def write_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def relative_name(value):
    require(isinstance(value, str) and '\\' not in value and '\x00' not in value, 'Unsafe member name.')
    path = PurePosixPath(value)
    require(value == str(path) and not path.is_absolute() and all(p not in ('', '.', '..') for p in path.parts), 'Unsafe member path.')
    require(bool(path.parts) and not any(':' in p for p in path.parts), 'Unsafe member path.')
    return path


def integer(value, name, minimum=1):
    require(type(value) is int and value >= minimum, name + ' must be an integer in range.')
    return value


def scan(root):
    """No symlinks/special files, including beneath excluded directories."""
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), 'A real directory is required: ' + str(root))
    result = []
    for base, directories, files in os.walk(root, followlinks=False):
        directories.sort()
        for name in directories + sorted(files):
            path = Path(base) / name
            require(not path.is_symlink(), 'Symlinks are not archived: ' + str(path))
            mode = path.stat().st_mode
            require(stat.S_ISDIR(mode) or stat.S_ISREG(mode), 'Special files are not archived: ' + str(path))
            if stat.S_ISREG(mode):
                result.append(path)
    return sorted(result, key=lambda p: p.relative_to(root).as_posix())


@contextlib.contextmanager
def read_lock(campaign):
    # Driver creates this file; never create/change it from the archive tool.
    path = campaign / '.campaign.lock'
    require(path.is_file() and not path.is_symlink(), 'Missing driver lock file.')
    with path.open('rb') as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('The campaign driver is active; archive only after completion.') from exc
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def audit_campaign(campaign, files, *, engineering=False, fixed96=False):
    """Linear inventory audit, with cached hashes; no likelihood/NPZ evaluation."""
    hashes = {}; sizes = {}
    for path in files:
        rel = path.relative_to(campaign).as_posix()
        if rel == '.campaign.lock':
            continue
        require(not rel.startswith('raw/'), 'Completed campaign still has raw files: ' + rel)
        before = path.stat()
        hashes[rel] = digest(path); sizes[rel] = before.st_size
        after = path.stat()
        require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'Input changed during hashing.')
    def record(rel):
        relative_name(rel)
        require(rel in hashes, 'Missing campaign product: ' + rel)
        return read_json(campaign / rel)
    def artifact(rel, expected):
        relative_name(rel)
        require(hashes.get(rel) == expected, 'Artifact hash mismatch: ' + rel)
    plan = record('campaign_plan.json'); complete = record('campaign_complete.json')
    ids = plan['all_target_ids']
    require(isinstance(ids, list) and ids and all(type(t) is int and t >= 0 for t in ids) and len(ids) == len(set(ids)), 'Invalid planned target inventory.')
    require(not (engineering and fixed96), 'Engineering and fixed96 are distinct archive scopes.')
    if fixed96:
        require(plan.get('scope') == 'FIXED_TRUTH96_NOT_SBC' and plan.get('datasets') == 96 and plan.get('models') == ['A0_CN'] and sorted(ids) == list(range(96)), 'Fixed96 archive requires all96 A0_CN targets and its explicit scope.')
        require(complete.get('scope') == 'FIXED_TRUTH96_NOT_SBC', 'Fixed96 completion scope differs.')
    elif engineering:
        require(plan.get('scope') == 'ENGINEERING_ONLY', 'Engineering archive requires its explicit scope.')
    else:
        require(plan.get('scope') == 'PRIOR_PREDICTIVE500_POSTERIOR_NUMERICS' and plan.get('datasets') == 500 and sorted(ids) == list(range(2500)), 'Default archive requires all2500 targets; engineering or fixed96 must be explicit.')
    require(complete.get('status') == 'ALL_TARGET_PRODUCTS_ARCHIVED' and complete.get('driver_identity') == plan['driver_identity'] and complete.get('targets') == sorted(ids) and complete.get('no_SBC_uniformity_claim') is True, 'Campaign is not completely archived by the driver.')
    state_paths = [r for r in hashes if re.fullmatch(r'state/target_\d{6}\.json', r)]
    require(len(state_paths) == len(ids), 'Completed state count differs.')
    states = {}; all_raw = {}
    for rel in state_paths:
        row = record(rel); t = row.get('target'); prefix = f'{t:06d}' if type(t) is int else ''
        require(t in ids and t not in states and rel == f'state/target_{prefix}.json', 'Duplicate/unplanned target state.')
        require(row.get('status') == 'TARGET_ARCHIVED' and row.get('driver_identity') == plan['driver_identity'] and row.get('numerical_status') in NUMERICAL_STATES, 'Target state/identity mismatch.')
        require(row.get('no_scientific_calibration_claim') is True, 'Target must preserve the no-calibration-claim marker.')
        expected_artifacts = {f'production/target_{prefix}.json', f'diagnostics/diagnostic_target_{prefix}.json', f'diagnostics/diagnostic_target_{prefix}.npz', f'production/archive_receipt_target_{prefix}.json', f'production/released_target_{prefix}.json'}
        require({a['file'] for a in row['artifacts']} == expected_artifacts and len(row['artifacts']) == 5, 'State does not bind the five completed products.')
        for item in row['artifacts']:
            artifact(item['file'], item['sha256'])
        producer_rel = f'production/target_{prefix}.json'; producer = record(producer_rel)
        diag_rel = f'diagnostics/diagnostic_target_{prefix}.json'; diag = record(diag_rel)
        receipt_rel = f'production/archive_receipt_target_{prefix}.json'; receipt = record(receipt_rel)
        release = record(f'production/released_target_{prefix}.json')
        for item in (producer, diag, receipt, release):
            require(item.get('identity') == plan['identity'] and item.get('target') == t, 'Product identity/target mismatch.')
        require(producer.get('status') == 'IID_COMPLETE_AWAITING_DIAGNOSTICS' and diag.get('status') == 'NUMERICAL_DIAGNOSTICS_COMPLETE', 'Incomplete target products.')
        require((row['model'], row['datum']) == (producer['model'], producer['datum']) == (diag['model'], diag['datum']), 'Model/datum mismatch.')
        if fixed96:
            require(row.get('fixed_masked_scope_preserved') is True and row['model'] == 'A0_CN' and row['datum'] == t, 'Fixed96 target mapping or masked-scope marker differs.')
            require(diag.get('schema') == 'C07_FIXED_MASKED_IID_DIAGNOSTICS_v2_OPERATIONAL' and diag.get('scope') == 'FIXED_TRUTH96_NOT_SBC', 'Fixed96 masked diagnostic schema/scope differs.')
            diagnostic_inputs = diag.get('diagnostic_inputs', {})
            require(diagnostic_inputs.get('generation_sha256') == plan['extra_input_sha256']['generation'] and diagnostic_inputs.get('truth_data_sha256') == plan['input_sha256']['data'] and diagnostic_inputs.get('protocol_sha256') == plan['extra_input_sha256']['protocol'], 'Fixed96 diagnostic generation/data/protocol differs.')
        require(producer['input_sha256'] == plan['input_sha256'], 'Producer input identity differs.')
        require(producer['levels'] == plan['levels'] and len(producer['replicates']) == 8, 'Two levels/four replicates not retained.')
        raw = {}; checkpoints = set()
        for cp in producer['replicates']:
            pair = (cp['level'], cp['replicate'])
            require(pair not in checkpoints and pair[0] in plan['levels'] and pair[1] in range(4), 'Checkpoint inventory differs.')
            checkpoints.add(pair)
            require(all(k in cp for k in ('rng_recipe', 'rng_state_before', 'rng_state_after', 'seed', 'proposal_sha256')), 'RNG replay recipe missing.')
            require(cp['proposal_sha256'] == producer['proposal_sha256'], 'Checkpoint proposal mismatch.')
            require(record(f'production/target_{prefix}_N{pair[0]}_rep_{pair[1]:02d}.json') == cp, 'Checkpoint content differs.')
            require(Path(cp['raw_file']).name == cp['raw_file'] and cp['raw_file'] not in raw, 'Raw filename collision.')
            raw[cp['raw_file']] = cp['raw_sha256']
        artifact(f'proposals/target_{prefix}.json', producer['proposal_sha256'])
        artifact('diagnostics/' + str(relative_name(diag['numeric_file'])), diag['numeric_sha256'])
        require(receipt.get('status') == 'RAW_ARCHIVE_VERIFIED' and receipt.get('archive_scope') == 'reproducible_target_summary' and receipt.get('raw_sha256') == raw == diag.get('raw_sha256'), 'Archive/raw inventory differs.')
        require(receipt.get('numerical_flags') == row['numerical_flags'] and all(diag['summary'][key] == value for key, value in row['numerical_flags'].items()), 'Numerical flags differ between state, receipt and diagnostic.')
        require(receipt.get('all_indicators_and_failures_retained') is True and receipt.get('no_scientific_calibration_claim') is True and receipt.get('numerical_status') == row['numerical_status'], 'Numerical failures were not retained.')
        roles = []
        for item in receipt['artifacts']:
            artifact('production/' + str(relative_name(item['file'])), item['sha256']); roles.append(item['role'])
        require(len(roles) == len(set(roles)) and {'producer', 'diagnostic', 'numeric', 'proposal'}.issubset(roles) and sum(r.startswith('checkpoint_') for r in roles) == 8, 'Archive roles incomplete.')
        require(release.get('status') == 'RAW_RELEASED' and release.get('raw_sha256') == raw and release.get('archive_receipt_sha256') == hashes[receipt_rel] and release.get('numerical_status') == row['numerical_status'], 'Raw retirement receipt differs.')
        require(not set(raw).intersection(all_raw), 'Duplicate raw IDs across targets.')
        all_raw.update(raw)
        states[t] = {k: row[k] for k in ('target', 'model', 'datum', 'numerical_status', 'numerical_flags')}
    unresolved = sorted(t for t, s in states.items() if s['numerical_status'] == 'NUMERICALLY_UNRESOLVED')
    require(complete.get('numerically_unresolved_targets') == unresolved, 'UNRESOLVED inventory differs.')
    # Audit every ledger event once, retaining failed and reserved attempts.
    intent_paths = sorted(r for r in hashes if re.fullmatch(r'ledger/event_\d{6}\.intent.json', r))
    require(intent_paths == [f'ledger/event_{i:06d}.intent.json' for i in range(len(intent_paths))], 'Ledger has a sequence gap.')
    totals = dict(training=0, production=0, other=0, unclosed_reservations=0)
    for rel in hashes:
        if re.fullmatch(r'ledger/event_\d{6}\.end.json', rel):
            require(rel.replace('.end.json', '.intent.json') in hashes, 'Ledger completion lacks an intent.')
    for rel in intent_paths:
        event = record(rel); reserved = integer(event['reserved_likelihood_values'], 'reservation', 0)
        require(event.get('driver_identity') == plan['driver_identity'] and event['kind'] in ('training', 'production', 'other'), 'Ledger identity/kind differs.')
        end_rel = rel.replace('.intent.json', '.end.json')
        if end_rel in hashes:
            end = record(end_rel); used = integer(end['likelihood_evaluations'], 'likelihood count', 0)
            require(end['intent_sha256'] == hashes[rel] and used <= reserved, 'Ledger hash/count differs.')
        else:
            used = reserved; totals['unclosed_reservations'] += 1
        totals[event['kind']] += used
    totals['total'] = sum(totals[k] for k in ('training', 'production', 'other'))
    require(complete['ledger'] == totals, 'Final ledger does not match immutable events.')
    provenance_rel = 'provenance/' + plan['identity'] + '/manifest.json'
    provenance = record(provenance_rel)
    require(provenance['identity'] == plan['identity'] and provenance['input_sha256'] == plan['input_sha256'], 'Runtime provenance differs.')
    snapshot_hashes = {h for r, h in hashes.items() if r.startswith(str(PurePosixPath(provenance_rel).parent) + '/')}
    require(set(provenance['source_sha256'].values()).issubset(snapshot_hashes), 'Runtime source bytes are missing.')
    base = 'driver_provenance/' + plan['driver_identity'] + '/'
    for name, h in plan['driver_source_sha256'].items():
        artifact(base + name + '.py', h)
    for name in ('protocol', 'generation' if fixed96 else 'truth_logl'):
        artifact(base + name + '.json', plan['extra_input_sha256'][name])
    if fixed96:
        generation = record(base + 'generation.json')
        require(plan['extra_input_sha256']['truth_data'] == plan['input_sha256']['data'], 'Fixed96 truth/data hashes differ.')
        require(generation.get('status') == 'FIXED_DATA_GENERATED_NOT_POSTERIOR_INFERENCE' and generation.get('data_sha256') == plan['input_sha256']['data'] and generation.get('preflight', {}).get('experiment_sha256') == plan['input_sha256']['experiment'], 'Fixed96 generation/configuration identity differs.')
        require(generation.get('truth_defined_per_parameter') == [64,64,64,96,96] and generation.get('defined_signal_model_logL_at_truth') == 64 and generation.get('row_ranges') == [[0,31],[32,63],[64,95]], 'Fixed96 generation mask inventory differs.')
    return dict(plan=plan, complete=complete, states=[states[t] for t in sorted(states)], raw_sha256=all_raw, hashes=hashes, sizes=sizes, ledger_events=len(intent_paths))


def named_paths(items):
    result = {}
    for value in items or []:
        name, sep, path = value.partition('=')
        require(sep and re.fullmatch('[A-Za-z0-9_-]+', name) and name not in result, 'Use unique LABEL=PATH arguments.')
        source = Path(path).absolute()
        require(not source.is_symlink() and source.exists(), 'Explicit input is missing/a symlink.')
        result[name] = source
    return result


def check_dependencies(expected, paths):
    verified = {}
    for name, path in paths.items():
        require(name in expected and path.is_file() and digest(path) == expected[name], 'External dependency hash differs: ' + name)
        verified[name] = dict(path=str(path), sha256=expected[name], bytes=path.stat().st_size)
    return verified


def archive_bound(entry):
    # Conservative zlib compressBound plus ZIP64/name/central-directory allowance.
    n = entry['bytes']; return n + (n >> 12) + (n >> 14) + (n >> 25) + 13 + 512 + 4 * len(entry['member'].encode())


def partition(entries, cap):
    result = []; current = []; used = 1024
    for item in entries:
        cost = archive_bound(item)
        require(cost + 1024 <= cap, 'One member exceeds the archive limit: ' + item['member'])
        if current and used + cost > cap:
            result.append(current); current = []; used = 1024
        current.append(item); used += cost
    if current:
        result.append(current)
    return result


def pack(campaign, output, *, engineering=False, fixed96=False, block_size=64, maximum_archive_bytes=MAX_ARCHIVE_BYTES, supplements=None, dependencies=None):
    campaign = Path(campaign).absolute(); output = Path(output).absolute()
    output = output.parent.resolve() / output.name
    require(not campaign.is_symlink(), 'Campaign cannot be a symlink.')
    campaign = campaign.resolve()
    require(not output.exists() and output.parent.is_dir() and not output.is_relative_to(campaign), 'Output must be a new directory outside the campaign, under an existing parent.')
    integer(block_size, 'block size'); integer(maximum_archive_bytes, 'archive limit')
    require(maximum_archive_bytes < 100_000_000, 'Archive limit must be below the GitHub100MB file limit.')
    supplements = supplements or {}; dependencies = dependencies or {}
    with read_lock(campaign):
        files = scan(campaign); audit = audit_campaign(campaign, files, engineering=engineering, fixed96=fixed96)
        plan = audit['plan']; deps = check_dependencies(plan['input_sha256'], dependencies)
        ids = set(plan['all_target_ids']); groups = {}; entries = []; sources = {}
        def add(member, source, h=None, size=None, group='metadata'):
            relative_name(member); require(member not in sources, 'Duplicate member.')
            require(not source.is_symlink(), 'No symlink inputs.')
            row = dict(member=member, bytes=source.stat().st_size if size is None else size, sha256=digest(source) if h is None else h)
            sources[member] = source; entries.append(row); groups.setdefault(group, []).append(row)
        for rel in audit['hashes']:
            target_ids = {int(match.group(1)) for part in PurePosixPath(rel).parts for match in [TARGET_RE.search(part)] if match}
            require(len(target_ids) <= 1 and target_ids.issubset(ids), 'Filename contains unplanned/mixed target IDs: ' + rel)
            target = next(iter(target_ids), None)
            group = 'metadata' if target is None else f'targets_{target // block_size * block_size:06d}_{(target // block_size + 1) * block_size - 1:06d}'
            add('campaign/' + rel, campaign / rel, audit['hashes'][rel], audit['sizes'][rel], group)
        for label, root in sorted(supplements.items()):
            require(re.fullmatch('[A-Za-z0-9_-]+', label) is not None, 'Unsafe supplement label.')
            require(not root.is_symlink() and not root.resolve().is_relative_to(campaign), 'Supplements must be explicit independent paths, outside the campaign.')
            for path in scan(root) if root.is_dir() else [root]:
                member = 'supplements/' + label + '/' + (path.relative_to(root).as_posix() if root.is_dir() else path.name)
                add(member, path, group='supplements_' + label)
        # New directory is published only after every archive verifies. An exception
        # removes only this tool's temporary staging directory, never source inputs.
        with tempfile.TemporaryDirectory(prefix='.compact_', dir=output.parent) as name:
            stage = Path(name); archives = []
            for group, values in sorted(groups.items()):
                for part, subset in enumerate(partition(sorted(values, key=lambda r: r['member']), maximum_archive_bytes)):
                    filename = f'{group}_part{part:03d}.zip'; path = stage / filename
                    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
                        for row in subset:
                            info = zipfile.ZipInfo(row['member'], date_time=(1980, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
                            info.external_attr = (stat.S_IFREG | 0o644) << 16; info.create_system = 3
                            h = hashlib.sha256(); count = 0
                            with sources[row['member']].open('rb') as src, archive.open(info, 'w', force_zip64=True) as dst:
                                for block in iter(lambda: src.read(1024**2), b''):
                                    h.update(block); count += len(block); dst.write(block)
                            require(count == row['bytes'] and h.hexdigest() == row['sha256'], 'Source changed while packaging: ' + row['member'])
                            row['archive'] = filename
                    require(path.stat().st_size <= maximum_archive_bytes, 'Compressed archive exceeded the declared cap.')
                    archives.append(dict(file=filename, bytes=path.stat().st_size, sha256=digest(path), group=group, members=len(subset)))
            inventory = dict(schema=SCHEMA, files=sorted(entries, key=lambda r: r['member']), targets=audit['states'], retired_raw_sha256=audit['raw_sha256'], excluded_transient_files=['campaign/.campaign.lock'])
            inventory_path = stage / 'inventory.json.gz'
            with inventory_path.open('xb') as raw:
                with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0, compresslevel=6) as stream:
                    stream.write(json.dumps(inventory, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
            require(inventory_path.stat().st_size < 100_000_000, 'Inventory exceeds the individual Git file limit.')
            shutil.copyfile(__file__, stage / 'compactar_calibracao.py')
            summary = dict(schema=SCHEMA, status='LOSSLESS_COMPACT_ARCHIVE_NO_CALIBRATION_CLAIM', campaign_scope=plan['scope'], runtime_identity=plan['identity'], driver_identity=plan['driver_identity'], target_count=len(ids), unresolved_count=len(audit['complete']['numerically_unresolved_targets']), all_ids_retained=True, originals_removed=False, raw_arrays_included=False, scientific_approval_inferred=False, file_count=len(entries), restored_bytes=sum(r['bytes'] for r in entries), archive_bytes=sum(r['bytes'] for r in archives), maximum_archive_bytes=maximum_archive_bytes, block_size=block_size, ledger_events=audit['ledger_events'], archives=archives, inventory=dict(file='inventory.json.gz', bytes=inventory_path.stat().st_size, sha256=digest(inventory_path)), input_dependencies=plan['input_sha256'], dependencies_verified_at_pack=deps, script_sha256=digest(stage/'compactar_calibracao.py'))
            write_json(stage/'bundle.json', summary)
            (stage/'README.md').write_text(bundle_readme(summary))
            verify(stage)
            # Refuse new files appearing during the operation, including raw.
            require([p.relative_to(campaign).as_posix() for p in scan(campaign)] == [p.relative_to(campaign).as_posix() for p in files], 'Campaign inventory changed during packaging.')
            require(not output.exists(), 'Output appeared during packaging.')
            os.rename(stage, output)
    return summary


def bundle_readme(summary):
    return f'''# C07 — arquivo compacto e verificável

{summary['target_count']} alvos preservados; {summary['unresolved_count']} com estado NUMERICALLY_UNRESOLVED. Escopo original: `{summary['campaign_scope']}`. Nenhum alvo foi descartado por resultado científico ou numérico. Este pacote transporta artefatos; não aprova calibração. O escopo FIXED_TRUTH96_NOT_SBC preserva a geração e as máscaras de verdades indefinidas; os cenários fixos não constituem SBC.

```sh
python3 compactar_calibracao.py verify --bundle .
python3 compactar_calibracao.py extract --bundle . --destination /caminho/novo
```

A extração restaura `campaign/` e eventuais `supplements/`, byte por byte, sem sobrescrever destinos. Os ZIPs também podem ser abertos por ferramentas padrão, mas use o verificador para conferir o inventário completo. `inventory.json.gz` associa cada caminho ao SHA256 e ao ZIP, preserva todos os IDs/estados e os hashes dos raws aposentados. O próprio inventário e cada ZIP são vinculados por `bundle.json`. Preserve o SHA256 deste arquivo no commit/release: hashes oferecem integridade, não autenticação independente.

As fontes, configurações, propostas congeladas, receitas/estados RNG, oito checkpoints, recibos, diagnósticos, ledger e tentativas permanecem nos caminhos originais dentro de `campaign/`. Pequenas amostras descritivas não são amostras IID da posterior e não substituem os diagnósticos. Os raws grandes já aposentados pelo driver não são incluídos. Nenhum original é removido por este utilitário.

Para reproduzir, restaure o pacote fora da árvore versionada, disponibilize as dependências de entrada com os SHA256 de `bundle.json` e use as fontes/receitas congeladas. `verify --dependency data=... --dependency table=...` verifica explicitamente esses arquivos externos; também admite qualquer outro papel de `input_dependencies`. Configurações copiadas estão em cada `archive_target_*/input_*.json`; dados/tabela/binário nativo podem existir separadamente no repositório. O manifesto de build preservado permite reconstruir o backend; igualdade binária entre plataformas não é prometida. Uma nova produção deve usar destino separado e a mesma proposta/agenda RNG; restaurar um alvo finalizado não autoriza sobrescrever checkpoints para recriar raw. O driver com `--resume` apenas revalida alvos já finalizados.

A verificação não deserializa posteriors nem refaz SBC. Logs externos, síntese e evidências só estão incluídos quando explicitamente passados como suplementos. Os limites científicos da síntese original permanecem válidos.
'''


def verify(bundle, *, dependencies=None):
    bundle = Path(bundle).resolve(); summary = read_json(bundle/'bundle.json')
    require(summary.get('schema') == SCHEMA and summary.get('status') == 'LOSSLESS_COMPACT_ARCHIVE_NO_CALIBRATION_CLAIM', 'Unknown compact archive schema/status.')
    require(digest(bundle/'compactar_calibracao.py') == summary['script_sha256'], 'Packager source changed.')
    desc = summary['inventory']; relative_name(desc['file'])
    require(desc['file'] == 'inventory.json.gz' and (bundle/desc['file']).stat().st_size == desc['bytes'] and digest(bundle/desc['file']) == desc['sha256'], 'Inventory hash/size differs.')
    with gzip.open(bundle/desc['file'], 'rb') as stream:
        raw_inventory = stream.read(128*1024**2 + 1)
    require(len(raw_inventory) <= 128*1024**2, 'Inventory exceeds the 128MiB reader budget.')
    inventory = json.loads(raw_inventory)
    require(inventory.get('schema') == SCHEMA, 'Inventory schema differs.')
    files = inventory['files']; names = [r['member'] for r in files]
    require(len(names) == len(set(names)) == summary['file_count'], 'Duplicate/missing inventory members.')
    for member in names:
        require(relative_name(member).parts[0] in ('campaign', 'supplements'), 'Unexpected extraction namespace.')
        require(not member.startswith('campaign/raw/'), 'Raw arrays must not enter this compact archive.')
    targets = inventory['targets']; tids = [t['target'] for t in targets]
    require(len(tids) == len(set(tids)) == summary['target_count'] and all(t['numerical_status'] in NUMERICAL_STATES for t in targets), 'Target state inventory differs.')
    require(sum(t['numerical_status'] == 'NUMERICALLY_UNRESOLVED' for t in targets) == summary['unresolved_count'], 'Unresolved count differs.')
    archives = summary['archives']; archive_names = [r['file'] for r in archives]
    require(len(archive_names) == len(set(archive_names)), 'Duplicate archive filename.')
    groups = {name: {} for name in archive_names}
    for row in files:
        require(row['archive'] in groups, 'Unknown member archive.')
        integer(row['bytes'], 'member bytes', 0); groups[row['archive']][row['member']] = row
    require(sum(r['bytes'] for r in files) == summary['restored_bytes'], 'Restored byte count differs.')
    for desc in archives:
        require(str(relative_name(desc['file'])) == Path(desc['file']).name, 'Archive must be a flat file.')
        path = bundle/desc['file']; require(not path.is_symlink(), 'Archive cannot be a symlink.')
        require(path.stat().st_size == desc['bytes'] <= summary['maximum_archive_bytes'] and digest(path) == desc['sha256'], 'Archive SHA256/size differs: ' + desc['file'])
        expected = groups[desc['file']]
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist(); require(len(infos) == len(expected) == desc['members'] and set(i.filename for i in infos) == set(expected), 'ZIP inventory differs.')
            for info in infos:
                row = expected[info.filename]
                require(not info.is_dir() and stat.S_IFMT(info.external_attr >> 16) == stat.S_IFREG and info.file_size == row['bytes'], 'ZIP member type/size differs.')
                h = hashlib.sha256(); count = 0
                with archive.open(info) as stream:
                    for block in iter(lambda: stream.read(1024**2), b''):
                        h.update(block); count += len(block)
                        require(count <= row['bytes'], 'ZIP member exceeds its declared size.')
                require(count == row['bytes'] and h.hexdigest() == row['sha256'], 'ZIP member hash differs.')
    check_dependencies(summary['input_dependencies'], dependencies or {})
    return summary, inventory


def extract(bundle, destination, *, maximum_restored_bytes=8*1024**3):
    """Verify all compressed bytes before creating a fresh extraction tree."""
    bundle = Path(bundle).resolve(); destination = Path(destination).absolute()
    destination = destination.parent.resolve() / destination.name
    require(not destination.exists() and destination.parent.is_dir() and not destination.is_relative_to(bundle), 'Extraction requires a new destination outside the bundle.')
    integer(maximum_restored_bytes, 'restoration budget')
    # Budget checked before decompression; inventory/hash validation follows.
    require(read_json(bundle/'bundle.json')['restored_bytes'] <= maximum_restored_bytes, 'Restoration budget exceeded.')
    summary, inventory = verify(bundle)
    require(summary['restored_bytes'] <= maximum_restored_bytes, 'Restoration budget exceeded.')
    expected = {r['member']: r for r in inventory['files']}
    with tempfile.TemporaryDirectory(prefix='.restore_', dir=destination.parent) as name:
        stage = Path(name)
        for desc in summary['archives']:
            with zipfile.ZipFile(bundle/desc['file']) as archive:
                for info in archive.infolist():
                    row = expected[info.filename]; path = stage.joinpath(*relative_name(info.filename).parts)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info) as src, path.open('xb') as dst:
                        shutil.copyfileobj(src, dst, length=1024**2)
                    require(path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], 'Extraction bytes differ.')
        # Empty retired raw directory and transient lock can safely be recreated
        # by the driver; their absence does not change any archived artifact.
        require(not destination.exists(), 'Extraction destination appeared during operation.')
        os.rename(stage, destination)
    return dict(status='RESTORED_ALL_ARCHIVED_BYTES', files=summary['file_count'], targets=summary['target_count'], raw_arrays_restored=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('pack'); p.add_argument('--campaign', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    scope = p.add_mutually_exclusive_group()
    scope.add_argument('--engineering', action='store_true'); scope.add_argument('--fixed96', action='store_true')
    p.add_argument('--block-size', type=int, default=64); p.add_argument('--maximum-archive-bytes', type=int, default=MAX_ARCHIVE_BYTES)
    p.add_argument('--supplement', action='append', default=[], metavar='LABEL=PATH'); p.add_argument('--dependency', action='append', default=[], metavar='ROLE=PATH')
    p = commands.add_parser('verify'); p.add_argument('--bundle', type=Path, required=True); p.add_argument('--dependency', action='append', default=[], metavar='ROLE=PATH')
    p = commands.add_parser('extract'); p.add_argument('--bundle', type=Path, required=True); p.add_argument('--destination', type=Path, required=True); p.add_argument('--maximum-restored-bytes', type=int, default=8*1024**3)
    args = parser.parse_args()
    if args.command == 'pack':
        result = pack(args.campaign, args.output, engineering=args.engineering, fixed96=args.fixed96, block_size=args.block_size, maximum_archive_bytes=args.maximum_archive_bytes, supplements=named_paths(args.supplement), dependencies=named_paths(args.dependency))
        result = {k: result[k] for k in ('status', 'target_count', 'unresolved_count', 'file_count', 'restored_bytes', 'archive_bytes')}
        result['bundle_sha256'] = digest(args.output/'bundle.json')
    elif args.command == 'verify':
        result, _ = verify(args.bundle, dependencies=named_paths(args.dependency)); result = dict(status='ALL_ARCHIVED_BYTES_VERIFIED', targets=result['target_count'], files=result['file_count'], scientific_approval_inferred=False)
    else:
        result = extract(args.bundle, args.destination, maximum_restored_bytes=args.maximum_restored_bytes)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
