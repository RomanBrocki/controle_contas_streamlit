# ====================================
# 📦 IMPORTAÇÕES (em ordem alfabética)
# ====================================

import streamlit as st


# ========================
# 🔗 CONFIGURAÇÃO SUPABASE
# ========================

# Esses valores são lidos de .streamlit/secrets.toml no ambiente local
# ou de variáveis de ambiente no Streamlit Cloud

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
TABELA = "controle_contas"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}
