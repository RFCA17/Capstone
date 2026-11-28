"""Calcula VSS, VMS y la cota wait-and-see del modelo base (arbol de 11 nodos).

Uso:  python vss_vms.py      (junto a modelo_gurobi.py)
Resultado: resultados/vss_vms.csv  (en pesos)
"""
import copy
from pathlib import Path

import pandas as pd

import modelo_gurobi as M

# variables de produccion; los inventarios y atrasos se ajustan solos
DECISIONES = ["w_b", "w_bl", "w_l", "z_b", "z_bl", "z_l", "y", "u"]


def resolver(m):
    """Resuelve con las mismas opciones que modelo_gurobi.py y devuelve el costo."""
    m.Params.OutputFlag = 0
    m.Params.MIPGap = 1e-8
    m.Params.Seed = 0
    m.Params.IntFeasTol = 1e-9
    m.optimize()
    return m.ObjVal


def lista_decisiones(v):
    """Lista de (nombre, indice, nodo, variable). Cada clave es p.ej. (vino, nodo)."""
    lista = []
    for nombre in DECISIONES:
        for clave, var in v[nombre].items():
            indice = clave[:-1]  # todo menos el nodo
            nodo = clave[-1]  # el nodo va al final
            if nodo != 0:  # el nodo 0 es la condicion inicial
                lista.append((nombre, indice, nodo, var))
    return lista


def etapa_de_cada_nodo(inst):
    etapa = {}
    for s in inst.N_etapa:
        for n in inst.N_etapa[s]:
            etapa[n] = s
    return etapa


# 1) MULTIETAPA: el modelo normal
def costo_multietapa(inst, C, PL):
    m, v, _ = M.construir_modelo(inst, C, PL)
    return resolver(m)


# 2) DOS ETAPAS: los nodos de una misma etapa deben decidir lo mismo
def costo_dos_etapas(inst, C, PL):
    m, v, _ = M.construir_modelo(inst, C, PL)
    etapa = etapa_de_cada_nodo(inst)
    for nombre, indice, nodo, var in lista_decisiones(v):
        primer_nodo = inst.N_etapa[etapa[nodo]][0]
        if nodo != primer_nodo:
            var_de_referencia = v[nombre][indice + (primer_nodo,)]
            m.addConstr(var == var_de_referencia)
    return resolver(m)


# 3) EEV: planificar con la demanda promedio y aplicar ese plan al arbol real
def instancia_demanda_promedio(inst):
    """Arbol de 3 nodos (1 por etapa) con la demanda promedio de cada etapa."""
    nueva = copy.copy(inst)
    nueva.N = list(inst.N_etapa)  # nodos 1, 2, 3 = etapas
    nueva.N_etapa = {s: [s] for s in nueva.N}
    nueva.a = {s: s - 1 for s in nueva.N}  # el nodo 1 cuelga del nodo 0
    nueva.p = {s: 1.0 for s in nueva.N}
    nueva.D = {}
    for s in inst.N_etapa:
        nodos = inst.N_etapa[s]
        prob_etapa = sum(inst.p[n] for n in nodos)
        for i, j in inst.P:
            suma = sum(inst.p[n] * inst.D[i, j, n] for n in nodos)
            nueva.D[i, j, s] = suma / prob_etapa
    return nueva


def costo_eev(inst, C, PL):
    # a) resolver con la demanda promedio y guardar el plan de cada etapa
    inst_prom = instancia_demanda_promedio(inst)
    m_prom, v_prom, _ = M.construir_modelo(inst_prom, C, PL)
    resolver(m_prom)
    plan = {}
    for nombre, indice, nodo, var in lista_decisiones(v_prom):
        plan[nombre, indice, nodo] = var.X  # aqui nodo = etapa

    # b) fijar ese plan en el arbol completo y resolver (solo se ajustan inventarios)
    m, v, _ = M.construir_modelo(inst, C, PL)
    etapa = etapa_de_cada_nodo(inst)
    for nombre, indice, nodo, var in lista_decisiones(v):
        x = plan[nombre, indice, etapa[nodo]]
        if nombre.startswith("z") or nombre == "y":
            x = round(x)  # las binarias y enteras deben ser exactas
        var.LB = x
        var.UB = x
    for clave, var in v["z_pos"].items():
        var.LB = var.UB = round(v_prom["z_pos"][clave].X)
    return resolver(m)


# 4) WAIT-AND-SEE: resolver cada trayectoria conociendo su demanda
def costo_wait_and_see(inst, C, PL):
    total = 0.0
    for camino in M.trayectorias(inst):  # camino = [nodo1, nodo2, nodo_terminal]
        solo = copy.copy(inst)
        solo.N = camino
        solo.N_etapa = {k + 1: [n] for k, n in enumerate(camino)}
        solo.a = {camino[0]: 0, camino[1]: camino[0], camino[2]: camino[1]}
        solo.p = {n: 1.0 for n in camino}
        solo.D = {k: x for k, x in inst.D.items() if k[2] in camino}
        m, _, _ = M.construir_modelo(solo, C, PL)
        total += inst.p[camino[-1]] * resolver(m)
    return total


def main():
    inst = M.cargar_instancia("cubierta")
    filas = []
    for C in [21, 42, 63, 84]:
        for PL in [0, 2, 3, 4, 5]:
            ws = costo_wait_and_see(inst, C, PL)
            ms = costo_multietapa(inst, C, PL)
            dos = costo_dos_etapas(inst, C, PL)
            eev = costo_eev(inst, C, PL)
            filas.append({"C": C, "PL": PL, "WS": ws, "MS": ms, "2S": dos, "EEV": eev,
                          "VMS": dos - ms, "VSS": eev - ms, "EVPI": ms - ws})
    df = pd.DataFrame(filas)
    carpeta = Path(__file__).resolve().parent / "resultados"
    carpeta.mkdir(exist_ok=True)
    df.to_csv(carpeta / "vss_vms.csv", index=False)
    print((df.set_index(["C", "PL"]) / 1e6).round(2).to_string())


if __name__ == "__main__":
    main()
