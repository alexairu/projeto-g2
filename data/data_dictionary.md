# Dicionário de dados

**Fonte:** IBGE, Pesquisa de Orçamentos Familiares (POF) 2002-2003, Tabela 1461 – *Famílias, por existência de problemas no domicílio, segundo as 12 maiores capitais, 2002-2003 (%)*. Tabela adaptada pela equipe do IPP (Instituto Municipal de Urbanismo Pereira Passos) em fev. 2005 e disponibilizada no Armazém de Dados / data.rio.
**Granularidade:** uma linha por *capital × problema*. Dados agregados (percentuais); não há microdados.
**Informante:** um único membro indicado pela família respondeu "sim" ou "não" para cada um dos 8 problemas apresentados.
**Licença dos dados derivados:** CC BY 4.0 (os dados brutos mantêm os termos do IBGE/IPP).

## `data/raw/1461.xls`
Planilha original, sem alterações: formato Excel 97-2003, página de código 1252, título, cabeçalho em duas linhas com células mescladas (problema / Sim–Não) e notas de rodapé duplicadas.

## `data/processed/problemas_domicilio_capitais.csv.gz` (formato tidy)
UTF-8, separador `,`, compressão gzip, 96 linhas (12 capitais × 8 problemas).

| Variável | Tipo | Formato / domínio | Descrição |
|---|---|---|---|
| `capital` | string | 12 valores (ex.: "Belém") | Capital onde a família reside. |
| `regiao` | string | Norte, Nordeste, Sudeste, Sul, Centro-Oeste | Macrorregião IBGE da capital. **Derivada** (não consta na fonte). |
| `problema` | string | snake_case, 8 valores | Identificador curto do problema (ver tabela abaixo). **Derivada**. |
| `problema_original` | string | texto da fonte | Rótulo literal da coluna na planilha original. |
| `pct_sim` | float64 | 0–100, 2 casas decimais | % de famílias que **relataram** o problema. |
| `pct_nao` | float64 | 0–100, 2 casas decimais | % de famílias que **não** relataram o problema. `pct_sim + pct_nao = 100`. |
| `rank_capital_no_problema` | int64 | 1–12 | Posição da capital no problema (1 = maior `pct_sim`; empates recebem o mesmo rank). **Derivada**. |
| `ano_referencia` | string | "2002-2003" | Período de coleta da POF. |

### Valores de `problema`
| `problema` | Rótulo original |
|---|---|
| `pouco_espaco` | Pouco espaço |
| `barulho` | Rua ou vizinhos barulhentos |
| `casa_escura` | Casa escura |
| `goteira` | Telhado com goteira |
| `umidade` | Fundação, paredes ou chão úmidos |
| `madeira_deteriorada` | Madeira das janelas, portas ou assoalhos deteriorados |
| `poluicao` | Poluição ou problemas ambientais causados pelo trânsito ou indústria |
| `violencia` | Violência ou vandalismo na área de residência |

## `data/processed/matriz_capital_problema.csv.gz` (formato largo)
Índice = `capital` (12 linhas); 8 colunas = valores de `problema`; células = `pct_sim` (float64, 0–100). Usada para correlações e mapas de calor.

## Valores ausentes e regras de qualidade
Não há valores ausentes. `src/etl.py::validate` interrompe o pipeline se houver: número de capitais ≠ 12 ou de problemas ≠ 8; nulos; `pct_sim + pct_nao` ≠ 100 (tolerância 0,05); valores fora de [0, 100]; capital sem região mapeada.

## Métricas derivadas no artigo (não persistidas no CSV)
- **Índice médio de incidência** da capital: média aritmética simples dos 8 valores de `pct_sim`.
- **Índice estrutural**: média de `goteira`, `umidade` e `madeira_deteriorada`.
- **Coeficiente de variação (CV)** por problema: desvio-padrão amostral ÷ média.
- **z-score** por problema: (valor − média) ÷ desvio-padrão; |z| ≥ 1,8 é tratado como valor extremo.
