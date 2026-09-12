# C11 — Decisão de aplicação

Decisão registrada em 12/09/2026, antes da execução física do piloto C11.

Adota-se a extensão periódica simulada com geometria pública MeerKAT, comparando P12K4 e P16K8 aninhados. Tempos de chegada públicos existem; a limitação local é a ausência de um adaptador validado de timing, janela irregular e ruído para a verossimilhança desta pesquisa. Não se declara ausência de dados nem se reconstrói informação espectral a partir de produtos comprimidos. Distâncias, amplitudes e ruídos serão sintéticos. Nenhuma restrição observacional será atribuída a essa extensão.

Os registros NANOGrav timing v2.1.0 e KDE v2.0.0 foram reconferidos em 12/09/2026 nas páginas primárias abaixo. A reconferência web MeerKAT/DataCite falhou; sua licença e geometria permanecem apoiadas na evidência local obtida em 10/09/2026, sem alegar nova verificação. A auditoria original e seus limites seguem preservados abaixo. O piloto não autoriza automaticamente a campanha estatística.

---

# C11 — Viabilidade de aplicação a produtos públicos de PTA

Consulta: **10 de setembro de 2026**. Parecer preparatório; nenhuma observação foi submetida ao simulador, a uma verossimilhança ou a inferência. Este documento não conclui C11 nem antecipa sua decisão formal de ramo. Foram lidos `implementation_plan/commits/C11_aplicacao.md`, `docs/contrato_comparacoes.md`, a configuração integrada C06 e o estudo temporário de custo de uma população de 12 pulsares.

**Recomendação condicional:** manter a extensão simulada como ramo executável com o contrato atual. Uma aplicação observacional é possível em princípio com TOAs públicos, mas depende de implementar e validar a amostragem, o ajuste de timing e o ruído do conjunto escolhido. EPTA DR2new é um candidato inicial manejável para essa preparação; NANOGrav15 é uma alternativa com documentação e produtos derivados mais amplos. A recomendação não decorre de ausência de dados públicos, nem de impossibilidade física de aplicar o método.

## 1. Evidência e limite de aquisição

O teto autorizado foi **20.000.000 bytes**, sem baixar conjuntos gigantes. `evidence/download_manifest.json` registra URLs, datas UTC, bytes e SHA-256 dos conteúdos adquiridos; `evidence/meerkat_head.json` registra consultas HEAD, sem corpos de dados. `audit_summary.json` contém o balanço final e hashes dos documentos locais utilizados.

Foram adquiridos metadados oficiais, documentação, dois notebooks e um arquivo de código apenas para leitura; nenhum código externo foi executado. O único pacote completo de observações transferido foi o `partim.tar.gz` MeerKAT, de 7.283.924 bytes: inspecionaram-se o inventário e os nomes das opções dos arquivos `.par`; não se calcularam resíduos, espectros ou estatísticas dos TOAs. O ZIP EPTA foi consultado por intervalos HTTP: diretório central e cinco pequenos arquivos de documentação/configuração. Não se baixou seu corpo completo. Arquivos grandes NANOGrav/IPTA, cadeias e vídeos não foram transferidos.

Há três níveis de evidência: **conteúdo conferido** em arquivo pequeno; **conteúdo declarado** pelo depositante, sem inspeção de todo o pacote; e **não estabelecido** nesta auditoria. Ausência em um inventário específico não prova ausência em todos os canais de uma colaboração. As falhas de acesso ao GitLab IN2P3 foram contornadas pela distribuição oficial Zenodo; não são tratadas como inexistência de dados.

## 2. Produtos identificados

| Produto/versionamento conferido | Conteúdo e custo de transferência | Licença declarada | Adequação imediata ao contrato atual |
|---|---|---|---|
| NANOGrav15 timing **v2.1.0**, 17/07/2025, DOI 16051178 | TOAs/modelos; resíduos e matrizes de parâmetros; 638.719.668 B | CC-BY-4.0 | Insumos para reconstrução observacional; não é vetor `q_n` próprio independente |
| NANOGrav15 KDE **v2.0.0**, 07/08/2026, DOI 21844115 | Densidades espectrais e frequências; 2.975.291 B | CC-BY-4.0 | Não recupera A0 nem A; uso limitado como referência de modelo compatível |
| `nanograv/15yr_stochastic_analysis`, commit `a3e8b8776a646208ca2d307f83c20bc70e029933` | Receitas de figuras, cadeias externas e estatística ótima; repositório consultado por arquivos | MIT no repositório | Ajuda a reproduzir um benchmark; não torna produtos resumidos equivalentes aos dados originais |
| MeerKAT PTA **4,5 anos/DR2**, DOI `10.57891/j0vh-5g31`, documentação 01/11/2024 | `partim`: 7.283.924 B; arquivos de perfis: 867.068.478 B; retratos: 3.922.099 B | CC-BY-4.0 via DataCite | TOAs/modelos disponíveis; configuração completa da análise estocástica ainda precisa ser estabelecida |
| EPTA DR2 **v2.1**, DOI 8300645 | ZIP 39.275.794 B; TOAs, modelos, relógios e configurações de ruído | CC-BY-4.0 | Candidato para construir um novo modelo observacional consistente |
| EPTA GWB, **v2.0**, DOI 8091568 | `chains.zip`, 649.471.499 B | CC-BY-4.0 | Cadeias condicionadas à análise publicada; não substituem TOAs nem fornecem A0 |
| IPTA **DR2 final**, commit `96a7c69caaf5da5cd22532784a3063b98b500dbe` | Combinações VersionA/VersionB e relógios; tamanho total não apurado | Licença não identificada na API, raiz e READMEs examinados | Reconstrução possível em princípio; preparação menos delimitada nesta auditoria |

Os identificadores abreviados DOI NANOGrav/EPTA correspondem a `10.5281/zenodo.<identificador>`. Fontes primárias: [NANOGrav timing](https://zenodo.org/records/16051178), [KDE](https://zenodo.org/records/21844115), [repositório oficial NANOGrav](https://github.com/nanograv/15yr_stochastic_analysis/tree/a3e8b8776a646208ca2d307f83c20bc70e029933), [MeerKAT/Data Central](https://docs.datacentral.org.au/meerkat-pulsar-timing-array/45-year/accessing-the-data/), [licença e descrição DataCite](https://api.datacite.org/dois/10.57891/j0vh-5g31), [EPTA dados](https://zenodo.org/records/8300645), [EPTA cadeias](https://zenodo.org/records/8091568), [IPTA oficial](https://ipta4gw.org/data-release/).

O acesso consultado é público e não apresentou cobrança de aquisição. Isso não mede tempo de CPU, memória, manutenção de ambiente ou trabalho de validação. A licença do repositório de código não deve ser estendida automaticamente a arquivos externos ligados por ele. A licença não estabelecida do IPTA deve ser resolvida antes de redistribuir seus arquivos; não se infere proibição de leitura a partir desse silêncio.

### 2.1 NANOGrav: distinguir quatro tipos de matriz/produto

A distribuição atual contém narrowband e wideband `.tim/.par`, relógios, parâmetros de ruído e cadeias; v2 acrescentou correlações entre **parâmetros de timing**, e v2.1 acrescentou resíduos narrowband pós-ajuste, completos ou por época, embranquecidos ou não. Os arquivos de correlação em TXT/NPZ/HDF5 não são, só por seu nome, a covariância conjunta pulsar–frequência. O README declara PINT 0.9.1 e tempo2 2022.01.1 na análise original; reproduzir o benchmark exige fixar também relógios e convenções. Essa caracterização é documental: o tarball não foi inspecionado integralmente. [Registro v2.1.0](https://zenodo.org/records/16051178).

Nos notebooks oficiais da Figura 1 conferidos, `upper_left.ipynb` usa 30 frequências `n/Tspan`, com `Tspan=505861299.1401644 s`, e cadeias de **amplitudes espectrais** `gw_hd_log10_rho_i`; `lower_right.ipynb` usa sete parâmetros de uma ORF spline. São produtos condicionados ao modelo de inferência. O arquivo `optimal_statistic_covariances.py` calcula covariâncias de estimadores da estatística ótima; sua existência não comprova uma matriz numérica conjunta de todos os coeficientes observados e frequências. O README distingue dados completos de publicação e dados reduzidos dos tutoriais. [Receita fixada por commit](https://github.com/nanograv/15yr_stochastic_analysis/tree/a3e8b8776a646208ca2d307f83c20bc70e029933/data_release/figure_1), [README oficial](https://github.com/nanograv/15yr_stochastic_analysis/blob/a3e8b8776a646208ca2d307f83c20bc70e029933/README.md).

O KDE atual fornece `density.npy`, `freqs.npy`, grade de amplitudes, rótulos e metadados de análises CURN/HD. A revisão de 07/08/2026 declara correção de posteriors afetados por um erro no temperamento paralelo do PTMCMCSampler, além de indicar exceções às reexecuções. Deve-se verificar a análise e versão concreta antes de usar qualquer cadeia/KDE como referência. A descrição do pacote não autoriza generalizar o erro a todos os resultados PTA. Mesmo corrigidos, log-densidades marginais de potência não recuperam fases complexas, autos, covariância de amostragem nem uma resposta dispersiva arbitrária. [Descrição e histórico v2.0.0](https://zenodo.org/records/21844115).

### 2.2 MeerKAT: 32 canais de rádio não são 32 frequências gravitacionais

O pacote `partim` inspecionado tem exatamente 83 `.par` e 83 `.tim`, sem outro arquivo regular. Nos `.par` constam modelo determinístico, opções de relógio/efeméride e termos como DM, derivadas, FD e JUMP; não constam palavras EFAC/EQUAD/ECORR ou uma configuração de red noise estocástico. Isso não implica inexistência desses ruídos: implica que **este pacote** não especifica sozinho a análise estocástica completa. Os inventários e o esquema estão em `evidence/meerkat_partim_*.json`. [Aquisição oficial](https://docs.datacentral.org.au/meerkat-pulsar-timing-array/45-year/accessing-the-data/).

A descrição DataCite fornece 32 sub-bandas da emissão de rádio. São frequências eletromagnéticas usadas no tratamento cromático; não correspondem aos modos nHz da série temporal. A caracterização de ruído considera processos brancos, vermelhos, DM, espalhamento e vento solar. O artigo de cartografia trabalha nos três primeiros canais gravitacionais mais sensíveis e distingue covariância dos resíduos de covariância entre estimadores de pares. Essas derivações não demonstram que todas as respectivas matrizes estejam depositadas como produtos reutilizáveis. [Registro DataCite](https://api.datacite.org/dois/10.57891/j0vh-5g31), [Miles et al., seções 2–4](https://arxiv.org/html/2412.01148v1), [Grunthal et al., seções 2, 3.5 e Apêndice A](https://arxiv.org/html/2412.01214v1).

O suplemento de anisotropia tem 443.539.544 B segundo HEAD; sua descrição destaca vídeos de mapas e regularização. Não foi baixado, e não se certifica que forneça coeficientes ou covariância conjunta. Uma figura/vídeo de um mapa não os substitui. O artigo de mapas usa o modelo conservador ALT: reproduzi-lo exige obter sua receita precisa, não apenas inserir parâmetros determinísticos dos `.par`. O portal oficial consultado lista releases de 2,5 e 4,5 anos; a inspeção não é garantia de inexistência de qualquer outro produto posterior. [Portal MPTA](https://mpta-gw.github.io/data.html), [artigo de mapas](https://arxiv.org/html/2412.01214v1).

### 2.3 EPTA e IPTA: melhores insumos não dispensam a transformação observacional

O inventário parcial remoto EPTA foi completado pelo diretório central: 2.931 entradas. Há TOAs, modelos, relógios, 112 JSONs e quatro subconjuntos `DR2full`, `DR2new` e versões `+` com InPTA. Foram lidos README e configurações `red_dict`, `dm_dict`, `chrom_dict` e um arquivo de ruído de DR2new. O README identifica números de modos ótimos até `N/T` e recomenda versões modificadas de `enterprise`/`enterprise_extensions`; também registra um relógio NRT corrigido e scripts ainda por acrescentar naquela distribuição. Não foi encontrado um produto anunciado como vetor Fourier observado com sua covariância conjunta. A identificação dos insumos de ruído é concreta; a reconstrução integral da análise não foi executada. [Distribuição EPTA v2.1](https://zenodo.org/records/8300645), [documentação oficial](https://epta.pages.in2p3.fr/epta-dr2/dr2.html).

O índice oficial IPTA continua apontando DR2. O README final distingue VersionA, com modelos/ruídos herdados, de VersionB, com parâmetros brancos e vermelhos estimados na combinação. Essas letras não têm relação com nossas análises A/B. O índice VersionB contém diretórios por pulsar, mas não foi percorrido integralmente. A API informa `license=null`; os READMEs consultados não trazem concessão explícita. Trata-se de uma limitação documental delimitada. Combinar IPTA com componentes NANOGrav/EPTA sem verificar sobreposição também reutilizaria observações: não se deve tratá-los como experimentos independentes. [IPTA DR2](https://ipta4gw.org/data-release/), [repositório fixado](https://gitlab.com/IPTA/DR2/-/tree/96a7c69caaf5da5cd22532784a3063b98b500dbe/release).

## 3. Mapeamento necessário para A0/A/B/C

Esta seção é uma consequência matemática do contrato local, não uma alegação sobre produtos ocultos das colaborações.

No experimento atual, os `q_n` são realizações **latentes diretamente observadas por definição**, CN próprias e independentes entre modos. Um PTA real observa TOAs irregulares, afetados por ajuste temporal e ruídos cromáticos. Coeficientes de uma base Fourier usados como variáveis latentes por `enterprise` não são automaticamente observações independentes com a distribuição de A0.

Um modelo observacional mínimo teria, esquematicamente,

`d = M δξ + F a + n`,

com datas, frequências de rádio, flags instrumentais e incertezas efetivas documentadas. `M` representa derivadas do modelo temporal e `F` a base amostrada nas datas reais. A marginalização de `a` e dos parâmetros lineares de timing produz uma verossimilhança dos resíduos com covariância `K(θ)`. É necessário conservar a mesma janela, projeção e modelo de ruído em todas as análises.

Por exemplo, seja `GᵀM=0` uma base fixa do complemento do modelo linearizado e `D` uma transformação complexa fixa. Então, para `q_tilde = D Gᵀ d` e covariância real dos TOAs `K`,

`C_tilde = D Gᵀ K G D†`,

`P_tilde = D Gᵀ K G Dᵀ`.

Em geral surgem correlações entre frequências e `P_tilde ≠ 0`. Não se obtém independência por realizar uma DFT ou por escolher frequências `n/T`. Se houver redução de posto, trabalha-se no suporte de dimensão correta; uma diagonal artificial não restaura a informação projetada. A covariância de parâmetros ajustados, uma cadeia posterior e `C_tilde` são objetos diferentes.

| Análise | Produto necessário na aplicação | O que os produtos públicos auditados permitem |
|---|---|---|
| A0 observacional | Verossimilhança temporal ou dos coeficientes transformados, com janela, normalização, `C` e pseudocovariância `P` corretas | Reconstruível em princípio de TOAs/modelos/ruído; o backend atual precisa ser estendido |
| A | Mesma transformação dos dados; Re/Im dos pares e autos por frequência; momentos com todos os acoplamentos | Pode ser construída após essa extensão; não a partir de KDEs ou splines de ORF |
| B | Um `W` fixado antes da análise, aplicado ao A reconstruído | `W μ` e `W Σ Wᵀ` permanecem válidos; a soma apenas dos blocos diagonais não |
| C_full | Exatamente o vetor observado de B; substituir apenas a resposta por `Γ(f_ref)` e recalcular média e covariância | Exige o mesmo modelo observacional; não equivale a ajustar uma curva angular publicada |
| C_beta | Mesmo B; congelar β, conservar fases físicas por frequência e todo o restante | Precisa de suporte de frequência e distâncias definidos de modo consistente |
| Controle normal G | Simulações normais com os mesmos momentos | Continua sendo outro experimento; não transforma dados reais em normais |

Para observações reais gaussianas `x` e formas quadráticas simétricas `J_i`, os momentos são `μ_i=tr(J_i K)` e `Σ_ij=2tr(J_i K J_j K)`. Alternativamente usa-se a representação real completa de `C_tilde,P_tilde`. Reutilizar cegamente a fórmula complexa própria, sem o fator dois da representação real, seria um erro. Os estimadores quadráticos continuam não gaussianos, portanto A/B físicas exigem sua própria calibração.

O ruído precisa incluir as escolhas pertinentes ao conjunto: EFAC/EQUAD/ECORR e agrupamento por época, ruído vermelho individual, componentes cromáticos e eventos determinísticos, além das opções de relógio/efeméride. Congelar uma média posterior de ruído como se fosse conhecida pode ser um estudo condicional, desde que declarado e calibrado; não reproduz marginalização conjunta. Resíduos embranquecidos ou médias por época também exigem a transformação correspondente, não podem ser tratados como TOAs originais.

## 4. Limites concretos do estudo de 12 pulsares/quatro canais

`tmp/c06_design/orf_table_cost.json` descreve **um estudo temporário de custo**, com 12 pulsares, quatro frequências, `T=4,5 anos`, distâncias entre **300 e 1.000 anos-luz**, e máximo `fL/c=888,8889`. Não são 300–1.000 parsecs. O próprio resultado recusa a interpolação linear testada: erro máximo ≈0,01116. A comparação independente de um par não certifica toda uma tabela interpolada, nem uma população real.

O C06 integrado é ainda outro experimento: **10 pulsares, três canais, 15 anos, 100–300 anos-luz**, portanto `max(fL/c)=60`. Sua validação de momentos não mede cobertura ou inferência em uma população observada. A bateria C05 também contém casos isolados de fase maior; sucesso em pontos selecionados não constitui certificação uniforme em geometria, massa, distâncias e frequências.

A dimensão sem unidade é `f_n L/c = n L_ly/T_yr`; a fase usada pelo código é `y=2π f_n L/c`. Como exemplos de escala, não medições de distâncias dos datasets:

- A 1 kpc e `T=4,5 anos`, o quarto modo tem `fL/c≈2.899`, mais de três vezes o teto do piloto de custo.
- A 1 kpc e `T=15 anos`, o trigésimo modo tem `fL/c≈6.523`; aumentar somente o número de pulsares não cobre essa mudança de regime.
- Doze pulsares produzem 66 pares cruzados; 83 produzem 3.403. As 51,6 vezes mais combinações não se convertem diretamente em uma estimativa de tempo, pois a resolução angular e a estratégia de cache também mudam.

Uma aplicação deve medir o maior `fL/c` no suporte dos priors de distância, os produtos `βfL/c` e os pares quase coincidentes, e repetir refinamento de quadratura, multipolos e nós em pontos internos e fronteiras. Distâncias pontuais conhecidas são hipótese do protótipo; incertezas que alteram fases exigem marginalização ou uma aproximação de média de fase derivada e validada. Não se pode escolher retrospectivamente pulsares/canais que produzam maior diferença B–C.

Também muda o domínio físico: o prior `u=f_g T≤1` foi definido para uma banda discreta viajante. Um modelo temporal com contribuição de frequências abaixo de `1/T`, vazamento espectral ou bandas adicionais precisa especificar integral e corte inferior; não basta eliminar canais quando `f_g` aumenta. Congelar fases em C_full pode produzir discrepância já em massa zero; C_beta deve recuperar B nessa fronteira. Esses controles precisam sobreviver à nova janela.

## 5. Regra proposta para a decisão de C11

Antes de calcular qualquer resultado observacional, registrar dataset, versão, subconjunto, parâmetros, priors e critérios numéricos em `configs/application/`, com hashes e receita de aquisição. O ramo real só fica apto quando todos os seguintes itens forem demonstrados:

1. **Observação definida:** TOAs, seleção, flags, frequências de rádio, relógios, efeméride, tratamento de timing e ruído obtidos e congelados; versão exata do código de referência identificada. Para EPTA, resolver a dependência das variantes modificadas de `enterprise`; para MeerKAT, obter a receita estocástica pertinente ao benchmark escolhido.
2. **Benchmark reproduzido:** reproduzir primeiro um resultado publicado compatível com o subconjunto, a versão e o modelo de ruído. Não exigir igualdade entre releases que corrigiram produtos; documentar o alvo atual e as diferenças justificadas.
3. **Modelo observacional validado:** simular sob a mesma janela e reconstruir A0/A/B/C; testar momentos, posto, pseudocovariância e limites GR/limiar. Demonstrar convergência ORF no suporte físico, inclusive distâncias.
4. **Comparabilidade preservada:** mesmo dado B para C_full/C_beta, `W` fixo e normalização comum; média e covariância recalculadas. Se o estimador público embutir filtros dependentes da massa ou do espectro ajustado, derivar seu efeito ou construir estimadores próprios fixos.
5. **Calibração completada:** SBC e/ou cobertura condicional nos termos pré-especificados, análise de dependência do prior e identificação dos modos informativos. Um quantil dominado pela priori não deve ser chamado restrição observacional sensível à massa.

Se esses itens não estiverem concluídos na janela dos meses 19–20, executar a **extensão simulada documentada**. Ela deve acrescentar progressivamente heterogeneidade de distâncias/ruídos, dimensão da população, frequências e, quando implementada, janela irregular/ajuste temporal. Geometria ou cadência baseadas em metadados públicos podem motivar configurações, mas todos os resíduos continuam sintéticos. A extensão ideal periódica deve conservar esse rótulo; só uma extensão com janela efetivamente implementada pode testar seus efeitos.

O resultado publicável permanece uma comparação metodológica com envelope de validade, custos e falhas quantificados. A aplicação real é uma extensão condicional, não um requisito a ser satisfeito por renomear simulações ou por reaproveitar ORFs já comprimidas. A decisão formal deve ser registrada pelo projeto antes da execução de C11 e reavaliar versões/licenças nessa data.

## 6. Integração sugerida, sem execução nesta auditoria

- Usar este texto como base de `docs/dados_publicos.md`, com atualização das versões na abertura de C11.
- Versionar o parecer, o resumo de produtos e o manifesto de metadados; decidir separadamente se os dados de 7,28 MB devem permanecer apenas no cache local. O download nesta tarefa não implica redistribuição automática.
- Preservar `evidence/` como cache auditável temporário. Os binários parciais ZIP só servem para inventário; não são um dataset EPTA utilizável.
- Não marcar a checklist de aplicação, inferência ou release C11 como concluída: esta entrega contém somente auditoria de viabilidade.
