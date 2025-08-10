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

    def autopct_cond(pct):
        return f"{pct:.1f}%" if pct >= 6 else ""  # só mostra dentro se ≥ 6%

    fig, ax = plt.subplots(figsize=(7, 6))
    wedges, *_ = ax.pie(
        categorias_ordenadas,
        startangle=90,
        explode=explode,
        labels=None,
        autopct=autopct_cond,
        textprops=dict(color="white", fontsize=8),
        pctdistance=0.6,
        radius=0.85
    )

    # Nome fora da fatia + seta opcional
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

        if percentual <= 0.08:
            anotacao["arrowprops"] = dict(arrowstyle="-", lw=0.8)

        ax.annotate(str(categorias_ordenadas.index[i]), **anotacao)

    # Legenda: inclui percentual se não foi mostrado dentro
    legendas = []
    for nome, valor in zip(categorias_ordenadas.index, categorias_ordenadas):
        pct = valor / total_gastos * 100
        if pct < 6:
            legendas.append(f"{nome}: R$ {valor:,.2f} ({pct:.1f}%)".replace('.', ','))
        else:
            legendas.append(f"{nome}: R$ {valor:,.2f}".replace('.', ','))

    ax.legend(
        wedges,
        legendas,
        title="Categorias",
        loc="lower center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=2,
        fontsize=8
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
    Gráfico de linha com:
    - range mínimo de Y para evitar distorção em variações pequenas
    - rótulos de valores com deslocamento proporcional e clamp dentro do gráfico
    """

    if df.empty or "mes" not in df.columns or "ano" not in df.columns or "valor_total" not in df.columns:
        raise ValueError("DataFrame de entrada está vazio ou incompleto.")

    df["mes"] = df["mes"].astype(int)
    df["ano"] = df["ano"].astype(int)
    df["periodo"] = df.apply(lambda row: f"{int(row['mes']):02d}/{int(row['ano'])}", axis=1)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["periodo"], df["valor_total"], marker="o", linestyle="-", color="#4FC3F7", linewidth=2)

    # ===== Escala dinâmica com range mínimo =====
    y_min = float(df["valor_total"].min())
    y_max = float(df["valor_total"].max())
    data_range = y_max - y_min

    # range mínimo (evita “explodir” o gráfico por diferença de centavos)
    min_visual_range = max(10.0, 0.2 * max(y_max, 1.0))  # 10 reais ou 20% do valor típico

    if data_range < min_visual_range:
        # Expande em torno do valor médio
        mid = (y_min + y_max) / 2.0
        y_range = min_visual_range
        pad_up = 0.12 * y_range
        pad_dn = 0.10 * y_range
        bottom = max(0.0, mid - y_range / 2.0 - pad_dn)
        top = mid + y_range / 2.0 + pad_up
    else:
        # Usa range real + margens proporcionais
        y_range = data_range
        pad_up = 0.12 * y_range
        pad_dn = 0.10 * y_range
        bottom = max(0.0, y_min - pad_dn)
        top = y_max + pad_up

    ax.set_ylim(bottom=bottom, top=top)

    # ===== Rótulos dos pontos (proporcionais ao range + clamp) =====
    for i, valor in enumerate(df["valor_total"]):
        desloc = (0.04 * y_range) if (i % 2 == 0) else (-0.06 * y_range)
        y_text = float(valor) + desloc
        # mantém o texto dentro do gráfico
        y_text = min(top - 0.04 * y_range, max(bottom + 0.04 * y_range, y_text))
        va = 'bottom' if desloc > 0 else 'top'
        ax.annotate(
            f"R$ {float(valor):.2f}",
            xy=(i, float(valor)),
            xytext=(i, y_text),
            textcoords='data',
            ha='center',
            va=va,
            fontsize=7,
            clip_on=True
        )

    # Título
    titulo = f"Comparativo de conta '{nome_conta}' - {mes_inicio:02d}/{ano_inicio} a {mes_fim:02d}/{ano_fim}"
    ax.set_title(titulo, fontsize=14, pad=40)

    # Linha de média
    media = float(df["valor_total"].mean())
    ax.axhline(media, linestyle="--", color="gray", linewidth=1.2, label=f"Média da conta: R$ {media:.2f}")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.20), fontsize=9, frameon=False)

    # Limpeza estética
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#888888")
    ax.tick_params(left=False, right=False)
    ax.set_yticks([])
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.grid(False)

    plt.xticks(rotation=45)

    # Reserva espaço p/ título/legenda/ticks no PDF
    fig.subplots_adjust(top=0.80, bottom=0.20)

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