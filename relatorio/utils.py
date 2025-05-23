# ====================================
# 🛠️ FUNÇÕES AUXILIARES PARA RELATÓRIOS
# ====================================

from datetime import datetime
from dateutil.relativedelta import relativedelta

import pandas as pd

from supabase import carregar_tabela



# =====================================================
# 📥 Carregar dados de uma conta em um intervalo de meses
# =====================================================

def carregar_dados_conta_periodo(mes_inicio, ano_inicio, mes_fim, ano_fim, nome_da_conta):
    """
    Carrega os dados de uma conta específica ou de todas as contas ao longo de um intervalo de meses.

    Parâmetros:
    - mes_inicio (int): Mês inicial (1–12)
    - ano_inicio (int): Ano inicial (ex: 2024)
    - mes_fim (int): Mês final (1–12)
    - ano_fim (int): Ano final (ex: 2025)
    - nome_da_conta (str | None): Nome da conta a ser filtrada. Se None, retorna todas as contas.

    Retorno:
    - pd.DataFrame:
        - Se nome_da_conta for fornecido: DataFrame com ['ano', 'mes', 'valor_total']
        - Se nome_da_conta for None: DataFrame original com todos os campos das contas
    """
    data_inicio = datetime(ano_inicio, mes_inicio, 1)
    data_fim = datetime(ano_fim, mes_fim, 1)

    if data_inicio > data_fim:
        data_inicio, data_fim = data_fim, data_inicio

    registros = []
    data_atual = data_inicio

    while data_atual <= data_fim:
        mes = data_atual.month
        ano = data_atual.year
        df_mes = carregar_tabela(mes, ano)

        if not df_mes.empty:
            if nome_da_conta is not None:
                df_filtrado = df_mes[df_mes["nome_da_conta"] == nome_da_conta].copy()
            else:
                df_filtrado = df_mes.copy()

            df_filtrado["mes"] = mes
            df_filtrado["ano"] = ano
            registros.append(df_filtrado)

        data_atual += relativedelta(months=1)

    if not registros:
        return pd.DataFrame()

    df_todos = pd.concat(registros, ignore_index=True)
    df_todos["valor"] = pd.to_numeric(df_todos["valor"], errors="coerce").fillna(0)

    # Caso o nome da conta tenha sido informado → retorna o DataFrame agrupado
    if nome_da_conta is not None:
        df_agrupado = (
            df_todos.groupby(["ano", "mes"])["valor"]
            .sum()
            .reset_index()
            .rename(columns={"valor": "valor_total"})
            .sort_values(by=["ano", "mes"])
        )
        return df_agrupado

    # Caso contrário, retorna todos os dados originais para geração de relatório
    return df_todos

# =====================================================
# 💰 Cálculo de Saldos entre Pagadores
# =====================================================

def calcular_saldo_entre_pagadores(df, ajuste_escolar=929.0):
    """
    Calcula o saldo financeiro entre Roman e Tati com base nas contas divididas.

    A função identifica quais contas foram marcadas como "divididas" e determina
    o valor pago por cada pagador. Considerando que cada um deveria pagar metade
    do total dessas contas, calcula-se o saldo entre eles. O ajuste fixo é sempre
    somado ao saldo final em favor de Roman.

    Parâmetros:
        df (pd.DataFrame): DataFrame contendo os dados das contas do mês.
        ajuste_escolar (float): Valor fixo a ser ajustado em favor de Roman.

    Retorno:
        tuple:
            - saldo (float): Valor que Roman deve a Tati (negativo) ou Tati deve a Roman (positivo).
            - saldo_ajustado (float): Saldo final com ajuste aplicado.
            - dict: Detalhamento com:
                - 'D_R': total pago por Roman
                - 'D_T': total pago por Tati
                - 'total': soma das contas divididas
                - 'metade': quanto cada um deveria pagar
                - 'ajuste': valor ajustado a favor de Roman
    """
    # -----------------------------
    # 🔍 Filtrar apenas contas divididas
    # -----------------------------
    df_divididas = df[df["dividida"] == True]

    # -----------------------------
    # 💰 Totais pagos por cada um
    # -----------------------------
    total_dividido_roman = df_divididas[df_divididas["quem_pagou"] == "Roman"]["valor"].sum()
    total_dividido_tati = df_divididas[df_divididas["quem_pagou"] == "Tati"]["valor"].sum()

    # -----------------------------
    # 🧮 Cálculo do saldo
    # -----------------------------
    total_dividido = total_dividido_roman + total_dividido_tati
    metade = total_dividido / 2
    saldo = total_dividido_roman - metade

    # -----------------------------
    # 🎓 Aplicação do ajuste escolar a favor de Roman
    # -----------------------------
    saldo_ajustado = saldo + ajuste_escolar

    # -----------------------------
    # 📦 Retorno estruturado
    # -----------------------------
    return saldo, saldo_ajustado, {
        "D_R": total_dividido_roman,
        "D_T": total_dividido_tati,
        "total": total_dividido,
        "metade": metade,
        "ajuste": ajuste_escolar
    }

# =====================================================
# 🔁 Agrupamento por Mês para Relatório
# =====================================================

def agrupar_por_mes(df):
    df["chave"] = df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)
    return df.groupby(["ano", "mes"]).apply(lambda g: g.to_dict(orient="records")).to_dict()

# =====================================================
# 🔍 Identificação de Contas Recorrentes
# =====================================================

def filtrar_contas_repetidas(df):
    return df["nome_da_conta"].value_counts()[lambda x: x > 1].index.tolist()