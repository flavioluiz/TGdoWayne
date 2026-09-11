# Ampliação opcional da proposta gaussiana

A transformação ocorre depois do ajuste EM de quatro componentes e antes da
validação, do novo `proposal_content_hash` e da gravação exclusiva do registro.
Ela não faz outro ajuste nem acessa dados ou verdades. As médias são duplicadas;
as covariâncias propostas são C e9C. A massa total da mistura é:

- 0,75 nas quatro Gaussianas originais;
- 0,10 nas quatro cópias com variâncias multiplicadas por9 (desvios por3);
- 0,15 na Student defensiva global original, inteiramente preservada.

O construtor existente espera pesos condicionais à escolha da parte gaussiana.
Por isso, os oito pesos são `(0.75/0.85)*w` e `(0.10/0.85)*w`. O módulo distingue
quatro componentes ajustadas de oito propostas. Registra o ajuste original
completo e seu SHA256 em `unbroadened_gaussian_fit` / `_sha256`, além da descrição
da transformação e do limite de densidade. O novo hash inclui todos esses dados.
Nenhum hash de proposta antiga é herdado.

Se q_old =0,85 p_narrow +0,15 p_Student e
q_new =0,75 p_narrow +0,10 p_wide +0,15 p_Student, então, para c=0,75/0,85,

`q_new - c*q_old = 0.10*p_wide + 0.15*(1-c)*p_Student >=0`.

Logo q_new≥c q_old em todo ponto logit; a transformação comum de coordenadas
preserva a desigualdade. Isso limita a deterioração pontual da proposta, sem
certificar ESS, caudas não observadas ou precisão de CDF da produção.

Configuração opcional:

```json
"training": {
  "gaussian_broadening": {
    "wide_total_probability": 0.10,
    "variance_multiplier": 9
  }
}
```

Sem a chave, a distribuição e os campos do registro seguem o comportamento
original, com quatro Gaussianas. O sourcegraph do runtime inclui o novo módulo
somente quando a chave está presente. Como qualquer edição de fonte, a integração
produz uma nova identidade de execução; não reclassifica arquivos históricos.

Entrega: `proposal_broadening.py`, cópias de `campaign_training.py` e
`campaign_runtime.py` com alterações mínimas, patches correspondentes e testes.
`patch_bases.json` registra o SHA anterior e o posterior; verificar a base antes
de copiar. Nenhuma fonteROOT foi alterada por esta tarefa.

Cinco testes passaram: oito Gaussianas/Student contra SciPy; integral independente
unidimensional normalizada; limite inferior de densidade em pontos centrais e
caudas; não mutação e entradas inválidas; integração treino opcional→novo hash→
produtor IID. O default sem configuração preserva parâmetros e conjunto de
metadados. A igualdade dos pesos sob aritmética de máquina foi verificada a2ULP.
O teste com hash herdado falha antes de gerar pontos. Nenhuma campanha500 foi
iniciada e nenhuma aprovação de precisão decorre desses testes de distribuição.
