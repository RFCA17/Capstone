"""Figura 5.2: sensibilidad a lambda (alpha = 0,7)."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

SALIDA = Path("figuras")
SALIDA.mkdir(exist_ok=True)

df = pd.read_csv(next(Path("Resultados").rglob("sensibilidad_riesgo_lambda.csv")))

for col in ["CTE", "CVaR"]:
    df[col] = df[col] / 1e6                  # millones de pesos
LAMBDAS = sorted(df["lambda"].unique())
COMA = FuncFormatter(lambda x, _: f"{x:g}".replace(".", ","))



# Figura 5.2: reducción de CTE y CVaR al pasar de PL = 0 a PL = 5, un panel por C
fig, ejes = plt.subplots(1, 4, figsize=(11, 3))
for eje, C in zip(ejes, [21, 42, 63, 84]):
    d = df[df.C == C]
    base = d[d.PL == 0].set_index("lambda").loc[LAMBDAS]
    post = d[d.PL == 5].set_index("lambda").loc[LAMBDAS]
    eje.plot(LAMBDAS, base.CTE - post.CTE, marker="o", color="#1f77b4", label="Reducción del CTE")
    eje.plot(LAMBDAS, base.CVaR - post.CVaR, marker="s", color="#ff7f0e",
             label="Reducción del CVaR$_{0,7}$")
    eje.set_title(f"C = {C} h")
    eje.set_xlabel("λ")
    eje.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    eje.xaxis.set_major_formatter(COMA)
    eje.yaxis.set_major_formatter(COMA)
    eje.grid(alpha=0.3)
ejes[0].set_ylabel("Millones de pesos")
ejes[0].legend(fontsize=7)
fig.tight_layout()
fig.savefig(SALIDA / "reduccion_cte_cvar_lambda.png", dpi=300, bbox_inches="tight")

plt.show()
