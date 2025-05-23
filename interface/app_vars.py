# ====================================
# 📦 IMPORTAÇÕES (em ordem alfabética)
# ====================================

from datetime import datetime
import streamlit as st

# ====================================
# 🧠 ESTADO DE SESSÃO (st.session_state)
# ====================================
# Inicializa variáveis de controle e cache da aplicação

def inicializar_sessao():
    """
    Inicializa as variáveis padrão no st.session_state, caso ainda não existam.
    """
    valores_iniciais = {
        "tela_atual": "inicial",
        "modo_nova_conta": False,
        "ano_historico": datetime.now().year,
        "mes_historico": datetime.now().month,
        "df_original": None,
        "nova_conta_cache": None,
        "historico_carregado": False,
        "nome_mes_historico": "",
        "gerar_relatorio": False,
    }

    for key, value in valores_iniciais.items():
        if key not in st.session_state:
            st.session_state[key] = value