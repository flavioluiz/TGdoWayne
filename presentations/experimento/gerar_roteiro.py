"""Sincroniza roteiro e notas Beamer a partir de timing.json (biblioteca padrão)."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent

def tex_escape(text):
    chars = {'&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
             '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}',
             '^': r'\textasciicircum{}', '\\': r'\textbackslash{}'}
    return ''.join(chars.get(char, char) for char in text)

def clock(seconds):
    return f'{seconds // 60:02d}:{seconds % 60:02d}'

def main():
    data = json.loads((BASE / 'timing.json').read_text())
    slides = data['slides']
    assert sum(s['seconds'] for s in slides) == data['suggested_seconds']
    assert sum(not s['backup'] for s in slides) == data['main_slides']
    assert sum(s['backup'] for s in slides) == data['backup_slides']
    text = f'''# Roteiro da apresentação do experimento

{data['main_slides']} slides principais e {data['backup_slides']} de apoio. Duração sugerida: **{clock(data['suggested_seconds'])}**, incluindo a abertura da discussão. Público: pós-graduação, sem pressupor conhecimento de ondas gravitacionais.

O roteiro orienta a fala, sem leitura literal dos slides. Os tempos são sugestões, sem ensaio cronometrado. As notas Beamer ficam em `notas.tex`, ocultas no PDF da audiência.

## Ritmo e adaptações

- **20 minutos:** usar os 12 slides, reduzindo as pausas de discussão. Reservar cerca de um minuto para o encerramento e resumir em um minuto cada os slides 8, 9 e 10.
- **25 minutos:** seguir os tempos abaixo, com espaço para a pergunta inicial e a abertura do debate no slide 12.
- **30 minutos:** acrescentar cinco minutos à discussão final.
- **Apoio:** slides 13–15, sobre métricas, custos e acesso às fontes, fora do tempo principal.

## Sequência e fala sugerida

'''
    notes = ['% Gerado por gerar_roteiro.py a partir de timing.json.\n% Notas ocultas no PDF da audiência.\n']
    elapsed = 0
    for slide in slides:
        title = slide['title'].replace('\n', ' ')
        text += f"### {slide['slide']}. {title}\n\n"
        if slide['backup']:
            text += 'Apoio opcional.\n\n'
        else:
            text += f"{clock(elapsed)}–{clock(elapsed + slide['seconds'])} ({slide['seconds']} s)\n\n"
            elapsed += slide['seconds']
        text += slide['note'] + '\n\n**Fontes:** ' + slide['source'] + '\n\n'
        notes.append(r'\expandafter\def\csname fala' + str(slide['slide']) +
                     r'\endcsname{' + tex_escape(slide['note']) +
                     r'\par Fontes: ' + tex_escape(slide['source']) + '}\n')
    (BASE / 'roteiro.md').write_text(text.rstrip() + '\n')
    (BASE / 'notas.tex').write_text('\n'.join(notes).rstrip() + '\n')

if __name__ == '__main__':
    main()
