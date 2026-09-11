# Comandos de verificação e reprodução

Executar a partir da raiz do repositório. A primeira operação apenas lê arquivos:

```sh
.venv/bin/python - <<'PY'
from pathlib import Path
import hashlib, json
base = Path('results/C07/compact_archive_review/fixed96_extension')
m = json.loads((base/'manifest.json').read_text())
for row in m['files']:
    p = base/row['path']
    assert p.stat().st_size == row['bytes'], p
    assert hashlib.sha256(p.read_bytes()).hexdigest() == row['sha256'], p
print('Inventário documental verificado:', len(m['files']), 'arquivos')
PY
```

O comando ROOT que reproduz a suíte atual, se seus hashes coincidirem com os registrados, é:

```sh
.venv/bin/python -m unittest discover -s tests -p test_compact_archive.py -v
```

Para reproduzir os **snapshots v2** em isolamento, inclusive o ataque independente corrigido, sem gravar sobre registros históricos:

```sh
.venv/bin/python - <<'PY'
from pathlib import Path
import hashlib, json, shutil, subprocess, sys, tempfile
base = Path('results/C07/compact_archive_review/fixed96_extension').resolve()
m = json.loads((base/'manifest.json').read_text())
for row in m['files']:
    p = base/row['path']
    assert p.stat().st_size == row['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest() == row['sha256']
work = Path(tempfile.mkdtemp(prefix='c07_transport_replay_', dir='tmp')).resolve()
(work/'scripts').mkdir()
(work/'tests').mkdir()
review = work/'tmp'/'review'
review.mkdir(parents=True)
for source, target in (
    ('history/review_sources/v2_compactar_calibracao.py', work/'scripts'/'compactar_calibracao.py'),
    ('history/review_sources/v2_test_compact_archive.py', work/'tests'/'test_compact_archive.py'),
    ('history/independent_checks_v2.py', review/'independent_checks_v2.py'),
):
    shutil.copyfile(base/source, target)
commands = [
    [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_compact_archive.py', '-v'],
    [sys.executable, str(review/'independent_checks_v2.py')],
]
for i, cmd in enumerate(commands):
    run = subprocess.run(cmd, cwd=work, capture_output=True, text=True)
    (work/f'replay_{i}.txt').write_text(run.stdout + run.stderr)
    if run.returncode:
        raise SystemExit(f'Reprodução reprovada; registro preservado em {work}')
print('TOY de transporte concluído; novos registros em', work)
PY
```

Esses comandos não foram executados novamente durante a integração documental. A reprodução cria fixtures descartáveis de transporte, não simula o experimento PTA, não lê uma campanha ativa e não valida posteriores. Os snapshots `history/review_sources/compactar_calibracao.py`, `test_compact_archive.py` e `history/independent_checks.py` permitem reproduzir o achado anterior em uma árvore isolada análoga; seu resultado esperado contém T1 reproduzido, sem modificar a evidência histórica.

A verificação antiga de compatibilidade usou a operação de leitura:

```sh
.venv/bin/python scripts/compactar_calibracao.py verify --bundle tmp/c07_integrated_wide3_bundle
```

Esse último caminho é uma origem histórica e pode não existir em outro checkout. O JSON preservado documenta a verificação realizada; não constitui uma alegação de que o pacote de engenharia esteja incluído neste diretório.
