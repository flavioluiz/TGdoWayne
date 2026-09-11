# Dados independentes para SBC

500 verdades contínuas foram sorteadas da priori congelada em `configs/calibration/prior_predictive_500_v1.json`, com semente 707409101; as observações usam707409102. O gerador físico CN e os controles gaussianos pareados são os validados em C06. Não foram reutilizados os 16 dados de engenharia.

A construção preserva 503 nós ORF calculados diretamente (verdades+âncoras), com dois refinamentos e sete confrontos diretos independentes. A geração não usa a tabela interpolada de inferência. Dados e matrizes têm hashes nos relatórios e foram regenerados numericamente dentro de1e−12.

Receita de verificação: `.venv/bin/python scripts/gerar_calibracao.py verify`. A existência destes 500 dados não significa que a inferência ou SBC foi executada.
