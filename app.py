import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuração inicial
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
# Filtros
# ===========================
if not df.empty:
    agencias = df["agencia"].dropna().unique().tolist()
    agencia_sel = st.sidebar.selectbox("Agência de fomento", ["Todos"] + agencias)

    prazo_sel = st.sidebar.selectbox(
        "Prazo de inscrição",
        ["Todos", "Até 7 dias", "Mais de 7 dias", "Encerrados"]  # <-- nova opção
    )

    # Filtrar dados
    df_filtrado = df.copy()
    if agencia_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["agencia"] == agencia_sel]

    if prazo_sel != "Todos":
        hoje = pd.Timestamp('today').normalize()  # só a data
        df_filtrado["data_fim"] = pd.to_datetime(df_filtrado["data_fim"], errors="coerce", dayfirst=True)

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
# Exibir editais
# ===========================
st.subheader("📢 Editais de Fomento Abertos")

if not df_filtrado.empty:
    for _, row in df_filtrado.iterrows():
        with st.container():
            st.markdown(f"**{row['titulo']}**")
            st.write(f"📌 Agência: {row['agencia']}")
            st.write(f"🗓️ Início: {row['data_inicio']} | Fim: {row['data_fim']}")
            st.write(f"🏷️ Tema: {row.get('tema', '')}")
            if pd.notna(row.get("link", "")):
                st.markdown(f"[🔗 Acesse o edital]({row['link']})")
            st.markdown("---")
else:
    st.warning("Nenhum edital disponível no momento.")

# ===========================
# Nuvem de palavras
# ===========================
st.subheader("📊 Temas mais frequentes")

if not df.empty and "tema" in df.columns:
    texto = " ".join(df["tema"].dropna().astype(str))
    if texto.strip():
        wc = WordCloud(width=800, height=400, background_color="white").generate(texto)
        fig, ax = plt.subplots()
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)
    else:
        st.info("Nenhum tema informado ainda.")
else:
    st.info("Nenhum tema disponível para gerar a nuvem de palavras.")

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
