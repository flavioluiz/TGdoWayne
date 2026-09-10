#!/usr/bin/env python3
"""Gera metadados e quadro dos capítulos da dissertação a partir do estado editorial."""
import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTHS = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
          "agosto", "setembro", "outubro", "novembro", "dezembro")


def tex_escape(value):
    return "".join({"&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#",
                    "$": r"\$", "{": r"\{", "}": r"\}", "\\": r"\textbackslash{}",
                    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}.get(c, c)
                   for c in str(value))


def generated_files():
    status = json.loads((ROOT / "project_status.json").read_text())
    chapters = json.loads((ROOT / "latex/chapters.json").read_text())
    day = date.fromisoformat(status["updated_at"])
    metadata = "% Gerado por scripts/update_document_state.py; não editar manualmente.\n"
    values = {"VersaoTrabalho": status["latest_version"], "EtapaTrabalho": status["current_stage"],
              "DataTrabalho": f"{day.day} de {MONTHS[day.month-1]} de {day.year}"}
    metadata += "".join("\\newcommand{\\"+key+"}{"+tex_escape(value)+"}\n" for key, value in values.items())
    lines = ["% Gerado por scripts/update_document_state.py; não editar manualmente.",
             r"\chapter*{Estado dos capítulos}",
             r"\addcontentsline{toc}{chapter}{Estado dos capítulos}",
             r"O quadro descreve o conteúdo desta versão. Capítulos planejados ainda não",
             r"integram o corpo da dissertação e não são apresentados como resultados obtidos.",
             r"\begingroup\small\singlespacing",
             r"\begin{longtable}{@{}p{0.08\textwidth}p{0.55\textwidth}p{0.20\textwidth}p{0.08\textwidth}@{}}",
             r"\toprule Cap. & Conteúdo & Estado & Marco \\",
             r"\midrule\endhead"]
    for chapter in chapters:
        if chapter["status"] == "Concluído" and not (ROOT / chapter["source"]).is_file():
            raise ValueError("Capítulo declarado concluído sem fonte: " + chapter["source"])
        lines.append(" & ".join(tex_escape(chapter[k]) for k in ("number", "title", "status", "stage"))
                     + r" \\ \addlinespace[5pt]")
    lines += [r"\bottomrule\end{longtable}\endgroup",
              r"A introdução delimita as hipóteses e as condições de validação. A classificação",
              r"de um capítulo como concluído refere-se à entrega daquela etapa; revisões posteriores",
              r"serão incorporadas com rastreabilidade nos próximos releases.", ""]
    return {ROOT / "latex/metadados_dissertacao.tex": metadata,
            ROOT / "latex/estado_capitulos.tex": "\n".join(lines)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for path, expected in generated_files().items():
        if args.check:
            if not path.exists() or path.read_text() != expected:
                raise SystemExit(f"Estado editorial desatualizado: {path.relative_to(ROOT)}")
        else:
            path.write_text(expected)
    print("Metadados e estado dos capítulos " + ("conferidos." if args.check else "atualizados."))


if __name__ == "__main__":
    main()
