#!/usr/bin/env python3
"""Compila o LaTeX ITA e prepara PDF e manifesto antes do commit de marco."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version")
    parser.add_argument("--document", choices=["proposta", "dissertacao"])
    parser.add_argument("--build-only", action="store_true", help="Compila em tmp sem alterar a versão publicada")
    args = parser.parse_args()
    status = json.loads((ROOT / "project_status.json").read_text())
    args.version = args.version or status["latest_version"]
    args.document = args.document or status["document"]
    if not re.fullmatch(r"v\d+\.\d+\.\d+", args.version):
        raise SystemExit("Versão inválida; use vMAJOR.MINOR.PATCH")
    if (args.version, args.document) != (status["latest_version"], status["document"]):
        raise SystemExit("Atualize project_status.json para o marco que será compilado.")
    tag_exists = subprocess.run(["git", "rev-parse", "--verify", f"refs/tags/{args.version}"],
                                cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if tag_exists and not args.build_only:
        raise SystemExit("Tag já existe. Use --build-only para conferir, ou publique uma nova versão.")
    if args.document == "dissertacao":
        subprocess.run([sys.executable, str(ROOT / "scripts/update_document_state.py"), "--check"], check=True)
    env = os.environ.copy()
    env["PATH"] = "/Library/TeX/texbin:" + env.get("PATH", "")
    for binary in ("latexmk", "pdflatex", "biber"):
        if not shutil.which(binary, path=env["PATH"]):
            raise SystemExit(f"Dependência ausente: {binary}. Consulte README.md.")
    env["TEXINPUTS"] = f'{ROOT}/templates/ita//:{ROOT}/latex//:' + env.get("TEXINPUTS", "")
    env["BIBINPUTS"] = f'{ROOT}/latex//:' + env.get("BIBINPUTS", "")
    epoch = datetime.fromisoformat(status["updated_at"]).replace(tzinfo=timezone.utc)
    env["SOURCE_DATE_EPOCH"] = str(int(epoch.timestamp()))
    env["FORCE_SOURCE_DATE"] = "1"
    build = ROOT / "tmp/latex" / args.document
    build.mkdir(parents=True, exist_ok=True)
    command = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
               "-pdflatex=pdflatex -no-shell-escape %O %S", f"-outdir={build}", f"{args.document}.tex"]
    subprocess.run(command, cwd=ROOT / "latex", env=env, check=True)
    log = (build / f"{args.document}.log").read_text(errors="replace")
    issues = [line for line in log.splitlines() if "Overfull \\" in line or
              re.search(r"(Citation|Reference).*undefined|There were undefined|Please.*rerun Biber", line)]
    if issues:
        raise SystemExit("Corrija antes da publicação:\n" + "\n".join(issues))
    pdf = build / f"{args.document}.pdf"
    if args.build_only:
        print(f"PDF de conferência: {pdf}")
        return
    release_dir = ROOT / "releases" / args.version
    if not (release_dir / "RELEASE_NOTES.md").exists():
        raise SystemExit("Crie as notas da versão antes de preparar o release.")
    dest = ROOT / status["latest_pdf"]
    if dest.parent != ROOT / "output/pdf" / args.version or dest.suffix != ".pdf":
        raise SystemExit("latest_pdf deve estar em output/pdf/<versão>/ e terminar em .pdf")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf, dest)
    external_assets = []
    distribution = ROOT / "results/C10/production_reproducibility/distribution.json"
    if distribution.exists():
        external_assets = json.loads(distribution.read_text())["assets"]
        for entry in external_assets:
            path = ROOT / entry["path"]
            if path.exists() and (path.stat().st_size != entry["bytes"] or digest(path) != entry["sha256"]):
                raise ValueError("External archive differs from its catalog: " + str(path))
    external_paths = {entry["path"] for entry in external_assets}
    files = [ROOT / p for p in ("README.md", "Makefile", ".gitignore", "project_status.json", "TG_Wayne.pdf")]
    files.extend(ROOT.glob("Template*.zip"))
    files.extend(p for p in (ROOT / "pyproject.toml", ROOT / "uv.lock", ROOT / "requirements.txt") if p.exists())
    for directory in ("latex", "scripts", "templates", "implementation_plan", "output/pesquisa", ".github", "docs", "literature",
                      "src", "tests", "configs", "results", "figures"):
        files.extend(p for p in (ROOT / directory).rglob("*") if p.is_file()
                     and "__pycache__" not in p.parts and p.name != ".DS_Store"
                     and not p.is_relative_to(ROOT / "literature/papers")
                     and str(p.relative_to(ROOT)) not in external_paths)
    files.append(release_dir / "RELEASE_NOTES.md")
    manifest = {
        "schema_version": 1, "version": args.version, "stage": status["current_stage"],
        "document": args.document, "source_entry": f"latex/{args.document}.tex",
        "pdf": str(dest.relative_to(ROOT)), "pdf_sha256": digest(dest),
        "date": status["updated_at"],
        "toolchain": {binary: subprocess.check_output([binary, "--version"], env=env, text=True).splitlines()[0]
                      for binary in ("pdflatex", "latexmk", "biber")},
        "external_assets": external_assets,
        "inputs_sha256": {str(p.relative_to(ROOT)): digest(p) for p in sorted(set(files))}
    }
    (release_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"PDF e manifesto preparados: {dest}")


if __name__ == "__main__":
    main()
