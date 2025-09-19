# app (9).py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
from datetime import datetime

st.set_page_config(
    page_title="Painel de Editais",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Painel de Editais de Fomento à Pesquisa e Extensão")

# ===========================
# Orientações (topo)
# ===========================
with st.expander("📌 Orientações", expanded=True):
    st.markdown("""
    - A lista é atualizada semanalmente, sempre às segundas.
    - Os editais encerrados foram mantidos para possibilitar a análise para futuras oportunidades.
    - Os temas são listados de forma a introduzir inicialmente o objetivo do edital, mas seu conteúdo pode abarcar mais questões.
    - Esse é um painel experimental. Em caso de erro, dúvidas ou sugestões, utilize a caixinha no menu lateral.
    """)

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
# Filtros no sidebar (mantidos)
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
        ["Todos", "Até 7 dias", "Mais de 7 dias", "Encerrados"]
    )

    # Página (Abertos/Encerrados) agora como controle na página principal (não no sidebar)
else:
    # valores padrão caso df vazio
    agencia_sel = "Todos"
    modalidade_sel = []
    tema_sel = []
    ano_sel = []
    prazo_sel = "Todos"

# ===========================
# Filtro aplicado (com cópia)
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
        elif prazo_sel == "Encerrados":
            df_filtrado = df_filtrado[mask & (delta < 0)]
else:
    df_filtrado = pd.DataFrame()

# ===========================
# Controle Abertos / Encerrados na página inicial
# ===========================
pagina = st.radio("📌 Mostrar", ["Abertos", "Encerrados"], horizontal=True)

# ===========================
# Exibição dos editais (Acesse os editais)
# ===========================
st.subheader("📢 Acesse os editais")

if not df_filtrado.empty:
    if pagina == "Abertos":
        df_abertos = df_filtrado[df_filtrado["data_fim"] >= pd.Timestamp.today()]
        if not df_abertos.empty:
            for _, row in df_abertos.sort_values("data_fim").iterrows():
                with st.container():
                    st.markdown(f"**{row.get('titulo','(sem título)')}**")
                    st.write(f"📌 Agência: {row.get('agencia','')}")
                    st.write(f"🎓 Modalidade: {row.get('modalidade','')}")
                    st.write(f"💰 Tipo de financiamento: {row.get('tipo_financiamento','')}")
                    inicio_txt = row['data_inicio'].date() if pd.notna(row.get('data_inicio')) else ""
                    fim_txt = row['data_fim'].date() if pd.notna(row.get('data_fim')) else ""
                    st.write(f"🗓️ Início: {inicio_txt} | Fim: {fim_txt}")
                    st.write(f"🏷️ Tema: {row.get('tema','')}")
                    if pd.notna(row.get('link', '')) and row.get('link','').strip():
                        st.markdown(f"[🔗 Acesse o edital]({row['link']})")
                    st.markdown("---")
        else:
            st.warning("Nenhum edital aberto disponível com os filtros aplicados.")
    else:  # Encerrados
        df_encerrados = df_filtrado[df_filtrado["data_fim"] < pd.Timestamp.today()]
        if not df_encerrados.empty:
            for _, row in df_encerrados.sort_values("data_fim", ascending=False).iterrows():
                with st.container():
                    st.markdown(f"**{row.get('titulo','(sem título)')}**")
                    st.write(f"📌 Agência: {row.get('agencia','')}")
                    st.write(f"🎓 Modalidade: {row.get('modalidade','')}")
                    st.write(f"💰 Tipo de financiamento: {row.get('tipo_financiamento','')}")
                    inicio_txt = row['data_inicio'].date() if pd.notna(row.get('data_inicio')) else ""
                    fim_txt = row['data_fim'].date() if pd.notna(row.get('data_fim')) else ""
                    st.write(f"🗓️ Início: {inicio_txt} | Fim: {fim_txt}")
                    st.write(f"🏷️ Tema: {row.get('tema','')}")
                    if pd.notna(row.get('link', '')) and row.get('link','').strip():
                        st.markdown(f"[🔗 Acesse o edital]({row['link']})")
                    st.markdown("---")
        else:
            st.info("Nenhum edital encerrado disponível com os filtros aplicados.")
else:
    st.info("Nenhum edital carregado ou os filtros resultaram em lista vazia.")

# ===========================
# Visão geral dos editais (resumo numérico)
# ===========================
if not df.empty:
    st.subheader("📈 Visão Geral dos Editais")
    total = len(df)
    por_agencia = df['agencia'].value_counts()
    por_ano = df['data_fim'].dt.year.value_counts().sort_index()

    st.write(f"**Total de editais carregados:** {total}")
    st.write(f"**Número de agências distintas:** {len(por_agencia)}")
    if not por_ano.empty:
        st.write(f"**Ano mais antigo nos dados:** {int(por_ano.index.min())}")
        st.write(f"**Ano mais recente nos dados:** {int(por_ano.index.max())}")
    else:
        st.write("**Sem informações de ano de encerramento disponíveis**")

    # Pequeno resumo por agência (apenas números, sem tabela)
    st.write("**Editais por agência (principais 5):**")
    for ag, cnt in por_agencia.head(5).items():
        st.write(f"- {ag}: {cnt}")

# ===========================
# Nuvem de palavras (Principais temas - proporcional, visual menor)
# ===========================
if not df.empty and "tema_lista" in df.columns:
    termos = [t.strip() for lista in df["tema_lista"] for t in lista if t.strip()]
    if termos:
        freq = Counter(termos)
        wc = WordCloud(width=600, height=300, background_color="white").generate_from_frequencies(freq)
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.subheader("☁️ Principais temas")
        st.pyplot(fig)

# ===========================
# Gráficos de distribuição por agência (% stacked, legenda embaixo)
# ===========================
st.subheader("📊 Distribuições por Agência")

if not df.empty:
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
        ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=2)
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
        ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=2)
        st.pyplot(fig)

# ===========================
# Feedback no Google Sheets
# ===========================
st.sidebar.markdown("## 📝 Reportar erro ou dúvida")

nome = st.sidebar.text_input("Nome (opcional)")
email = st.sidebar.text_input("E-mail (opcional)")
mensagem = st.sidebar.text_area("Mensagem")

if st.sidebar.button("Enviar"):
    try:
        # Autenticação com a service account (secrets devem existir)
        import gspread
        from google.oauth2.service_account import Credentials

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
