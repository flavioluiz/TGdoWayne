#!/usr/bin/env python3
"""Baixa ou verifica PDFs do catálogo versionado, sem redistribuí-los no Git."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import urllib.request


def validate_record(record: dict, root: Path) -> Path:
    aid = record["arxiv_id"]
    version = record["version"]
    if not re.fullmatch(r"(?:\d{4}\.\d{4,5}|[a-z][a-z0-9.-]*/\d{7})", aid):
        raise ValueError("Identificador arXiv inválido")
    if not re.fullmatch(r"v[1-9]\d*", version):
        raise ValueError("Versão arXiv explícita obrigatória")
    if record["pdf_url"] != f"https://arxiv.org/pdf/{aid}{version}":
        raise ValueError("URL não corresponde ao identificador e à versão")
    expected_path = f"literature/papers/{aid.replace('/', '_')}{version}.pdf"
    if record["local_path"] != expected_path:
        raise ValueError("Destino não corresponde ao caminho padronizado da biblioteca")
    if not re.fullmatch(r"[0-9a-f]{64}", record["sha256"]):
        raise ValueError("SHA-256 inválido")
    if not isinstance(record["size_bytes"], int) or record["size_bytes"] <= 0:
        raise ValueError("Tamanho inválido")
    destination = (root / expected_path).resolve()
    destination.relative_to(root / "literature" / "papers")
    return destination


def validate_content(content: bytes, record: dict) -> None:
    if not content.startswith(b"%PDF"):
        raise ValueError("Conteúdo não é PDF")
    if len(content) != record["size_bytes"]:
        raise ValueError("Tamanho diverge do catálogo")
    if hashlib.sha256(content).hexdigest() != record["sha256"]:
        raise ValueError("SHA-256 diverge do catálogo")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Raiz do repositório; por padrão, pai da pasta scripts.")
    parser.add_argument("--catalog", type=Path,
                        help="Catálogo alternativo; padrão: literature/catalog.json na raiz.")
    parser.add_argument("--verify", action="store_true",
                        help="Verifica somente PDFs locais; não acessa a rede.")
    args = parser.parse_args()
    root = args.root.resolve()
    catalog_path = args.catalog if args.catalog else root / "literature" / "catalog.json"
    try:
        records = json.loads(catalog_path.read_text(encoding="utf-8"))["papers"]
        destinations = [validate_record(record, root) for record in records]
        if len(set(destinations)) != len(destinations):
            raise ValueError("Catálogo contém destinos duplicados")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Catálogo inválido: {error}", file=sys.stderr)
        return 1
    failures = []
    for record, destination in zip(records, destinations):
        try:
            if destination.exists():
                content = destination.read_bytes()
                validate_content(content, record)
            elif args.verify:
                raise FileNotFoundError(destination)
            else:
                request = urllib.request.Request(record["pdf_url"], headers={"User-Agent": "TGdoWayne bibliography downloader"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    content = response.read()
                validate_content(content, record)
                destination.parent.mkdir(parents=True, exist_ok=True)
                temporary_path = None
                try:
                    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
                        temporary_path = Path(temporary.name)
                        temporary.write(content)
                    temporary_path.replace(destination)
                finally:
                    if temporary_path is not None:
                        temporary_path.unlink(missing_ok=True)
            print(f"OK {record['arxiv_id']}{record['version']}")
        except (OSError, ValueError) as error:
            failures.append(f"{record.get('key', '?')}: {error}")
    for failure in failures:
        print(failure, file=sys.stderr)
    print(f"{len(records) - len(failures)}/{len(records)} PDFs verificados")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
