"""Ilustração analítica de dispersão, com eixos em linguagem acessível."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
u=np.linspace(0,1,400)
plt.rcParams.update({'font.size':13,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(7,4))
for k,label,col in [(1,'Frequência baixa','#E6A23C'),(2,'Dobro da frequência','#008C95'),(4,'Quatro vezes a frequência','#17324D')]:
 ax.plot(u,100*np.sqrt(1-(u/k)**2),label=label,color=col,lw=3)
ax.set(xlabel='Massa considerada (escala relativa)',ylabel='Velocidade (% da velocidade da luz)',xlim=(0,1),ylim=(0,105))
ax.legend(frameon=False,loc='lower left',fontsize=12)
fig.tight_layout()
fig.savefig(Path(__file__).parent/'dispersao_didatica.pdf',metadata={'CreationDate':None,'ModDate':None})
