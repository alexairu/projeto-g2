"""Métricas, estatísticas e figuras estáticas do artigo (RQ1-RQ3).

Uso (a partir da raiz do repositório):  python -m src.analise
Gera:  docs/assets/*.png  e  docs/assets/estatisticas.json
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from src.etl import REGIAO

PROCESSED = Path("data/processed/problemas_domicilio_capitais.csv.gz")
ASSETS = Path("docs/assets")

ROTULOS = {
    "violencia": "Violência/vandalismo",
    "pouco_espaco": "Pouco espaço",
    "barulho": "Barulho (rua/vizinhos)",
    "umidade": "Umidade (fundação/paredes/chão)",
    "goteira": "Telhado com goteira",
    "madeira_deteriorada": "Madeira deteriorada",
    "poluicao": "Poluição/problemas ambientais",
    "casa_escura": "Casa escura",
}
ESTRUTURAIS = ["goteira", "umidade", "madeira_deteriorada"]
CORES_REGIAO = {"Norte": "#1b9e77", "Nordeste": "#d95f02", "Sudeste": "#7570b3",
                "Sul": "#e7298a", "Centro-Oeste": "#66a61e"}


def carregar() -> pd.DataFrame:
    return pd.read_csv(PROCESSED)


def matriz(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot(index="capital", columns="problema", values="pct_sim")


def calcular_estatisticas(df: pd.DataFrame) -> dict:
    w = matriz(df)
    desc = w.describe().T
    desc["cv"] = desc["std"] / desc["mean"]
    desc["amplitude"] = desc["max"] - desc["min"]
    indice = w.mean(axis=1).sort_values(ascending=False)
    estrutural = w[ESTRUTURAIS].mean(axis=1).sort_values(ascending=False)
    regiao = indice.groupby(indice.index.map(REGIAO)).mean().sort_values(ascending=False)
    norte_ne = [c for c, r in REGIAO.items() if r in ("Norte", "Nordeste")]
    demais = [c for c in REGIAO if c not in norte_ne]
    rho, p = stats.spearmanr(w["goteira"], w["madeira_deteriorada"])
    z = (w - w.mean()) / w.std(ddof=1)
    outliers = [(c, prob, round(float(w.loc[c, prob]), 2), round(float(z.loc[c, prob]), 2))
                for c in w.index for prob in w.columns if abs(z.loc[c, prob]) >= 1.8]
    return {
        "descritiva": desc.round(2).to_dict(orient="index"),
        "indice_capital": indice.round(2).to_dict(),
        "indice_estrutural": estrutural.round(2).to_dict(),
        "indice_regiao": regiao.round(2).to_dict(),
        "media_norte_nordeste": round(float(indice[norte_ne].mean()), 2),
        "media_demais": round(float(indice[demais].mean()), 2),
        "pearson": w.corr().round(2).to_dict(),
        "spearman": w.corr(method="spearman").round(2).to_dict(),
        "spearman_goteira_madeira": {"rho": round(float(rho), 2), "p": round(float(p), 5)},
        "outliers_z>=1.8": outliers,
    }


def fig_prevalencia(df: pd.DataFrame, destino: Path) -> None:
    w = matriz(df)
    ordem = w.mean().sort_values()
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=200)
    pos = np.arange(len(ordem))
    ax.barh(pos, ordem.values, height=.5, color="#1f4e79", alpha=.85, zorder=1,
            label="Média das 12 capitais")
    for i, prob in enumerate(ordem.index):
        ax.scatter(w[prob], [i] * len(w), color="#9aa5b1", s=22, alpha=.9, zorder=2,
                   label="Capital" if i == 0 else None)
    ax.set_yticks(pos, [ROTULOS[p] for p in ordem.index])
    ax.set_xlabel("% de famílias que relataram o problema")
    ax.set_title("Prevalência por problema: média (barra) e cada capital (ponto)",
                 fontsize=10, loc="left")
    ax.set_xlim(0, 70)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    ax.grid(axis="x", alpha=.3, zorder=0)
    sns.despine()
    fig.tight_layout()
    fig.savefig(destino / "fig1_prevalencia.png")
    plt.close(fig)


def fig_ranking_capitais(df: pd.DataFrame, destino: Path) -> None:
    w = matriz(df)
    indice = w.mean(axis=1).sort_values()
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=200)
    ax.barh(indice.index, indice.values, color=[CORES_REGIAO[REGIAO[c]] for c in indice.index])
    for i, v in enumerate(indice.values):
        ax.text(v + .5, i, f"{v:.1f}", va="center", fontsize=8)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in CORES_REGIAO.values()]
    ax.legend(handles, CORES_REGIAO.keys(), title="Região", loc="lower right", frameon=False)
    ax.set_xlabel("Índice médio de incidência (% médio dos 8 problemas)")
    ax.set_title("Capitais ordenadas pelo índice médio de problemas no domicílio",
                 fontsize=10, loc="left")
    ax.set_xlim(0, 55)
    sns.despine()
    fig.tight_layout()
    fig.savefig(destino / "fig2_ranking_capitais.png")
    plt.close(fig)


def fig_heatmap(df: pd.DataFrame, destino: Path) -> None:
    w = matriz(df)
    w = w.loc[w.mean(axis=1).sort_values(ascending=False).index,
              w.mean().sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(9, 5.4), dpi=200)
    sns.heatmap(w.rename(columns=ROTULOS), annot=True, fmt=".0f", cmap="YlOrRd",
                cbar_kws={"label": "% de famílias"}, linewidths=.5, ax=ax)
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    ax.set_title("% de famílias com cada problema, por capital (POF 2002-2003)",
                 fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(destino / "fig3_heatmap.png")
    plt.close(fig)


def fig_correlacao(df: pd.DataFrame, destino: Path) -> None:
    w = matriz(df)
    ordem = w.mean().sort_values(ascending=False).index
    corr = w[ordem].corr(method="spearman").rename(index=ROTULOS, columns=ROTULOS)
    fig, ax = plt.subplots(figsize=(7.6, 6), dpi=200)
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1,
                linewidths=.5, cbar_kws={"label": "Correlação de Spearman"}, ax=ax)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    ax.set_title("Correlação entre problemas (n = 12 capitais)", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(destino / "fig4_correlacao.png")
    plt.close(fig)


def fig_dispersao_estrutural(df: pd.DataFrame, destino: Path) -> None:
    w = matriz(df)
    fig, ax = plt.subplots(figsize=(6.4, 5), dpi=200)
    for cap in w.index:
        x, y = w.loc[cap, "goteira"], w.loc[cap, "madeira_deteriorada"]
        ax.scatter(x, y, s=60, color=CORES_REGIAO[REGIAO[cap]], zorder=3)
        ax.annotate(cap, (x, y), textcoords="offset points", xytext=(5, 4), fontsize=7)
    m, b = np.polyfit(w["goteira"], w["madeira_deteriorada"], 1)
    xs = np.linspace(0, 60, 50)
    ax.plot(xs, m * xs + b, color="#555", lw=1, ls="--", zorder=2)
    handles = [plt.Line2D([], [], marker="o", ls="", color=c) for c in CORES_REGIAO.values()]
    ax.legend(handles, CORES_REGIAO.keys(), title="Região", loc="upper left",
              frameon=False, fontsize=8)
    ax.set_xlabel("% com telhado com goteira")
    ax.set_ylabel("% com madeira deteriorada")
    ax.set_title("Goteira × madeira deteriorada", fontsize=10, loc="left")
    ax.grid(alpha=.3)
    sns.despine()
    fig.tight_layout()
    fig.savefig(destino / "fig5_dispersao_estrutural.png")
    plt.close(fig)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    df = carregar()
    sns.set_theme(style="white", font_scale=.9)
    for f in (fig_prevalencia, fig_ranking_capitais, fig_heatmap, fig_correlacao,
              fig_dispersao_estrutural):
        f(df, ASSETS)
    est = calcular_estatisticas(df)
    (ASSETS / "estatisticas.json").write_text(json.dumps(est, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
    print("Figuras e estatísticas geradas em", ASSETS)


if __name__ == "__main__":
    main()
