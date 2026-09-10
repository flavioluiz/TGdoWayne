# Validação de C06 / v0.6.0

Data: 10/09/2026. PDF cumulativo: **56 páginas A4**, 593060 bytes.
SHA-256: `3b23940ce8d8c5191d74651ed4698a8fa536ff93e421ff8afdae3fc366aeee4f`.

## Verificação científica e reprodução

Os três novos módulos do pacote PTA implementam o experimento Fourier periódico,
os estimadores quadráticos e a montagem auditada de matrizes. Os cinco módulos
científicos de C05 foram preservados. As convenções de PSD unilateral, unidades,
fases complexas, pseudocovariância e compressão são explicitadas no capítulo 5 e
no contrato de comparações.

Onze testes integrados passaram. Três campanhas foram executadas contra os arquivos
integrados ao repositório: massa positiva, GR e apenas ruído branco. Cada caso gerou
131072 realizações físicas e controles normais pareados, divididos em 128 blocos.
Os maiores desvios de momentos foram 3,502, 3,936 e 3,187 erros-padrão, abaixo do limiar
empírico predefinido de 6. O relatório não interpreta esse limiar como cobertura
simultânea rigorosa. Foram auditadas 605 avaliações de pares das matrizes distintas;
a maior discrepância de controles ORF foi 3,1131e-13.

`scripts/validar_simulador.py --check` reexecutou os 11 testes, conferiu hashes de
fontes/configurações/relatórios e regenerou as 32 amostras pequenas salvas em cada
caso, a partir do primeiro bloco e da semente. Uma cópia separada dos módulos,
testes, scripts e resultados passou a mesma conferência, verificando os caminhos
portáveis no mesmo sistema. As receitas completas estão em `docs/dados_sinteticos.md`.
Não se presume identidade binária de NPZ entre bibliotecas distintas.

Os 19 testes simbólicos C04 e os 23 testes C05 passaram; a procedência dos 58 casos
da campanha de ORFs também foi conferida. O workflow de publicação reexecuta as
baterias curtas e a conferência das evidências, incluindo a regeneração das amostras
C06. Não repete todos os grandes sorteios e integrais a cada release.

## Figura e acervo

O script da figura 5.1 gerou 65536 sorteios novos com a semente 2026091066.
O PDF vetorial e o JSON foram reproduzidos byte a byte após integrar o script.
Padronização teórica, denominador total dos histogramas e autos gaussianos negativos
foram preservados. O registro contém cumulantes, frações fora da janela, contagens,
versões e hashes. A figura demonstra a distribuição nesta configuração, sem testar
posteriors. O acervo local de 26 PDFs, 600 páginas, passou novamente a verificação
de tamanho e SHA-256; os quatro novos registros metodológicos distinguem preprint
e publicação editorial.

## Conferência editorial

Todas as 56 páginas foram renderizadas a 95 dpi com Poppler e inspecionadas. Capa,
resumo com palavras-chave, quadro de capítulos, sumário, cinco capítulos e referências
estão legíveis, sem sobreposição ou truncamento. A tabela dos momentos, figura 5.1
e equação 5.14 foram examinadas também em páginas individuais 50–52. Cabeçalhos
foram conferidos em ampliação e contra a camada textual do PDF. A compilação final
não contém caixas Overfull nem referências/citações indefinidas. O capítulo novo
possui 14 equações numeradas e cinco seções.

A introdução e as passagens dos capítulos anteriores foram atualizadas. README,
estado JSON e quadro editorial indicam C01–C06 concluídos e C07 em andamento.
O manifesto inclui fontes, configurações, relatórios, amostras pequenas e figuras.

## Alcance

A população é tensorial, isotrópica e gaussiana em coeficientes Fourier próprios.
Há covariância conhecida e ruído heterogêneo, sem ajuste de temporização ou janela
irregular. Os momentos quadráticos são exatos no experimento declarado; sua família
normal de inferência permanece uma aproximação a calibrar. Diferenças de momentos
entre B/C não são interpretadas como viés, KL, perda de informação ou cobertura.
C06 não apresenta posterior, SBC, restrição observacional ou detecção escalar.
