#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export PROJECT_ROOT
: "${PRESENTATIONS_SKILL:?Defina o diretório da skill presentations}"
: "${RUNTIME_NODE_MODULES:?Defina o node_modules que contém @oai/artifact-tool}"
export PRESENTATIONS_SKILL RUNTIME_NODE_MODULES
export PYTHON_EXECUTABLE="${PYTHON_EXECUTABLE:-python3}"
NODE_EXECUTABLE="${NODE_EXECUTABLE:-node}"
SOFFICE_EXECUTABLE="${SOFFICE_EXECUTABLE:-soffice}"
task_tmp="$PROJECT_ROOT/tmp/presentations/experimento"
mkdir -p "$task_tmp/pdf" "$PROJECT_ROOT/output/pdf/experimento"
ln -sfn "$RUNTIME_NODE_MODULES" "$task_tmp/node_modules"
cp "$PROJECT_ROOT/presentations/experimento/build.mjs" "$task_tmp/build.mjs"
cd "$PROJECT_ROOT"
"$NODE_EXECUTABLE" "$task_tmp/build.mjs"
final_pptx="$(cat "$task_tmp/final-path.txt")"
cp "$final_pptx" "$PROJECT_ROOT/presentations/experimento/experimento_codex.pptx"
"$SOFFICE_EXECUTABLE" --headless --convert-to pdf --outdir "$task_tmp/pdf" "$PROJECT_ROOT/presentations/experimento/experimento_codex.pptx"
cp "$task_tmp/pdf/experimento_codex.pdf" "$PROJECT_ROOT/output/pdf/experimento/experimento_codex.pdf"
