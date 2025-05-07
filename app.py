# ====================================
# 🚀 APP PRINCIPAL - Controle de Contas
# ====================================

# --------- Imports padrão ---------
from datetime import datetime
import base64

# --------- Imports de terceiros ---------
import pandas as pd
import streamlit as st

# --------- Módulos internos ---------
from relatorio_utils import (
    gerar_relatorio_pdf, 
    gerar_grafico_comparativo_linha, 
    carregar_dados_conta_periodo, 
    gerar_pdf_comparativo_conta
)
from supabase_utils import (
    carregar_tabela,
    excluir_conta,
    get_nomes_conta_unicos,
    salvar_conta,
    get_anos_meses_disponiveis
)
from estilo import aplicar_estilo_mockup, set_background


# --------- Configuração da Página ---------
st.set_page_config(page_title="Controle de Contas", page_icon="💸", layout="wide")


# ====================================
# 🧠 ESTADO DE SESSÃO (st.session_state)
# ====================================
# Inicializa variáveis de controle e cache da aplicação

for key, value in {
    "tela_atual": "inicial",
    "modo_nova_conta": False,
    "ano_historico": datetime.now().year,
    "mes_historico": datetime.now().month,
    "df_original": None,
    "nova_conta_cache": None,
    "historico_carregado": False,
    "nome_mes_historico": "",
    "gerar_relatorio": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ====================================
# 🔀 NAVEGAÇÃO ENTRE TELAS
# ====================================

def ir_para_mes_vigente():
    """Define a tela atual como 'mes_vigente'."""
    st.session_state["tela_atual"] = "mes_vigente"
    st.session_state["modo_nova_conta"] = False


def ir_para_historico():
    """Define a tela atual como 'historico'."""
    st.session_state["tela_atual"] = "historico"
    st.session_state["modo_nova_conta"] = False


def voltar_tela_inicial():
    """Retorna à tela inicial do aplicativo."""
    st.session_state["tela_atual"] = "inicial"


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

# ====================================
# 🖥️ FLUXO PRINCIPAL DO APLICATIVO
# ====================================

if st.session_state["tela_atual"] == "inicial":
    # --------------------------
    # 🏠 Tela Inicial
    # --------------------------
    set_background("assets/bg_1.png")
    st.markdown("<h1>Controle de Contas</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.write("")

    with col2:
        if st.button("Mês Vigente"):
            ir_para_mes_vigente()
            st.rerun()
        if st.button("Histórico"):
            ir_para_historico()
            st.rerun()
        if st.button("Relatórios"):
            st.session_state["tela_atual"] = "relatorios"
            st.session_state["grafico_comparativo_pronto"] = False
            st.session_state["pdf_comparativo_pronto"] = False
            st.rerun()



    with col3:
        st.write("")

else:
    # --------------------------
    # 🎨 Estilo aplicado fora da tela inicial
    # --------------------------
    aplicar_estilo_mockup()

    # --------------------------
    # 📆 Tela: Mês Vigente
    # --------------------------
    if st.session_state["tela_atual"] == "mes_vigente":
        st.button("Voltar", on_click=voltar_tela_inicial)

        hoje = datetime.today()
        nome_mes = hoje.strftime("%B").capitalize()
        ano = hoje.year

        df = carregar_tabela(hoje.month, hoje.year)
        st.session_state["df_original"] = df.copy()

        exibir_contas_mes(df, nome_mes, ano, hoje.month)

    # --------------------------
    # 📚 Tela: Histórico
    # --------------------------
    elif st.session_state["tela_atual"] == "historico":
        st.button("Voltar", on_click=voltar_tela_inicial)
        st.header("Histórico")

        anos = list(range(datetime.now().year, datetime.now().year - 10, -1))
        meses = list(range(1, 13))

        col_ano, col_mes = st.columns(2)
        with col_ano:
            ano_selecionado = st.selectbox("Ano", anos, index=0, key="ano_hist")
        with col_mes:
            mes_selecionado = st.selectbox("Mês", meses, index=datetime.now().month - 1, key="mes_hist")

        if st.button("Carregar Mês"):
            df = carregar_tabela(mes_selecionado, ano_selecionado)
            st.session_state["df_original"] = df.copy()
            st.session_state["nome_mes_historico"] = datetime(1900, mes_selecionado, 1).strftime("%B").capitalize()
            st.session_state["ano_historico"] = ano_selecionado
            st.session_state["historico_carregado"] = True

        if st.session_state.get("historico_carregado", False):
            exibir_contas_mes(
                st.session_state["df_original"],
                st.session_state["nome_mes_historico"],
                st.session_state["ano_historico"],
                mes_selecionado,
            )
    # --------------------------
    # 📊 Tela: Relatórios
    # --------------------------
    elif st.session_state["tela_atual"] == "relatorios":
        st.button("Voltar", on_click=voltar_tela_inicial)
        st.header("📊 Relatórios")

        # --------------------------
        # 📈 Seção: Comparativo de Conta por Período
        # --------------------------
        st.subheader("📈 Comparativo de Conta por Período")

        # Obter anos e meses disponíveis no banco
        anos_disponiveis, meses_disponiveis = get_anos_meses_disponiveis()

        if not anos_disponiveis or not meses_disponiveis:
            st.warning("Não há dados disponíveis para gerar comparativos.")
            st.stop()

        # Linha de seleção de período e conta
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            ano_inicio = st.selectbox("Ano Inicial", anos_disponiveis, key="ano_inicio_comp")
        with col2:
            mes_inicio = st.selectbox("Mês Inicial", meses_disponiveis, key="mes_inicio_comp")
        with col3:
            ano_fim = st.selectbox("Ano Final", anos_disponiveis, key="ano_fim_comp")
        with col4:
            mes_fim = st.selectbox("Mês Final", meses_disponiveis, key="mes_fim_comp")

        # Seletor da conta
        contas_disponiveis = get_nomes_conta_unicos()
        conta_escolhida = st.selectbox("Conta", contas_disponiveis, key="conta_escolhida_comp")

        # Botões de ação
        col_a, col_b = st.columns([1, 1])
        with col_a:
            if st.button("Gerar Gráfico"):
                # Aqui no futuro: carregar dados do período e exibir gráfico
                st.session_state["grafico_comparativo_pronto"] = True

        with col_b:
            if st.button("Gerar PDF"):
                # Aqui no futuro: carregar dados e gerar PDF
                st.session_state["pdf_comparativo_pronto"] = True

        # Exibição de gráfico real
        if st.session_state.get("grafico_comparativo_pronto", False):
            # Carrega dados do período
            df_comparativo = carregar_dados_conta_periodo(
                mes_inicio, ano_inicio,
                mes_fim, ano_fim,
                conta_escolhida
            )

            if df_comparativo.empty:
                st.warning("Nenhum dado encontrado para o período selecionado.")
            else:
                # Gera o gráfico
                fig = gerar_grafico_comparativo_linha(
                    df_comparativo,
                    conta_escolhida,
                    mes_inicio,
                    ano_inicio,
                    mes_fim,
                    ano_fim
                )
                # Exibe o gráfico no Streamlit
                st.pyplot(fig)

            # Geração de PDF do gráfico comparativo
            if st.session_state.get("pdf_comparativo_pronto", False):
                # Resetar flag para não gerar várias vezes
                st.session_state["pdf_comparativo_pronto"] = False

                # Carrega os dados do mesmo período e conta
                df_pdf = carregar_dados_conta_periodo(
                    mes_inicio, ano_inicio,
                    mes_fim, ano_fim,
                    conta_escolhida
                )

                if df_pdf.empty:
                    st.warning("Não foi possível gerar o PDF. Nenhum dado encontrado no período selecionado.")
                else:
                    # Gera o PDF
                    pdf_bytes = gerar_pdf_comparativo_conta(
                        df_pdf,
                        conta_escolhida,
                        mes_inicio,
                        ano_inicio,
                        mes_fim,
                        ano_fim
                    )

                    nome_arquivo = f"relatorio_{conta_escolhida.lower()}_{mes_inicio:02d}{ano_inicio}_{mes_fim:02d}{ano_fim}.pdf"

                    # Botão para download
                    st.download_button(
                        label="📄 Baixar PDF do Comparativo",
                        data=pdf_bytes,
                        file_name=nome_arquivo,
                        mime="application/pdf"
                    )









































































































































































































































































































































































































































































































































































































