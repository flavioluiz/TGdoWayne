#!/usr/bin/env python3
"""Summarize all96 fixed targets only after the complete masked archive exists."""
from pathlib import Path
import argparse
import importlib
import importlib.util
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--module-path', type=Path, help='Explicit candidate during review; omit after integration.')
    for name in ['campaign', 'experiment', 'data', 'generation', 'numerical_protocol',
                 'scientific_protocol', 'synthesis_config', 'validation_evidence', 'output']:
        p.add_argument('--'+name.replace('_', '-'), type=Path, required=True)
    args = p.parse_args()
    sys.path.insert(0, str(args.project_root.resolve()/'src'))
    if args.module_path:
        spec = importlib.util.spec_from_file_location('inference.fixed_synthesis', args.module_path.resolve())
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module('inference.fixed_synthesis')
    from inference.campaign_io import sha256, write_json_new, write_npz_new
    from inference.iid_diagnostics import json_safe
    if args.output.exists():
        raise FileExistsError('Use a new synthesis directory; preserve previous records.')
    arrays, cfg, provenance = module.load_campaign(args.campaign, args.experiment, args.data,
        args.generation, args.numerical_protocol, args.scientific_protocol, args.synthesis_config,
        args.validation_evidence)
    report, intervals = module.synthesize(arrays, cfg)
    arrays.update(intervals)
    report.update(config=cfg, provenance=provenance)
    import inference.sbc_sensitivity as sensitivity
    import inference.diagnostics as diagnostics
    report['executed_source_sha256'] = {str(path): sha256(path) for path in
        [Path(__file__), Path(module.__file__), Path(sensitivity.__file__), Path(diagnostics.__file__)]}
    write_npz_new(args.output/'arrays.npz', **arrays)
    report['arrays_sha256'] = sha256(args.output/'arrays.npz')
    write_json_new(args.output/'summary.json', json_safe(report))
    lines = ['# Injeções fixas: síntese condicional', '', report['scope'], '',
        'Todos os96 alvos A0 foram retidos. Cada cenário contém32 realizações.', '',
        'Intervalos Clopper–Pearson são pontuais. As faixas de sensibilidade numérica usam '
        '0,002 + z×MCSE, alphaMC0,01/família576, com [0,1] para funções não resolvidas. '
        'Elas são aproximações condicionais, não certificados exatos. Não há teste KS ou de uniformidade.', '',
        '| Cenário | PITs aplicáveis | Estruturais | Numéricos não resolvidos |',
        '|---|---:|---:|---:|']
    lines += [f"| {r['id']} | {r['applicable_pits']} | {r['structural_pits']} | {r['unresolved_nonstructural_pits']} |"
              for r in report['scenarios']]
    lines += ['', 'Em u=0, [0,U90] cobre estruturalmente a verdade e o intervalo central a exclui. '
        'Na ausência de GW, massa/amplitude/inclinação e logL-na-verdade são indefinidos; '
        'seus quantis continuam apenas descritivos. Nenhuma cobertura nominal Bayes é exigida universalmente '
        'nos cenários fixos. Os detalhes por parâmetro e todos os IDs constam em summary.json/arrays.npz.']
    (args.output/'README.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(report['scope'] + ':96 targets preserved')


if __name__ == '__main__':
    main()
