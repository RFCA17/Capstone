"""Gráficos de 5.1.3 (cambios en la correlación): positiva vs negativa."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

SALIDA = Path("figuras")

pos = pd.read_csv("Resultados/barrido_correlacion_positiva.csv")
neg = pd.read_csv("Resultados/barrido_correlacion_negativa.csv")
for df in (pos, neg):
    df["V_POST"] = df["V_POST"] / 1e6      # millones de pesos
CVS = [0.1, 0.3, 0.5]

# Figura 1: V_POST según CV, un panel por capacidad (PL = 5)
fig, ejes = plt.subplots(1, 4, figsize=(9, 3))
for eje, C in zip(ejes, [21, 42, 63, 84]):
    for df, nombre, color in [(pos, "positiva", "#2a78d6"), (neg, "negativa", "#eb6834")]:
        d = df[(df.C == C) & (df.PL == 5)].sort_values("CV")
        eje.plot(d.CV * 100, d.V_POST, marker="o", color=color, label=f"Correlación {nombre}")
    eje.set_title(f"C = {C} h")
    eje.set_xlabel("CV (%)")
    eje.set_xticks([10, 30, 50])
    eje.set_ylim(bottom=0)
ejes[0].set_ylabel("V_POST (millones de pesos)")
handles, textos = ejes[0].get_legend_handles_labels()
fig.legend(handles, textos, loc="lower center", ncol=2, frameon=False)
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(SALIDA / "vpost_vs_cv_corr.png", dpi=300, bbox_inches="tight")

# Figura 2: V_POST según PL, con C = 42 h, un panel por CV
fig, ejes = plt.subplots(1, 3, figsize=(9, 3))
for eje, cv in zip(ejes, CVS):
    for df, nombre, color in [(pos, "positiva", "#2a78d6"), (neg, "negativa", "#eb6834")]:
        d = df[(df.C == 42) & (df.CV == cv)].sort_values("PL")
        eje.plot(d.PL, d.V_POST, marker="o", color=color, label=f"Correlación {nombre}")
    eje.set_title(f"CV = {int(cv * 100)}%")
    eje.set_xlabel("PL (productos habilitados)")
    eje.set_xticks([0, 2, 3, 4, 5])
    eje.set_ylim(bottom=0)
ejes[0].set_ylabel("V_POST (millones de pesos)")
handles, textos = ejes[0].get_legend_handles_labels()
fig.legend(handles, textos, loc="lower center", ncol=2, frameon=False)
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(SALIDA / "vpost_vs_pl_C42_corr.png", dpi=300, bbox_inches="tight")

