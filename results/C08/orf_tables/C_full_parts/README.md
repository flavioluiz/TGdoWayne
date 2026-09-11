# Arquivo numérico em partes

As partes conservam todos os bytes do arquivo original, incluindo metadados internos. Nenhum float foi arredondado ou reconstruído.

Restaurar com `python3 compactar_arquivo.py unpack --bundle . --output /caminho/novo.npz`. O destino deve ser novo. O comando verifica cada parte, o fluxo gzip e o SHA256 original. Os hashes garantem integridade em relação ao manifesto versionado, não validação científica.
