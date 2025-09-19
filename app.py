import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

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
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1qNzze7JpzCwzEE2MQ4hhxWnUXuZvrQ0qpZoMT3BE8G4/gviz/tq?tqx=out:csv&sheet=editais_abertos"
    df = pd.read_csv(url)
    # Remove colunas extras (Unnamed)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

df = carregar_dados()

# ===========================
# Pré-processamento
# ===========================
if not df.empty:
    # Garantir que datas estão no formato datetime
    df["data_fim"] = pd.to_datetime(df["data_fim"], errors="coerce", dayfirst=True)
    df["data_inicio"] = pd.to_datetime(df["data_inicio"], errors="coerce", dayfirst=True)

    # Tratar colunas com múltiplos valores
    if "modalidade" in df.columns:
        df["modalidade"] = df["modalidade"].fillna("").astype(str)
        df["modalidade_lista"] = df["modalidade"].str.split(";")
    else:
        df["modalidade_lista"] = [[] for _ in range(len(df))]

    if "tema" in df.columns:
        df["tema"] = df["tema"].fillna("").astype(str)
        df["tema_lista"] = df["tema"].str.split(";")
    else:
        df["tema_lista"] = [[] for _ in range(len(df))]

    if "tipo_financiamento" in df.columns:
        df["tipo_financiamento"] = df["tipo_financiamento"].fillna("").astype(str)
        df["tipo_financiamento_lista"] = df["tipo_financiamento"].str.split(";")
    else:
        df["tipo_financiamento_lista"] = [[] for _ in range(len(df))]

# ===========================
# Filtros no sidebar
# ===========================
if not df.empty:
    agencias = df["agencia"].dropna().unique().tolist()
    agencia_sel = st.sidebar.selectbox("Agência de fomento", ["Todos"] + agencias)

    modalidades = sorted(set(sum(df["modalidade_lista"], [])))
    temas = sorted(set(sum(df["tema_lista"], [])))

    modalidade_sel = st.sidebar.multiselect("Modalidade", modalidades)
    tema_sel = st.sidebar.multiselect("Tema", temas)

    # Filtro por ano
    anos = sorted(df["data_fim"].dropna().dt.year.unique())
    ano_sel = st.sidebar.multiselect("Ano de encerramento", anos)

    prazo_sel = st.sidebar.selectbox(
        "Prazo de inscrição",
        ["Todos", "Até 7 dias", "Mais de 7 dias", "Encerrados"]
    )

    # Página (abertos/encerrados)
    pagina = st.sidebar.radio("📌 Escolha a página", ["Abertos", "Encerrados"])

    # ===========================
    # Filtrar dados
    # ===========================
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
        elif prazo_sel == "Encerrados":
            df_filtrado = df_filtrado[mask & (delta < 0)]
else:
    df_filtrado = pd.DataFrame()

# ===========================
# Nuvem de palavras (decorativa, menor e sem duplicados)
# ===========================
if not df.empty and "tema_lista" in df.columns:
    termos = sum(df["tema_lista"].tolist(), [])
    termos_unicos = list(set([t.strip() for t in termos if t.strip()]))
    texto = " ".join(termos_unicos)
    if texto.strip():
        wc = WordCloud(width=600, height=200, background_color="white").generate(texto)
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

# ===========================
# Gráficos de distribuição por agência (% stacked, agência no eixo Y)
# ===========================
st.subheader("📊 Distribuições por Agência")

# Tipo de financiamento por agência
tipos_expandidos = []
for _, row in df.iterrows():
    for tf in row["tipo_financiamento_lista"]:
        tf = tf.strip()
        if tf:
            tipos_expandidos.append({"agencia": row["agencia"], "tipo_financiamento": tf})

if tipos_expandidos:
    df_tipos = pd.DataFrame(tipos_expandidos)
    tabela_tipos = df_tipos.pivot_table(index="agencia", columns="tipo_financiamento", aggfunc=len, fill_value=0)
    tabela_tipos_pct = tabela_tipos.div(tabela_tipos.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(8, 5))
    tabela_tipos_pct.plot(kind="barh", stacked=True, ax=ax)
    ax.set_title("Distribuição Percentual de Tipos de Financiamento por Agência")
    ax.set_xlabel("% do total na agência")
    ax.set_ylabel("Agência")
    st.pyplot(fig)

# Modalidade por agência
modalidades_expandidas = []
for _, row in df.iterrows():
    for mod in row["modalidade_lista"]:
        mod = mod.strip()
        if mod:
            modalidades_expandidas.append({"agencia": row["agencia"], "modalidade": mod})

if modalidades_expandidas:
    df_mods = pd.DataFrame(modalidades_expandidas)
    tabela_mods = df_mods.pivot_table(index="agencia", columns="modalidade", aggfunc=len, fill_value=0)
    tabela_mods_pct = tabela_mods.div(tabela_mods.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(8, 5))
    tabela_mods_pct.plot(kind="barh", stacked=True, ax=ax)
    ax.set_title("Distribuição Percentual de Modalidades por Agência")
    ax.set_xlabel("% do total na agência")
    ax.set_ylabel("Agência")
    st.pyplot(fig)

# ===========================
# Orientações
# ===========================
with st.expander("📌 Orientações", expanded=True):
    st.markdown("""
    - A lista é atualizada semanalmente, sempre às segundas.
    - Os editais encerrados foram mantidos para possibilitar a análise para futuras oportunidades.
    - Os temas são listados de forma a introduzir inicialmente o objetivo do edital, mas seu conteúdo pode abarcar mais questões. Exemplo: editais de bolsas de formação costumam abranger todas as áreas do conhecimento. 
    - Esse é um painel experimental. Em caso de erro, dúvidas ou sugestões, utilize a caixinha no menu lateral.
    """)

# ===========================
# Exibição por página
# ===========================
if pagina == "Abertos":
    st.subheader("📢 Editais de Fomento Abertos")
    df_abertos = df_filtrado[df_filtrado["data_fim"] >= pd.Timestamp.today()]
    if not df_abertos.empty:
        for _, row in df_abertos.iterrows():
            with st.container():
                st.markdown(f"**{row['titulo']}**")
                st.write(f"📌 Agência: {row['agencia']}")
                st.write(f"🎓 Modalidade: {row.get('modalidade', '')}")
                st.write(f"💰 Tipo de financiamento: {row.get('tipo_financiamento', '')}")
                st.write(f"🗓️ Início: {row['data_inicio'].date()} | Fim: {row['data_fim'].date() if pd.notna(row['data_fim']) else ''}")
                st.write(f"🏷️ Tema: {row.get('tema', '')}")
                if pd.notna(row.get('link', '')):
                    st.markdown(f"[🔗 Acesse o edital]({row['link']})")
                st.markdown("---")
    else:
        st.warning("Nenhum edital aberto disponível no momento.")

elif pagina == "Encerrados":
    st.subheader("📚 Editais Encerrados")
    df_encerrados = df[df["data_fim"] < pd.Timestamp.today()]
    if not df_encerrados.empty:
        st.dataframe(df_encerrados)
    else:
        st.info("Nenhum edital encerrado disponível.")

# ===========================
# Feedback no Google Sheets
# ===========================
st.sidebar.markdown("## 📝 Reportar erro ou dúvida")

nome = st.sidebar.text_input("Nome (opcional)")
email = st.sidebar.text_input("E-mail (opcional)")
mensagem = st.sidebar.text_area("Mensagem")

if st.sidebar.button("Enviar"):
    try:
        # Autenticação com a service account
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scope
        )
        client = gspread.authorize(creds)

        # Abrir planilha de feedbacks (precisa existir no Google Sheets!)
        sheet = client.open("feedback_editais").sheet1

        sheet.append_row([nome, email, mensagem, str(datetime.now())])
        st.sidebar.success("✅ Feedback enviado com sucesso!")
    except Exception as e:
        st.sidebar.error(f"Erro ao salvar feedback: {e}")
