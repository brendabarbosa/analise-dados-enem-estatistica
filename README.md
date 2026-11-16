# Análise do ENEM 2023 — Rio Grande do Sul: População × Amostra

Dashboard interativo em Streamlit que analisa os microdados do ENEM 2023 dos participantes do Rio Grande do Sul. Ele compara a **população** com uma **amostra aleatória simples** retirada dela e apresenta inferência estatística sobre proporções e médias.

**Autora:** Brenda Anghinoni Barbosa

---

## Painéis

1. **Análise descritiva da população:** descrição da base, indicadores, distribuições, tabelas de frequência e medidas descritivas das notas.
2. **Análise descritiva da amostra:** dimensionamento e seleção da amostra e a mesma análise do painel 1. Cada indicador mostra a diferença (delta) em relação à população.
3. **Inferência estatística e comparação dos resultados:**
   - dois testes de proporção: sexo feminino (H₀: p = 0,5) e cor/raça branca (H₀: p = proporção do Censo 2022 no RS);
   - um teste de média de uma amostra: Matemática (H₀: μ = 500);
   - um teste de diferença de médias: nota geral de escola privada × pública (t de Welch, unilateral);
   - a seção final compara as estimativas com os parâmetros populacionais e inclui uma simulação de variabilidade amostral e as limitações da análise.

O nível de significância do painel 3 (1%, 5% ou 10%) pode ser alterado no próprio dashboard.

---

## Pré-requisitos

- Python 3.10 ou superior

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

---

## Dados

**Fonte:** [INEP — Microdados do ENEM](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem), edição 2023.

O ano de 2023 foi escolhido porque, a partir de 2024, os microdados deixaram de permitir a ligação entre as informações do participante e suas notas (LGPD).

O dashboard usa dois arquivos da pasta `data/`:

| Arquivo | Conteúdo |
|---|---|
| `PARTICIPANTES_ENEM_2023_RS.csv` | População do estudo: 110.735 participantes que fizeram a prova no RS e estiveram presentes nas quatro provas objetivas. Contém só as colunas usadas nas análises |
| `AMOSTRA_ENEM_2023_RS.csv` | Amostra aleatória simples de 2.351 participantes, gerada por `gerar_amostra.py` |

Para obter os microdados originais, baixe o ZIP da edição 2023 no portal do INEP. O CSV principal fica em `DADOS/MICRODADOS_ENEM_2023.csv` (76 variáveis).

### Regra de notas válidas

- **Todas as provas:** todas as notas registradas são consideradas, inclusive notas zero.
- **Nota geral:** média das cinco notas, calculada só para quem tem as quatro notas objetivas válidas e a redação.

---

## População e amostra

**Dimensionamento.** O tamanho da amostra foi obtido na [calculadora de tamanho amostral da SurveyMonkey](https://pt.surveymonkey.com/learn/research-and-analysis/sample-size-calculator/) com estes parâmetros:

- **População:** 110.735
- **Nível de confiança:** 95%
- **Margem de erro:** 2%
- **Proporção:** 50% (escolha conservadora, que maximiza o tamanho da amostra)

O resultado foi **n = 2.351**. A justificativa de cada parâmetro está no painel 2.

**Seleção (AAS).** `gerar_amostra.py` sorteia 2.351 participantes **sem reposição** a partir da lista completa da população. O sorteio usa `polars.DataFrame.sample` com semente fixa (42), então é reprodutível e cada participante tem a mesma probabilidade de seleção (n/N).

Para gerar (ou regerar) a amostra:

```bash
python gerar_amostra.py
```

---

## Execução

```bash
streamlit run app.py
```

O dashboard abre em `http://localhost:8501`.

---

## Estrutura do projeto

```
.
├── app.py                               # Dashboard (3 painéis)
├── gerar_amostra.py                     # Gera a amostra; define colunas, arquivos e parâmetros da amostra
├── data/
│   ├── PARTICIPANTES_ENEM_2023_RS.csv   # População (RS, presentes nas quatro provas objetivas)
│   └── AMOSTRA_ENEM_2023_RS.csv         # Amostra aleatória simples (n = 2.351)
├── .streamlit/
│   └── config.toml                      # Configurações de tema
└── requirements.txt
```
