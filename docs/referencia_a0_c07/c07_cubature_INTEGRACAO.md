# Integração possível, ainda não realizada

O núcleo reutilizável é pequeno: `SpectralCN(e,q,Gamma,b).coefficients(a,gamma)`
retorna `χ,D` da CN, e `mass_integral(Gamma,e,q,box,orders)` integra a escala e
as três coordenadas remanescentes para um dado e uma massa. `Gamma` entra por
uma interface de arranjo explícito `K×Np×Np`, sem vínculo a um interpolador.
`FrozenMassTable` é apenas o adaptador temporário do cache C07; não deve ser
confundido com um novo certificado de precisão da ORF.

Para produção, antes de integrar ao repositório:

1. Revalidar as 16 realizações e todos os modelos desejados. Uma ordem que
   resolve A0 no dado14 pode não resolver A0 em outro dado nem A/B/G.
2. Para A0 em vários dados, a mesma decomposição espectral pode projetar todos
   os vetores `q` de uma vez. Os autovalores e determinantes independem dos
   dados; somente as potências projetadas mudam. Esta extensão ainda não está
   implementada neste pacote. Não extrapolar os tempos de uma realização
   linearmente como medida de uma campanha.
3. Determinar os quantis nuisance por CDFs contínuas nos parâmetros originais.
   As CDFs de caixas truncadas podem ser avaliadas por bisseção com tolerância
   em **largura de suporte**, preservando o limite numérico adicional da CDF.
   Uma malha de CDF deve ter convergência verificada antes de interpolação.
   As diferenças nos 20 cortes aqui calculados não bastam para isso.
4. Antes de produção longa, criar checkpoints por massa com hashes da
   configuração, dados e fontes e gravação atômica. Os scripts atuais guardam
   seus JSONs completos ao fim e preservam os arquivos existentes.
5. Preservar a validação por Cholesky como referência do atalho espectral;
   evitar recortes de autovalores. Se forem ampliados suporte ou geometria,
   reavaliar condicionamento e limites de recursos.
6. A rota GaussianScaleKernel do outro agente pode reutilizar os painéis e o
   fator de volumes para numeradores truncados. O seu custo e precisão da
   integral condicional de escala precisam de avaliação própria; a exatidão
   analítica da escala CN não se transfere automaticamente.

Os limites de erro de quadratura apresentados são comparações numéricas
realizadas, não limites matemáticos universais. Os controles analíticos
validam identidades e implementações em casos independentes. A diferença entre
essas duas formas de evidência deve continuar explícita no capítulo C07.
