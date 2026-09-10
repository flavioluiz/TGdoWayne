# Auditoria independente: Einstein linear e normalização da massa

Data da inspeção: 10/09/2026. Esta nota confirma o diagnóstico da leitura inicial das equações históricas e acrescenta uma verificação simbólica independente da conexão. Não modifica o TG, o artigo histórico, a parametrização da implementação ou a identificação de massas de uma ação não linear.

## Fontes e escopo realmente examinados

- `TG_Wayne.pdf`: páginas PDF 33–34, numeração impressa 23–24, Eqs. (4.8)–(4.22) e texto da velocidade imediatamente posterior. Inspeção visual dos PNGs `tg-33.png` e `tg-34.png`.
- de Paula, Miranda e Marinho, *Polarization States of Gravitational Waves with a Massive Graviton*, versão arXiv `gr-qc/0409041v1`, páginas PDF 3–4, Eqs. (4)–(13). Inspeção visual de `paper-03.png` e `paper-04.png`; [PDF primário consultado](https://arxiv.org/pdf/gr-qc/0409041v1).
- `src/polarizacoes/foundations.py` e a seção de Fierz–Pauli de [derivação geral](derivacao_geral.md): convenção de Riemann, vínculos de amplitude e sinal do termo de massa linear.

A conclusão abaixo deriva dessas equações. Não é uma declaração de errata editorial reconhecida, uma reconstrução variacional da ação completa, uma análise de estabilidade ou uma prova da equivalência não linear entre modelos. A nota da raiz sobre Visser não foi usada para compensar os coeficientes das outras fontes.

## Identidade geométrica e teste independente

A implementação adota assinatura `(+---)` e

```text
R^a_bcd = partial_c Gamma^a_db - partial_d Gamma^a_cb,
partial_a -> i q_a,
Box -> -q^a q_a.
```

Construímos a conexão linear a partir de uma amplitude simétrica com dez componentes independentes e de quatro componentes livres de `q_a`. A contração direta da conexão foi comparada à contração de Riemann da implementação, para `eta` e `-eta`. Nenhuma equação de propagação ou vínculo de polarização foi aplicado nessa comparação.

Com `hbar_mn = h_mn - eta_mn h/2` e `B_n = q^a hbar_an`, a identidade exata é

```text
G_mn = -Box hbar_mn / 2
       - (q_m B_n + q_n B_m) / 2
       + eta_mn q^a B_a / 2.
```

O teste também verifica `q^m G_mn = 0` antes de impor Lorenz. Sob `B_n=0`, portanto, `G_aqui = -Box hbar/2`. Inverter a convenção de Riemann inverte Ricci e Einstein: `G_histórico = +Box hbar/2`. A Eq. (10) do artigo de 2004 contém precisamente a ordem oposta de derivadas à usada pela implementação; as Eqs. (4.10) e (4.15) do TG são consistentes com esse sinal histórico.

A assinatura muda o sinal de `q^a q_a` e da representação de `Box` para uma mesma onda de Fourier. Ela não elimina o fator `1/2` de Einstein linear. Nas fórmulas desta nota `Box` é o operador de segunda ordem; o símbolo `Box²` impresso no TG designa esse d'Alembertiano e não sua composição de quarta ordem.

## Cadeia literal do TG

Se a Eq. (4.8) for linearizada exatamente como impressa, seu coeficiente é

```text
Tmass_mn = tau_TG hbar_mn,
tau_TG = -m_TG² c² / (8 pi G hbar_Planck²).
```

O uso de `kappa=8 pi G/c⁴`, `G_histórico=Box hbar/2` e `G=kappa Tmass` em vácuo produz

```text
(Box + 2 m_TG² / (hbar_Planck² c²)) hbar_mn = 0.
```

O fator dois está preservado nas Eqs. (4.17)–(4.19): não há uma discrepância interna de fator dois entre essas expressões e a Eq. (4.8). Porém, sob a interpretação explícita de `m_TG` como massa SI e `x⁰=ct`,

```text
[m_TG²/(hbar_Planck² c²)] = L⁻⁶ T⁴,
[(m_TG c/hbar_Planck)²]   = L⁻².
```

Falta uma potência `c⁴` no primeiro coeficiente relativamente ao segundo. Do mesmo modo, o `Tmass` literal do TG não tem dimensão de densidade de energia sob essa interpretação. Um sistema no qual o símbolo `m_TG` tenha sido previamente reescalado poderia mudar a leitura dimensional, mas essa reinterpretação exigiria uma definição explícita e uma tradução consistente da fórmula de velocidade. A fórmula posterior à Eq. (4.22), com `m_g² c⁴/(hbar_Planck² omega²)`, não pode simultaneamente usar a mesma massa SI e a identificação literal de `M²` em (4.19). Tomar `c=1` oculta a discrepância dimensional; também não resolve, por si só, a identificação numérica da massa.

## Cadeia literal do artigo de 2004

As Eqs. (4)–(5) usam `c⁶` no numerador de `Tmass`, restaurando a dimensão de densidade de energia:

```text
tau_2004 = -m_a² c⁶/(8 pi G hbar_Planck²).
```

A assinatura é `(-+++)`, e a Eq. (6) escreve `G=-kappa Tmass` em vácuo. Com a Eq. (10), a substituição resulta em

```text
(Box - 2 m_a² c²/hbar_Planck²) hbar_mn = 0.
```

Já a Eq. (12) imprime `Box hbar_mn - m² hbar_mn=0`, definindo `m²=m_a² c²/hbar_Planck²`. Há, assim, uma diferença algébrica de fator dois na cadeia literal das equações consultadas, quando o símbolo da massa é mantido. A mudança de assinatura justifica o sinal relativo à equação do TG; não justifica a remoção do dois.

Existem convenções capazes de produzir a Eq. (12), mas representam escolhas distintas: reduzir pela metade o coeficiente fonte mantendo a massa definida, ou interpretar a massa de dispersão por `m_disp²=2 m_a²` mantendo a cadeia literal. Aplicar ambas simultaneamente seria uma compensação dupla. Esta auditoria não escolhe uma correção histórica.

## Dinâmica FP da implementação

A equação apresentada em [derivação geral](derivacao_geral.md), nas convenções atuais,

```text
E_mn = G_mn^(1) - mu² (h_mn - eta_mn h)/2 = 0,
```

tem sinal e prefator consistentes. O teste independente verifica as identidades

```text
q^m E_mn = -mu² (q^m h_mn - q_n h)/2,
eta^mn E_mn = q^n(q^m h_mn - q_n h) + 3 mu² h/2.
```

Para `mu != 0`, a divergência impõe o vínculo; o traço então impõe `h=0`. Sobre a parametrização FP da implementação, `E_mn=(Delta-mu²)h_mn/2`, que é equivalente a `(Box+mu²)h_mn=0` para `(+---)`. Esses passos não autorizam dividir por `mu²` no caso estritamente sem massa.

## Formulação recomendada para a dissertação

“Adotamos a massa de dispersão `m_g`, definida operacionalmente por `omega_SI²=c²k²+(m_g c²/hbar_Planck)²`, e escrevemos `mu=m_g c/hbar_Planck`. As expressões geométricas do TG são reproduzidas em função de `omega` e `k`, com suas convenções explicitadas. A identificação dessa massa com parâmetros de ações históricas depende da normalização: a substituição literal das equações consultadas revela discrepâncias de unidades no TG e de fator dois no artigo de 2004, registradas sem alterar as fontes.”

Todas as tabelas e limites futuros em `eV/c²` devem usar essa massa operacional. Quando for necessário comparar à cadeia literal do artigo de 2004, registrar `m_disp=sqrt(2) m_a`; não usar essa tradução automaticamente para a Eq. (12) impressa, que já escolhe outra normalização. Para o TG, a dimensão exige primeiro esclarecer a definição dos símbolos; uma simples troca de nome não resolve o problema em SI.

## Artefatos e resultado

- `tests/test_normalizacao.py`: sete testes simbólicos independentes, incluindo comparação conexão/Riemann com ambas as assinaturas, identidade de Einstein e Bianchi, vínculo Visser, dinâmica FP, prefatores literais, dimensões SI e massa operacional.
- `results/C04/validacao.json`: **PASS**, 19 testes no registro integrado, sendo sete desta auditoria; zero falhas e zero erros, SymPy 1.14.0. A execução isolada dos sete testes levou aproximadamente 2,3 segundos.
- Comando executado a partir da raiz: `.venv/bin/python scripts/reproduzir_tg.py`.

O teste importa `src/polarizacoes/foundations.py` somente para os objetos a auditar e para a comparação; a conexão, Ricci e Einstein são construídos separadamente. As identidades dimensionais são verificadas com geradores independentes das dimensões de massa, comprimento e tempo. Os testes documentam consistência algébrica das convenções escolhidas; não fornecem validação observacional ou uma seleção empírica entre teorias.
