# trecho atualizado dos gráficos de distribuição (app 13)

st.subheader("📊 Distribuições por Agência")

if not df.empty:
    # Tipo de financiamento por agência
    tipos_expandidos = []
    for _, row in df.iterrows():
        for tf in row["tipo_financiamento_lista"]:
            if tf.strip():
                tipos_expandidos.append({"agencia": row["agencia"], "tipo_financiamento": tf.strip()})

    if tipos_expandidos:
        df_tipos = pd.DataFrame(tipos_expandidos)
        tabela_tipos = df_tipos.pivot_table(index="agencia", columns="tipo_financiamento", aggfunc=len, fill_value=0)
        tabela_tipos_pct = tabela_tipos.div(tabela_tipos.sum(axis=1), axis=0) * 100
        fig, ax = plt.subplots(figsize=(5, 3))
        tabela_tipos_pct.plot(kind="barh", stacked=True, ax=ax, width=0.6)

        ax.set_title("Distribuição de Tipos de Financiamento", fontsize=10)
        ax.set_xlabel("%", fontsize=8)
        ax.set_ylabel("Agência", fontsize=8)

        # Rótulos discretos
        for container in ax.containers:
            ax.bar_label(container, fmt="%.0f%%", fontsize=7, label_type="center")

        # Legenda embaixo
        ax.legend(
            loc='upper center',
            bbox_to_anchor=(0.5, -0.15),
            ncol=3,
            fontsize=7,
            frameon=False
        )

        plt.tight_layout()
        plt.subplots_adjust(bottom=0.25)  # espaço para legenda
        st.pyplot(fig)

    # Modalidade por agência
    modalidades_expandidas = []
    for _, row in df.iterrows():
        for mod in row["modalidade_lista"]:
            if mod.strip():
                modalidades_expandidas.append({"agencia": row["agencia"], "modalidade": mod.strip()})

    if modalidades_expandidas:
        df_mods = pd.DataFrame(modalidades_expandidas)
        tabela_mods = df_mods.pivot_table(index="agencia", columns="modalidade", aggfunc=len, fill_value=0)
        tabela_mods_pct = tabela_mods.div(tabela_mods.sum(axis=1), axis=0) * 100
        fig, ax = plt.subplots(figsize=(5, 3))
        tabela_mods_pct.plot(kind="barh", stacked=True, ax=ax, width=0.6)

        ax.set_title("Distribuição de Modalidades", fontsize=10)
        ax.set_xlabel("%", fontsize=8)
        ax.set_ylabel("Agência", fontsize=8)

        for container in ax.containers:
            ax.bar_label(container, fmt="%.0f%%", fontsize=7, label_type="center")

        ax.legend(
            loc='upper center',
            bbox_to_anchor=(0.5, -0.15),
            ncol=3,
            fontsize=7,
            frameon=False
        )

        plt.tight_layout()
        plt.subplots_adjust(bottom=0.25)
        st.pyplot(fig)
