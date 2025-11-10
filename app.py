import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# ===========================
# Configuração inicial
# ===========================
st.set_page_config(
    page_title="Painel de Editais",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Painel de Editais de Fomento à Pesquisa e Extensão")

# ===========================
# Carregar dados do Google Sheets
# ===========================
@st.cache_data
@st.cache_data
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1qNzze7JpzCwzEE2MQ4hhxWnUXuZvrQ0qpZoMT3BE8G4/export?format=csv&gid=313632666"
    df = pd.read_csv(url, sep=";")  # 👈 diferença: separador ajustado
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df


df = carregar_dados()
st.write("✅ Dados carregados:", df.shape)
st.dataframe(df.head())

# ===========================
# Pré-processamento
# ===========================
if not df.empty:
    df["data_fim"] = pd.to_datetime(df["data_fim"], errors="coerce", dayfirst=True)
    df["data_inicio"] = pd.to_datetime(df["data_inicio"], errors="coerce", dayfirst=True)

    for col in ["modalidade", "tema", "tipo_financiamento"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
            df[f"{col}_lista"] = df[col].str.split(";")
        else:
            df[f"{col}_lista"] = [[] for _ in range(len(df))]

# ===========================
# Filtros no sidebar
# ===========================
if not df.empty:
    agencias = df["agencia"].dropna().unique().tolist()
    agencia_sel = st.sidebar.selectbox("Agência de fomento", ["Todos"] + sorted(agencias))

    modalidades = sorted(set(sum(df["modalidade_lista"], [])))
    temas = sorted(set(sum(df["tema_lista"], [])))

    modalidade_sel = st.sidebar.multiselect("Modalidade", modalidades)
    tema_sel = st.sidebar.multiselect("Tema", temas)

    anos = sorted(df["data_fim"].dropna().dt.year.unique())
    ano_sel = st.sidebar.multiselect("Ano de encerramento", anos)

    prazo_sel = st.sidebar.selectbox(
        "Prazo de inscrição",
        ["Todos", "Até 7 dias", "Mais de 7 dias"]
    )

    # ===========================
    # NOVO: Filtro por titularidade exigida
    # ===========================
    if "titularidade" in df.columns:
        titularidades = sorted(df["titularidade"].dropna().unique().tolist())
        titularidade_sel = st.sidebar.multiselect("Titularidade exigida", titularidades)
    else:
        titularidade_sel = []
else:
    agencia_sel = "Todos"
    modalidade_sel = []
    tema_sel = []
    ano_sel = []
    prazo_sel = "Todos"
    titularidade_sel = []

# ===========================
# Aplicar filtros
# ===========================
if not df.empty:
    df_filtrado = df.copy()

    if agencia_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["agencia"] == agencia_sel]

    if modalidade_sel:
        df_filtrado = df_filtrado[df_filtrado["modalidade_lista"].apply(lambda x: any(m in x for m in modalidade_sel))]

    if tema_sel:
        df_filtrado = df_filtrado[df_filtrado["tema_lista"].apply(lambda x: any(t in x for t in tema_sel))]

    if ano_sel:
        df_filtrado = df_filtrado[df_filtrado["data_fim"].dt.year.isin(ano_sel)]

    if prazo_sel != "Todos":
        hoje = pd.Timestamp('today').normalize()
        mask = df_filtrado["data_fim"].notna()
        delta = (df_filtrado["data_fim"] - hoje).dt.days

        if prazo_sel == "Até 7 dias":
            df_filtrado = df_filtrado[mask & (delta >= 0) & (delta <= 7)]
        elif prazo_sel == "Mais de 7 dias":
            df_filtrado = df_filtrado[mask & (delta > 7)]

    # NOVO: aplicar filtro de titularidade
