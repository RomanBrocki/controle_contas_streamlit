# ====================================
# 📦 IMPORTAÇÕES (em ordem alfabética)
# ====================================


from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import json

import pandas as pd
import requests

from .supabase_config import SUPABASE_URL, SUPABASE_KEY, TABELA, HEADERS

# ==============================
# 📥 CARREGAMENTO DE DADOS
# ==============================

def carregar_tabela(mes: int, ano: int):
    """
    Carrega os registros da tabela do Supabase para um mês e ano específicos.

    Parâmetros:
    - mes (int): Mês desejado (1 a 12)
    - ano (int): Ano desejado (ex: 2025)

    Retorno:
    - pd.DataFrame: DataFrame com os dados da tabela 'controle_contas' filtrados
    """
    url = f"{SUPABASE_URL}/rest/v1/{TABELA}?mes=eq.{mes}&ano=eq.{ano}&select=*"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        # Retorna DataFrame vazio em caso de erro
        return pd.DataFrame()


# ==============================
# ➕ INSERÇÃO DE NOVA CONTA
# ==============================

def inserir_nova_conta(dados_dict):
    """
    Insere uma nova conta no banco Supabase.

    Parâmetros:
    - dados_dict (dict): Dicionário contendo os campos da nova conta.

    Retorno:
    - bool: True se a inserção foi bem-sucedida (status 201), False caso contrário.
    """
    url = f"{SUPABASE_URL}/rest/v1/{TABELA}"
    payload = json.dumps([dados_dict])  # Envia como lista com um dicionário dentro
    response = requests.post(url, headers=HEADERS, data=payload)

    return response.status_code == 201


# ==============================
# ✏️ EDIÇÃO DE CONTA EXISTENTE
# ==============================

def editar_conta(id_conta, dados_dict):
    """
    Atualiza os dados de uma conta existente no Supabase.

    Parâmetros:
    - id_conta (int): ID único da conta a ser atualizada.
    - dados_dict (dict): Dicionário com os novos valores dos campos.

    Retorno:
    - bool: True se a atualização foi bem-sucedida (status 204), False caso contrário.
    """
    url = f"{SUPABASE_URL}/rest/v1/{TABELA}?id=eq.{id_conta}"

    # Remove o campo 'id' se estiver no dicionário (não pode ser alterado)
    dados_dict.pop("id", None)

    payload = json.dumps(dados_dict)
    response = requests.patch(url, headers=HEADERS, data=payload)

    return response.status_code == 204


# ==============================
# ❌ EXCLUSÃO DE CONTA EXISTENTE
# ==============================

def excluir_conta(id_conta):
    """
    Exclui uma conta existente do Supabase com base no ID.

    Parâmetros:
    - id_conta (int): ID único da conta a ser removida.

    Retorno:
    - bool: True se a exclusão foi bem-sucedida (status 200 ou 204), False caso contrário.
    """
    url = f"{SUPABASE_URL}/rest/v1/{TABELA}?id=eq.{id_conta}"

    # Headers específicos para que a API retorne algo (mesmo que vazio)
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"  # Importante para evitar erro de content-type
    }

    response = requests.delete(url, headers=headers)

    print(f"🔁 DELETE {url} | Status: {response.status_code} | Response: {response.text}")

    return response.status_code in [200, 204]


# ==============================
# 💾 SALVAR CONTA (INSERIR OU EDITAR)
# ==============================

def salvar_conta(dados_dict):
    """
    Salva uma conta no Supabase. Insere uma nova conta se não houver 'id',
    ou edita uma conta existente se 'id' estiver presente.

    Também garante que o campo 'data_de_pagamento' esteja no formato ISO.

    Parâmetros:
    - dados_dict (dict): Dicionário com os dados da conta.

    Retorno:
    - bool: True se a operação (inserção ou edição) for bem-sucedida.
    """
    # Certifica-se de que a data esteja no formato ISO (string 'YYYY-MM-DD')
    if isinstance(dados_dict.get("data_de_pagamento"), (datetime, date)):
        dados_dict["data_de_pagamento"] = dados_dict["data_de_pagamento"].isoformat()

    # Se tiver ID → editar; senão → inserir
    if 'id' in dados_dict and dados_dict['id']:
        return editar_conta(dados_dict["id"], dados_dict)
    else:
        return inserir_nova_conta(dados_dict)


# ==============================
# 📋 NOMES ÚNICOS DE CONTAS
# ==============================

def get_nomes_conta_unicos():
    """
    Retorna uma lista ordenada com os nomes únicos da coluna 'nome_da_conta',
    excluindo:
    - Registros com 'instancia' igual a 'legado'
    - Registros com 'nome_da_conta' igual a 'solar'

    Retorno:
    - list: Lista de strings com nomes de contas únicas (sem repetições).
    """
    url = f"{SUPABASE_URL}/rest/v1/{TABELA}?select=nome_da_conta,instancia"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        dados = response.json()

        nomes = list({
            item["nome_da_conta"].strip()
            for item in dados
            if item.get("nome_da_conta")
            and item["nome_da_conta"].strip().lower() != "solar"
            and item.get("instancia", "").lower() != "legado"
        })
        return sorted(nomes)

    return []



# ==============================
# 📆 CARREGAR MÊS REFERENTE
# ==============================

def carregar_mes_referente(mes, ano, delta_meses=0, delta_anos=0):
    """
    Carrega os dados de um mês e ano ajustado por um deslocamento (delta).

    Usado para buscar, por exemplo, o mês anterior ou o mesmo mês do ano anterior.

    Parâmetros:
    - mes (int): Mês base (1 a 12)
    - ano (int): Ano base (ex: 2025)
    - delta_meses (int, opcional): Quantidade de meses para ajustar (+/-). Ex: -1 para mês anterior.
    - delta_anos (int, opcional): Quantidade de anos para ajustar (+/-). Ex: -1 para ano anterior.

    Retorno:
    - pd.DataFrame: DataFrame com os dados do mês/ano ajustado.
    """
    # Cria um objeto de data base (dia 1 do mês)
    data_base = datetime(ano, mes, 1)

    # Aplica os ajustes (ex: -1 mês, -1 ano)
    data_destino = data_base + relativedelta(months=delta_meses, years=delta_anos)

    # Reutiliza a função principal de carregamento
    return carregar_tabela(data_destino.month, data_destino.year)

# ==============================
# 📅 LISTAR ANOS E MESES DISPONÍVEIS
# ==============================


def get_anos_meses_disponiveis():
    """
    Retorna os anos de primeiro registro até o ano atual, e os meses de 1 a 12.

    Retorno:
    - tuple: (lista de anos, lista de meses)
    """
    try:
        url = f"{SUPABASE_URL}/rest/v1/{TABELA}?select=ano&order=ano.asc&limit=10000"
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            dados = response.json()
            anos_extraidos = [
                int(item["ano"]) for item in dados
                if "ano" in item and str(item["ano"]).isdigit()
            ]

            if not anos_extraidos:
                return [], []

            primeiro_ano = min(anos_extraidos)
            ano_atual = datetime.now().year

            anos = list(range(ano_atual, primeiro_ano - 1, -1))  # mais recente primeiro
            meses = list(range(1, 13))

            return anos, meses

    except Exception as e:
        print(f"Erro ao montar intervalo de anos baseados em today: {e}")
        return [], []