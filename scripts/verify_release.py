#!/usr/bin/env python3
"""Verifica versão, estado do README e hashes do PDF e de suas entradas."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def verify(version):
    if not re.fullmatch(r"v\d+\.\d+\.\d+", version):
        raise ValueError("Tag inválida")
    manifest = json.loads((ROOT / "releases" / version / "manifest.json").read_text())
    status = json.loads((ROOT / "project_status.json").read_text())
    roadmap = json.loads((ROOT / "implementation_plan/roadmap.json").read_text())
    if manifest["version"] != version or status["latest_version"] != version:
        raise ValueError("Versão não corresponde ao estado deste commit. Para versão antiga, faça checkout da tag.")
    if manifest["stage"] != status["current_stage"] or manifest["pdf"] != status["latest_pdf"]:
        raise ValueError("Manifesto e estado divergem")
    if manifest["document"] != status["document"]:
        raise ValueError("Tipo de documento diverge do estado")
    ids = [stage["id"] for stage in roadmap["stages"]]
    if status["completed_stages"] != ids[:ids.index(status["current_stage"]) + 1]:
        raise ValueError("Marcos concluídos devem formar um prefixo do roadmap")
    for stage in status.get("in_progress_stages", []):
        if stage not in ids or stage in status["completed_stages"]:
            raise ValueError("Marco em andamento inválido ou já concluído: " + stage)
    checks = {manifest["pdf"]: manifest["pdf_sha256"], **manifest["inputs_sha256"]}
    for relative, expected in checks.items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError(f"Arquivo ausente ou fora do projeto: {relative}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Hash divergente: {relative}")
    pdf = ROOT / manifest["pdf"]
    if not pdf.read_bytes().startswith(b"%PDF-"):
        raise ValueError("Arquivo não é PDF")
    subprocess.run([sys.executable, str(ROOT / "scripts/update_readme.py"), "--check"], check=True)
    if manifest["document"] == "dissertacao":
        subprocess.run([sys.executable, str(ROOT / "scripts/update_document_state.py"), "--check"], check=True)
        chapters = json.loads((ROOT / "latex/chapters.json").read_text())
        main = (ROOT / "latex/dissertacao.tex").read_text()
        for chapter in chapters:
            if (chapter["stage"] in status["completed_stages"]) != (chapter["status"] == "Concluído"):
                raise ValueError("Estado do capítulo diverge do marco: " + chapter["title"])
            if chapter["status"] == "Concluído":
                source = Path(chapter["source"])
                include = str(source.relative_to("latex").with_suffix(""))
                if chapter["stage"] not in status["completed_stages"] or not (ROOT / source).is_file():
                    raise ValueError("Capítulo concluído sem marco ou fonte: " + chapter["title"])
                if "\\input{" + include + "}" not in main:
                    raise ValueError("Capítulo concluído não incluído no documento: " + chapter["title"])
    print(f'{version}: PDF e {len(manifest["inputs_sha256"])} entradas conferidos.')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    verify(parser.parse_args().version)


if __name__ == "__main__":
    main()
