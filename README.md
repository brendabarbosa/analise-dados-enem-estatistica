# Análise de Microdados do ENEM — Rio Grande do Sul (2021–2023)

Dashboard interativo para exploração dos microdados do ENEM com foco nos participantes do Rio Grande do Sul, cobrindo as edições de 2021, 2022 e 2023.

**Autora:** Brenda Anghinoni Barbosa  

---

## Pré-requisitos

- Python 3.10 ou superior
---

## Instalação

1. Acesse a pasta do projeto.

2. Crie e ative um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## Dados

Os arquivos de microdados já estão incluídos na pasta `data/` do projeto, prontos para uso:

```
data/
├── MICRODADOS_ENEM_2021.csv
├── MICRODADOS_ENEM_2022.csv
└── MICRODADOS_ENEM_2023.csv
```

Não é necessário nenhum download adicional para executar o dashboard.

### Caso precise reobter os dados

O dashboard suporta as edições de **2021, 2022 e 2023** — individualmente ou em conjunto. Para cada edição desejada:

1. Baixe o ZIP dos microdados da edição correspondente no portal do INEP:
   - https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem
2. Extraia o arquivo. Dentro da subpasta `DADOS/` você encontrará o CSV principal:

```
microdados_enem_<ano>/
└── DADOS/
    └── MICRODADOS_ENEM_<ANO>.csv  ← copie este arquivo
```

3. Copie o arquivo para a pasta `data/` do projeto, mantendo o nome original.

> **Nota:** não é necessário ter os três arquivos. O dashboard carrega automaticamente apenas as edições cujos arquivos estiverem presentes na pasta `data/`. Se algum arquivo estiver faltando, uma mensagem de erro indicará quais edições não foram encontradas.

---

## Execução

```bash
streamlit run app.py
```

O dashboard abrirá automaticamente no navegador em `http://localhost:8501`.

---

## Estrutura do projeto

```
.
├── app.py                        # Aplicação principal
├── data/
│   ├── MICRODADOS_ENEM_2021.csv  # Microdados do ENEM 2021 (opcional)
│   ├── MICRODADOS_ENEM_2022.csv  # Microdados do ENEM 2022 (opcional)
│   └── MICRODADOS_ENEM_2023.csv  # Microdados do ENEM 2023 (opcional)
├── .streamlit/
│   └── config.toml               # Configurações de tema
└── requirements.txt
```
