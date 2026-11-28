from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import argparse
BASE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description="Gráficos de implementación y piloto sin Gurobi")
parser.add_argument('--datos', type=Path, default=BASE.parent / 'Resultados' / 'Correlaciones')
parser.add_argument('--salida', type=Path, default=BASE / 'Implementacion')
args = parser.parse_args()
out = args.salida
out.mkdir(parents=True, exist_ok=True)
def find_csv(name):
    matches = list(args.datos.rglob(name))
    if len(matches) != 1:
        raise ValueError(f'Se esperaba exactamente un archivo {name} en {args.datos}: {matches}')
    return matches[0]
d = pd.concat([pd.read_csv(find_csv(f'barrido_correlacion_{s}.csv')).assign(corr=s) for s in ['positiva','negativa']], ignore_index=True)
expected = pd.MultiIndex.from_product([['positiva','negativa'], [.1,.3,.5], [21,42,63,84], [0,2,3,4,5]], names=['corr','CV','C','PL'])
if len(d) != 120 or not d.groupby(['corr','CV','C','PL']).size().reindex(expected).eq(1).all() or not d.status.eq(2).all():
    raise ValueError('Se requieren 120 configuraciones factoriales únicas y óptimas.')
if not np.isfinite(d.tiempo_s).all() or not d.tiempo_s.gt(0).all():
    raise ValueError('Tiempos inválidos para escala logarítmica.')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelsize':10,'figure.facecolor':'white','savefig.dpi':300,'axes.titleweight':'normal'})
navy='#1c4b77'; teal='#299d9e'; gray='#C7CED1'; wine='#a5262a'; ink='#23313C'
def save(fig,name):
 fig.savefig(out/name,bbox_inches='tight',pad_inches=.15); plt.close(fig)
def fmt(v,n=2): return f'{v:,.{n}f}'.replace(',','_').replace('.',',').replace('_','.')
# 1. Medianas de seis corridas por capacidad y PL.
caps = [21,42,63,84]
med = d.groupby(['C','PL']).tiempo_s.median().unstack()
fig, ax = plt.subplots(figsize=(6.1,4.2))
colors = ['#1c4b77','#158ab2','#299d9e','#e49b38','#a5262a']
for pl, color in zip([0,2,3,4,5], colors):
    ax.plot(med.index, med[pl], 'o-', color=color, linewidth=1.7, markersize=6, label=f'PL={pl}')
ax.set_xticks(caps)
ax.set_xlabel('Capacidad (h/nodo)')
ax.set_ylabel('Mediana del tiempo de resolución (s)')
ax.set_yscale('log')
ax.grid(True, which='major', color='#d0d0d0', alpha=.55, linewidth=.8)
ax.set_axisbelow(True)
ax.legend(loc='upper right', frameon=False)
ax.margins(x=.045,y=.15)
fig.tight_layout()
save(fig,'imp_tiempos.png')
print(med.to_string())
# 2. selection stability exact sets, rather than invented probabilities
fig,ax=plt.subplots(figsize=(8.1,3.1)); cols=[(s,cv) for s in ['positiva','negativa'] for cv in [.1,.3,.5]]; zz=np.zeros((4,6)); labels=[]
for i,c in enumerate(caps):
 row=[]
 for j,(s,cv) in enumerate(cols):
  a=d[(d.C==c)&(d.PL==2)&(d.CV==cv)&(d['corr']==s)].iloc[0].productos_habilitados
  zz[i,j]=a=='[(1, 1), (1, 2)]'; row.append(a.replace('[','').replace(']','').replace('), (',')\n(').replace(', ',',') )
 labels.append(row)
ax.imshow(zz,cmap=ListedColormap(['#E7E9E8',navy]),vmin=0,vmax=1,aspect='auto');
for i in range(4):
 for j in range(6): ax.text(j,i,labels[i][j],ha='center',va='center',color='white' if zz[i,j] else ink,fontsize=9)
ax.set_xticks(range(6),[f'{int(cv*100)}%' for s,cv in cols]);ax.set_yticks(range(4),[f'{c} h' for c in caps]);ax.tick_params(length=0);ax.set_xlabel('Coeficiente de variación de la demanda');ax.set_ylabel('Capacidad');ax.axvline(2.5,color='white',lw=3);ax.text(1,-.79,'Correlación positiva',ha='center',va='bottom',weight='bold');ax.text(4,-.79,'Correlación negativa',ha='center',va='bottom',weight='bold');ax.set_ylim(3.5,-1.25);[s.set_visible(False) for s in ax.spines.values()];fig.tight_layout();save(fig,'imp_seleccion.png')
# 3. pilot economics: marginal gains vs levels, service points with own axes (separate panel)
x=d[(d.C==42)&(d.CV==.3)&(d['corr']=='negativa')].sort_values('PL'); levels=x.PL.to_numpy(); cte=x.CTE.to_numpy()/1e6; ns=x['NS_%'].to_numpy();
fig,axs=plt.subplots(1,2,figsize=(8.5,3.3),gridspec_kw={'width_ratios':[1.15,1]}); ax=axs[0]; y=np.arange(4); delta=-np.diff(cte); ax.barh(y,delta,color=[navy,teal,teal,teal],height=.58); ax.set_yticks(y,[f'{a} → {b}' for a,b in zip(levels[:-1],levels[1:])]); ax.invert_yaxis(); ax.set_xlabel('Ahorro marginal (MM$)');ax.set_ylabel('Ampliación de PL');ax.set_xlim(0,230);ax.grid(axis='x',alpha=.2); 
for i,v in enumerate(delta): ax.text(v+3,i,fmt(v),va='center',fontsize=9)
ax=axs[1];ax.plot(range(5),ns,'o-',color=wine,lw=2);ax.set_xticks(range(5),levels);ax.set_xlabel('Productos habilitados (PL)');ax.set_ylabel('Nivel de servicio (%)');ax.set_ylim(94.8,100.6);ax.grid(axis='y',alpha=.2)
for i,v in enumerate(ns): ax.annotate(fmt(v)+'%',(i,v),xytext=(10 if i==0 else 0,8 if i<3 else -15),textcoords='offset points',ha='left' if i==0 else 'center',fontsize=8)
fig.tight_layout(w_pad=2);save(fig,'imp_alcance_piloto.png')
# 4. allocation and WIP, actual decision data, no double count of wine variables
p=pd.read_csv(find_csv('produccion_correlacion_negativa.csv')); p=p[(p.C==42)&(p.CV==.3)&(p.PL==2)&(p.vino==1)&(p.nodo.isin([1,2,3,4]))]; initial=p.loc[p.nodo==1,'w_b'].iloc[0]; q=p[p.nodo.isin([2,3,4])]; q1=q[q.etiqueta==1].sort_values('nodo').w_l.to_numpy();q2=q[q.etiqueta==2].sort_values('nodo').w_l.to_numpy(); rem=q.drop_duplicates('nodo').sort_values('nodo').s_b.to_numpy(); assert np.max(abs(q1+q2+rem-initial))<.03
fig,ax=plt.subplots(figsize=(7.5,3.2)); ids=np.arange(3); ax.barh(ids,q1,color=navy,label='Etiqueta (1,1)'); ax.barh(ids,q2,left=q1,color=teal,label='Etiqueta (1,2)');ax.barh(ids,rem,left=q1+q2,color=gray,label='Remanente genérico');ax.set_yticks(ids,['Nodo 2','Nodo 3','Nodo 4']);ax.invert_yaxis();ax.set_xlim(0,initial*1.04);ax.set_xlabel('Botellas del Vino 1');ax.axvline(initial,color=ink,ls='--',lw=1);ax.set_title('Disponibilidad común: '+fmt(initial,2)+' botellas',fontsize=10);ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v,pos:fmt(v,0)));ax.grid(axis='x',alpha=.18);ax.legend(loc='upper center',bbox_to_anchor=(.5,-.26),ncol=3,frameon=False,fontsize=9);
for i,(a,b) in enumerate(zip(q1,q2)):
 ax.text(a/2,i,fmt(a,0),ha='center',va='center',color='white',fontsize=9);ax.text(a+b/2,i,fmt(b,0),ha='center',va='center',color='white',fontsize=9)
fig.tight_layout();save(fig,'imp_asignacion_piloto.png')

print(f'OK: 4 figuras; {len(d)} corridas; balance verificado. Salida: {out.resolve()}')
