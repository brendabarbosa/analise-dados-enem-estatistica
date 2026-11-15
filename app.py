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
    # abas fixas no topo durante o scroll (logo abaixo do cabeçalho do Streamlit)
    " div[data-testid='stTabs'] [role='tablist'] {"
    "   position: sticky !important; top: 3.75rem; z-index: 999 !important;"
    "   background-color: #ffffff;"
    "   padding-top: 0.25rem;"
    "   border-bottom: 1px solid rgba(49, 51, 63, 0.2);"
    " }"
    "</style>",
    unsafe_allow_html=True,
)

# ============================================================
# CONSTANTES E MAPEAMENTOS
# ============================================================

COLUMNS = [
    "TP_FAIXA_ETARIA", "TP_SEXO", "TP_COR_RACA", "TP_ESCOLA", "IN_TREINEIRO",
    "TP_ST_CONCLUSAO",
    "SG_UF_PROVA", "Q006",
    "NO_MUNICIPIO_PROVA",
    "CO_MUNICIPIO_ESC", "NO_MUNICIPIO_ESC", "SG_UF_ESC",
    "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO",
    "TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT",
]

NOTAS_COLS    = ["NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO"]
PRESENCA_COLS = ["TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT"]

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

DATA_FILE = "data/MICRODADOS_ENEM_2023.csv"

if not __import__("pathlib").Path(DATA_FILE).exists():
    st.error(
        "**Arquivo de dados não encontrado.**\n\n"
        f"- `{DATA_FILE}`\n\n"
        "Consulte o **README** para instruções de como obter os dados antes de executar o dashboard."
    )
    st.stop()


@st.cache_data
def get_enem_dataset(columns: tuple):
    return pl.read_csv(DATA_FILE, separator=";", encoding="latin1", columns=list(columns))


PRESENCA_FILTER = pl.all_horizontal([pl.col(c) == 1 for c in PRESENCA_COLS])

enem_df = get_enem_dataset(tuple(COLUMNS)).filter(pl.col("SG_UF_PROVA") == "RS")

if enem_df.is_empty():
    st.warning("Nenhum dado encontrado.")
    st.stop()

enem_participantes = enem_df.filter(PRESENCA_FILTER)

if enem_participantes.is_empty():
    st.warning("Nenhum participante efetivo encontrado.")
    st.stop()

# Amostra aleatória simples (sem reposição) dos participantes.
# Tamanho calculado com 95% de confiança, margem de erro de 2% e proporção de 50%.
TAMANHO_AMOSTRA = 2_351
SEMENTE_AMOSTRA = 42  # semente fixa para a amostra ser reprodutível
enem_amostra = enem_participantes.sample(n=TAMANHO_AMOSTRA, with_replacement=False, seed=SEMENTE_AMOSTRA)




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

def _render_indicadores(kpis):
    st.divider()
    st.subheader(":material/leaderboard: Indicadores gerais")

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.metric("Total de Participantes", f"{kpis['total_participantes']:,}")
    with col2:
        with st.container(border=True):
            st.metric(
                "Média Geral",
                f"{kpis['media_geral']:.2f}",
                help=(
                    "Média aritmética de todas as notas válidas dos participantes "
                    "(presentes nas quatro provas objetivas), considerando as cinco áreas em conjunto: "
                    "Ciências da Natureza, Ciências Humanas, Linguagens e Códigos, Matemática e Redação. "
                    "Notas ausentes são descartadas."
                ),
            )
    with col3:
        with st.container(border=True):
            st.metric(
                "Mediana Geral",
                f"{kpis['mediana_geral']:.2f}",
                help=(
                    "Valor central de todas as notas válidas dos participantes "
                    "(presentes nas quatro provas objetivas), considerando as cinco áreas em conjunto: "
                    "metade das notas fica abaixo e metade acima desse valor. "
                    "Notas ausentes são descartadas. É menos sensível a valores extremos que a média."
                ),
            )



def _render_analises(participantes: pl.DataFrame, chave: str):
    """Seções: faixa etária e sexo, cor/raça, perfil escolar e distribuição das notas."""
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
    gender_df  = (
        pyramid_source
        .group_by("sexo")
        .agg(pl.col("total").sum().alias("total"))
        .sort("sexo")
        .to_pandas()
    )

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
                    alt.Tooltip(["faixa_etaria:N", "sexo:N", "total:Q"]),
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
                    alt.Tooltip(["faixa_etaria:N", "sexo:N", "total:Q"]),
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
            st.altair_chart(pyramid_chart, use_container_width=True)

        with col_gender:
            gender_chart = (
                alt.Chart(gender_df)
                .transform_calculate(sexo_abrev="datum.sexo == 'Feminino' ? 'F' : 'M'")
                .mark_bar()
                .encode(
                    alt.X("sexo_abrev:N").title(None).sort(["F", "M"]).axis(labelAngle=0),
                    alt.Y("total:Q").title("Participantes"),
                    alt.Color("sexo:N").scale(color_scale).legend(None),
                    alt.Tooltip(["sexo:N", "total:Q"]),
                )
                .properties(title="Distribuição por sexo", height=540, padding={"top": 40, "left": 5, "right": 5, "bottom": 5})
                .configure_title(fontSize=14, anchor="middle")
            )
            st.altair_chart(gender_chart, use_container_width=True)

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
            use_container_width=True,
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
            use_container_width=True,
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
            use_container_width=True,
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
    st.plotly_chart(fig_box, use_container_width=True)

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
        """Notas válidas para a opção escolhida, conforme as regras de exclusão.
        `chave_cache` diferencia população e amostra no cache (o DataFrame não é usado no hash)."""
        objetivas = [("NU_NOTA_CN", "TP_PRESENCA_CN"), ("NU_NOTA_CH", "TP_PRESENCA_CH"),
                     ("NU_NOTA_LC", "TP_PRESENCA_LC"), ("NU_NOTA_MT", "TP_PRESENCA_MT")]
        if opcao == "Nota geral":
            # presente em todas as provas, quatro objetivas > 0 e redação não nula
            cond = [pl.col(p) == 1 for _, p in objetivas]
            cond += [pl.col(n).is_not_null() & (pl.col(n) > 0) for n, _ in objetivas]
            cond += [pl.col("NU_NOTA_REDACAO").is_not_null()]
            serie = _df.filter(pl.all_horizontal(cond)).select(
                pl.mean_horizontal(NOTAS_COLS).alias("v")
            )["v"]
        else:
            nota, presenca = _HIST_OPCOES[opcao]
            cond = (pl.col(presenca) == 1) & pl.col(nota).is_not_null()
            if nota != "NU_NOTA_REDACAO":
                cond = cond & (pl.col(nota) > 0)
            serie = _df.filter(cond)[nota]
        return serie.cast(pl.Float64).to_numpy()

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

        st.plotly_chart(fig_hist, use_container_width=True)

        _fmt = lambda v: f"{v:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
        _kpis_hist = [
            ("n", f"{_n:,}".replace(",", ".")),
            ("Média", _fmt(_media)),
            ("Mediana", _fmt(_mediana)),
            ("Desvio-padrão", _fmt(float(np.std(_vals, ddof=1)) if _n > 1 else 0.0)),
            ("Mínimo", _fmt(float(np.min(_vals)))),
            ("Máximo", _fmt(float(np.max(_vals)))),
        ]
        for _kc, (_rot, _v) in zip(st.columns(len(_kpis_hist)), _kpis_hist):
            with _kc:
                with st.container(border=True):
                    st.metric(_rot, _v)

        st.caption(
            f"Classes de {_HIST_BIN} pontos (20 classes de 0 a 1000). {_escala_txt}. "
            "Foram considerados apenas participantes presentes; notas zero ou vazias das provas objetivas "
            "são excluídas. A nota geral é a média das cinco notas e só é calculada para quem possui as cinco."
        )


# ============================================================
# ABA 1 — VISÃO GERAL
# ============================================================

def get_enem_kpis(data):
    total_inscritos   = data.height
    participantes_df  = data.filter(PRESENCA_FILTER)
    total_participantes = participantes_df.height

    notas_validas = (
        participantes_df.select(NOTAS_COLS).unpivot().drop_nulls("value")["value"]
    )
    media_geral       = round(notas_validas.mean(), 2) if notas_validas.len() > 0 else 0.0
    mediana_geral     = round(notas_validas.median(), 2) if notas_validas.len() > 0 else 0.0

    return {
        "total_inscritos":     total_inscritos,
        "total_participantes": total_participantes,
        "media_geral":         media_geral,
        "mediana_geral":       mediana_geral,
    }


enem_kpis = get_enem_kpis(enem_df)

with tab_populacao:
    st.markdown(
        "Análise dos microdados do ENEM para o Rio Grande do Sul, cobrindo perfil demográfico, socioeconômico e desempenho acadêmico dos participantes.  \n"
        f"**Edição analisada:** {ANO}  \n"
        f"**Filtro:** Participantes do Rio Grande do Sul  \n"
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

    def _tabela_codigos(itens):
        st.dataframe(
            pd.DataFrame(itens, columns=["Código", "Descrição"]).astype(str),
            hide_index=True,
            use_container_width=True,
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
        ("Qualitativa", "Tipo de escola", "Nominal (binária)", [
            (1, "Não respondeu"), (2, "Pública"), (3, "Privada"),
        ]),
        ("Quantitativa", "Nota", "Contínua", [
            ("CN", "Nota da prova de Ciências da Natureza"),
            ("CH", "Nota da prova de Ciências Humanas"),
            ("LC", "Nota da prova de Linguagens e Códigos"),
            ("MT", "Nota da prova de Matemática"),
            ("RED", "Nota da prova de Redação"),
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
    st.markdown(
        "Análise descritiva de uma **amostra** dos participantes do ENEM no Rio Grande do Sul, "
        "replicando as análises realizadas para a população.  \n"
        "**Grau de confiança:** 95%  \n"
        "**Margem de erro:** 2%  \n"
        "**Proporção:** 50%  \n"
        "**Total da amostra:** 2.351 participantes"
    )

    _render_indicadores(get_enem_kpis(enem_amostra))
    _render_analises(enem_amostra, chave="amostra")


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
        "t": t_obs, "t_crit": t_crit, "p_valor": p_valor, "rejeita": p_valor < alpha,
    }


def _br(v: float, casas: int = 4) -> str:
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


with tab_comparacao:
    st.markdown(
        "Inferência estatística realizada **exclusivamente com os dados da amostra** "
        f"({TAMANHO_AMOSTRA:,} participantes)".replace(",", ".") + ". "
        "A comparação com os valores da população será apresentada em seção posterior."
    )

    _alpha_rot = st.segmented_control(
        "Nível de significância (α) — aplicado a todos os testes desta aba",
        options=["1%", "5%", "10%"], default="5%", key="inf_alpha",
    ) or "5%"
    ALPHA = int(_alpha_rot.rstrip("%")) / 100
    CONF = 1 - ALPHA

    st.divider()
    st.subheader(":material/functions: Inferência para uma proporção — participantes do sexo feminino")

    # --- Definição ---
    st.markdown("##### 1. Variável e evento de interesse")
    st.markdown(
        "- **Variável qualitativa:** Sexo (`TP_SEXO`), nominal binária  \n"
        "- **Evento de interesse:** o participante ser do sexo **Feminino**  \n"
        "- **Parâmetro:** $p$ = proporção de mulheres entre os participantes do ENEM 2023 no RS"
    )

    # --- Hipóteses ---
    P0 = 0.5
    st.markdown("##### 2. Hipóteses")
    st.markdown(
        "O valor de referência é definido a partir de um critério teórico de **paridade entre os sexos**, "
        "sem uso de informações da população. O teste é **bilateral**, pois não se assume de antemão "
        "qual sexo predomina."
    )
    _h1, _h2 = st.columns(2)
    with _h1:
        with st.container(border=True):
            st.markdown("**Hipótese nula** — participação igual entre os sexos")
            st.latex(r"H_0:\; p = 0{,}5")
    with _h2:
        with st.container(border=True):
            st.markdown("**Hipótese alternativa** — participação diferente entre os sexos")
            st.latex(r"H_1:\; p \neq 0{,}5")

    res =_inferencia_proporcao(enem_amostra, pl.col("TP_SEXO") == "F", P0, ALPHA)

    # --- Estimativa pontual e IC ---
    st.markdown(f"##### 3. Estimação da proporção — intervalo de {CONF:.0%} de confiança")
    st.latex(
        r"\hat{p} = \frac{x}{n} \qquad "
        r"IC_{" + f"{CONF*100:.0f}" + r"\%}(p) = \hat{p} \pm z_{\alpha/2}\sqrt{\frac{\hat{p}(1-\hat{p})}{n}}"
    )
    _c = st.columns(5)
    for _col, (_rot, _val) in zip(_c, [
        ("Mulheres na amostra (x)", f"{res['x']:,}".replace(",", ".")),
        ("Tamanho da amostra (n)", f"{res['n']:,}".replace(",", ".")),
        ("Proporção amostral (p̂)", _br(res["p_hat"])),
        ("Erro-padrão", _br(res["ep"])),
        (f"IC {CONF:.0%}", f"[{_br(res['ic_inf'])}; {_br(res['ic_sup'])}]"),
    ]):
        with _col:
            with st.container(border=True):
                st.metric(_rot, _val)
    st.caption(
        f"Com {CONF:.0%} de confiança, a proporção de mulheres entre os participantes está entre "
        f"{_br(res['ic_inf']*100, 2)}% e {_br(res['ic_sup']*100, 2)}%. "
        f"Valor crítico utilizado: z = {_br(res['z_crit'], 3)}."
    )

    # --- Teste de hipótese ---
    st.markdown("##### 4. Teste de hipótese para a proporção")
    st.latex(
        r"Z = \frac{\hat{p} - p_0}{\sqrt{\dfrac{p_0(1-p_0)}{n}}} \qquad "
        r"\text{valor-p} = 2\,P(Z > |z_{obs}|)"
    )
    st.caption(
        f"Condição para a aproximação normal: n·p₀ = n·(1 − p₀) = {_br(res['cond'], 1)} ≥ 10 — atendida."
        if res["cond"] >= 10 else
        f"Atenção: n·p₀ = {_br(res['cond'], 1)} < 10 — a aproximação normal não é adequada."
    )
    _t = st.columns(4)
    _pval_txt = "< 0,0001" if res["p_valor"] < 1e-4 else _br(res["p_valor"])
    for _col, (_rot, _val, _help) in zip(_t, [
        ("Nível de significância (α)", _br(ALPHA, 2), None),
        ("Estatística de teste (z)", _br(res["z"], 2), None),
        ("Valor crítico", f"± {_br(res['z_crit'], 3)}", None),
        ("Valor-p", _pval_txt, f"Valor exato: {res['p_valor']:.2e}"),
    ]):
        with _col:
            with st.container(border=True):
                st.metric(_rot, _val, help=_help)

    # curva normal padrão com regiões de rejeição e z observado
    _zc, _zo = res["z_crit"], res["z"]
    _lim = max(4.0, abs(_zo) + 1)
    _xs = np.linspace(-_lim, _lim, 1200)
    _ys = np.exp(-0.5 * _xs**2) / np.sqrt(2 * np.pi)
    fig_z = go.Figure()
    fig_z.add_trace(go.Scatter(x=_xs, y=_ys, mode="lines", line=dict(color="#374151", width=2),
                               name="N(0, 1)", hoverinfo="skip"))
    for _mask, _show in [(_xs <= -_zc, True), (_xs >= _zc, False)]:
        fig_z.add_trace(go.Scatter(
            x=_xs[_mask], y=_ys[_mask], fill="tozeroy", mode="none",
            fillcolor="rgba(214,39,40,0.35)", name=f"Região de rejeição (α = {_br(ALPHA, 2)})",
            showlegend=_show, hoverinfo="skip",
        ))
    fig_z.add_vline(x=_zo, line=dict(color=CORES_SEXO["Feminino"], width=3),
                    annotation_text=f"z observado = {_br(_zo, 2)}", annotation_position="top left")
    for _s in (-_zc, _zc):
        fig_z.add_vline(x=_s, line=dict(color="#D62728", width=1.5, dash="dash"),
                        annotation_text=_br(_s, 2), annotation_position="bottom right")
    fig_z.update_layout(
        title=dict(text="Distribuição da estatística de teste sob H₀", x=0.5, xanchor="center", font=dict(size=15)),
        xaxis=dict(title="z", range=[-_lim, _lim], fixedrange=True),
        yaxis=dict(title="Densidade", fixedrange=True),
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
        separators=",.", margin=dict(t=60, b=40, l=60, r=20), height=380,
    )
    st.plotly_chart(fig_z, use_container_width=True)

    # --- Conclusão ---
    st.markdown("##### 5. Conclusão")
    if res["rejeita"]:
        _dir = "superior" if res["p_hat"] > P0 else "inferior"
        st.success(
            f"Como |z| = {_br(abs(_zo), 2)} > {_br(_zc, 3)} e o valor-p ({_pval_txt}) é menor que "
            f"α = {_br(ALPHA, 2)}, **rejeitamos H₀**. Há evidência estatística, ao nível de "
            f"{_alpha_rot} de significância, de que a proporção de mulheres entre os participantes "
            f"do ENEM 2023 no RS é diferente de 50%. O intervalo de confiança "
            f"[{_br(res['ic_inf'])}; {_br(res['ic_sup'])}] está inteiramente {_dir} a 0,5, "
            f"indicando que as mulheres são {'maioria' if _dir == 'superior' else 'minoria'} entre os participantes.",
            icon=":material/check_circle:",
        )
    else:
        st.warning(
            f"Como |z| = {_br(abs(_zo), 2)} ≤ {_br(_zc, 3)} e o valor-p ({_pval_txt}) é maior ou igual a "
            f"α = {_br(ALPHA, 2)}, **não rejeitamos H₀**. Não há evidência estatística suficiente para "
            "afirmar que a proporção de mulheres difere de 50%.",
            icon=":material/info:",
        )

    # ========================================================
    # (b) Inferência para média — nota geral: privada × pública
    # ========================================================
    st.divider()
    st.subheader(":material/school: Inferência para médias — nota geral: escola privada × escola pública")

    _OBJ = ["NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT"]
    _amostra_geral = (
        enem_amostra
        .filter(pl.all_horizontal([pl.col(c).is_not_null() & (pl.col(c) > 0) for c in _OBJ])
                & pl.col("NU_NOTA_REDACAO").is_not_null())
        .with_columns(pl.mean_horizontal(NOTAS_COLS).alias("NOTA_GERAL"))
    )
    _n_geral = _amostra_geral.height
    _n_sem_escola = _amostra_geral.filter(pl.col("TP_ESCOLA") == 1).height
    _priv = _amostra_geral.filter(pl.col("TP_ESCOLA") == 3)["NOTA_GERAL"].to_numpy()
    _pub = _amostra_geral.filter(pl.col("TP_ESCOLA") == 2)["NOTA_GERAL"].to_numpy()

    # --- Definição ---
    st.markdown("##### 1. Variável e grupos")
    st.markdown(
        "- **Variável quantitativa:** nota geral — média das cinco notas (CN, CH, LC, MT e Redação), contínua  \n"
        "- **Grupos (`TP_ESCOLA`):** escola **privada** e escola **pública** (amostras independentes)  \n"
        r"- **Parâmetros:** $\mu_{priv}$ e $\mu_{pub}$ = nota geral média de cada grupo"
    )
    st.info(
        f"Dos {_n_geral:,} participantes da amostra com nota geral válida, ".replace(",", ".")
        + f"**{_n_sem_escola:,} ({_n_sem_escola / _n_geral:.0%}) não informaram o tipo de escola**".replace(",", ".")
        + " (código 1 — a pergunta é respondida principalmente por concluintes do Ensino Médio). "
        f"A análise considera apenas os {len(_priv) + len(_pub):,} que declararam escola pública ou privada, ".replace(",", ".")
        + "e as conclusões se referem a esse grupo.",
        icon=":material/info:",
    )

    # --- Hipóteses ---
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

    # --- Intervalos de confiança ---
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
    st.dataframe(_tab_ic, hide_index=True, use_container_width=True)

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
    st.plotly_chart(fig_ic, use_container_width=True)
    st.caption(
        f"Com {CONF:.0%} de confiança, a nota geral média dos alunos de escola privada está entre "
        f"{_br(rm['a']['ic_inf'], 2)} e {_br(rm['a']['ic_sup'], 2)}, e a dos alunos de escola pública entre "
        f"{_br(rm['b']['ic_inf'], 2)} e {_br(rm['b']['ic_sup'], 2)}. A diferença entre as médias está entre "
        f"{_br(rm['ic_inf'], 2)} e {_br(rm['ic_sup'], 2)} pontos."
    )

    # --- Teste t de Welch ---
    st.markdown("##### 4. Teste de hipótese para a diferença de médias (t de Welch)")
    st.latex(
        r"t = \frac{\bar{x}_{priv} - \bar{x}_{pub}}{\sqrt{\dfrac{s_{priv}^2}{n_{priv}} + \dfrac{s_{pub}^2}{n_{pub}}}}"
        r"\qquad \text{valor-p} = P(T_{gl} > t_{obs})"
    )
    st.caption(
        "O teste de Welch não supõe variâncias iguais entre os grupos; os graus de liberdade (gl) são obtidos "
        "pela aproximação de Welch–Satterthwaite. Com amostras grandes, o Teorema Central do Limite garante "
        "que as médias amostrais têm distribuição aproximadamente normal."
    )
    _pval_m = "< 0,0001" if rm["p_valor"] < 1e-4 else _br(rm["p_valor"])
    for _col, (_rot, _val, _help) in zip(st.columns(5), [
        ("Nível de significância (α)", _br(ALPHA, 2), None),
        ("Estatística de teste (t)", _br(rm["t"], 2), None),
        ("Graus de liberdade", _br(rm["gl"], 1), None),
        ("Valor crítico", _br(rm["t_crit"], 3), "Unilateral à direita"),
        ("Valor-p", _pval_m, f"Valor exato: {rm['p_valor']:.2e}"),
    ]):
        with _col:
            with st.container(border=True):
                st.metric(_rot, _val, help=_help)

    from scipy import stats as _stats
    _tc, _to = rm["t_crit"], rm["t"]
    _lim = max(4.0, abs(_to) + 1)
    _xs = np.linspace(-_lim, _lim, 1500)
    _ys = _stats.t.pdf(_xs, rm["gl"])
    fig_t = go.Figure()
    fig_t.add_trace(go.Scatter(x=_xs, y=_ys, mode="lines", line=dict(color="#374151", width=2),
                               name=f"t de Student (gl = {_br(rm['gl'], 1)})", hoverinfo="skip"))
    _m = _xs >= _tc
    fig_t.add_trace(go.Scatter(
        x=_xs[_m], y=_ys[_m], fill="tozeroy", mode="none", fillcolor="rgba(214,39,40,0.35)",
        name=f"Região de rejeição (α = {_br(ALPHA, 2)})", hoverinfo="skip",
    ))
    fig_t.add_vline(x=_to, line=dict(color=CORES_ESCOLA["Privada"], width=3),
                    annotation_text=f"t observado = {_br(_to, 2)}", annotation_position="top left")
    fig_t.add_vline(x=_tc, line=dict(color="#D62728", width=1.5, dash="dash"),
                    annotation_text=_br(_tc, 3), annotation_position="bottom right")
    fig_t.update_layout(
        title=dict(text="Distribuição da estatística de teste sob H₀", x=0.5, xanchor="center", font=dict(size=15)),
        xaxis=dict(title="t", range=[-_lim, _lim], fixedrange=True),
        yaxis=dict(title="Densidade", fixedrange=True),
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
        separators=",.", margin=dict(t=60, b=40, l=60, r=20), height=380,
    )
    st.plotly_chart(fig_t, use_container_width=True)

    # --- Conclusão ---
    st.markdown("##### 5. Conclusão")
    if rm["rejeita"]:
        st.success(
            f"Como t = {_br(_to, 2)} > {_br(_tc, 3)} e o valor-p ({_pval_m}) é menor que α = {_br(ALPHA, 2)}, "
            f"**rejeitamos H₀**. Há evidência estatística, ao nível de {_alpha_rot} de significância, de que "
            "alunos de escola privada obtêm nota geral média maior que alunos de escola pública. "
            f"Estima-se que a diferença seja de {_br(rm['dif'], 1)} pontos, com IC {CONF:.0%} entre "
            f"{_br(rm['ic_inf'], 1)} e {_br(rm['ic_sup'], 1)} pontos.",
            icon=":material/check_circle:",
        )
    else:
        st.warning(
            f"Como t = {_br(_to, 2)} ≤ {_br(_tc, 3)} e o valor-p ({_pval_m}) é maior ou igual a "
            f"α = {_br(ALPHA, 2)}, **não rejeitamos H₀**. Não há evidência estatística suficiente para afirmar "
            "que alunos de escola privada obtêm nota geral média maior que alunos de escola pública.",
            icon=":material/info:",
        )
