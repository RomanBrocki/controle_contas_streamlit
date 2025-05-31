# ====================================
# 📊 GERAÇÃO DE GRÁFICOS PARA RELATÓRIOS
# ====================================

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


# =====================================================
# 🍕 Gráfico de Pizza: Gastos por Categoria
# =====================================================

def gerar_grafico_pizza_periodo(df, nome_arquivo):
    categorias = df.groupby('nome_da_conta')['valor'].sum().sort_values(ascending=False)
    total_gastos = categorias.sum()

    if len(categorias) > 6:
        top5 = categorias.head(5)
        outros = categorias.iloc[5:].sum()
        categorias_ordenadas = pd.concat([top5, pd.Series({'Outros': outros})])
    else:
        categorias_ordenadas = categorias

    explode = [0.01 + (v / categorias_ordenadas.max()) * 0.1 for v in categorias_ordenadas]

    fig, ax = plt.subplots(figsize=(7, 6))
    wedges, _, _ = ax.pie(
        categorias_ordenadas,
        startangle=90,
        explode=explode,
        labels=None,
        autopct=lambda pct: f'{pct:.1f}%',
        textprops=dict(color="white", fontsize=8),
        pctdistance=0.7,
        radius=0.85,
    )
    pos = ax.get_position()
    ax.set_position([pos.x0 - 0.07, pos.y0, pos.width, pos.height])

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1) / 2. + p.theta1
        x = np.cos(np.deg2rad(ang))
        y = np.sin(np.deg2rad(ang))
        valor = categorias_ordenadas.iloc[i]
        percentual = valor / total_gastos

        anotacao = {
            "xy": (x, y),
            "xytext": (1.2 * x, 1.2 * y),
            "textcoords": "data",
            "ha": "center",
            "va": "center",
            "fontsize": 8,
            "color": "black"
        }

        if percentual <= 0.3:
            anotacao["arrowprops"] = dict(arrowstyle="-")

        ax.annotate(
            f'{categorias_ordenadas.index[i]}: R$ {valor:,.2f}'.replace('.', ','),
            **anotacao
        )

    plt.title("Gastos por Categoria no Período")
    plt.tight_layout()
    plt.savefig(nome_arquivo)
    plt.close()
    return nome_arquivo

# =====================================================
# 📈 Gráfico de Linha: Conta ao longo do tempo
# =====================================================

def gerar_grafico_comparativo_linha(df, nome_conta, mes_inicio, ano_inicio, mes_fim, ano_fim):
    """
    Gera um gráfico de linha visualmente limpo para exibir a variação de uma conta específica
    ao longo de um intervalo de meses, com escala ajustada automaticamente e estética minimalista.
    """
    
    if df.empty or "mes" not in df.columns or "ano" not in df.columns or "valor_total" not in df.columns:
        raise ValueError("DataFrame de entrada está vazio ou incompleto.")

    df["mes"] = df["mes"].astype(int)
    df["ano"] = df["ano"].astype(int)
    df["periodo"] = df.apply(lambda row: f"{int(row['mes']):02d}/{int(row['ano'])}", axis=1)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["periodo"], df["valor_total"], marker="o", linestyle="-", color="#4FC3F7", linewidth=2)

    # Escala dinâmica (sem base zero, nem espaço exagerado)
    y_min = df["valor_total"].min()
    y_max = df["valor_total"].max()
    margem_superior = (y_max - y_min) * 0.08 if y_max > y_min else 10
    margem_inferior = (y_max - y_min) * 0.1 if y_max > y_min else 5

    ax.set_ylim(
        bottom=max(0, y_min - margem_inferior),
        top=y_max + margem_superior
    )

    # Rótulos afastados dos pontos
    for i, valor in enumerate(df["valor_total"]):
        deslocamento = 12 if i % 2 == 0 else -16
        va = 'bottom' if deslocamento > 0 else 'top'
        ax.text(i, valor + deslocamento, f"R$ {valor:.2f}", ha='center', va=va, fontsize=9)


    # Título
    titulo = f"Comparativo de conta '{nome_conta}' - {mes_inicio:02d}/{ano_inicio} a {mes_fim:02d}/{ano_fim}"
    ax.set_title(titulo, fontsize=14, pad=40)  # aumenta distância do gráfico para o topo
    # Linha de média
    media = df["valor_total"].mean()
    ax.axhline(media, linestyle="--", color="gray", linewidth=1.2, label=f"Média da conta: R$ {media:.2f}")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.20), fontsize=9, frameon=False)


    # Limpeza estética
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#888888")  # manter apenas linha do eixo X

    ax.tick_params(left=False, right=False)
    ax.set_yticks([])  # remove marcações do Y
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.grid(False)

    plt.xticks(rotation=45)
    plt.tight_layout()

    return fig

# =====================================================
# 📊 Gráfico comparativo duplo: mês anterior e ano anterior
# =====================================================
def gerar_grafico_comparativo_duplo(df_atual, df_mes_anterior, df_ano_passado, nome_arquivo):
    """
    Gera um gráfico comparativo horizontal em barras duplas com:
    - Comparação do mês atual vs mês anterior
    - Comparação do mês atual vs mesmo mês do ano anterior

    Parâmetros:
        df_atual (pd.DataFrame): Dados do mês atual.
        df_mes_anterior (pd.DataFrame): Dados do mês anterior.
        df_ano_passado (pd.DataFrame): Dados do mesmo mês do ano anterior.
        nome_arquivo (str): Caminho de saída para salvar o gráfico gerado (.png).

    Retorno:
        str: Caminho do arquivo de imagem gerado.
    """
    contas_desejadas = ["Condomínio", "Luz", "Empregada", "Cartão de crédito", "Gás"]

    # ------------------------
    # Preparo dos dados
    # ------------------------
    def preparar(df, label):
        if df is None or df.empty or 'nome_da_conta' not in df.columns:
            return pd.DataFrame({
                "nome_da_conta": contas_desejadas,
                label: [0] * len(contas_desejadas)
            })
        df_filtrado = df[df['nome_da_conta'].isin(contas_desejadas)]
        return (
            df_filtrado
            .groupby("nome_da_conta")["valor"]
            .sum()
            .reindex(contas_desejadas)
            .fillna(0)
            .reset_index()
            .rename(columns={"valor": label})
        )

    atual = preparar(df_atual, "Atual")
    anterior = preparar(df_mes_anterior, "Anterior")
    ano_passado = preparar(df_ano_passado, "Ano Passado")

    df_anterior = pd.merge(anterior, atual, on="nome_da_conta")
    df_ano = pd.merge(ano_passado, atual, on="nome_da_conta")

    # ------------------------
    # Criação do gráfico
    # ------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), sharey=True)
    y = np.arange(len(contas_desejadas))
    width = 0.35

    def plot_duplo(ax, df, col_ref, col_atual, titulo, cor_ref, cor_atual, label_ref, label_atual):
        ax.barh(y - width/2, df[col_ref], height=width, label=label_ref, color=cor_ref)
        ax.barh(y + width/2, df[col_atual], height=width, label=label_atual, color=cor_atual)
        for i in y:
            v_ref = df[col_ref][i]
            v_atual = df[col_atual][i]
            ax.text(v_ref / 2, i - width/2, f"         R$ {int(v_ref)}", ha='center', va='center', fontsize=8, color='black')
            ax.text(v_atual / 2, i + width/2, f"         R$ {int(v_atual)}", ha='center', va='center', fontsize=8, color='black')

        ax.set_yticks(y)
        ax.set_yticklabels(contas_desejadas)
        ax.invert_yaxis()
        ax.set_title(titulo)
        # Criação da legenda com ordem customizada
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(
            handles[::-1], labels[::-1],  # inverte ordem: Atual em cima
            loc='lower right',
            fontsize=9
        )


    # ------------------------
    # Títulos e rótulos de tempo
    # ------------------------
    mes_ano_atual = df_atual.iloc[0]["mes"]
    ano_atual = df_atual.iloc[0]["ano"]
    nome_mes = datetime(1900, mes_ano_atual, 1).strftime("%B").capitalize()

    mes_ano_anterior = (datetime(ano_atual, mes_ano_atual, 1) - pd.DateOffset(months=1)).strftime("%B/%Y")
    ano_anterior = f"{nome_mes}/{ano_atual - 1}"
    atual_label = f"{nome_mes}/{ano_atual}"

    # ------------------------
    # Gerar os dois gráficos comparativos
    # ------------------------
    plot_duplo(
        ax1, df_anterior,
        col_ref="Anterior", col_atual="Atual",
        titulo=f"Comparativo com {mes_ano_anterior}",
        cor_ref="#f58518", cor_atual="#4c78a8",
        label_atual=atual_label, label_ref=mes_ano_anterior,
    )

    plot_duplo(
        ax2, df_ano,
        col_ref="Ano Passado", col_atual="Atual",
        titulo=f"Comparativo com {ano_anterior}",
        cor_ref="#54a24b", cor_atual="#4c78a8",
        label_atual=atual_label, label_ref=ano_anterior
    )
    
    plt.tight_layout()
    plt.savefig(nome_arquivo)
    plt.close()
    return nome_arquivo