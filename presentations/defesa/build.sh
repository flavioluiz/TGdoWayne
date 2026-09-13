#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p ../../tmp/beamer_defesa ../../output/pdf/defesa
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=../../tmp/beamer_defesa defesa.tex
cp ../../tmp/beamer_defesa/defesa.pdf ../../output/pdf/defesa/defesa_mestrado_50min.pdf
