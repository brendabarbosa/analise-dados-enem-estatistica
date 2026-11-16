"""Gera a amostra aleatória simples dos participantes do ENEM 2023 no RS e salva em CSV.

Uso:
    python gerar_amostra.py

Lê PARTICIPANTES_FILE, que já contém só os participantes do Rio Grande do Sul presentes
nas quatro provas objetivas (a população do estudo), e sorteia TAMANHO_AMOSTRA
participantes sem reposição, com semente fixa para que a amostra seja reprodutível.
O resultado é salvo em AMOSTRA_FILE. Os dois arquivos são consumidos pelo app.py.
"""

from pathlib import Path

import polars as pl

PARTICIPANTES_FILE = "data/PARTICIPANTES_ENEM_2023_RS.csv"
AMOSTRA_FILE = "data/AMOSTRA_ENEM_2023_RS.csv"

COLUMNS = [
    "TP_FAIXA_ETARIA", "TP_SEXO", "TP_COR_RACA", "TP_ESCOLA", "IN_TREINEIRO",
    "TP_ST_CONCLUSAO",
    "SG_UF_PROVA", "Q006",
    "NO_MUNICIPIO_PROVA",
    "CO_MUNICIPIO_ESC", "NO_MUNICIPIO_ESC", "SG_UF_ESC",
    "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO",
    "TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT",
]

# Tamanho obtido na calculadora de tamanho amostral da SurveyMonkey
# (https://pt.surveymonkey.com/learn/research-and-analysis/sample-size-calculator/)
# com: população N = 110.735, nível de confiança de 95%, margem de erro de 2% e proporção de 50%.
TAMANHO_AMOSTRA = 2_351
CONFIANCA_AMOSTRA = 0.95
MARGEM_ERRO_AMOSTRA = 0.02
PROPORCAO_AMOSTRA = 0.50
CALCULADORA_URL = "https://pt.surveymonkey.com/learn/research-and-analysis/sample-size-calculator/"
SEMENTE_AMOSTRA = 42  # semente fixa para a amostra ser reprodutível


def carregar_participantes() -> pl.DataFrame:
    """Participantes do RS presentes nas quatro provas objetivas (a população do estudo)."""
    return pl.read_csv(PARTICIPANTES_FILE, separator=";", columns=COLUMNS)


def gerar_amostra(participantes: pl.DataFrame) -> pl.DataFrame:
    return participantes.sample(n=TAMANHO_AMOSTRA, with_replacement=False, seed=SEMENTE_AMOSTRA)


if __name__ == "__main__":
    if not Path(PARTICIPANTES_FILE).exists():
        raise SystemExit(f"Arquivo de participantes não encontrado: {PARTICIPANTES_FILE}")
    amostra = gerar_amostra(carregar_participantes())
    amostra.write_csv(AMOSTRA_FILE, separator=";")
    print(f"Amostra com {amostra.height:,} participantes salva em {AMOSTRA_FILE}".replace(",", "."))
