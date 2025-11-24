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
    # NOVO: Filtro por perfil exigido (proponente)
    # ===========================
    col_perfil = "perfil exigido (proponente)"
    if col_perfil in df.columns:
        perfis = sorted(df[col_perfil].dropna().unique().tolist())
        perfil_sel = st.sidebar.multiselect("Perfil exigido (proponente)", perfis)
    else:
        perfil_sel = []
else:
    agencia_sel = "Todos"
    modalidade_sel = []
    tema_sel = []
    ano_sel = []
    prazo_sel = "Todos"
    perfil_sel = []

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

    # Aplicar filtro de perfil exigido (proponente)
    if perfil_sel:
        df_filtrado = df_filtrado[df_filtrado[col_perfil].isin(perfil_sel)]
else:
    df_filtrado = pd.DataFrame()

# ===========================
# Navegação principal
# ===========================
pagina = st.radio("📌 Navegação", ["Inicial", "Abertos", "Encerrados"], horizontal=True)

# ===========================
# Orientações
# ===========================
with st.expander("📌 Orientações", expanded=True):
    st.markdown("""
    - A lista é atualizada semanalmente, sempre às segundas.
    - Os editais encerrados foram mantidos para prospectar futuras oportunidades.
    - O único filtro aplicado na construção do banco de dados foi o período (a partir de 2023).
    - Os temas estão resumidos de forma objetiva; recomenda-se ler o edital completo, visto que muitos são transversais.
    - Esse é um painel experimental. Em caso de erro, dúvidas ou sugestões, utilize a caixinha no menu lateral.
    """)

# ===========================
# Paleta de cores pastel
# ===========================
cores_pastel = [
    "#A8DADC", "#F4A261", "#E9C46A",
    "#90BE6D", "#F6BD60", "#B56576", "#6D597A"
]

# ===========================
# Página Inicial
# ===========================
if pagina == "Inicial":
    if not df.empty:
        st.subheader("📈 Visão Geral dos Editais")
        total = len(df)
        por_agencia = df['agencia'].value_counts()
        por_ano = df['data_fim'].dt.year.value_counts().sort_index()

        st.write(f"**Total de editais carregados:** {total}")
        st.write(f"**Número de agências distintas:** {len(por_agencia)}")
        if not por_ano.empty:
            st.write(f"**Ano mais antigo:** {int(por_ano.index.min())}")
            st.write(f"**Ano mais recente:** {int(por_ano.index.max())}")

        # Gráfico: Tipos de financiamento
        st.subheader("📊 Distribuições por Agência")

        tipos_expandidos = []
        if "tipo_financiamento_lista" in df.columns:
            for _, row in df.iterrows():
                for tf in row["tipo_financiamento_lista"]:
                    if isinstance(tf, str) and tf.strip():
                        tipos_expandidos.append({"agencia": row["agencia"], "tipo_financiamento": tf.strip()})

        if tipos_expandidos:
            df_tipos = pd.DataFrame(tipos_expandidos)
            tabela_tipos = df_tipos.pivot_table(index="agencia", columns="tipo_financiamento", aggfunc=len, fill_value=0)
            tabela_tipos_pct = tabela_tipos.div(tabela_tipos.sum(axis=1), axis=0) * 100
            df_tipos_plot = tabela_tipos_pct.reset_index().melt(id_vars="agencia", var_name="tipo_financiamento", value_name="percentual")

            fig = px.bar(df_tipos_plot, x="percentual", y="agencia", color="tipo_financiamento",
                         orientation="h", color_discrete_sequence=cores_pastel, text="tipo_financiamento")
            fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x:.1f}%% - %{text}<extra></extra>")
            fig.update_layout(barmode="stack", title="Distribuição de Tipos de Financiamento", xaxis_title="%", yaxis_title="Agência")
            st.plotly_chart(fig, use_container_width=True)

        # Gráfico: Modalidades
        modalidades_expandidas = []
        if "modalidade_lista" in df.columns:
            for _, row in df.iterrows():
                for mod in row["modalidade_lista"]:
                    if isinstance(mod, str) and mod.strip():
                        modalidades_expandidas.append({"agencia": row["agencia"], "modalidade": mod.strip()})

        if modalidades_expandidas:
            df_mods = pd.DataFrame(modalidades_expandidas)
            tabela_mods = df_mods.pivot_table(index="agencia", columns="modalidade", aggfunc=len, fill_value=0)
            tabela_mods_pct = tabela_mods.div(tabela_mods.sum(axis=1), axis=0) * 100
            df_mods_plot = tabela_mods_pct.reset_index().melt(id_vars="agencia", var_name="modalidade", value_name="percentual")

            fig = px.bar(df_mods_plot, x="percentual", y="agencia", color="modalidade",
                         orientation="h", color_discrete_sequence=cores_pastel, text="modalidade")
            fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x:.1f}%% - %{text}<extra></extra>")
            fig.update_layout(barmode="stack", title="Distribuição de Modalidades", xaxis_title="%", yaxis_title="Agência")
            st.plotly_chart(fig, use_container_width=True)

        # Nuvem de palavras
        if "tema_lista" in df.columns:
            termos = [t.strip() for lista in df["tema_lista"] for t in lista if isinstance(t, str) and t.strip()]
            if termos:
                freq = Counter(termos)
                wc = WordCloud(width=600, height=300, background_color="white").generate_from_frequencies(freq)
                fig, ax = plt.subplots(figsize=(6, 3))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                st.subheader("☁️ Principais temas")
                st.pyplot(fig)

# ===========================
# Página Abertos
# ===========================
elif pagina == "Abertos":
    st.subheader("📢 Editais de Fomento Abertos")
    df_abertos = df_filtrado[df_filtrado["data_fim"] >= pd.Timestamp.today()]
    if not df_abertos.empty:
        for _, row in df_abertos.sort_values("data_fim").iterrows():
            with st.container():
                st.markdown(f"**{row.get('titulo','(sem título)')}**")
                st.write(f"📌 Agência: {row.get('agencia','')}")
                st.write(f"🎓 Modalidade: {row.get('modalidade','')}")
                st.write(f"💰 Tipo de financiamento: {row.get('tipo_financiamento','')}")
                st.write(f"👤 Perfil exigido: {row.get(col_perfil, '')}")
                inicio_txt = row['data_inicio'].date() if pd.notna(row.get('data_inicio')) else ""
                fim_txt = row['data_fim'].date() if pd.notna(row.get('data_fim')) else ""
                st.write(f"🗓️ Início: {inicio_txt} | Fim: {fim_txt}")
                st.write(f"🏷️ Tema: {row.get('tema','')}")
                if pd.notna(row.get('link', '')) and row.get('link','').strip():
                    st.markdown(f"[🔗 Acesse o edital]({row['link']})")
                st.markdown("---")
    else:
        st.warning("Nenhum edital aberto disponível com os filtros aplicados.")
# ===========================
# Página Encerrados
# ===========================
elif pagina == "Encerrados":
    st.subheader("📁 Editais Encerrados")

    df_encerrados = df_filtrado[df_filtrado["data_fim"] < pd.Timestamp.today()]

    if not df_encerrados.empty:
        df_encerrados = df_encerrados.sort_values("data_fim", ascending=False)

        st.dataframe(
            df_encerrados[[
                "titulo",
                "agencia",
                "modalidade",
                "tipo_financiamento",
                "perfil exigido (proponente)",
                "tema",
                "data_inicio",
                "data_fim",
                "link"
            ]],
            us
