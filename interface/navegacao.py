# ====================================
# 📦 IMPORTAÇÕES (em ordem alfabética)
# ====================================

import streamlit as st

# ====================================
# 🔀 NAVEGAÇÃO ENTRE TELAS
# ====================================

def ir_para_mes_vigente():
    """Define a tela atual como 'mes_vigente'."""
    st.session_state["tela_atual"] = "mes_vigente"
    st.session_state["modo_nova_conta"] = False
    st.session_state["df_original"] = None

def ir_para_historico():
    """Define a tela atual como 'historico'."""
    st.session_state["tela_atual"] = "historico"
    st.session_state["modo_nova_conta"] = False
    st.session_state["df_original"] = None
    st.session_state["historico_carregado"] = False

def voltar_tela_inicial():
    """Retorna à tela inicial do aplicativo."""
    st.session_state["tela_atual"] = "inicial"
    st.session_state["modo_nova_conta"] = False
    st.session_state["df_original"] = None
    st.session_state["historico_carregado"] = False