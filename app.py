import streamlit as st
import pandas as pd
from datetime import datetime
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# =======================
# Configuração inicial
# =======================
st.set_page_config(
    page_title="Painel de Editais - AEDB",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =======================
# Carregar dados (Google Drive CSV)
# =======================
# Substitua pelo link direto do seu arquivo no Google Drive (formato: https://drive.google.com/uc?id=ARQUIVO_ID)
URL = "https://drive.google.com/file/d/16KynnqClb97FeozpdJAYL0TEQ34CktH5"

@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv(URL, sep=";", encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(URL, sep=";", encoding="latin-1")
    return df

df = carregar_dados()

# =======================
# Sidebar
# =======================
st.sidebar.image("1.png", use_container_width=True)

st.sidebar.markdown(
    """
    <div style='font-size:12px; margin-top:10px; color:#444;'>
        Gerado no GPAQ, para uso exclusivo dos docentes e funcionários da AEDB.
    </div>
    """, unsafe_allow_html=True
)

# Filtros
if not df.empty:
    agencias = df["agencia"].dropna().unique().tolist()
    agencias_selecionadas = st.sidebar.multiselect(
        "Agência de fomento", agencias, default=agencias
    )

    opcoes_prazo = ["Todos", "Fecham em até 7 dias", "Fecham em até 30 dias"]
    prazo_selecionado = st.sidebar.selectbox("Prazo de inscrição", opcoes_prazo)

# =======================
# Sidebar - Feedback
# =======================
st.sidebar.markdown("<h4>📩 Reportar erro ou dúvida</h4>", unsafe_allow_html=True)

with st.sidebar.form("feedback_form"):
    nome = st.text_input("Nome (opcional)")
    email = st.text_input("E-mail (opcional)")
    mensagem = st.text_area("Mensagem", height=80)

    enviar = st.form_submit_button("Enviar")

    if enviar:
        if mensagem.strip() == "":
            st.sidebar.error("Por favor, escreva uma mensagem antes de enviar.")
        else:
            with open("feedback.csv", "a", encoding="utf-8") as f:
                f.write(f"{datetime.today().strftime('%Y-%m-%d %H:%M:%S')};{nome};{email};{mensagem}\n")
            st.sidebar.success("✅ Obrigado! Sua mensagem foi registrada.")

# =======================
# Filtros aplicados
# =======================
if not df.empty:
    df = df[df["agencia"].isin(agencias_selecionadas)]

    def parse_data(x):
        for fmt in ["%d/%m/%Y", "%Y-%m-%d"]:
            try:
                return datetime.strptime(str(x), fmt)
            except:
                continue
        return None

    df["data_fim_dt"] = df["data_fim"].apply(parse_data)
    hoje = datetime.today()

    # Remover editais encerrados
    df = df[df["data_fim_dt"].isna() | (df["data_fim_dt"] >= hoje)]

    # Aplicar filtro de prazo
    if prazo_selecionado == "Fecham em até 7 dias":
        df = df[df["data_fim_dt"].notna() & (df["data_fim_dt"] <= hoje + pd.Timedelta(days=7))]
    elif prazo_selecionado == "Fecham em até 30 dias":
        df = df[df["data_fim_dt"].notna() & (df["data_fim_dt"] <= hoje + pd.Timedelta(days=30))]

# =======================
# Card de Orientações
# =======================
st.markdown("<h4>📌 Orientações</h4>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="background:#E8F4FF; padding:12px; border-radius:8px; margin-bottom:20px; font-size:13px;">
    - A lista é atualizada semanalmente, sempre às segundas.<br>
    - Apenas editais com inscrições abertas são exibidos (encerrados não aparecem).<br>
    - Em caso de erros ou dúvidas, utilize a caixinha de <i>Reportar erro ou dúvida</i> no menu lateral.<br>
    - Editais que encerram em até 7 dias aparecem destacados em amarelo.  
    </div>
    """, unsafe_allow_html=True
)

# =======================
# Listagem principal
# =======================
st.markdown("<h4>📢 Editais de Fomento Abertos</h4>", unsafe_allow_html=True)

if df.empty:
    st.warning("Nenhum edital disponível no momento.")
else:
    for _, row in df.iterrows():
        data_fim_txt = row["data_fim"]
        fundo_card = "background:white;"

        if row["data_fim_dt"] is not None:
            dias = (row["data_fim_dt"] - hoje).days
            if dias <= 7:
                data_fim_txt = f"{row['data_fim']} 🔔"
                fundo_card = "background:#FFF9E6;"  # amarelinho

        # card
        st.markdown(f"""
        <div style="
            {fundo_card}
            border-radius: 8px;
            border: 1px solid #ddd;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            padding: 10px;
            margin-bottom: 12px;
        ">
          <h4 style="margin:0; font-size:15px; color:#007BFF;">{row['titulo']}</h4>
          <p style="margin:3px 0; font-size:12px;"><b>Agência:</b> {row['agencia']}</p>
          <p style="margin:3px 0; font-size:12px;"><b>Data início:</b> {row['data_inicio']}</p>
          <p style="margin:3px 0; font-size:12px;"><b>Data final:</b> {data_fim_txt}</p>
          <p style="margin:3px 0; font-size:12px;"><b>Tema:</b> {row['tema'] if pd.notna(row['tema']) else '-'}</p>
          <a href="{row['link']}" target="_blank"
             style="text-decoration:none; color:white; background:#007BFF;
                    padding:4px 8px; border-radius:4px; display:inline-block; margin-top:4px; font-size:12px;">
             Acessar edital
          </a>
        </div>
        """, unsafe_allow_html=True)

# =======================
# Nuvem de Palavras
# =======================
st.markdown("<h4>📊 Temas mais frequentes</h4>", unsafe_allow_html=True)

if "tema" in df.columns and df["tema"].notna().any():
    texto_temas = " ".join(df["tema"].dropna().astype(str))
else:
    texto_temas = "Ciência Educação Inovação Tecnologia Saúde Sustentabilidade Pesquisa Extensão"

wc = WordCloud(width=600, height=300, background_color="white", colormap="Blues").generate(texto_temas)

fig, ax = plt.subplots(figsize=(8,4))
ax.imshow(wc, interpolation="bilinear")
ax.axis("off")
st.pyplot(fig)
