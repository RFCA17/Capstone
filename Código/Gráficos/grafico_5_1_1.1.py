"""Figura 5.1: sensibilidad a lambda (alpha = 0,7)."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
SALIDA = Path("figuras")
SALIDA.mkdir(exist_ok=True)
df = pd.read_csv(next(Path("Resultados").rglob("sensibilidad_riesgo_lambda.csv")))
for col in ["CTE", "CVaR"]:
    df[col] = df[col] / 1e6                  # millones de pesos


def fmt(x):
    return f"{x:g}".replace(".", ",")


def agrupar(d, tol=10):
    """Agrupa lambdas consecutivos cuyos puntos (CTE, CVaR) difieren < tol millones."""
    grupos = [[d.iloc[0]]]
    for _, fila in d.iloc[1:].iterrows():
        prev = grupos[-1][-1]
        if abs(fila.CTE - prev.CTE) < tol and abs(fila.CVaR - prev.CVaR) < tol:
            grupos[-1].append(fila)
        else:
            grupos.append([fila])
    return grupos


def etiqueta(grupo):
    ls = [fmt(f["lambda"]) for f in grupo]
    if len(ls) == 1:
        return f"λ = {ls[0]}"
    if len(ls) == 2:
        return f"λ = {ls[0]} y {ls[1]}"
    return f"λ = {ls[0]} a {ls[-1]}"


# Figura 5.1: CTE vs CVaR según lambda, PL = 0 y PL = 5, con C = 42 h
fig, eje = plt.subplots(figsize=(7, 4))
series = [(0, "o", "#c44e52", [(5, 6)]),                 # etiquetas arriba
          (5, "s", "#4c72b0", [(5, 8), (5, -12)])]       # alterna arriba/abajo
for PL, marca, color, offsets in series:
    d = df[(df.C == 42) & (df.PL == PL)].sort_values("lambda")
    eje.plot(d.CTE, d.CVaR, marker=marca, color=color, lw=2, ms=7, label=f"PL = {PL}")
    for i, grupo in enumerate(agrupar(d)):
        eje.annotate(etiqueta(grupo), (grupo[0].CTE, grupo[0].CVaR),
                     textcoords="offset points", xytext=offsets[i % len(offsets)],
                     fontsize=8)
eje.set_xlabel("Costo total esperado (millones de pesos)")
eje.set_ylabel("CVaR$_{0,7}$ (millones de pesos)")
eje.grid(alpha=0.3)
eje.legend()
fig.tight_layout()
fig.savefig(SALIDA / "cte_vs_cvar_lambda_C42.png", dpi=300, bbox_inches="tight")

plt.show()
