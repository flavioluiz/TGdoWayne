#!/usr/bin/env python3
"""Atualiza somente o painel de estado e roadmap do README, a partir dos JSONs."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- PROJECT_STATUS:START -->"
END = "<!-- PROJECT_STATUS:END -->"


def status_block():
    status = json.loads((ROOT / "project_status.json").read_text())
    roadmap = json.loads((ROOT / "implementation_plan/roadmap.json").read_text())
    stages = roadmap["stages"]
    current = next(s for s in stages if s["id"] == status["current_stage"])
    completed = status["completed_stages"]
    in_progress = status.get("in_progress_stages", [])
    paused = status.get("paused_stages", [])
    next_stage = next((s for s in stages if s["id"] not in completed), None)
    version = status["latest_version"]
    base = "https://github.com/flavioluiz/TGdoWayne/releases"
    pdf_name = Path(status["latest_pdf"]).name
    lines = [START, "## Estado atual", "",
        f'**{status["status_label"]}**', "",
        f'**Última etapa concluída:** {current["id"]} — {current["title"]}.', "",
        f'**Progresso:** {len(completed)} de {len(stages)} marcos concluídos.', "",
        f'**Próxima etapa:** {next_stage["id"] + " — " + next_stage["title"] if next_stage else "Todos os marcos planejados concluídos"}.', "",
        f'**Atualização:** {status["updated_at"]}.', "",
        f'**[Baixar o PDF mais recente — {version}]({base}/download/{version}/{pdf_name})** · '
        f'[Notas do release]({base}/tag/{version}) · '
        f'[PDF versionado no repositório]({status["latest_pdf"]})', "",
        "### O que já foi executado", ""]
    lines += ["- " + item for item in status["completed_work"]]
    lines += ["", "### O que está em andamento e o que falta", "", status["current_work"], "",
              "## Roadmap", "", "Cada linha corresponde a um commit de marco e a um PDF cumulativo. "
              "A primeira versão contém a proposta; de C02 em diante, a dissertação em desenvolvimento.", "",
              "| Etapa | Entrega | Versão do PDF | Estado | Plano do commit |",
              "|---|---|---|---|---|"]
    for stage in stages:
        state = ("Concluída" if stage["id"] in completed else "Pausada — draft" if stage["id"] in paused else "Em andamento" if stage["id"] in in_progress
                 else "Próxima — não iniciada" if stage == next_stage else "Planejada")
        lines.append(f'| {stage["id"]} | {stage["title"]} | `{stage["version"]}` | {state} | '
                     f'[Detalhes](implementation_plan/commits/{stage["plan_file"]}) |')
    lines += ["", "[Plano geral de execução](implementation_plan/README.md). "
              "O cronograma científico é de 24 meses; os marcos são liberados por critérios de conclusão, não só por data.", "", END]
    return "\n".join(lines)


def render_readme():
    path = ROOT / "README.md"
    text = path.read_text()
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    return before + status_block() + after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render_readme()
    path = ROOT / "README.md"
    if args.check:
        if path.read_text() != expected:
            raise SystemExit("README desatualizado: execute python3 scripts/update_readme.py")
        print("README consistente com o estado e o roadmap.")
    else:
        path.write_text(expected)
        print("Painel do README atualizado.")


if __name__ == "__main__":
    main()
