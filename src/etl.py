"""ETL da Tabela 1461 (IBGE/POF 2002-2003, via Armazém de Dados da Prefeitura do Rio).

Autor: Alexandre Souza de Abreu Junior
Centro Universitário La Salle do Rio de Janeiro · Bacharelado em Sistemas de Informação
Disciplina: Linguagens de Programação (6º período, 2026.2) · Prof. Alexandre Neves Louzada
Licença: MIT

Transforma a planilha "larga" e com cabeçalho em duas linhas (problema + Sim/Não)
em um formato tidy (uma linha por capital x problema), valida e persiste.

Uso (a partir da raiz do repositório):
    python -m src.etl                      # usa os caminhos padrão
    python -m src.etl --raw caminho.xls    # caminho alternativo
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DEFAULT = Path("data/raw/1461.xls")
OUT_DIR_DEFAULT = Path("data/processed")

# Nomes curtos e estáveis (snake_case) para as 8 variáveis de problema.
SLUGS = {
    "Pouco espaço": "pouco_espaco",
    "Rua ou vizinhos barulhentos": "barulho",
    "Casa escura": "casa_escura",
    "Telhado com goteira": "goteira",
    "Fundação, paredes ou chão úmidos": "umidade",
    "Madeira das janelas, portas ou assoalhos deteriorados": "madeira_deteriorada",
    "Poluição ou problemas ambientais causados pelo trânsito ou indústria": "poluicao",
    "Violência ou vandalismo na área de residência": "violencia",
}

# Macrorregião de cada capital (IBGE) - metadado derivado, documentado no dicionário.
REGIAO = {
    "Belém": "Norte", "Manaus": "Norte",
    "Fortaleza": "Nordeste", "Recife": "Nordeste", "Salvador": "Nordeste",
    "Belo Horizonte": "Sudeste", "Rio de Janeiro": "Sudeste", "São Paulo": "Sudeste",
    "Curitiba": "Sul", "Porto Alegre": "Sul",
    "Brasília": "Centro-Oeste", "Goiânia": "Centro-Oeste",
}


def read_raw(path: Path) -> pd.DataFrame:
    """Lê a planilha sem cabeçalho (header=None) para tratar a estrutura manualmente.

    O arquivo original é .xls (Excel 97-2003), lido com o motor xlrd.
    """
    path = Path(path)
    engine = "xlrd" if path.suffix.lower() == ".xls" else "openpyxl"
    return pd.read_excel(path, header=None, engine=engine)


def parse_wide(raw: pd.DataFrame) -> pd.DataFrame:
    """Localiza o bloco de dados pelo conteúdo e devolve o formato tidy.

    Estrutura da planilha: linha com nomes dos problemas (cada um ocupa 2 colunas,
    célula mesclada), linha seguinte com 'Sim'/'Não' e, abaixo, uma linha por capital.
    As notas de rodapé aparecem duplicadas e são descartadas.
    """
    # 1) linha dos problemas: a que contém "Pouco espaço"
    row_prob = raw.index[raw.eq("Pouco espaço").any(axis=1)][0]
    # 2) linha Sim/Não: a primeira linha abaixo com "Sim"
    row_sn = raw.index[(raw.index > row_prob) & raw.eq("Sim").any(axis=1)][0]

    # propaga o nome do problema para a coluna "Não" vizinha (forward fill horizontal)
    problemas = raw.loc[row_prob].ffill()
    respostas = raw.loc[row_sn]
    colunas = {
        c: (problemas[c], respostas[c])
        for c in raw.columns[1:]
        if pd.notna(problemas[c]) and pd.notna(respostas[c])
    }

    # 3) linhas de dados: após Sim/Não, linhas com nome de capital e valor numérico
    bloco = raw.loc[row_sn + 1:].copy()
    primeira_col = list(colunas)[0]
    bloco = bloco[bloco[0].notna()
                  & pd.to_numeric(bloco[primeira_col], errors="coerce").notna()]

    registros = []
    for _, linha in bloco.iterrows():
        capital = str(linha[0]).strip()
        for col, (prob, resp) in colunas.items():
            registros.append(
                {"capital": capital, "problema_original": prob, "resposta": resp,
                 "percentual": pd.to_numeric(linha[col], errors="coerce")}
            )
    longo = pd.DataFrame(registros)

    # 4) pivot Sim/Não -> colunas
    tidy = (longo.pivot_table(index=["capital", "problema_original"], columns="resposta",
                              values="percentual", aggfunc="first")
            .rename(columns={"Sim": "pct_sim", "Não": "pct_nao"})
            .reset_index())
    tidy.columns.name = None
    return tidy


def enrich(tidy: pd.DataFrame) -> pd.DataFrame:
    """Cria colunas derivadas (problema, região, ranking) sem alterar os valores originais."""
    df = tidy.copy()
    df["problema"] = df["problema_original"].map(SLUGS)
    df["regiao"] = df["capital"].map(REGIAO)
    df["ano_referencia"] = "2002-2003"
    df["rank_capital_no_problema"] = (
        df.groupby("problema")["pct_sim"].rank(ascending=False, method="min").astype(int)
    )
    cols = ["capital", "regiao", "problema", "problema_original", "pct_sim", "pct_nao",
            "rank_capital_no_problema", "ano_referencia"]
    return df[cols].sort_values(["problema", "rank_capital_no_problema"]).reset_index(drop=True)


def validate(df: pd.DataFrame) -> dict:
    """Regras de qualidade: 12 capitais, 8 problemas, sem nulos, Sim+Não≈100, faixa [0,100]."""
    erros = []
    if df["capital"].nunique() != 12:
        erros.append(f"esperadas 12 capitais, encontradas {df['capital'].nunique()}")
    if df["problema"].nunique() != 8 or df["problema"].isna().any():
        erros.append("problemas não mapeados ou em quantidade diferente de 8")
    if df[["pct_sim", "pct_nao"]].isna().any().any():
        erros.append("há valores ausentes")
    if not np.allclose(df["pct_sim"] + df["pct_nao"], 100, atol=0.05):
        erros.append("Sim + Não difere de 100% em alguma linha")
    if not df["pct_sim"].between(0, 100).all():
        erros.append("percentual fora de [0, 100]")
    if df["regiao"].isna().any():
        erros.append("capital sem região mapeada")
    if erros:
        raise ValueError("Validação falhou: " + "; ".join(erros))
    return {"linhas": len(df), "capitais": 12, "problemas": 8, "nulos": 0}


def to_wide(df: pd.DataFrame) -> pd.DataFrame:
    """Matriz capital x problema (% Sim) para correlações e mapas de calor."""
    return df.pivot(index="capital", columns="problema", values="pct_sim")


def run(raw_path: Path = RAW_DEFAULT, out_dir: Path = OUT_DIR_DEFAULT) -> pd.DataFrame:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = enrich(parse_wide(read_raw(raw_path)))
    resumo = validate(df)
    df.to_csv(out_dir / "problemas_domicilio_capitais.csv.gz", index=False,
              compression="gzip", encoding="utf-8")
    to_wide(df).to_csv(out_dir / "matriz_capital_problema.csv.gz",
                       compression="gzip", encoding="utf-8")
    print("ETL concluído:", resumo)
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=RAW_DEFAULT)
    ap.add_argument("--out", type=Path, default=OUT_DIR_DEFAULT)
    a = ap.parse_args()
    run(a.raw, a.out)
