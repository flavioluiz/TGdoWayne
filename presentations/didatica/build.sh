#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p ../../tmp/beamer_didatica ../../output/pdf/didatica
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=../../tmp/beamer_didatica apresentacao.tex
cp ../../tmp/beamer_didatica/apresentacao.pdf ../../output/pdf/didatica/tg_wayne_para_nao_especialistas.pdf
