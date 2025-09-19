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
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

df = carregar_dados()

# ===========================
# Pré-processamento
# ===========================
if not df.empty:
    df["data_fim"] = pd.to_datetime(df["data_fim"], errors="coerce", dayfirst=True)
    df["data_inicio"] = pd.to_datetime(df["data_inicio"], errors="coerce", dayfirst=True)

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
# Sidebar – escolha da página
# ===========================
pagina = st.sidebar.radio("📌 Escolha a página", ["Início", "Abertos", "Encerrados"])

# ===========================
# Página Inicial (Resumo)
# ===========================
if pagina == "Início":
    st.header("✨ Visão Geral dos Editais")

    # KPIs
    total_abertos = df[df["data_fim"] >= pd.Timestamp.today()].shape[0]
    total_encerrados = df[df["data_fim"] < pd.Timestamp.today()].shape[0]
    total_geral = df.shape[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("📢 Abertos", total_abertos)
    col2.metric("📚 Encerrados", total_encerrados)
    col3.metric("📊 Total", total_geral)

    # Próximos prazos
    st.subheader("🗓️ Próximos prazos de encerramento")
    proximos = df[df["data_fim"] >= pd.Timestamp.today()].sort_values("data_fim").head(5)
    if not proximos.empty:
        st.table(proximos[["titulo", "agencia", "data_fim"]])
    else:
        st.info("Nenhum prazo próximo disponível.")

    # Linha do tempo dos encerramentos
    st.subheader("📆 Linha do tempo de encerramentos futuros")
    df_futuros = df[df["data_fim"] >= pd.Timestamp.today()].copy()
    if not df_futuros.empty:
        df_futuros = df_futuros.groupby("data_fim").size().reset_index(name="qtd")
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.bar(df_futuros["data_fim"], df_futuros["qtd"], color="skyblue")
        ax.set_title("Quantidade de editais por data de encerramento")
        ax.set_xlabel("Data de encerramento")
        ax.set_ylabel("Nº de editais")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("Nenhum encerramento futuro disponível.")

    # Nuvem de palavras
    st.subheader("☁️ Principais Temas")
    termos = sum(df["tema_lista"].tolist(), [])
    termos_unicos = list(set([t.strip() for t in termos if t.strip()]))
    texto = " ".join(termos_unicos)
    if texto.strip():
        wc = WordCloud(width=600, height=200, background_color="white").generate(texto)
        fig, ax = plt.subplots(figsize=(8, 2.5))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

    # Distribuições
    st.subheader("📊 Distribuições por Agência")

    # Tipo de financiamento
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
        fig, ax = plt.subplots(figsize=(7, 3))
        tabela_tipos_pct.plot(kind="barh", stacked=True, ax=ax)
        ax.set_title("Distribuição Percentual de Tipos de Financiamento por Agência")
        ax.set_xlabel("% do total na agência")
        ax.set_ylabel("Agência")
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
        st.pyplot(fig)

    # Modalidade
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
        fig, ax = plt.subplots(figsize=(7, 3))
        tabela_mods_pct.plot(kind="barh", stacked=True, ax=ax)
        ax.set_title("Distribuição Percentual de Modalidades por Agência")
        ax.set_xlabel("% do total na agência")
        ax.set_ylabel("Agência")
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
        st.pyplot(fig)

    # Orientações
    with st.expander("📌 Orientações", expanded=True):
        st.markdown("""
        - A lista é atualizada semanalmente, sempre às segundas.
        - Os editais encerrados foram mantidos para possibilitar a análise para futuras oportunidades.
        - Os temas são listados de forma a introduzir inicialmente o objetivo do edital, mas seu conteúdo pode abarcar mais questões.
        - Esse é um painel experimental. Em caso de erro, dúvidas ou sugestões, utilize a caixinha no menu lateral.
        """)

    # Botões de navegação
    st.subheader("➡️ Acesse os editais")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📢 Ver Abertos"):
            st.session_state["pagina"] = "Abertos"
    with col2:
        if st.button("📚 Ver Encerrados"):
            st.session_state["pagina"] = "Encerrados"

# ===========================
# Página Abertos
# ===========================
elif pagina == "Abertos":
    st.subheader("📢 Editais de Fomento Abertos")
    df_abertos = df[df["data_fim"] >= pd.Timestamp.today()]
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

# ===========================
# Página Encerrados
# ===========================
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
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scope
        )
        client = gspread.authorize(creds)
        sheet = client.open("feedback_editais").sheet1
        sheet.append_row([nome, email, mensagem, str(datetime.now())])
        st.sidebar.success("✅ Feedback enviado com sucesso!")
    except Exception as e:
        st.sidebar.error(f"Erro ao salvar feedback: {e}")
