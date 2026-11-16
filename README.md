# Problemas no domicílio nas 12 maiores capitais brasileiras: análise exploratória da POF 2002-2003

![Python](https://img.shields.io/badge/Python-3.12%2B-blue) ![Código: MIT](https://img.shields.io/badge/c%C3%B3digo-MIT-green) ![Dados: CC BY 4.0](https://img.shields.io/badge/dados-CC%20BY%204.0-lightgrey) ![FAIR](https://img.shields.io/badge/FAIR-compliant-orange)

**Autor:** Alexandre Souza de Abreu Junior
**Instituição:** Centro Universitário La Salle do Rio de Janeiro · Bacharelado em Sistemas de Informação · 6º período
**Disciplina:** Linguagens de Programação (Análise e Visualização de Dados com Python) · 2026.2
**Professor:** Prof. Alexandre Neves Louzada
**Artigo publicado:** https://alexairu.github.io/projeto-g2/

## Resumo
Pipeline reprodutível em Python que trata a Tabela 1461 da POF 2002-2003 (IBGE), com o percentual de famílias que relataram 8 problemas no domicílio em 12 capitais, e um artigo acadêmico em HTML com os resultados. Principais achados: violência/vandalismo (45,3%) e pouco espaço (43,6%) são os problemas mais frequentes; Belém tem o maior índice médio de incidência (46,6%) e Brasília o menor (15,7%); goteira, umidade e madeira deteriorada são fortemente correlacionadas (ρ de Spearman 0,82–0,85).

**Palavras-chave:** condições de moradia; POF 2002-2003; capitais brasileiras; análise exploratória de dados; ciência aberta.

## Perguntas de pesquisa
- **RQ1.** Quais problemas são mais frequentes e quanto variam entre capitais?
- **RQ2.** Quais capitais e regiões concentram mais problemas?
- **RQ3.** Os problemas ocorrem de forma associada?

## Fonte dos dados
IBGE, Pesquisa de Orçamentos Familiares 2002-2003. Tabela 1461 adaptada pelo IPP (Instituto Municipal de Urbanismo Pereira Passos), fev. 2005.
Link original (data.rio / Armazém de Dados): https://www.data.rio/documents/21e108c3f4574658bd06759c6602b9e3/about
Cópia sem alterações em `data/raw/1461.xls`.

## Estrutura
```
├── data/
│   ├── raw/1461.xls                         # planilha original
│   ├── processed/
│   │   ├── problemas_domicilio_capitais.csv.gz  # tidy: capital × problema (96 linhas)
│   │   └── matriz_capital_problema.csv.gz       # largo: 12 × 8 (% sim)
│   └── data_dictionary.md
├── notebooks/analise_exploratoria.ipynb     # exploração e validação
├── src/
│   ├── etl.py                               # leitura, reestruturação, validação, persistência
│   └── analise.py                           # estatísticas e figuras do artigo
└── docs/                                    # artigo (GitHub Pages)
    ├── index.html
    └── assets/                              # figuras PNG + estatisticas.json
```

## Como reproduzir
```bash
git clone https://github.com/alexairu/projeto-g2.git
cd projeto-g2
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.etl                # gera data/processed/
python -m src.analise            # gera docs/assets/
```
Para abrir o artigo localmente, abra `docs/index.html` no navegador.

Para executar o notebook: `pip install notebook` e depois `jupyter notebook notebooks/analise_exploratoria.ipynb` (a partir da raiz do repositório).

## Publicação no GitHub Pages
*Settings → Pages → Build and deployment → Deploy from a branch → `main` / pasta `/docs`.*

## Licenças
- Código: MIT (`LICENSE`).
- Dados derivados e texto do artigo: CC BY 4.0.
- Dados brutos: termos originais do IBGE/IPP.

## Como citar
ABREU JUNIOR, Alexandre Souza de. *Problemas no domicílio nas 12 maiores capitais brasileiras: análise exploratória da POF 2002-2003*. Rio de Janeiro: Centro Universitário La Salle do Rio de Janeiro, 2026. Disponível em: https://github.com/alexairu/projeto-g2.
