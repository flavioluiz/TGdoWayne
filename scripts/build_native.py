#!/usr/bin/env python3
"""Compile the optional C07 C++ kernel locally; preserve source and binary hashes.

No downloads, shell expansion, fast-math, or publication of machine binaries.
An existing cache entry must match its manifest; divergent bytes are preserved
and rejected. NumPy remains the reference implementation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(compiler=None, output_root=None):
    source = ROOT / 'src/inference/native/likelihood.cpp'
    if not source.is_file():
        raise FileNotFoundError(source)
    system = platform.system()
    if system not in ('Darwin', 'Linux'):
        raise RuntimeError('The native backend is supported on macOS/Linux; use NumPy on other systems.')
    command = shutil.which(compiler or 'c++')
    if command is None:
        raise FileNotFoundError('A local C++17 compiler is required for this optional backend.')
    compiler_path = str(Path(command).resolve())
    version = subprocess.check_output([compiler_path, '--version'], text=True).strip()
    flags = ['-O3', '-std=c++17', '-ffp-contract=off', '-fPIC',
             '-dynamiclib' if system == 'Darwin' else '-shared']
    recipe = {'source': str(source.relative_to(ROOT)), 'source_sha256': digest(source),
              'compiler': compiler_path, 'compiler_version': version, 'flags': flags,
              'system': system, 'machine': platform.machine(), 'byteorder': sys.byteorder}
    recipe_hash = hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest()
    directory = Path(output_root or ROOT / 'tmp/native').resolve() / recipe_hash[:24]
    library = directory / ('libpta_likelihood.dylib' if system == 'Darwin' else 'libpta_likelihood.so')
    manifest_path = directory / 'build_manifest.json'
    if library.exists() or manifest_path.exists():
        if not library.is_file() or not manifest_path.is_file():
            raise RuntimeError('Incomplete native cache preserved; inspect it or choose another output root.')
        saved = json.loads(manifest_path.read_text())
        if saved['recipe'] != recipe or saved['recipe_sha256'] != recipe_hash or saved['binary_sha256'] != digest(library):
            raise RuntimeError('Native cache differs from its source/build manifest; existing files were preserved.')
        return library, manifest_path
    directory.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='compile-', suffix=library.suffix, dir=directory, delete=False) as handle:
            temporary = Path(handle.name)
        subprocess.run([compiler_path, *flags, str(source), '-o', str(temporary)], check=True)
        if digest(source) != recipe['source_sha256']:
            raise RuntimeError('C++ source changed during compilation; binary not accepted.')
        binary_hash = digest(temporary)
        # Link creation is exclusive. Another process cannot be overwritten.
        os.link(temporary, library)
        record = {'recipe': recipe, 'recipe_sha256': recipe_hash,
                  'binary': library.name, 'binary_sha256': binary_hash,
                  'scope': 'Local compiled artifact only; numerical validation is separate.'}
        with manifest_path.open('x') as output:
            json.dump(record, output, indent=2)
            output.write('\n')
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return library, manifest_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', help='Local compiler executable; default c++.')
    parser.add_argument('--output-root', type=Path, help='Cache root; default tmp/native.')
    args = parser.parse_args()
    library, manifest = build(args.compiler, args.output_root)
    print(json.dumps({'library': str(library), 'manifest': str(manifest)}, indent=2))


if __name__ == '__main__':
    main()
