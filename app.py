import altair as alt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import polars as pl
import streamlit as st

st.set_page_config(
    page_title="ENEM — RS",
    page_icon=":material/bar_chart:",
    layout="wide",
)

st.markdown(
    "<style>"
    "div[data-testid='stCaptionContainer'] p { text-align: justify; }"
    " section[data-testid='stSidebar'] .stMarkdown a { color: #ffffff; }"
    #" [data-testid='stMetricLabel'] * { font-weight: 700 !important; }"
    " .stMainBlockContainer { padding-top: 1rem !important; }"
    "</style>",
    unsafe_allow_html=True,
)

# ============================================================
# CONSTANTES E MAPEAMENTOS
# ============================================================

# colunas, arquivos e parâmetros da amostra ficam em gerar_amostra.py (fonte única)
from gerar_amostra import (
    AMOSTRA_FILE, CALCULADORA_URL, COLUMNS, CONFIANCA_AMOSTRA, MARGEM_ERRO_AMOSTRA,
    PARTICIPANTES_FILE, PROPORCAO_AMOSTRA, SEMENTE_AMOSTRA, TAMANHO_AMOSTRA,
)

NOTAS_COLS    = ["NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO"]
N_VARIAVEIS_ORIGINAIS = 76  # colunas do arquivo MICRODADOS_ENEM_2023.csv (INEP)

# Proporção de pessoas autodeclaradas brancas no RS — Censo Demográfico 2022 (IBGE): 78,4%.
# Fonte: https://agenciadenoticias.ibge.gov.br/agencia-noticias/2012-agenciade-noticias/noticias/38719-censo-2022-pela-primeira-vez-desde-1991a-maior-parte-da-populacao-do-brasil-se-declara-parda
P0_BRANCOS_CENSO = 0.784
IBGE_CENSO_RS_URL = "https://www.ibge.gov.br/cidades-e-estados/rs.html"
MU0_MATEMATICA = 500  # média de referência da escala de notas do ENEM
INEP_GUIA_NOTA_URL = (
    "https://www.gov.br/inep/pt-br/centrais-de-conteudo/acervo-linha-editorial/publicacoes-institucionais/"
    "avaliacoes-e-exames-da-educacao-basica/entenda-a-sua-nota-no-enem-guia-do-participante"
)

FAIXA_ETARIA_MAP = {
    1: "Menor de 17 anos", 2: "17 anos", 3: "18 anos", 4: "19 anos", 5: "20 anos",
    6: "21 anos", 7: "22 anos", 8: "23 anos", 9: "24 anos", 10: "25 anos",
    11: "Entre 26 e 30 anos", 12: "Entre 31 e 35 anos", 13: "Entre 36 e 40 anos",
    14: "Entre 41 e 45 anos", 15: "Entre 46 e 50 anos", 16: "Entre 51 e 55 anos",
    17: "Entre 56 e 60 anos", 18: "Entre 61 e 65 anos", 19: "Entre 66 e 70 anos",
    20: "Maior de 70 anos",
}
FAIXA_ORDER = list(FAIXA_ETARIA_MAP.values())

RACA_MAP = {
    0: "Não declarado", 1: "Branca", 2: "Preta", 3: "Parda",
    4: "Amarela", 5: "Indígena", 6: "Não dispõe da informação",
}

ESCOLA_MAP = {1: "Não Respondeu", 2: "Pública", 3: "Privada"}

ST_CONCLUSAO_MAP = {
    1: "Já concluiu o Ensino Médio",
    2: "Concluirá no ano do exame",
    3: "Concluirá após o ano do exame",
    4: "Não concluiu e não está cursando",
}

NOTAS_PROVAS = {
    "NU_NOTA_CN":      "Ciências da Natureza",
    "NU_NOTA_CH":      "Ciências Humanas",
    "NU_NOTA_LC":      "Linguagens",
    "NU_NOTA_MT":      "Matemática",
    "NU_NOTA_REDACAO": "Redação",
}

CORES_AREAS = {
    "Ciências da Natureza": "#D97A5C",
    "Ciências Humanas":     "#E9B44C",
    "Linguagens":           "#47A398",
    "Matemática":           "#7B5EA7",
    "Redação":              "#8BC9D0",
}

MAPA_RENDA_SM = {
    "A": "Sem renda",
    "B": "Até 2 SM", "C": "Até 2 SM", "D": "Até 2 SM",
    "E": "2 a 4 SM",  "F": "2 a 4 SM",  "G": "2 a 4 SM",
    "H": "4 a 8 SM",  "I": "4 a 8 SM",  "J": "4 a 8 SM", "K": "4 a 8 SM",
    "L": "8 a 12 SM", "M": "8 a 12 SM", "N": "8 a 12 SM",
    "O": "Acima de 12 SM", "P": "Acima de 12 SM", "Q": "Acima de 12 SM",
}
ANO = 2023
SALARIO_MINIMO = 1_320  # salário mínimo vigente em 2023
ORDEM_SM = ["Sem renda", "Até 2 SM", "2 a 4 SM", "4 a 8 SM", "8 a 12 SM", "Acima de 12 SM"]

FAIXA_ETARIA_AGRUPADA = {
    1:  "Até 17 anos",
    2:  "Até 17 anos",
    3:  "18 anos",
    4:  "19 anos",
    5:  "20-24 anos",
    6:  "20-24 anos",
    7:  "20-24 anos",
    8:  "20-24 anos",
    9:  "20-24 anos",
    10: "25-30 anos",
    11: "25-30 anos",
    12: "31-40 anos",
    13: "31-40 anos",
    14: "41-50 anos",
    15: "41-50 anos",
    16: "51-70 anos",
    17: "51-70 anos",
    18: "51-70 anos",
    19: "51-70 anos",
    20: "Mais de 70 anos",
}
ORDEM_FAIXA_AGRUPADA = ["Até 17 anos", "18 anos", "19 anos", "20-24 anos", "25-30 anos", "31-40 anos", "41-50 anos", "51-70 anos", "Mais de 70 anos"]

AREA_OPTIONS = {
    "Ciências da Natureza": "NU_NOTA_CN",
    "Ciências Humanas":     "NU_NOTA_CH",
    "Linguagens":           "NU_NOTA_LC",
    "Matemática":           "NU_NOTA_MT",
    "Redação":              "NU_NOTA_REDACAO",
    "Média Geral":          "MEDIA_GERAL",
}

COR_PUBLICA  = "#4E79D9"
COR_PRIVADA  = "#F28E2B"
COR_NEUTRO   = "#B8C2CC"   # Não informado
COR_NEUTRO2  = "#D6DCE5"   # Sem resposta
COR_OUTROS   = "#94A3B8"   # Outros / residual

CORES_ESCOLA = {
    "Pública":        "#4E79D9",
    "Privada":        "#F28E2B",
    "Não Respondeu":  "#B8C2CC",
}

CORES_SEXO = {
    "Masculino":     "#4E79D9",
    "Feminino":      "#D46A92",
    "Não Informado": "#B8C2CC",
}

CORES_RACA = {
    "Branca":                    "#5D5C86",
    "Parda":                     "#5D5C86",
    "Preta":                     "#5D5C86",
    "Amarela":                   "#5D5C86",
    "Indígena":                  "#5D5C86",
    "Não declarado":             "#B8C2CC",
    "Não dispõe da informação":  "#D6DCE5",
}

CHART_HEIGHT = 550


def _heatmap_annotations(pivot, col_labels, threshold=35):
    """Build Plotly annotation dicts for a heatmap pivot (rows × cols)."""
    anns = []
    for ri, row_label in enumerate(pivot.index.tolist()):
        for ci, col_label in enumerate(col_labels):
            val = pivot.values[ri, ci]
            txt = f"{val:.1f}%" if not np.isnan(val) else "—"
            ink = "#0b0b0b" if (not np.isnan(val) and val < threshold) else "#ffffff"
            anns.append(dict(
                x=col_label, y=row_label,
                text=f"<b>{txt}</b>",
                showarrow=False,
                font=dict(size=12, color=ink),
                xref="x", yref="y",
            ))
    return anns


def _interp_color(v, stops=None):
    """Linearly interpolate a hex colour from a list of (pos, hex) stops."""
    if stops is None:
        stops = [
            (0.0, "#fde8e8"), (0.25, "#f4a9a9"),
            (0.5, "#e86262"), (0.75, "#c93232"), (1.0, "#8b0000"),
        ]
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= v <= t1:
            f = (v - t0) / (t1 - t0)
            r = int(int(c0[1:3], 16) + f * (int(c1[1:3], 16) - int(c0[1:3], 16)))
            g = int(int(c0[3:5], 16) + f * (int(c1[3:5], 16) - int(c0[3:5], 16)))
            b = int(int(c0[5:7], 16) + f * (int(c1[5:7], 16) - int(c0[5:7], 16)))
            return f"#{r:02x}{g:02x}{b:02x}"
    return stops[-1][1]


# ============================================================
# CARREGAMENTO E PRÉ-PROCESSAMENTO DOS DADOS
# ============================================================

_faltando = [f for f in (PARTICIPANTES_FILE, AMOSTRA_FILE) if not __import__("pathlib").Path(f).exists()]
if _faltando:
    st.error(
        "**Arquivo de dados não encontrado.**\n\n"
        + "".join(f"- `{f}`\n" for f in _faltando)
        + "\nConsulte o **README** para instruções de como obter os microdados"
        + " e gerar os arquivos (`python gerar_amostra.py`) antes de executar o dashboard."
    )
    st.stop()


@st.cache_data
def get_participantes_dataset():
    return pl.read_csv(PARTICIPANTES_FILE, separator=";")


@st.cache_data
def get_amostra_dataset():
    return pl.read_csv(AMOSTRA_FILE, separator=";")


# Participantes do RS presentes nas quatro provas objetivas (já filtrados por gerar_amostra.py).
enem_participantes = get_participantes_dataset().select(COLUMNS)

if enem_participantes.is_empty():
    st.warning("Nenhum participante efetivo encontrado.")
    st.stop()

# Amostra aleatória simples (sem reposição) dos participantes, gerada por gerar_amostra.py.
# Os tipos das colunas são alinhados aos da população para que as análises se comportem igual.
enem_amostra = get_amostra_dataset().select(COLUMNS).cast(dict(enem_participantes.schema))


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _br(v: float, casas: int = 4) -> str:
    """Formata número no padrão brasileiro (milhar com ponto, decimal com vírgula)."""
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _notas_validas(df: pl.DataFrame) -> pl.DataFrame:
    """Regra única de notas: todas as notas registradas são consideradas, inclusive notas zero.
    Mantém quem tem as cinco notas preenchidas (não nulas) e acrescenta NOTA_GERAL = média das cinco notas."""
    return (
        df.filter(pl.all_horizontal([pl.col(c).is_not_null() for c in NOTAS_COLS]))
        .with_columns(pl.mean_horizontal(NOTAS_COLS).alias("NOTA_GERAL"))
    )




# ============================================================
# CABEÇALHO E INTRODUÇÃO
# ============================================================

st.markdown('<div id="topo"></div>', unsafe_allow_html=True)

st.title(f":material/bar_chart: Análise do Exame Nacional do Ensino Médio (ENEM) de {ANO} do Rio Grande do Sul - População x Amostra")

tab_populacao, tab_amostra, tab_comparacao = st.tabs([
    "Análise descritiva da população",
    "Análise descritiva da amostra",
    "Inferência estatística e comparação dos resultados"
])


# ============================================================
# SEÇÕES REUTILIZÁVEIS (população e amostra)
# ============================================================

def _render_indicadores(kpis, kpis_ref=None):
    """KPIs gerais. Quando `kpis_ref` (população) é informado, cada métrica mostra o delta amostra − população."""
    st.divider()
    st.subheader(":material/leaderboard: Indicadores gerais")
    if kpis_ref is not None:
        st.caption(
            "Os valores em cinza abaixo de cada indicador mostram a diferença **amostra − população**."
        )

    def _delta(chave, casas=2):
        if kpis_ref is None:
            return None
        dv = kpis[chave] - kpis_ref[chave]
        return f"{'+' if dv >= 0 else ''}{_br(dv, casas)}"


    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.metric("Total de Participantes", _br(kpis["total_participantes"], 0))
    with col2:
        with st.container(border=True):
            st.metric(
                "Média de todas as notas",
                _br(kpis["media_geral"], 2),
                delta=_delta("media_geral"), delta_color="off",
                help=(
                    "Média aritmética de todas as notas válidas, considerando as cinco áreas em conjunto "
                    "(CN, CH, LC, MT e Redação) como um único conjunto de valores. Difere da \"nota geral\", "
                    "que é a média das cinco notas calculada por participante." 
                ),
            )
    with col3:
        with st.container(border=True):
            st.metric(
                "Mediana de todas as notas",
                _br(kpis["mediana_geral"], 2),
                delta=_delta("mediana_geral"), delta_color="off",
                help=(
                    "Valor central de todas as notas válidas das cinco áreas em conjunto: "
                    "metade das notas fica abaixo e metade acima desse valor. "
                    "É menos sensível a valores extremos que a média." 
                ),
            )



def _render_analises(participantes: pl.DataFrame, chave: str, ref: pl.DataFrame | None = None):
    """Seções: faixa etária e sexo, cor/raça, perfil escolar e distribuição das notas.
    `ref` (população) é usado apenas para exibir deltas nas medidas descritivas da amostra."""
    st.divider()

    # --- Seção 1: Distribuição por Faixa Etária e Sexo ---
    st.subheader(":material/person: Distribuição por faixa etária e sexo")

    st.caption(
        "A pirâmide etária compara o volume de participantes femininos e masculinos em cada faixa, "
        "permitindo identificar em quais faixas a diferença entre os sexos é mais acentuada. "
        "O gráfico ao lado mostra o total geral por sexo."
    )

    # --- Pirâmide etária ---
    # Mapeamento final: códigos 1-20 → rótulos da pirâmide (51-70 já mesclados)
    _FAIXA_MAP_PYRAMID = {
        1: "Menor de 17 anos", 2: "17 anos", 3: "18 anos", 4: "19 anos",
        5: "20 anos", 6: "21 anos", 7: "22 anos", 8: "23 anos", 9: "24 anos",
        10: "25 anos", 11: "Entre 26 e 30 anos", 12: "Entre 31 e 35 anos",
        13: "Entre 36 e 40 anos", 14: "Entre 41 e 45 anos", 15: "Entre 46 e 50 anos",
        16: "Entre 51 e 70 anos", 17: "Entre 51 e 70 anos",
        18: "Entre 51 e 70 anos", 19: "Entre 51 e 70 anos",
        20: "Maior de 70 anos",
    }
    _FAIXA_ORDER_PYRAMID = list(dict.fromkeys(_FAIXA_MAP_PYRAMID.values()))

    pyramid_source = (
        participantes
        .filter(pl.col("TP_FAIXA_ETARIA").is_in(list(_FAIXA_MAP_PYRAMID.keys())))
        .with_columns([
            pl.col("TP_FAIXA_ETARIA").cast(pl.String)
              .replace({str(k): v for k, v in _FAIXA_MAP_PYRAMID.items()})
              .alias("faixa_etaria"),
            pl.col("TP_SEXO")
              .replace({"M": "Masculino", "F": "Feminino"}).cast(pl.String)
              .alias("sexo"),
        ])
        .group_by("faixa_etaria", "sexo")
        .agg(pl.len().alias("total"))
    )

    pyramid_df = pyramid_source.to_pandas()
    pyramid_df["pct"] = (pyramid_df["total"] / pyramid_df["total"].sum() * 100).round(2)
    gender_df  = (
        pyramid_source
        .group_by("sexo")
        .agg(pl.col("total").sum().alias("total"))
        .sort("sexo")
        .to_pandas()
    )
    gender_df["pct"] = (gender_df["total"] / gender_df["total"].sum() * 100).round(2)

    col_pyramid, col_gender = st.columns([6, 2], gap="large")

    if not pyramid_df.empty:
        color_scale = alt.Scale(
            domain=["Masculino", "Feminino"],
            range=[CORES_SEXO["Masculino"], CORES_SEXO["Feminino"]],
        )

        _max_pyramid = int(pyramid_df["total"].max())
        _x_scale = alt.Scale(domain=[0, _max_pyramid])

        with col_pyramid:
            base = alt.Chart(pyramid_df)

            nearest = alt.selection_point(nearest=True, on="pointerover", fields=["faixa_etaria"], empty=False)

            left = (
                base.transform_filter(alt.datum.sexo == "Feminino")
                .encode(
                    alt.Y("faixa_etaria:O").sort(_FAIXA_ORDER_PYRAMID).axis(None),
                    alt.X("total:Q").title("Quantidade").sort("descending").scale(_x_scale),
                    alt.Color("sexo:N").scale(color_scale).title("Sexo"),
                    tooltip=["faixa_etaria:N", "sexo:N", "total:Q", alt.Tooltip("pct:Q", title="% do total")],
                    opacity=alt.condition(nearest, alt.value(1), alt.value(0.8)),
                )
                .mark_bar()
                .add_params(nearest)
                .properties(title="Feminino", height=420)
            )

            middle = (
                base.encode(
                    alt.Y("faixa_etaria:O").sort(_FAIXA_ORDER_PYRAMID).axis(None),
                    alt.Text("faixa_etaria:N"),
                )
                .mark_text(fontSize=10)
                .properties(width=150, height=420)
            )

            nearest_right = alt.selection_point(nearest=True, on="pointerover", fields=["faixa_etaria"], empty=False)

            right = (
                base.transform_filter(alt.datum.sexo == "Masculino")
                .encode(
                    alt.Y("faixa_etaria:O").sort(_FAIXA_ORDER_PYRAMID).axis(None),
                    alt.X("total:Q").title("Quantidade").scale(_x_scale),
                    alt.Color("sexo:N").scale(color_scale).title("Sexo"),
                    tooltip=["faixa_etaria:N", "sexo:N", "total:Q", alt.Tooltip("pct:Q", title="% do total")],
                    opacity=alt.condition(nearest_right, alt.value(1), alt.value(0.8)),
                )
                .mark_bar()
                .add_params(nearest_right)
                .properties(title="Masculino", height=420)
            )

            pyramid_chart = (
                alt.hconcat(left, middle, right, spacing=5)
                .resolve_scale(x="independent", color="shared")
                .properties(title="Distribuição por faixa etária e sexo")
                .configure_view(stroke=None)
                .configure_title(fontSize=14, anchor="middle")
                .configure_legend(orient="bottom", title=None, labelFontSize=12)
            )
            st.altair_chart(pyramid_chart, width="stretch")

        with col_gender:
            gender_chart = (
                alt.Chart(gender_df)
                .transform_calculate(sexo_abrev="datum.sexo == 'Feminino' ? 'F' : 'M'")
                .mark_bar()
                .encode(
                    alt.X("sexo_abrev:N").title(None).sort(["F", "M"]).axis(labelAngle=0),
                    alt.Y("total:Q").title("Participantes"),
                    alt.Color("sexo:N").scale(color_scale).legend(None),
                    tooltip=["sexo:N", "total:Q", alt.Tooltip("pct:Q", title="% do total")],
                )
                .properties(title="Distribuição por sexo", height=540, padding={"top": 40, "left": 5, "right": 5, "bottom": 5})
                .configure_title(fontSize=14, anchor="middle")
            )
            st.altair_chart(gender_chart, width="stretch")

    # --- Seção: Distribuição por cor/raça ---
    st.divider()
    st.subheader(":material/diversity_3: Distribuição por cor/raça")
    st.caption(
        "Número de participantes por cor/raça autodeclarada, em ordem decrescente. "
        "Passe o cursor sobre as barras para ver o total e o percentual de cada grupo."
    )
    col_raca = st.columns(1)[0]

    with col_raca:
        raca_df = (
            participantes
            .filter(pl.col("TP_COR_RACA").is_not_null())
            .with_columns(
                pl.col("TP_COR_RACA").cast(pl.String)
                  .replace({str(k): v for k, v in RACA_MAP.items()}).alias("raca")
            )
            .group_by("raca").agg(pl.len().alias("total"))
            .to_pandas()
        )
        _total_raca = raca_df["total"].sum()
        raca_df["pct"] = (raca_df["total"] / _total_raca * 100).round(1)
        nearest_raca = alt.selection_point(nearest=True, on="pointerover", fields=["raca"], empty=False)
        st.altair_chart(
            alt.Chart(raca_df).mark_bar().encode(
                alt.X("total:Q").title("Participantes"),
                alt.Y("raca:N").title(None).sort("-x"),
                alt.Color("raca:N").scale(
                    alt.Scale(
                        domain=list(CORES_RACA.keys()),
                        range=list(CORES_RACA.values()),
                    )
                ).legend(None),
                alt.Tooltip(["raca:N", "total:Q", "pct:Q"]),
                opacity=alt.condition(nearest_raca, alt.value(1), alt.value(1)),
            ).add_params(nearest_raca).properties(title="Participantes por cor/raça autodeclarada", height=280),
            width="stretch",
        )


    # --- Seção 2: Perfil Escolar ---
    st.divider()
    st.subheader(":material/school: Perfil escolar")
    st.caption(
        "Distribuição dos participantes por tipo de escola (pública ou privada) e por situação de conclusão do Ensino Médio. "
        "Apenas participantes que declararam escola pública ou privada são incluídos no gráfico de tipo de escola."
    )

    col_escola, col_conclusao = st.columns([2,4], gap="large")


    with col_escola:
        escola_df = (
            participantes
            .filter(pl.col("TP_ESCOLA").is_in([2, 3]))
            .with_columns(
                pl.col("TP_ESCOLA")
                  .replace_strict(ESCOLA_MAP, default="Não Respondeu", return_dtype=pl.String)
                  .alias("escola")
            )
            .group_by("escola").agg(pl.len().alias("total"))
            .to_pandas()
        )
        _total_escola = escola_df["total"].sum()
        escola_df["pct"] = (escola_df["total"] / _total_escola * 100).round(1)
        escola_df["_grupo"] = "Participantes"
        _ordem_escola_emp = ["Pública", "Privada"]
        st.altair_chart(
            alt.Chart(escola_df).mark_bar().encode(
                alt.X("total:Q").title("Participantes").stack("normalize"),
                alt.Y("_grupo:N").title(None),
                alt.Color("escola:N").scale(
                    alt.Scale(
                        domain=_ordem_escola_emp,
                        range=[CORES_ESCOLA["Pública"], CORES_ESCOLA["Privada"]],
                    )
                ).legend(orient="bottom", title=None),
                alt.Order("escola:N", sort="ascending"),
                alt.Tooltip(["escola:N", "total:Q", "pct:Q"]),
            ).properties(title="Participantes por tipo de escola", height=250),
            width="stretch",
        )

    with col_conclusao:
        conclusao_df = (
            participantes
            .filter(pl.col("TP_ST_CONCLUSAO").is_not_null())
            .with_columns(
                pl.col("TP_ST_CONCLUSAO").cast(pl.String)
                  .replace({str(k): v for k, v in ST_CONCLUSAO_MAP.items()}).alias("situacao")
            )
            .group_by("situacao").agg(pl.len().alias("total"))
            .to_pandas()
        )
        _total_conclusao = conclusao_df["total"].sum()
        conclusao_df["pct"] = (conclusao_df["total"] / _total_conclusao * 100).round(1)
        _ordem_conclusao = list(ST_CONCLUSAO_MAP.values())
        nearest_conclusao = alt.selection_point(nearest=True, on="pointerover", fields=["situacao"], empty=False)
        st.altair_chart(
            alt.Chart(conclusao_df).mark_bar().encode(
                alt.X("total:Q").title("Participantes"),
                alt.Y("situacao:N").title(None).sort(_ordem_conclusao).axis(labelLimit=230, labelFontSize=12),
                alt.Color("situacao:N").scale(
                    alt.Scale(
                        domain=_ordem_conclusao,
                        range=["#0F6E56", "#534AB7", "#D85A30", "#B4B2A9"],
                    )
                ).legend(None),
                alt.Tooltip(["situacao:N", "total:Q", "pct:Q"]),
                opacity=alt.condition(nearest_conclusao, alt.value(1), alt.value(1)),
            ).add_params(nearest_conclusao).properties(title="Situação escolar dos participantes", height=200),
            width="stretch",
        )



    st.divider()
    # --- Seção 1: Distribuição das Notas ---
    st.subheader(":material/bar_chart: Distribuição das notas por área do conhecimento")
    st.caption(
        "Distribuição das notas dos participantes em cada uma das cinco áreas do ENEM. "
        "A caixa cobre os 50% centrais (Q1–Q3) e a linha central indica a mediana; "
        "valores fora dos limites são considerados outliers e não são exibidos. "
        "Passe o cursor para ver os valores detalhados de cada área. "
        "Abaixo, o histograma mostra a distribuição completa das notas, com a nota geral como visão padrão "
        "e a opção de alternar para cada área."
    )
    # todas as notas registradas são consideradas, inclusive notas zero (regra única do app)
    enem_df_geral = (
        participantes
        .select(list(NOTAS_PROVAS.keys()))
        .to_pandas()
    )

    fig_box   = go.Figure()
    annotations = []

    for coluna, titulo in NOTAS_PROVAS.items():
        dados   = enem_df_geral[coluna].dropna()
        mediana = round(dados.median(), 0)
        cor     = CORES_AREAS[titulo]
        fig_box.add_trace(go.Box(
            y=dados, name=titulo,
            boxpoints=False,
            marker_color=cor, line_color=cor, fillcolor=cor, opacity=0.8,
            hovertemplate=(
                f"<b>{titulo}</b><br>"
                "Máx (sem outliers): %{upperfence:.0f}<br>"
                "Q3: %{q3:.0f}<br>"
                "Mediana: %{median:.0f}<br>"
                "Q1: %{q1:.0f}<br>"
                "Mín (sem outliers): %{lowerfence:.0f}<extra></extra>"
            ),
        ))
        annotations.append(dict(
            x=titulo, y=mediana,
            text=f"<b>{mediana:.0f}</b>",
            showarrow=False, xanchor="left", xshift=22,
            font=dict(size=10, color=cor),
        ))

    fig_box.update_layout(
        title=dict(text="Distribuição das notas por área do conhecimento", x=0.5, xanchor="center", font=dict(size=15)),
        yaxis=dict(title="Nota", range=[300, 900], tickfont=dict(size=11)),
        xaxis=dict(tickfont=dict(size=11)),
        showlegend=False,
        annotations=annotations,
        margin=dict(t=60, b=40, l=60, r=20),
        height=420,
    )
    st.plotly_chart(fig_box, width="stretch")

    # --- Histograma interativo das notas (mesma seção) ---

    _HIST_OPCOES = {
        "Nota geral":           None,
        "Ciências da Natureza": ("NU_NOTA_CN", "TP_PRESENCA_CN"),
        "Ciências Humanas":     ("NU_NOTA_CH", "TP_PRESENCA_CH"),
        "Linguagens e Códigos": ("NU_NOTA_LC", "TP_PRESENCA_LC"),
        "Matemática":           ("NU_NOTA_MT", "TP_PRESENCA_MT"),
        "Redação":              ("NU_NOTA_REDACAO", "TP_PRESENCA_LC"),  # redação é aplicada no 1º dia, com LC
    }
    _HIST_BIN = 50
    _HIST_EDGES = np.arange(0, 1000 + _HIST_BIN, _HIST_BIN)  # 0, 50, ..., 1000 → 20 classes

    @st.cache_data
    def _hist_notas(_df: pl.DataFrame, opcao: str, chave_cache: str) -> np.ndarray:
        """Notas não nulas para a opção escolhida, inclusive notas zero.
        A nota geral segue a regra de `_notas_validas`.
        `chave_cache` diferencia população e amostra no cache (o DataFrame não é usado no hash)."""
        if opcao == "Nota geral":
            serie = _notas_validas(_df)["NOTA_GERAL"]
        else:
            nota, presenca = _HIST_OPCOES[opcao]
            serie = _df.filter((pl.col(presenca) == 1) & pl.col(nota).is_not_null())[nota]
        return serie.cast(pl.Float64).to_numpy()

    def _medidas(v: np.ndarray) -> dict:
        n = len(v)
        media = float(np.mean(v))
        dp = float(np.std(v, ddof=1)) if n > 1 else 0.0
        return {
            "n": n, "Média": media, "Mediana": float(np.median(v)), "Desvio-padrão": dp,
            "Coef. de variação (%)": dp / media * 100 if media else 0.0,
            "Mínimo": float(np.min(v)), "Máximo": float(np.max(v)),
        }

    def _hist_pct(valores: np.ndarray):
        contagem, _ = np.histogram(np.clip(valores, 0, 1000), bins=_HIST_EDGES)
        pct = contagem / max(len(valores), 1) * 100
        return contagem, pct

    def _densidade(valores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """KDE gaussiana (regra de Silverman) calculada sobre histograma fino, em % por classe de 50 pts."""
        x = np.arange(0, 1001, 2.0)
        if len(valores) < 2:
            return x, np.zeros_like(x)
        fino, _ = np.histogram(valores, bins=np.append(x, 1002) - 1)
        h = 1.06 * np.std(valores) * len(valores) ** (-1 / 5)
        h = max(h, 2.0)
        k = np.arange(-4 * h, 4 * h + 2, 2.0)
        kernel = np.exp(-0.5 * (k / h) ** 2)
        kernel /= kernel.sum()
        dens = np.convolve(fino, kernel, mode="same") / len(valores)  # proporção por passo de 2 pts
        return x, dens * (_HIST_BIN / 2.0) * 100

    _hc1, _hc3 = st.columns([4, 1.3])
    with _hc1:
        _hist_sel = st.segmented_control(
            "Matéria", options=list(_HIST_OPCOES.keys()), default="Nota geral",
            key=f"{chave}_hist_materia",
        ) or "Nota geral"
    with _hc3:
        _hist_kde = st.toggle("Curva de densidade", value=False, key=f"{chave}_hist_kde")

    _vals = _hist_notas(participantes, _hist_sel, chave)
    _n = len(_vals)

    if _n == 0:
        st.warning("Não há notas válidas para a opção selecionada.")
    else:
        _cont, _pct = _hist_pct(_vals)
        _media, _mediana = float(np.mean(_vals)), float(np.median(_vals))
        _cor = CORES_AREAS.get(
            "Linguagens" if _hist_sel == "Linguagens e Códigos" else _hist_sel, COR_PUBLICA
        )

        # eixo Y fixo: mesmo limite para todas as matérias (maior contagem entre as seis opções)
        _ymax = max(_hist_pct(_hist_notas(participantes, o, chave))[0].max() for o in _HIST_OPCOES) * 1.15
        _escala_txt = "Eixo Y fixo para todas as matérias"

        _centros = (_HIST_EDGES[:-1] + _HIST_EDGES[1:]) / 2
        _faixas = [f"{a:.0f}–{b:.0f}" for a, b in zip(_HIST_EDGES[:-1], _HIST_EDGES[1:])]
        _COR_MEDIA, _COR_MEDIANA = "#D62728", "#1F2937"

        fig_hist = go.Figure()
        fig_hist.add_trace(go.Bar(
            x=_centros, y=_cont, width=_HIST_BIN, name="Participantes",
            marker=dict(color=_cor, line=dict(color="white", width=0.5)),
            customdata=np.column_stack([_faixas, [f"{v:.2f}".replace(".", ",") for v in _pct]]),
            hovertemplate="<b>Nota %{customdata[0]}</b><br>Participantes: %{y:,}"
                          "<br>Percentual: %{customdata[1]}%<extra></extra>",
        ))
        if _hist_kde:
            _kx, _ky = _densidade(_vals)
            fig_hist.add_trace(go.Scatter(
                x=_kx, y=_ky / 100 * _n, mode="lines", name="Densidade (suavizada)",
                line=dict(color="#374151", width=2), hoverinfo="skip",
            ))
        for _valor, _nome, _dash, _c, _pos in [
            (_media, "Média", "dash", _COR_MEDIA, 0.97),
            (_mediana, "Mediana", "solid", _COR_MEDIANA, 0.89),
        ]:
            fig_hist.add_trace(go.Scatter(
                x=[_valor, _valor], y=[0, _ymax], mode="lines",
                name=f"{_nome}: {_valor:.1f}",
                line=dict(color=_c, width=2, dash=_dash),
                hovertemplate=f"{_nome}: {_valor:.1f}<extra></extra>",
            ))
            fig_hist.add_annotation(
                x=_valor, y=_pos, yref="paper", text=f"{_nome}: {_valor:.1f}",
                showarrow=False, font=dict(color=_c, size=11),
                # o maior valor recebe o rótulo à direita da linha, o menor à esquerda
                xanchor="left" if _valor == max(_media, _mediana) else "right",
                xshift=4 if _valor == max(_media, _mediana) else -4,
                bgcolor="rgba(255,255,255,0.7)",
            )

        fig_hist.update_layout(
            title=dict(text=f"Distribuição da nota de {_hist_sel}", x=0.5, xanchor="center", font=dict(size=15)),
            xaxis=dict(title="Nota", range=[0, 1000], dtick=100, fixedrange=True),
            yaxis=dict(title="Nº de participantes", range=[0, _ymax], tickformat=",d", fixedrange=True),
            separators=",.",
            bargap=0,
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            margin=dict(t=60, b=40, l=60, r=20),
            height=440,
        )
        fig_hist.add_annotation(
            x=0.01, y=0.99, xref="paper", yref="paper", xanchor="left", yanchor="top",
            text=f"n = {_n:,}".replace(",", ".") + f"<br><span style='font-size:10px'>{_escala_txt}</span>",
            showarrow=False, align="left", font=dict(size=12),
            bgcolor="rgba(255,255,255,0.8)", bordercolor="#D6DCE5", borderwidth=1,
        )

        st.plotly_chart(fig_hist, width="stretch")

        _med = _medidas(_vals)
        _med_ref = None
        if ref is not None:
            _vals_ref = _hist_notas(ref, _hist_sel, "pop")
            _med_ref = _medidas(_vals_ref) if len(_vals_ref) else None
        if _med_ref is not None:
            st.caption(
                "Medidas descritivas da amostra. Os valores em cinza mostram a diferença **amostra − população**."
            )
        for _kc, (_rot, _v) in zip(st.columns(len(_med)), _med.items()):
            _casas = 0 if _rot == "n" else 1
            _d = None
            if _med_ref is not None and _rot != "n":
                _dv = _v - _med_ref[_rot]
                _d = f"{'+' if _dv >= 0 else ''}{_br(_dv, _casas)}"
            with _kc:
                with st.container(border=True):
                    st.metric(_rot, _br(_v, _casas), delta=_d, delta_color="off")

        st.caption(
            f"Classes de {_HIST_BIN} pontos (20 classes de 0 a 1000). {_escala_txt}. "
            "Foram considerados apenas participantes presentes. Todas as notas registradas são consideradas, "
            "inclusive notas zero. A nota geral é a média das cinco notas de cada participante. "
            "Coeficiente de variação = desvio-padrão ÷ média."
        )

    # --- Média da nota geral por tipo de escola ---
    st.divider()
    st.subheader(":material/school: Média da nota geral por tipo de escola")
    st.caption(
        "Média da nota geral (média das cinco notas, inclusive zeros) para cada tipo de escola declarado. "
        "Passe o cursor sobre as barras para ver o número de participantes e o desvio-padrão."
        + (" O losango indica a média da população no mesmo grupo." if ref is not None else "")
    )

    def _media_por_escola(df: pl.DataFrame) -> pd.DataFrame:
        return (
            _notas_validas(df)
            .with_columns(
                pl.col("TP_ESCOLA").replace_strict(ESCOLA_MAP, default="Não Respondeu", return_dtype=pl.String)
                  .alias("escola")
            )
            .group_by("escola")
            .agg(
                pl.len().alias("n"),
                pl.col("NOTA_GERAL").mean().alias("media"),
                pl.col("NOTA_GERAL").std().alias("dp"),
            )
            .to_pandas()
            .set_index("escola")
            .reindex(["Pública", "Privada", "Não Respondeu"])
            .dropna(subset=["n"])
        )

    _esc = _media_por_escola(participantes)
    fig_esc = go.Figure(go.Bar(
        y=_esc.index, x=_esc["media"], orientation="h", name="Média",
        marker_color=[CORES_ESCOLA[e] for e in _esc.index],
        text=[_br(v, 1) for v in _esc["media"]], textposition="outside",
        customdata=np.column_stack([
            [_br(v, 0) for v in _esc["n"]], [_br(v, 1) for v in _esc["dp"]],
        ]),
        hovertemplate="<b>%{y}</b><br>Média: %{text}<br>n = %{customdata[0]}"
                      "<br>Desvio-padrão: %{customdata[1]}<extra></extra>",
    ))
    if ref is not None:
        _esc_pop = _media_por_escola(ref).reindex(_esc.index)
        fig_esc.add_trace(go.Scatter(
            y=_esc_pop.index, x=_esc_pop["media"], mode="markers", name="Média da população",
            marker=dict(symbol="diamond", size=12, color="#1F2937", line=dict(color="white", width=1)),
            customdata=[_br(v, 1) for v in _esc_pop["media"]],
            hovertemplate="<b>%{y}</b><br>Média da população: %{customdata}<extra></extra>",
        ))
    fig_esc.update_layout(
        title=dict(text="Média da nota geral por tipo de escola", x=0.5, xanchor="center", font=dict(size=15)),
        xaxis=dict(title="Média da nota geral", range=[0, max(_esc["media"].max() * 1.15, 700)]),
        yaxis=dict(title=None, autorange="reversed"),
        showlegend=ref is not None,
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
        margin=dict(t=60, b=40, l=110, r=20),
        height=320,
    )
    st.plotly_chart(fig_esc, width="stretch")


# ============================================================
# ABA 1 — VISÃO GERAL
# ============================================================

def get_enem_kpis(participantes_df):
    """Indicadores gerais; recebe apenas participantes (presentes nas quatro provas)."""
    # todas as notas registradas são consideradas, inclusive notas zero (regra única do app)
    notas_validas = (
        participantes_df.select(NOTAS_COLS).unpivot().drop_nulls("value")["value"]
    )
    media_geral       = round(notas_validas.mean(), 2) if notas_validas.len() > 0 else 0.0
    mediana_geral     = round(notas_validas.median(), 2) if notas_validas.len() > 0 else 0.0

    return {
        "total_participantes": participantes_df.height,
        "media_geral":         media_geral,
        "mediana_geral":       mediana_geral,
    }


enem_kpis = get_enem_kpis(enem_participantes)

DEF_POPULACAO = (
    f"participantes do ENEM {ANO} que realizaram a prova no Rio Grande do Sul e estiveram "
    "presentes nas quatro provas objetivas (Ciências da Natureza, Ciências Humanas, Linguagens e Matemática)"
)

with tab_populacao:
    st.markdown(
        "Análise dos microdados do ENEM para o Rio Grande do Sul, cobrindo perfil demográfico, escolar e desempenho acadêmico dos participantes.  \n"
        f"**Edição analisada:** {ANO}  \n"
        f"**População:** {DEF_POPULACAO}  \n"
        "**Fonte dos dados:** [INEP — Microdados do ENEM](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem)  "
    )
    st.info(
        f"A partir da edição de 2024, os microdados oficiais divulgados pelo INEP "
        "foram modificados para atender à Lei Geral de Proteção de Dados (LGPD), de modo que não é mais possível "
        "vincular informações do participante ao seu desempenho nas provas. Por este motivo, foi escolhido especificamente o ano de 2023.",
        icon=":material/info:",
    )

    _render_indicadores(enem_kpis)

    # --- Variáveis selecionadas ---
    st.divider()
    st.subheader(":material/list_alt: Variáveis selecionadas")
    st.caption("Variáveis dos microdados do ENEM 2023 utilizadas nas análises e sua classificação estatística.")
    for _col, (_rot, _val, _help) in zip(st.columns(2), [
        ("Variáveis nos microdados", str(N_VARIAVEIS_ORIGINAIS), f"Colunas do arquivo MICRODADOS_ENEM_{ANO}.csv divulgado pelo INEP."),
        ("Variáveis mantidas", str(len(COLUMNS)), "Colunas mantidas no arquivo da população; as analisadas estão listadas abaixo."),
    ]):
        with _col:
            with st.container(border=True):
                st.metric(_rot, _val, help=_help)

    def _tabela_codigos(itens):
        st.dataframe(
            pd.DataFrame(itens, columns=["Código", "Descrição"]).astype(str),
            hide_index=True,
            width="stretch",
        )

    # (tipo, variável, classificação, códigos) — ordenado por tipo e, dentro do tipo, alfabeticamente
    _VARIAVEIS = [
        ("Qualitativa", "Cor/raça", "Nominal", [
            (0, "Não declarado"), (1, "Branca"), (2, "Preta"), (3, "Parda"),
            (4, "Amarela"), (5, "Indígena"), (6, "Não dispõe da informação"),
        ]),
        ("Qualitativa", "Idade (em faixas)", "Ordinal",
            list(FAIXA_ETARIA_MAP.items())),
        ("Qualitativa", "Sexo", "Nominal (binária)", [
            ("M", "Masculino"), ("F", "Feminino"),
        ]),
        ("Qualitativa", "Situação escolar", "Nominal", [
            (1, "Já concluí o Ensino Médio"),
            (2, "Estou cursando e concluirei o Ensino Médio em 2023"),
            (3, "Estou cursando e concluirei o Ensino Médio após 2023"),
            (4, "Não concluí e não estou cursando o Ensino Médio"),
        ]),
        ("Qualitativa", "Tipo de escola", "Nominal", [
            (1, "Não respondeu"), (2, "Pública"), (3, "Privada"),
        ]),
        ("Quantitativa", "Nota", "Contínua", [
            ("CN", "Nota da prova de Ciências da Natureza"),
            ("CH", "Nota da prova de Ciências Humanas"),
            ("LC", "Nota da prova de Linguagens e Códigos"),
            ("MT", "Nota da prova de Matemática"),
            ("RED", "Nota da prova de Redação"),
        ]),
        ("Quantitativa", "Nota geral (derivada)", "Contínua", [
            ("NOTA_GERAL", "Média aritmética das cinco notas (CN, CH, LC, MT e Redação) de cada participante"),
            ("Regra", "Calculada para quem tem as cinco notas preenchidas, inclusive notas zero"),
        ]),
    ]

    _tipo_atual = None
    for _tipo, _var, _classif, _codigos in _VARIAVEIS:
        if _tipo != _tipo_atual:
            st.markdown(f"**{_tipo}**")
            _tipo_atual = _tipo
        with st.expander(f"**{_var}** — {_classif}"):
            _tabela_codigos(_codigos)

    _render_analises(enem_participantes, chave="pop")


# ============================================================
# ABA 2 — Análise descritiva da amostra
# ============================================================

with tab_amostra:
    _N_POP = enem_participantes.height
    st.markdown(
        "Análise descritiva de uma **amostra aleatória simples** dos participantes do ENEM no Rio Grande do Sul, "
        "replicando as análises realizadas para a população. As diferenças em relação à população aparecem "
        "como deltas (amostra − população) nos indicadores."
    )

    # --- Dimensionamento ---
    st.divider()
    st.subheader(":material/calculate: Dimensionamento da amostra")
    st.markdown(
        f"O tamanho da amostra foi obtido com a [calculadora de tamanho amostral da SurveyMonkey]({CALCULADORA_URL}), "
        "informando os parâmetros abaixo."
    )
    _p = st.columns(5)
    for _col, (_rot, _val) in zip(_p, [
        ("Tamanho da população (N)", _br(_N_POP, 0)),
        ("Nível de confiança", f"{CONFIANCA_AMOSTRA:.0%}"),
        ("Margem de erro", f"{MARGEM_ERRO_AMOSTRA:.0%}"),
        ("Proporção considerada", f"{PROPORCAO_AMOSTRA:.0%}"),
        ("Tamanho da amostra (n)", _br(TAMANHO_AMOSTRA, 0)),
    ]):
        with _col:
            with st.container(border=True):
                st.metric(_rot, _val)

    # --- Seleção ---
    st.subheader(":material/casino: Seleção da amostra (AAS)")
    st.markdown(
        f"1. Partiu-se da lista completa da população ({_br(_N_POP, 0)} participantes, arquivo "
        f"`{PARTICIPANTES_FILE}`).\n"
        f"2. Foram sorteados {_br(TAMANHO_AMOSTRA, 0)} participantes **sem reposição** com "
        f"`polars.DataFrame.sample(n={TAMANHO_AMOSTRA}, with_replacement=False, seed={SEMENTE_AMOSTRA})` "
        "(script `gerar_amostra.py`).\n"
        "3. Nesse sorteio, todos os subconjuntos de tamanho n têm a mesma chance de serem escolhidos; logo, cada "
        f"participante tem a mesma probabilidade de seleção, n/N = {_br(TAMANHO_AMOSTRA / _N_POP, 4)}.\n"
        f"4. A semente fixa ({SEMENTE_AMOSTRA}) torna o sorteio **reprodutível**: rodar o script novamente gera "
        f"exatamente a mesma amostra, salva em `{AMOSTRA_FILE}`."
    )

    _render_indicadores(get_enem_kpis(enem_amostra), kpis_ref=enem_kpis)
    _render_analises(enem_amostra, chave="amostra", ref=enem_participantes)


# ============================================================
# ABA 3 — Inferência estatística e comparação dos resultados
# ============================================================

def _inferencia_proporcao(amostra: pl.DataFrame, evento: pl.Expr, p0: float, alpha: float) -> dict:
    """IC e teste z bilateral para uma proporção, usando apenas a amostra."""
    from statistics import NormalDist

    normal = NormalDist()
    n = amostra.height
    x = int(amostra.select(evento.sum()).item())
    p_hat = x / n
    ep = (p_hat * (1 - p_hat) / n) ** 0.5            # erro-padrão para o IC (usa p̂)
    ep0 = (p0 * (1 - p0) / n) ** 0.5                 # erro-padrão sob H0 (usa p0)
    z_crit = normal.inv_cdf(1 - alpha / 2)
    z = (p_hat - p0) / ep0
    p_valor = 2 * (1 - normal.cdf(abs(z)))
    return {
        "n": n, "x": x, "p_hat": p_hat, "ep": ep, "ep0": ep0,
        "ic_inf": p_hat - z_crit * ep, "ic_sup": p_hat + z_crit * ep,
        "z": z, "z_crit": z_crit, "p_valor": p_valor,
        "rejeita": p_valor < alpha, "cond": min(n * p0, n * (1 - p0)),
    }


def _inferencia_media(v: np.ndarray, mu0: float, alpha: float) -> dict:
    """IC e teste t bilateral de uma amostra para a média (H0: μ = μ0)."""
    from scipy import stats

    n, m, s = len(v), float(np.mean(v)), float(np.std(v, ddof=1))
    ep = s / np.sqrt(n)
    gl = n - 1
    t_crit = float(stats.t.ppf(1 - alpha / 2, gl))
    t_obs = (m - mu0) / ep
    p_valor = float(2 * stats.t.sf(abs(t_obs), gl))
    return {
        "n": n, "media": m, "s": s, "ep": ep, "gl": gl,
        "ic_inf": m - t_crit * ep, "ic_sup": m + t_crit * ep,
        "t": t_obs, "t_crit": t_crit, "p_valor": p_valor, "rejeita": p_valor < alpha,
    }


def _inferencia_duas_medias(a: np.ndarray, b: np.ndarray, alpha: float) -> dict:
    """IC de cada média, IC da diferença (a − b) e teste t de Welch unilateral (H1: μa − μb > 0)."""
    from scipy import stats

    def _grupo(v):
        n, m, s = len(v), float(np.mean(v)), float(np.std(v, ddof=1))
        ep = s / np.sqrt(n)
        tc = stats.t.ppf(1 - alpha / 2, n - 1)
        return {"n": n, "media": m, "s": s, "ep": ep, "ic_inf": m - tc * ep, "ic_sup": m + tc * ep}

    ga, gb = _grupo(a), _grupo(b)
    va, vb = ga["ep"] ** 2, gb["ep"] ** 2
    ep = np.sqrt(va + vb)
    gl = (va + vb) ** 2 / (va**2 / (ga["n"] - 1) + vb**2 / (gb["n"] - 1))  # Welch–Satterthwaite
    dif = ga["media"] - gb["media"]
    t_obs = dif / ep
    t_crit = stats.t.ppf(1 - alpha, gl)                 # unilateral à direita
    t_ic = stats.t.ppf(1 - alpha / 2, gl)               # IC bilateral da diferença
    p_valor = float(stats.t.sf(t_obs, gl))
    return {
        "a": ga, "b": gb, "dif": dif, "ep": ep, "gl": gl,
        "ic_inf": dif - t_ic * ep, "ic_sup": dif + t_ic * ep,
        "lim_inf_unilateral": dif - t_crit * ep,        # limite inferior do IC unilateral (1 − α)
        "t": t_obs, "t_crit": t_crit, "p_valor": p_valor, "rejeita": p_valor < alpha,
    }


def _pval_txt(p: float) -> str:
    return "< 0,0001" if p < 1e-4 else _br(p)


def _metricas(itens):
    """Linha de st.metric com borda; itens = [(rótulo, valor, help|None), ...]."""
    for _col, (_rot, _val, _help) in zip(st.columns(len(itens)), itens):
        with _col:
            with st.container(border=True):
                st.metric(_rot, _val, help=_help)


def _plot_estatistica(obs: float, crit: float, alpha: float, cor: str,
                      gl: float | None = None, bilateral: bool = True, simbolo: str = "z"):
    """Curva da distribuição da estatística de teste sob H0 com região de rejeição e valor observado."""
    from scipy import stats

    lim = max(4.0, abs(obs) + 1)
    xs = np.linspace(-lim, lim, 1500)
    ys = stats.norm.pdf(xs) if gl is None else stats.t.pdf(xs, gl)
    nome_dist = "N(0, 1)" if gl is None else f"t de Student (gl = {_br(gl, 1)})"
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#374151", width=2),
                             name=nome_dist, hoverinfo="skip"))
    regioes = [(xs <= -crit, True), (xs >= crit, False)] if bilateral else [(xs >= crit, True)]
    for mask, show in regioes:
        fig.add_trace(go.Scatter(
            x=xs[mask], y=ys[mask], fill="tozeroy", mode="none",
            fillcolor="rgba(214,39,40,0.35)", name=f"Região de rejeição (α = {_br(alpha, 2)})",
            showlegend=show, hoverinfo="skip",
        ))
    fig.add_vline(x=obs, line=dict(color=cor, width=3),
                  annotation_text=f"{simbolo} observado = {_br(obs, 2)}", annotation_position="top left")
    for s in ((-crit, crit) if bilateral else (crit,)):
        fig.add_vline(x=s, line=dict(color="#D62728", width=1.5, dash="dash"),
                      annotation_text=_br(s, 3), annotation_position="bottom right")
    fig.update_layout(
        title=dict(text="Distribuição da estatística de teste sob H₀", x=0.5, xanchor="center", font=dict(size=15)),
        xaxis=dict(title=simbolo, range=[-lim, lim], fixedrange=True),
        yaxis=dict(title="Densidade", fixedrange=True),
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
        separators=",.", margin=dict(t=60, b=40, l=60, r=20), height=360,
    )
    st.plotly_chart(fig, width="stretch")


def _render_teste_proporcao(*, titulo, icone, variavel_md, evento_md, parametro_md, evento_expr,
                            p0, justificativa_md, h0_rot, h1_rot, sujeito, cor, alpha, alpha_rot, n_pop) -> dict:
    """Bloco completo (definição, hipóteses, IC, condições, teste e conclusão) para uma proporção."""
    conf = 1 - alpha
    p0_tex = _br(p0, 3).rstrip("0").replace(",", "{,}")
    st.divider()
    st.subheader(f"{icone} {titulo}")

    st.markdown("##### 1. Variável e evento de interesse")
    st.markdown(f"- **Variável qualitativa:** {variavel_md}  \n- **Evento de interesse:** {evento_md}  \n"
                f"- **Parâmetro:** {parametro_md}")

    st.markdown("##### 2. Hipóteses")
    st.markdown(justificativa_md)
    _h1, _h2 = st.columns(2)
    with _h1:
        with st.container(border=True):
            st.markdown(f"**Hipótese nula** — {h0_rot}")
            st.latex(r"H_0:\; p = " + p0_tex)
    with _h2:
        with st.container(border=True):
            st.markdown(f"**Hipótese alternativa** — {h1_rot}")
            st.latex(r"H_1:\; p \neq " + p0_tex)

    res = _inferencia_proporcao(enem_amostra, evento_expr, p0, alpha)

    st.markdown(f"##### 3. Estimação da proporção — intervalo de {conf:.0%} de confiança")
    st.latex(
        r"\hat{p} = \frac{x}{n} \qquad "
        r"IC_{" + f"{conf*100:.0f}" + r"\%}(p) = \hat{p} \pm z_{\alpha/2}\sqrt{\frac{\hat{p}(1-\hat{p})}{n}}"
    )
    _metricas([
        ("Casos na amostra (x)", _br(res["x"], 0), None),
        ("Tamanho da amostra (n)", _br(res["n"], 0), None),
        ("Proporção amostral (p̂)", _br(res["p_hat"]), None),
        ("Erro-padrão", _br(res["ep"]), None),
        (f"IC {conf:.0%}", f"[{_br(res['ic_inf'])}; {_br(res['ic_sup'])}]", None),
    ])
    st.caption(
        f"Com {conf:.0%} de confiança, a proporção de {sujeito} está entre "
        f"{_br(res['ic_inf']*100, 2)}% e {_br(res['ic_sup']*100, 2)}%. "
        f"Valor crítico utilizado: z = {_br(res['z_crit'], 3)}."
    )

    st.markdown("##### 4. Condições de aplicação")
    _frac = res["n"] / n_pop
    st.markdown(
        f"independentes — atendida. A correção para população finita, √(1 − n/N) = {_br((1 - _frac) ** 0.5, 3)}, "
        "teria efeito desprezível e não foi aplicada.  \n"
        + (f"- **Aproximação normal:** min(n·p₀, n·(1 − p₀)) = {_br(res['cond'], 1)} ≥ 10 — atendida."
           if res["cond"] >= 10 else
           f"- **Aproximação normal:** min(n·p₀, n·(1 − p₀)) = {_br(res['cond'], 1)} < 10 — **não atendida**.")
    )

    st.markdown("##### 5. Teste de hipótese para a proporção")
    st.latex(
        r"Z = \frac{\hat{p} - p_0}{\sqrt{\dfrac{p_0(1-p_0)}{n}}} \qquad "
        r"\text{valor-p} = 2\,P(Z > |z_{obs}|)"
    )
    _pv = _pval_txt(res["p_valor"])
    _metricas([
        ("Nível de significância (α)", _br(alpha, 2), None),
        ("Estatística de teste (z)", _br(res["z"], 2), None),
        ("Valor crítico", f"± {_br(res['z_crit'], 3)}", None),
        ("Valor-p", _pv, f"Valor exato: {res['p_valor']:.2e}"),
    ])
    _plot_estatistica(res["z"], res["z_crit"], alpha, cor)

    st.markdown("##### 6. Conclusão")
    _ic_txt = f"[{_br(res['ic_inf'])}; {_br(res['ic_sup'])}]"
    _p0_txt = _br(p0, 3).rstrip("0").rstrip(",")
    if res["rejeita"]:
        _dir = "acima" if res["p_hat"] > p0 else "abaixo"
        st.success(
            f"Como |z| = {_br(abs(res['z']), 2)} > {_br(res['z_crit'], 3)} e o valor-p ({_pv}) é menor que "
            f"α = {_br(alpha, 2)}, **rejeitamos H₀**. Há evidência estatística, ao nível de {alpha_rot} de "
            f"significância, de que a proporção de {sujeito} é diferente de {_p0_txt}. O intervalo de confiança "
            f"{_ic_txt} está inteiramente {_dir} de {_p0_txt}, o que indica que a proporção está {_dir} do valor de referência.",
            icon=":material/check_circle:",
        )
    else:
        st.warning(
            f"Como |z| = {_br(abs(res['z']), 2)} ≤ {_br(res['z_crit'], 3)} e o valor-p ({_pv}) é maior ou igual a "
            f"α = {_br(alpha, 2)}, **não rejeitamos H₀**. Não há evidência estatística suficiente para afirmar que "
            f"a proporção de {sujeito} difere de {_p0_txt}; coerentemente, o intervalo {_ic_txt} contém {_p0_txt}.",
            icon=":material/info:",
        )
    return res


def _qq_plot(grupos: list[tuple[str, np.ndarray, str]], titulo: str):
    """Gráfico Q-Q normal (quantis teóricos × quantis amostrais) para um ou mais grupos."""
    from scipy import stats

    fig = go.Figure()
    for nome, v, cor in grupos:
        (osm, osr), (slope, intercept, _r) = stats.probplot(v, dist="norm")
        fig.add_trace(go.Scatter(x=osm, y=osr, mode="markers", name=nome,
                                 marker=dict(color=cor, size=4, opacity=0.6),
                                 hovertemplate=f"{nome}<br>Teórico: %{{x:.2f}}<br>Nota: %{{y:.1f}}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[osm.min(), osm.max()], y=[intercept + slope * osm.min(), intercept + slope * osm.max()],
                                 mode="lines", line=dict(color=cor, dash="dash"), showlegend=False, hoverinfo="skip"))
    fig.update_layout(
        title=dict(text=titulo, x=0.5, xanchor="center", font=dict(size=14)),
        xaxis=dict(title="Quantis teóricos da normal padrão", fixedrange=True),
        yaxis=dict(title="Quantis amostrais (nota)", fixedrange=True),
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
        separators=",.", margin=dict(t=50, b=40, l=60, r=20), height=340,
    )
    st.plotly_chart(fig, width="stretch")


@st.cache_data(show_spinner="Simulando amostras aleatórias…")
def _simular_amostras(_pop: pl.DataFrame, n: int, n_sim: int, seed: int) -> dict:
    """Sorteia `n_sim` AAS de tamanho `n` da população e guarda as estimativas de p (feminino) e μ (Matemática).
    O DataFrame não entra no hash do cache (a população é fixa)."""
    rng = np.random.default_rng(seed)
    fem = (_pop["TP_SEXO"] == "F").to_numpy()
    mt = _pop["NU_NOTA_MT"].cast(pl.Float64).to_numpy()
    mt_ok = ~np.isnan(mt)  # todas as notas registradas, inclusive zero
    N = len(fem)
    p_hat, mt_media, mt_s, mt_n = (np.empty(n_sim) for _ in range(4))
    for i in range(n_sim):
        idx = rng.choice(N, size=n, replace=False)
        p_hat[i] = fem[idx].mean()
        v = mt[idx][mt_ok[idx]]
        mt_media[i], mt_s[i], mt_n[i] = v.mean(), v.std(ddof=1), len(v)
    return {"p_hat": p_hat, "mt_media": mt_media, "mt_s": mt_s, "mt_n": mt_n}


with tab_comparacao:

    _alpha_rot = st.segmented_control(
        "Nível de significância (α) — aplicado a todos os testes desta aba",
        options=["1%", "5%", "10%"], default="5%", key="inf_alpha",
    ) or "5%"
    ALPHA = int(_alpha_rot.rstrip("%")) / 100
    CONF = 1 - ALPHA
    N_POP = enem_participantes.height

    # ========================================================
    # (a1) Proporção — sexo feminino
    # ========================================================
    res_fem = _render_teste_proporcao(
        titulo="1. Inferência para uma proporção — participantes do sexo feminino",
        icone=":material/functions:",
        variavel_md="Sexo (`TP_SEXO`), nominal binária",
        evento_md="o participante ser do sexo **Feminino**",
        parametro_md="$p$ = proporção de mulheres entre os participantes do ENEM 2023 no RS",
        evento_expr=pl.col("TP_SEXO") == "F",
        p0=0.5,
        justificativa_md=(
            "O valor de referência é definido a partir de um critério teórico de **paridade entre os sexos**, "
            "sem uso de informações da população. O teste é **bilateral**, pois não se assume de antemão "
            "qual sexo predomina."
        ),
        h0_rot="participação igual entre os sexos", h1_rot="participação diferente entre os sexos",
        sujeito="mulheres entre os participantes", cor=CORES_SEXO["Feminino"],
        alpha=ALPHA, alpha_rot=_alpha_rot, n_pop=N_POP,
    )

    # ========================================================
    # (a2) Proporção — cor/raça branca × Censo 2022
    # ========================================================
    res_bra = _render_teste_proporcao(
        titulo="2. Inferência para uma proporção — participantes autodeclarados brancos",
        icone=":material/diversity_3:",
        variavel_md="Cor/raça (`TP_COR_RACA`), nominal",
        evento_md="o participante se autodeclarar de cor/raça **Branca** (código 1)",
        parametro_md="$p$ = proporção de participantes brancos entre os participantes do ENEM 2023 no RS",
        evento_expr=pl.col("TP_COR_RACA") == 1,
        p0=P0_BRANCOS_CENSO,
        justificativa_md=(
            "O valor de referência é a **proporção de pessoas autodeclaradas brancas na população do Rio Grande do Sul "
            f"segundo o Censo Demográfico 2022 do IBGE** ({_br(P0_BRANCOS_CENSO * 100, 1)}%). "
            f"Fonte: [IBGE — Cidades e Estados: Rio Grande do Sul]({IBGE_CENSO_RS_URL})."
        ),
        h0_rot="perfil racial igual ao do Censo", h1_rot="perfil racial diferente do Censo",
        sujeito="brancos entre os participantes", cor=CORES_RACA["Branca"],
        alpha=ALPHA, alpha_rot=_alpha_rot, n_pop=N_POP,
    )

    # ========================================================
    # (b1) Média — nota de Matemática × 500
    # ========================================================
    st.divider()
    st.subheader(":material/calculate: 3. Inferência para uma média — nota de Matemática")
    _mt = enem_amostra.filter(pl.col("NU_NOTA_MT").is_not_null())["NU_NOTA_MT"].cast(pl.Float64).to_numpy()

    st.markdown("##### 1. Variável de interesse")
    st.markdown(
        "- **Variável quantitativa:** nota da prova de Matemática (`NU_NOTA_MT`), contínua  \n"
        "- **Parâmetro:** $\\mu$ = nota média de Matemática dos participantes do ENEM 2023 no RS  \n"
        f"- Todas as notas registradas são consideradas, inclusive notas zero ({_br(len(_mt), 0)} participantes da amostra)."
    )
    st.markdown("##### 2. Hipóteses")
    st.markdown(
        f"O valor de referência é **{MU0_MATEMATICA} pontos**, a média de referência da escala de notas do ENEM "
        f"(fonte: [INEP — Entenda a sua nota no Enem: guia do participante]({INEP_GUIA_NOTA_URL})). "
        "O teste é **bilateral**."
    )
    _h1, _h2 = st.columns(2)
    with _h1:
        with st.container(border=True):
            st.markdown("**Hipótese nula** — média igual à referência da escala")
            st.latex(rf"H_0:\; \mu = {MU0_MATEMATICA}")
    with _h2:
        with st.container(border=True):
            st.markdown("**Hipótese alternativa** — média diferente da referência")
            st.latex(rf"H_1:\; \mu \neq {MU0_MATEMATICA}")

    res_mt = _inferencia_media(_mt, MU0_MATEMATICA, ALPHA)

    st.markdown(f"##### 3. Estimação da média — intervalo de {CONF:.0%} de confiança")
    st.latex(r"IC(\mu) = \bar{x} \pm t_{\alpha/2,\,n-1}\,\frac{s}{\sqrt{n}}")
    _metricas([
        ("Tamanho da amostra (n)", _br(res_mt["n"], 0), None),
        ("Média amostral (x̄)", _br(res_mt["media"], 2), None),
        ("Desvio-padrão (s)", _br(res_mt["s"], 2), None),
        ("Erro-padrão", _br(res_mt["ep"], 2), None),
        (f"IC {CONF:.0%}", f"[{_br(res_mt['ic_inf'], 2)}; {_br(res_mt['ic_sup'], 2)}]", None),
    ])
    st.caption(
        f"Com {CONF:.0%} de confiança, a nota média de Matemática está entre {_br(res_mt['ic_inf'], 2)} e "
        f"{_br(res_mt['ic_sup'], 2)} pontos. Valor crítico: t = {_br(res_mt['t_crit'], 3)} (gl = {res_mt['gl']})."
    )

    st.markdown("##### 4. Condições de aplicação")
    _cq1, _cq2 = st.columns([3, 2])
    with _cq1:
        st.markdown(
            f"- **Normalidade da média amostral:** n = {_br(res_mt['n'], 0)} ≥ 30. Pelo Teorema Central do Limite, "
            "x̄ tem distribuição aproximadamente normal mesmo que as notas não sejam exatamente normais. "
            "O gráfico Q-Q ao lado mostra que as notas seguem a reta da normal na maior parte da distribuição, "
            "com desvios apenas nas caudas (efeito dos limites da escala TRI), o que não compromete o teste "
            "com uma amostra deste tamanho."
        )
    with _cq2:
        _qq_plot([("Matemática", _mt, CORES_AREAS["Matemática"])], "Gráfico Q-Q — nota de Matemática")

    st.markdown("##### 5. Teste de hipótese para a média (t de uma amostra)")
    st.latex(r"t = \frac{\bar{x} - \mu_0}{s/\sqrt{n}} \qquad \text{valor-p} = 2\,P(T_{n-1} > |t_{obs}|)")
    _pv_mt = _pval_txt(res_mt["p_valor"])
    _metricas([
        ("Nível de significância (α)", _br(ALPHA, 2), None),
        ("Estatística de teste (t)", _br(res_mt["t"], 2), None),
        ("Graus de liberdade", _br(res_mt["gl"], 0), None),
        ("Valor crítico", f"± {_br(res_mt['t_crit'], 3)}", None),
        ("Valor-p", _pv_mt, f"Valor exato: {res_mt['p_valor']:.2e}"),
    ])
    _plot_estatistica(res_mt["t"], res_mt["t_crit"], ALPHA, CORES_AREAS["Matemática"], gl=res_mt["gl"], simbolo="t")

    st.markdown("##### 6. Conclusão")
    _ic_mt = f"[{_br(res_mt['ic_inf'], 2)}; {_br(res_mt['ic_sup'], 2)}]"
    if res_mt["rejeita"]:
        _dir = "acima" if res_mt["media"] > MU0_MATEMATICA else "abaixo"
        st.success(
            f"Como |t| = {_br(abs(res_mt['t']), 2)} > {_br(res_mt['t_crit'], 3)} e o valor-p ({_pv_mt}) é menor que "
            f"α = {_br(ALPHA, 2)}, **rejeitamos H₀**. Há evidência estatística, ao nível de {_alpha_rot} de "
            f"significância, de que a nota média de Matemática dos participantes do RS é diferente de {MU0_MATEMATICA}. "
            f"O intervalo {_ic_mt} está inteiramente {_dir} de {MU0_MATEMATICA}: a média está {_dir} da referência da escala.",
            icon=":material/check_circle:",
        )
    else:
        st.warning(
            f"Como |t| = {_br(abs(res_mt['t']), 2)} ≤ {_br(res_mt['t_crit'], 3)} e o valor-p ({_pv_mt}) é maior ou igual a "
            f"α = {_br(ALPHA, 2)}, **não rejeitamos H₀**. Não há evidência suficiente de que a nota média de "
            f"Matemática difira de {MU0_MATEMATICA}; o intervalo {_ic_mt} contém {MU0_MATEMATICA}.",
            icon=":material/info:",
        )

    # ========================================================
    # (b2) Diferença de médias — nota geral: privada × pública
    # ========================================================
    st.divider()
    st.subheader(":material/school: 4. Inferência para médias — nota geral: escola privada × escola pública")

    _amostra_geral = _notas_validas(enem_amostra)
    _n_geral = _amostra_geral.height
    _n_sem_escola = _amostra_geral.filter(pl.col("TP_ESCOLA") == 1).height
    _priv = _amostra_geral.filter(pl.col("TP_ESCOLA") == 3)["NOTA_GERAL"].to_numpy()
    _pub = _amostra_geral.filter(pl.col("TP_ESCOLA") == 2)["NOTA_GERAL"].to_numpy()

    st.markdown("##### 1. Variável e grupos")
    st.markdown(
        "- **Variável quantitativa:** nota geral — média das cinco notas (CN, CH, LC, MT e Redação), contínua  \n"
        "- **Grupos (`TP_ESCOLA`):** escola **privada** e escola **pública** (amostras independentes)  \n"
        r"- **Parâmetros:** $\mu_{priv}$ e $\mu_{pub}$ = nota geral média de cada grupo"
    )
    st.info(
        f"Dos {_br(_n_geral, 0)} participantes da amostra com nota geral válida, "
        f"**{_br(_n_sem_escola, 0)} ({_n_sem_escola / _n_geral:.0%}) não informaram o tipo de escola**"
        " (código 1 — a pergunta é respondida principalmente por concluintes do Ensino Médio). "
        f"A análise considera apenas os {_br(len(_priv) + len(_pub), 0)} que declararam escola pública ou privada, "
        "e as conclusões se referem a esse grupo.",
        icon=":material/info:",
    )

    st.markdown("##### 2. Hipóteses")
    st.markdown(
        "A hipótese de pesquisa é que alunos de escola privada obtêm nota geral **maior** que alunos de escola "
        "pública. Por indicar uma direção, o teste é **unilateral à direita**."
    )
    _h1, _h2 = st.columns(2)
    with _h1:
        with st.container(border=True):
            st.markdown("**Hipótese nula** — a nota da escola privada não é maior")
            st.latex(r"H_0:\; \mu_{priv} - \mu_{pub} \leq 0")
    with _h2:
        with st.container(border=True):
            st.markdown("**Hipótese alternativa** — a nota da escola privada é maior")
            st.latex(r"H_1:\; \mu_{priv} - \mu_{pub} > 0")

    rm = _inferencia_duas_medias(_priv, _pub, ALPHA)

    st.markdown(f"##### 3. Estimação das médias — intervalos de {CONF:.0%} de confiança")
    st.latex(
        r"IC(\mu) = \bar{x} \pm t_{\alpha/2,\,n-1}\,\frac{s}{\sqrt{n}} \qquad "
        r"IC(\mu_{priv}-\mu_{pub}) = (\bar{x}_{priv}-\bar{x}_{pub}) \pm t_{\alpha/2,\,gl}"
        r"\sqrt{\frac{s_{priv}^2}{n_{priv}} + \frac{s_{pub}^2}{n_{pub}}}"
    )
    _tab_ic = pd.DataFrame([
        {
            "Grupo": nome, "n": g["n"], "Média (x̄)": _br(g["media"], 2), "Desvio-padrão (s)": _br(g["s"], 2),
            "Erro-padrão": _br(g["ep"], 2), f"IC {CONF:.0%}": f"[{_br(g['ic_inf'], 2)}; {_br(g['ic_sup'], 2)}]",
        }
        for nome, g in [("Privada", rm["a"]), ("Pública", rm["b"])]
    ] + [{
        "Grupo": "Diferença (privada − pública)", "n": rm["a"]["n"] + rm["b"]["n"],
        "Média (x̄)": _br(rm["dif"], 2), "Desvio-padrão (s)": "—", "Erro-padrão": _br(rm["ep"], 2),
        f"IC {CONF:.0%}": f"[{_br(rm['ic_inf'], 2)}; {_br(rm['ic_sup'], 2)}]",
    }])
    st.dataframe(_tab_ic, hide_index=True, width="stretch")

    fig_ic = go.Figure()
    for nome, g in [("Pública", rm["b"]), ("Privada", rm["a"])]:
        fig_ic.add_trace(go.Scatter(
            x=[g["media"]], y=[nome], mode="markers",
            marker=dict(size=13, color=CORES_ESCOLA[nome]),
            error_x=dict(type="data", symmetric=False, array=[g["ic_sup"] - g["media"]],
                         arrayminus=[g["media"] - g["ic_inf"]], thickness=3, width=10,
                         color=CORES_ESCOLA[nome]),
            name=nome,
            hovertemplate=f"<b>{nome}</b><br>Média: {_br(g['media'], 2)}<br>"
                          f"IC {CONF:.0%}: [{_br(g['ic_inf'], 2)}; {_br(g['ic_sup'], 2)}]<extra></extra>",
        ))
    fig_ic.update_layout(
        title=dict(text=f"Nota geral média por tipo de escola (IC {CONF:.0%})", x=0.5, xanchor="center", font=dict(size=15)),
        xaxis=dict(title="Nota geral", fixedrange=True), yaxis=dict(fixedrange=True),
        showlegend=False, separators=",.", margin=dict(t=60, b=40, l=80, r=20), height=260,
    )
    st.plotly_chart(fig_ic, width="stretch")
    st.caption(
        f"Com {CONF:.0%} de confiança, a nota geral média dos alunos de escola privada está entre "
        f"{_br(rm['a']['ic_inf'], 2)} e {_br(rm['a']['ic_sup'], 2)}, e a dos alunos de escola pública entre "
        f"{_br(rm['b']['ic_inf'], 2)} e {_br(rm['b']['ic_sup'], 2)}. A diferença entre as médias está entre "
        f"{_br(rm['ic_inf'], 2)} e {_br(rm['ic_sup'], 2)} pontos."
    )
    st.info(
        f"**Relação entre o teste unilateral e o intervalo.** Um teste unilateral com nível α corresponde a um "
        f"**limite inferior unilateral** de confiança {CONF:.0%} (ou, de forma equivalente, a um IC bilateral de "
        f"{1 - 2 * ALPHA:.0%}). Com {CONF:.0%} de confiança, a diferença é **maior que "
        f"{_br(rm['lim_inf_unilateral'], 2)} pontos**; como esse limite "
        f"{'é maior que zero, a conclusão coincide com a rejeição de H₀' if rm['lim_inf_unilateral'] > 0 else 'não é maior que zero, a conclusão coincide com a não rejeição de H₀'}. "
        f"O IC bilateral de {CONF:.0%} acima é mostrado para estimar a magnitude da diferença.",
        icon=":material/lightbulb:",
    )

    st.markdown("##### 4. Condições de aplicação")
    _cw1, _cw2 = st.columns([3, 2])
    with _cw1:
        st.markdown(

            f"- **Tamanho dos grupos:** n_priv = {_br(rm['a']['n'], 0)} e n_pub = {_br(rm['b']['n'], 0)}, ambos ≥ 30. "
            "Pelo Teorema Central do Limite, as médias amostrais são aproximadamente normais; o gráfico Q-Q mostra "
            "notas próximas da normal, com desvios apenas nas caudas.  \n"
            f"- **Variâncias:** s_priv = {_br(rm['a']['s'], 2)} e s_pub = {_br(rm['b']['s'], 2)}. Como não se supõe "
            "variâncias iguais, usa-se o teste de **Welch**."
        )
    with _cw2:
        _qq_plot([("Privada", _priv, CORES_ESCOLA["Privada"]), ("Pública", _pub, CORES_ESCOLA["Pública"])],
                 "Gráfico Q-Q — nota geral por tipo de escola")

    st.markdown("##### 5. Teste de hipótese para a diferença de médias (t de Welch)")
    st.latex(
        r"t = \frac{\bar{x}_{priv} - \bar{x}_{pub}}{\sqrt{\dfrac{s_{priv}^2}{n_{priv}} + \dfrac{s_{pub}^2}{n_{pub}}}}"
        r"\qquad \text{valor-p} = P(T_{gl} > t_{obs})"
    )
 
    _pval_m = _pval_txt(rm["p_valor"])
    _metricas([
        ("Nível de significância (α)", _br(ALPHA, 2), None),
        ("Estatística de teste (t)", _br(rm["t"], 2), None),
        ("Graus de liberdade", _br(rm["gl"], 1), None),
        ("Valor crítico", _br(rm["t_crit"], 3), "Unilateral à direita"),
        ("Valor-p", _pval_m, f"Valor exato: {rm['p_valor']:.2e}"),
    ])
    _plot_estatistica(rm["t"], rm["t_crit"], ALPHA, CORES_ESCOLA["Privada"], gl=rm["gl"], bilateral=False, simbolo="t")

    st.markdown("##### 6. Conclusão")
    if rm["rejeita"]:
        st.success(
            f"Como t = {_br(rm['t'], 2)} > {_br(rm['t_crit'], 3)} e o valor-p ({_pval_m}) é menor que α = {_br(ALPHA, 2)}, "
            f"**rejeitamos H₀**. Há evidência estatística, ao nível de {_alpha_rot} de significância, de que "
            "alunos de escola privada obtêm nota geral média maior que alunos de escola pública. "
            f"Estima-se que a diferença seja de {_br(rm['dif'], 1)} pontos, com IC {CONF:.0%} entre "
            f"{_br(rm['ic_inf'], 1)} e {_br(rm['ic_sup'], 1)} pontos.",
            icon=":material/check_circle:",
        )
    else:
        st.warning(
            f"Como t = {_br(rm['t'], 2)} ≤ {_br(rm['t_crit'], 3)} e o valor-p ({_pval_m}) é maior ou igual a "
            f"α = {_br(ALPHA, 2)}, **não rejeitamos H₀**. Não há evidência estatística suficiente para afirmar "
            "que alunos de escola privada obtêm nota geral média maior que alunos de escola pública.",
            icon=":material/info:",
        )

    