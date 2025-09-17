# ===========================
# Filtros
# ===========================
if not df.empty:
    agencias = df["agencia"].dropna().unique().tolist()
    agencia_sel = st.sidebar.selectbox("Agência de fomento", ["Todos"] + agencias)

    # NOVO: filtro por modalidade (multiselect)
    modalidades = df["modalidade"].dropna().unique().tolist() if "modalidade" in df.columns else []
    modalidade_sel = st.sidebar.multiselect("Modalidade", modalidades)

    # NOVO: filtro por tema (multiselect)
    temas = df["tema"].dropna().unique().tolist() if "tema" in df.columns else []
    tema_sel = st.sidebar.multiselect("Tema", temas)

    prazo_sel = st.sidebar.selectbox(
        "Prazo de inscrição",
        ["Todos", "Até 7 dias", "Mais de 7 dias", "Encerrados"]
    )

    # Filtrar dados
    df_filtrado = df.copy()
    if agencia_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["agencia"] == agencia_sel]

    # NOVO: aplica filtro por modalidades (se alguma for escolhida)
    if modalidade_sel:
        df_filtrado = df_filtrado[df_filtrado["modalidade"].isin(modalidade_sel)]

    # NOVO: aplica filtro por temas (se algum for escolhido)
    if tema_sel:
        df_filtrado = df_filtrado[df_filtrado["tema"].isin(tema_sel)]

    if prazo_sel != "Todos":
        hoje = pd.Timestamp('today').normalize()
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
