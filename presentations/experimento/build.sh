#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"
task_tmp="$PROJECT_ROOT/tmp/presentations/experimento/beamer"
mkdir -p "$task_tmp" "$PROJECT_ROOT/output/pdf/experimento"
python3 presentations/experimento/gerar_roteiro.py
latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir="$task_tmp" -jobname=experimento_codex presentations/experimento/experimento.tex
cp "$task_tmp/experimento_codex.pdf" "$PROJECT_ROOT/output/pdf/experimento/experimento_codex.pdf"
cp "$task_tmp/experimento_codex.pdf" "$PROJECT_ROOT/output/pdf/experimento/experimento_codex_7.pdf"
