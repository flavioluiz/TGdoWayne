# Diretriz editorial para a dissertação final

Solicitação do usuário: apresentar um texto acadêmico autônomo, escrito para um
leitor humano, sem referências ao processo de desenvolvimento do repositório.

## Aplicação obrigatória na consolidação

- Retirar capa versionada, quadro de andamento, rótulos de draft e avisos de etapas futuras.
- Eliminar do texto, títulos, legendas e metadados PDF os identificadores C01–C13,
  commits, tags, releases e versões do próprio trabalho.
- Substituir nomes internos por referências aos capítulos ou por descrições científicas
  claras: estudo tensorial, robustez, extensão escalar e população ampliada.
- Reescrever históricos de execução como metodologia e resultados finais. Preservar
  limitações, falhas numéricas relevantes e decisões inconclusivas, sem narrar turnos,
  interrupções do ambiente, retomadas ou cronologia de commits.
- Transferir logs, caminhos internos, contagens operacionais sem interesse científico e
  notas de errata para a documentação técnica. Manter a formulação científica corrigida.
- Apresentar resumo, introdução, discussão e conclusões em linguagem acadêmica contínua,
  sem listas de entregas de engenharia.
- Conferir também textos embutidos nas figuras e tabelas geradas. Os nomes internos
  de arquivos podem permanecer no código, mas não devem aparecer para o leitor do PDF.
- Manter referências bibliográficas e a identificação científica dos conjuntos de dados;
  a reprodução técnica e seu histórico continuam disponíveis no repositório.

## Verificação final

Extrair e ler o texto do PDF final, inspecionar todas as páginas e procurar resíduos
de linguagem operacional. Conferir metadados, sumário, títulos e legendas. Uma busca
textual isolada não substitui a revisão editorial, porque nomes internos podem ter
sido apenas trocados por expressões igualmente artificiais.

A alteração integra a consolidação final; não exige um release intermediário.

## Identificação e template ITA

Usar as páginas nativas da classe `templates/ita/ita.cls` para mestrado.
Gráviton de Souza e Prof. Dr. Schrödinger GPT de Gotham são os nomes definitivos de autor e orientador escolhidos pelo
usuário; retirar os qualificadores pseudônimo e provisório. A banca inclui Emmy
Noether de Barros, Heisenberg da Silva, Planck de Oliveira e Autor do TG do Wayne. Não inventar data de
defesa, número de registro, assinatura ou aprovação.
