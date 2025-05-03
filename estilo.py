# ====================================
# 🎨 FUNÇÕES DE ESTILO VISUAL
# ====================================

import base64
import streamlit as st


def set_background(image_file):
    """
    Define uma imagem de fundo fixa para o aplicativo Streamlit.

    Parâmetros:
        image_file (str): Caminho para a imagem a ser usada como background.
    """
    with open(image_file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    css = f"""
    <style>
    .stApp {{
        background: url("data:image/png;base64,{encoded}") no-repeat center center fixed;
        background-size: cover;
        background-color: #111111;
    }}
    h1 {{
        text-align: center;
        color: #0d0d0d;
        font-size: 80px;
        font-weight: bold;
        margin-top: 50px;
        text-shadow: 6px 6px 15px rgba(0, 0, 0, 1);
    }}
    .stButton > button {{
        width: 100%;
        height: 90px;
        font-size: 26px;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def aplicar_estilo_mockup():
    """
    Aplica um estilo visual escuro e moderno ao app Streamlit,
    com cabeçalho flutuante e botões estilizados.
    Também reduz a chance de o teclado virtual abrir em dispositivos móveis
    ao tocar em selectboxes que não são campos de digitação.
    """
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

    .stApp {
        background-color: #1e1e1e;
        font-family: 'Roboto', sans-serif;
        color: #ffffff;
    }

    .floating-header {
        position: sticky;
        top: 0;
        background-color: #2c2c2c;
        padding: 10px 20px;
        z-index: 1000;
        border-bottom: 2px solid #555;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .month-title {
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 10px;
    }

    .header-actions {
        width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .stButton > button {
        border-radius: 10px;
        padding: 0.75em 1.5em;
        background-color: #4a5c6a;
        color: #ffffff;
        font-weight: bold;
        transition: 0.3s;
    }

    .stButton > button:hover {
        background-color: #6b7b8c;
        transform: scale(1.05);
    }

    /* Evita que o teclado seja ativado ao focar no selectbox em dispositivos móveis */
    @media (max-width: 768px) {
        .stSelectbox input {
            caret-color: transparent !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

