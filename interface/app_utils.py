# ====================================
# 📦 IMPORTAÇÕES (em ordem alfabética)
# ====================================

from datetime import datetime
import pandas as pd
import streamlit as st

# --------- Módulos internos ---------
from relatorio import (
    gerar_relatorio_pdf,
)

from supabase import (
    carregar_tabela,
    carregar_mes_referente,
    excluir_conta,
    get_nomes_conta_unicos,
    salvar_conta,
)

# ====================================
# 🧾 CABEÇALHO DO MÊS
# ====================================

def exibir_cabecalho_mes(nome_mes, ano, total):
    """
    Exibe o cabeçalho fixo do mês com nome, ano e total de contas pagas.

    Parâmetros:
        nome_mes (str): Nome do mês (ex: 'Abril').
        ano (int): Ano de referência.
        total (float): Soma dos valores pagos no mês.
    """
    st.markdown(f"""
    <div class="floating-header">
        <div class="month-title">{nome_mes} / {ano}</div>
        <div class="header-actions">
            <div><strong>Total:</strong> R$ {total:,.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ================================================
# 🧾 Flutuante controle de contas a pagar
# ================================================

def mostrar_lembrete_balanco(df_atual, mes, ano):
    from supabase import carregar_mes_referente

    df_anterior = carregar_mes_referente(mes, ano, delta_meses=-1)

    if df_anterior.empty or df_atual.empty or "nome_da_conta" not in df_atual.columns:
        return

    contas_atuais = set(df_atual["nome_da_conta"].str.strip().str.lower())
    contas_anteriores = df_anterior["nome_da_conta"].str.strip().str.lower()

    contas_nao_pagas = contas_anteriores[~contas_anteriores.isin(contas_atuais)].unique()

    if not len(contas_nao_pagas):
        return

    with st.expander("📌 Contas pendentes x último mês", expanded=False):
        for conta in contas_nao_pagas:
            linha = df_anterior[df_anterior["nome_da_conta"].str.strip().str.lower() == conta]
            nome_original = linha.iloc[0]["nome_da_conta"]
            data_pagamento = pd.to_datetime(linha.iloc[0]["data_de_pagamento"]).strftime("%d/%m")
            st.markdown(f"- **{nome_original}** → paga em {data_pagamento}")



# ====================================
# 📝 FORMULÁRIO DE CONTA
# ====================================

def exibir_formulario_conta(dados, idx_prefix="conta"):
    """
    Exibe o formulário para visualizar, editar ou criar uma conta.

    Parâmetros:
        dados (dict): Dicionário com os dados da conta.
        idx_prefix (str): Prefixo único para os campos do formulário (ex: 'nova', '42').

    Retorno:
        dict: Dicionário com os dados atualizados após preenchimento.
    """

    # Oculta o formulário de nova conta caso não esteja ativado
    if idx_prefix == "nova" and not st.session_state.get("modo_nova_conta", False):
        return dados

    # --------------------------
    # 🔘 Seção 1: Nome da Conta
    # --------------------------
    col1, col2, col3 = st.columns(3)
    with col1:
        opcoes_conta = ["Selecione..."] + get_nomes_conta_unicos() + ["Outros"]

        valor_inicial = (
            "Selecione..."
            if idx_prefix == "nova"
            else dados.get('nome_da_conta') if dados.get('nome_da_conta') in opcoes_conta else "Outros"
        )

        selecao = st.selectbox(
            "Nome da Conta",
            opcoes_conta,
            index=opcoes_conta.index(valor_inicial),
            key=f"nome_da_conta_{idx_prefix}"
        )

        if selecao == "Outros":
            custom_nome = st.text_input("Digite o nome da nova conta:", key=f"nome_custom_{idx_prefix}")
            dados['nome_da_conta'] = custom_nome
        else:
            dados['nome_da_conta'] = selecao

    # --------------------------
    # 💵 Seção 2: Valor e Data
    # --------------------------
    with col2:
        dados['valor'] = st.number_input(
            "Valor Pago",
            min_value=0.0,
            format="%.2f",
            value=float(dados.get('valor', 0.0)),
            key=f"valor_{idx_prefix}"
        )

    with col3:
        dados['data_de_pagamento'] = st.date_input(
            "Data de Pagamento",
            value=pd.to_datetime(dados.get('data_de_pagamento', datetime.today())),
            key=f"data_de_pagamento_{idx_prefix}"
        )

    # --------------------------
    # 🧾 Seção 3: Detalhes Adicionais
    # --------------------------
    col4, col5, col6 = st.columns(3)
    with col4:
        dados['instancia'] = st.text_input(
            "Instância",
            value=dados.get('instancia', ""),
            key=f"instancia_{idx_prefix}"
        )
    with col5:
        dados['quem_pagou'] = st.selectbox(
            "Quem Pagou",
            ["Roman", "Tati", "Outro"],
            index=["Roman", "Tati", "Outro"].index(dados.get('quem_pagou', "Roman")),
            key=f"quem_pagou_{idx_prefix}"
        )
    with col6:
        dados['dividida'] = st.checkbox(
            "Conta Dividida?",
            value=bool(dados.get('dividida', False)),
            key=f"dividida_{idx_prefix}"
        )

    # --------------------------
    # 🔗 Seção 4: Links (boletos e comprovantes)
    # --------------------------
    st.text(" ")  # Espaço visual

    if dados.get('link_boleto'):
        st.markdown(f"[Boleto]({dados['link_boleto']})", unsafe_allow_html=True)
    else:
        dados['link_boleto'] = st.text_input("Link do Boleto", value="", key=f"link_boleto_{idx_prefix}")

    if dados.get('link_comprovante'):
        st.markdown(f"[Comprovante]({dados['link_comprovante']})", unsafe_allow_html=True)
    else:
        dados['link_comprovante'] = st.text_input("Link do Comprovante", value="", key=f"link_comprovante_{idx_prefix}")

    # --------------------------
    # 💾 Seção 5: Ações (Salvar ou Excluir)
    # --------------------------
    col1, _, col3 = st.columns([1, 1, 1])

    with col1:
        if idx_prefix != "nova" and st.button("Salvar alterações", key=f"salvar_{idx_prefix}"):
            if dados['nome_da_conta'] in ["Selecione...", ""]:
                st.warning("Por favor, selecione ou preencha um nome de conta válido.")
            else:
                salvar_conta(dados)
                st.success("Conta salva com sucesso!")
                if st.session_state["tela_atual"] == "historico":
                    st.session_state["df_original"] = carregar_tabela(dados["mes"], dados["ano"])
                st.rerun()

    with col3:
        if idx_prefix != "nova" and st.button("Excluir conta", key=f"excluir_{idx_prefix}"):
            print(f"Tentando excluir conta ID: {dados['id']}")
            if excluir_conta(dados["id"]):
                print("Exclusão bem-sucedida.")
                st.warning("Conta excluída com sucesso!")
                if st.session_state["tela_atual"] == "historico":
                    st.session_state["df_original"] = carregar_tabela(dados["mes"], dados["ano"])
                st.rerun()
            else:
                print("Erro ao excluir conta.")

    return dados

# ====================================
# 📅 EXIBIÇÃO DAS CONTAS DO MÊS
# ====================================

def exibir_contas_mes(df, nome_mes, ano, mes):
    """
    Exibe as contas pagas do mês selecionado, incluindo:
    - Cabeçalho com total
    - Botões para nova conta e gerar relatório
    - Formulário de nova conta (se ativado)
    - Lista de contas pagas com formulários colapsáveis

    Parâmetros:
        df (pd.DataFrame): Dados do mês a ser exibido.
        nome_mes (str): Nome do mês (ex: 'Abril').
        ano (int): Ano de referência.
        mes (int): Número do mês (1 a 12).
    """

    # --------------------------
    # 🧾 Cabeçalho do Mês
    # --------------------------
    total = df['valor'].sum() if not df.empty else 0
    exibir_cabecalho_mes(nome_mes, ano, total)
    mostrar_lembrete_balanco(df, mes, ano)

    # --------------------------
    # 🧩 Botões: Nova Conta e Relatório
    # --------------------------
    col_btn1, _, col_btn3 = st.columns([1, 1, 1])
    with col_btn1:
        if st.button("Nova Conta"):
            st.session_state["modo_nova_conta"] = True

    with col_btn3:
        st.markdown("<div style='display: flex; justify-content: flex-end;'>", unsafe_allow_html=True)
        if st.button("Gerar Resumo do Mês 📄"):
            st.session_state["gerar_relatorio"] = True
        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------
    # 📄 Geração do Relatório PDF
    # --------------------------
    if st.session_state.get("gerar_relatorio", False):
        st.session_state["gerar_relatorio"] = False
        try:
            mes_detectado = int(df["mes"].iloc[0])
            ano_detectado = int(df["ano"].iloc[0])
            nome_mes_detectado = datetime(1900, mes_detectado, 1).strftime("%B").capitalize()
        except Exception:
            st.error("Erro ao detectar mês/ano das contas.")
            st.stop()

        pdf_bytes = gerar_relatorio_pdf(df.copy(), nome_mes_detectado, ano_detectado)
        nome_arquivo = f"relatorio_{nome_mes_detectado}_{ano_detectado}.pdf"
        st.download_button("Download Relatório PDF", data=pdf_bytes, file_name=nome_arquivo, mime="application/pdf")

    # --------------------------
    # ➕ Formulário de Nova Conta
    # --------------------------
    if st.session_state.get("modo_nova_conta"):
        st.markdown("---")
        st.subheader("Nova Conta")
        nova_conta = {
            'nome_da_conta': "Selecione...",
            'valor': 0.0,
            'data_de_pagamento': datetime.today(),
            'instancia': "",
            'quem_pagou': "Roman",
            'dividida': False,
            'link_boleto': "",
            'link_comprovante': "",
            'mes': mes,
            'ano': ano,
        }
        nova_conta = exibir_formulario_conta(nova_conta, idx_prefix="nova")
        col_salvar_nova, _ = st.columns([1, 2])
        with col_salvar_nova:
            if st.button("Salvar Nova Conta", key="salvar_nova_conta"):
                if nova_conta['nome_da_conta'] in ["Selecione...", ""]:
                    st.warning("Por favor, selecione ou preencha um nome de conta válido.")
                else:
                    salvar_conta(nova_conta)
                    st.session_state["modo_nova_conta"] = False
                    st.success("Nova conta adicionada com sucesso!")
                    if st.session_state["tela_atual"] == "historico":
                        st.session_state["df_original"] = carregar_tabela(mes, ano)
                    st.rerun()
        st.markdown("---")

    # --------------------------
    # 📋 Lista de Contas Pagas
    # --------------------------
    if not df.empty and "nome_da_conta" in df.columns:
        df = df.sort_values(by="nome_da_conta", ascending=True)

    if not df.empty:
        for idx, row in df.iterrows():
            nome = row.get("nome_da_conta", "Sem nome")
            instancia = row.get("instancia", "")
            valor = row.get("valor", 0.0)

            resumo = f"💼 {nome} | 🏷️ {instancia} | 💰 R$ {valor:,.2f}"

            with st.expander(resumo):
                exibir_formulario_conta(row.to_dict(), idx_prefix=f"{row['id']}")
            st.markdown("---")