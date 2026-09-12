# C11 — Reprodução, auditoria e alcance

A campanha usa posições celestes obtidas do catálogo público MeerKAT; distâncias,
sinais e ruídos são sintéticos. Não contém análise de TOAs nem nova restrição observacional.

## Recuperar os arquivos e conferir os componentes

```sh
.venv/bin/python scripts/restaurar_c11.py --destination .
make check-application
.venv/bin/python scripts/auditar_sintese_c11.py
.venv/bin/python scripts/figuras_resultados_c11.py
```

O manifesto em `results/C11/reproducibility/manifest.json` reúne 106941 arquivos
lógicos em oito ZIPs novos e dois ZIPs anteriores reutilizados por identidade de
conteúdo. Todos estão versionados no repositório. O restaurador confere SHA-256
antes de gravar e recusa sobrescrever arquivos diferentes. Preparação, falhas,
benchmark, piloto, referências diretas, geração, respostas, likelihoods e síntese
são preservados. O log do empacotamento foi capturado no início, ainda vazio;
o resultado final do empacotamento está no manifesto e no recibo de restauração.

Uma restauração em diretório separado conferiu os 106941 arquivos e executou
os três testes agregadores, que abrangem 13 casos de componentes. O recibo está
em `results/C11/reproducibility/restoration_validation.json`. Essa verificação
não equivale a repetir a campanha física inteira.

## Entradas e saídas científicas

- Desenho congelado: `configs/application/c11_production_design.json`.
- Geração e respostas: `tmp/c11_production_run_v1/` após restauração.
- Fontes da produção: `tmp/c11_production_v1/` após restauração.
- Síntese completa por realização: `tmp/c11_synthesis_v1/` após restauração.
- Auditoria das sementes e observações: `results/C11/production_generation_audit.json`.
- Agregação independente, decisões SBC e informação somente sob a priori:
  `results/C11/statistical_audit.json`.
- Referências funcionais: `results/C11/reference_consolidation.json`.

A auditoria estatística lê os 18 arquivos de síntese e verifica hashes, retenção
dos IDs, coberturas, testes KS e ajustes Holm. Não recalcula integrais posteriores.
As médias de KL usam apenas IDs 0–499; IDs 500–595 são recuperação condicional.
KL de modelos aproximados é descritiva, não informação mútua do mecanismo verdadeiro.

## Limites de portabilidade e validação

Os arquivos históricos preservam seus bytes, inclusive caminhos absolutos da
máquina original em alguns índices de caches e recibos. A auditoria estatística
e os testes de componentes usam caminhos relativos restaurados. Uma nova
execução física em outro diretório exige uma adaptação explícita desses índices
e novas vinculações, sem alterar os recibos históricos. Essa reprodução integral
não foi demonstrada pelo teste de restauração; integra a auditoria final C13.

Os controles numéricos são finitos, não uma garantia uniforme de erro físico ou
uma prova de ausência de raízes não amostradas. Eventos indeterminados permanecem
com intervalo [0,1], sem excluir realizações. Não rejeitar um teste não demonstra
equivalência ou aprendizado sobre a massa.
