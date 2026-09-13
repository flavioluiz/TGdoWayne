"""Regenerate selected central illustrations in the clean export and compare pixels.

Rendering equivalence complements numerical replay; it is not a substitute for it.
Historical PDFs in the repository are never overwritten.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clean-root', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    clean = args.clean_root.resolve()
    out = clean / 'tmp/c13_figure_table_replay'
    out.mkdir(exist_ok=False)
    jobs = [
        ('scripts/figuras_orf.py', []),
        ('scripts/figuras_simulacao.py', []),
        ('scripts/figura_validacao_inferencia.py', []),
        ('scripts/figuras_populacao_escalar_c10.py', []),
        ('scripts/figura_fisher_escalar_c10.py', []),
        ('scripts/figuras_resultados_c11.py', []),
        ('scripts/tabelas_populacao_escalar_c10.py', []),
        ('scripts/figuras_calibracao.py', ['--summary', 'results/C07/synthesis/summary.json',
         '--arrays', 'results/C07/synthesis/arrays.npz', '--output', str(out/'sbc_figures')]),
        ('scripts/tabelas_calibracao.py', ['--summary', 'results/C07/synthesis/summary.json',
         '--arrays', 'results/C07/synthesis/arrays.npz', '--output', str(out/'sbc_tables')]),
        ('scripts/tabelas_injecoes_fixas.py', ['--summary', 'results/C07/fixed_synthesis/summary.json',
         '--arrays', 'results/C07/fixed_synthesis/arrays.npz', '--output', str(out/'fixed_tables')]),
    ]
    runs = []
    for index, (worker, arguments) in enumerate(jobs):
        receipt = out/f'io_{index}.json'
        assert (root/worker).read_bytes() == (clean/worker).read_bytes()
        with (out/f'job_{index}.log').open('w') as log:
            subprocess.run([sys.executable, str(root/'scripts/executar_isolado_c13.py'),
                            '--original-root', str(root), '--clean-root', str(clean),
                            '--receipt', str(receipt), worker, *arguments],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        runs.append(json.loads(receipt.read_text()))
        print(f'Completed {worker}', flush=True)
    figure_paths = ['figures/C05/orf_limites.pdf', 'figures/C06/nao_normalidade.pdf',
                    'figures/C07/cubatura_convergencia.pdf', 'figures/aplicacao/resultados.pdf']
    figure_paths += [f'figures/escalar/{name}.pdf' for name in
                     ('sbc_ecdf', 'falsos_positivos', 'recuperacao_deteccao', 'fisher_compressao')]
    pairs = [(path, clean/path) for path in figure_paths]
    pairs += [(f'figures/C07/synthesis/ecdf_{model}.pdf', out/f'sbc_figures/ecdf_{model}.pdf')
              for model in ('A0_CN', 'A_G', 'B_G', 'A_CN', 'B_CN')]
    pairs += [('results/C07/synthesis_tables/tabelas.tex', out/'sbc_tables/tabelas.tex'),
              ('results/C07/fixed_tables/tabelas.tex', out/'fixed_tables/tabelas.tex')]
    pairs += [(str(p.relative_to(root)), clean/p.relative_to(root))
              for p in sorted((root/'figures/escalar').glob('tabela_*.tex'))]
    compared = []
    for index, (original, reproduced) in enumerate(pairs):
        source = root/original
        digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        row = dict(original=original, reproduced=str(reproduced.relative_to(clean)),
                   original_sha256=digest(source), reproduced_sha256=digest(reproduced))
        if source.suffix == '.pdf':
            images = []
            for label, pdf in [('old', source), ('new', reproduced)]:
                prefix = out/f'render_{index}_{label}'
                subprocess.run(['pdftoppm', '-singlefile', '-r', '120', '-png', str(pdf), str(prefix)],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                images.append(prefix.with_suffix('.png'))
            from PIL import Image, ImageChops
            with Image.open(images[0]) as a, Image.open(images[1]) as b:
                row['pixels_identical'] = a.size == b.size and ImageChops.difference(a.convert('RGB'), b.convert('RGB')).getbbox() is None
            row['passed'] = row['pixels_identical']
        else:
            row['bytes_identical'] = source.read_bytes() == reproduced.read_bytes()
            row['passed'] = row['bytes_identical']
        compared.append(row)
    result = dict(scope='Regenerated figures and tables from retained numerical inputs in clean export; PDF metadata excluded by raster comparison.',
                  runs=runs, comparisons=compared, passed=all(r['passed'] for r in compared))
    target = root/'results/C13/figure_table_replay.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'], products=len(compared))), flush=True)
    if not result['passed']:
        raise SystemExit('Inspect nonidentical rendered products; do not infer scientific mismatch from layout alone.')


if __name__ == '__main__':
    main()
