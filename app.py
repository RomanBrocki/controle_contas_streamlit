# ====================================
# 🚀 APP PRINCIPAL - Controle de Contas
# ====================================

# --------- Imports padrão ---------
from datetime import datetime

# --------- Imports de terceiros ---------
import pandas as pd
import streamlit as st

# --------- Módulos internos ---------

from interface import (
    ir_para_mes_vigente,
    ir_para_historico,
    voltar_tela_inicial,
    exibir_contas_mes,
    inicializar_sessao
)


from relatorio import (
    gerar_grafico_comparativo_linha,
    carregar_dados_conta_periodo,
    gerar_pdf_comparativo_conta,
    gerar_relatorio_periodo_pdf,
)

from supabase import (
    carregar_tabela,
    get_nomes_conta_unicos,
    get_anos_meses_disponiveis
)

from estilo import aplicar_estilo_mockup, set_background


# --------- Configuração da Página ---------
st.set_page_config(page_title="Controle de Contas", page_icon="💸", layout="wide")


# ====================================
# 🧠 ESTADO DE SESSÃO (st.session_state)
# ====================================
# Inicializa variáveis de controle e cache da aplicação

inicializar_sessao()

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
        

        # --------------------------
        # 📈 Seção: Comparativo de Conta por Período
        # --------------------------
        st.subheader("📈 Contas por Período")

        # Obter anos e meses disponíveis no banco
        anos_disponiveis, meses_disponiveis = get_anos_meses_disponiveis()

        if not anos_disponiveis or not meses_disponiveis:
            st.warning("Não há dados disponíveis para gerar comparativos.")
            st.stop()

        # Reseta o gráfico ao mudar de conta
        def ao_mudar_conta():
            st.session_state["grafico_comparativo_pronto"] = False

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
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("Gerar Gráfico"):
                st.session_state["grafico_comparativo_pronto"] = True
                
        with col_b:
            if st.button("Gerar PDF do Gráfico"):
                st.session_state["pdf_comparativo_pronto"] = True

        with col_c:
            if st.button("Gerar Resumo do Período 📄"):
                st.session_state["resumo_periodo_pronto"] = True
                
        # =============================
        # 📈 Geração do gráfico de linha
        # =============================
        if st.session_state.get("grafico_comparativo_pronto", False):
            st.session_state["grafico_comparativo_pronto"] = False  # limpa a flag após usar

            df_comparativo = carregar_dados_conta_periodo(
                mes_inicio, ano_inicio,
                mes_fim, ano_fim,
                conta_escolhida
            )

            if df_comparativo.empty:
                st.warning("Nenhum dado encontrado para o período selecionado.")
            else:
                fig = gerar_grafico_comparativo_linha(
                    df_comparativo,
                    conta_escolhida,
                    mes_inicio,
                    ano_inicio,
                    mes_fim,
                    ano_fim
                )
                st.pyplot(fig)

        # =============================
        # 📄 Geração do PDF do gráfico
        # =============================
        if st.session_state.get("pdf_comparativo_pronto", False):
            st.session_state["pdf_comparativo_pronto"] = False

            df_pdf = carregar_dados_conta_periodo(
                mes_inicio, ano_inicio,
                mes_fim, ano_fim,
                conta_escolhida
            )

            if df_pdf.empty:
                st.warning("Não foi possível gerar o PDF. Nenhum dado encontrado.")
            else:
                pdf_bytes = gerar_pdf_comparativo_conta(
                    df_pdf,
                    conta_escolhida,
                    mes_inicio,
                    ano_inicio,
                    mes_fim,
                    ano_fim
                )
                nome_arquivo = f"relatorio_{conta_escolhida.lower()}_{mes_inicio:02d}{ano_inicio}_{mes_fim:02d}{ano_fim}.pdf"
                st.download_button(
                    label="📄 Baixar PDF do Comparativo",
                    data=pdf_bytes,
                    file_name=nome_arquivo,
                    mime="application/pdf"
                )

        # =============================
        # 🧾 Geração do Resumo do Período
        # =============================
        if st.session_state.get("resumo_periodo_pronto", False):
            st.session_state["resumo_periodo_pronto"] = False

            df_periodo = carregar_dados_conta_periodo(
                mes_inicio, ano_inicio,
                mes_fim, ano_fim,
                nome_da_conta=None  # todas as contas
            )

            if df_periodo.empty:
                st.warning("Não há contas registradas no intervalo selecionado.")
            else:
                st.success("Resumo do período carregado com sucesso!")
                pdf_bytes = gerar_relatorio_periodo_pdf(
                    df_periodo,
                    mes_inicio,
                    ano_inicio,
                    mes_fim,
                    ano_fim
                )
                nome_arquivo = f"relatorio_resumo_{mes_inicio:02d}{ano_inicio}_{mes_fim:02d}{ano_fim}.pdf"
                st.download_button(
                    label="📄 Baixar PDF do Resumo",
                    data=pdf_bytes,
                    file_name=nome_arquivo,
                    mime="application/pdf"
                )










































































































































































































































































































































































































































































































































































































