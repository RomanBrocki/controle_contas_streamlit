import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fpdf import FPDF

from supabase_utils import carregar_mes_referente, carregar_tabela


# ------------------------
# Classe customizada para PDF
# ------------------------
class PDF(FPDF):
    """
    Extensão da classe FPDF com método auxiliar para inserção de links inline.
    Ideal para exibir boletos e comprovantes clicáveis diretamente no relatório.
    """
    def write_link_inline(self, label, url):
        """
        Escreve um texto com estilo de link sublinhado, clicável, na posição atual.

        Parâmetros:
            label (str): Texto a ser exibido.
            url (str): URL de destino do link.
        """
        self.set_text_color(0, 0, 255)  # Azul para indicar link
        self.set_font("Arial", style="U", size=10)
        self.cell(25, 6, label, border=0, ln=0, link=url)
        self.set_text_color(0, 0, 0)  # Retorna para cor padrão
        self.set_font("Arial", size=10)


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

# ======================================================================================
# Funções de suporte para gerar_relatorio_pdf e gerar_relatorio_periodo_pdf
# ======================================================================================

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
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        x = np.cos(np.deg2rad(ang))
        y = np.sin(np.deg2rad(ang))
        valor = categorias_ordenadas.iloc[i]
        ax.annotate(
            f'{categorias_ordenadas.index[i]}: R$ {valor:,.2f}'.replace('.', ','),
            xy=(x, y), xytext=(1.2*x, 1.2*y),
            ha='center', va='center',
            arrowprops=dict(arrowstyle='-'),
            fontsize=8,
            color='black'
        )

    plt.title("Gastos por Categoria no Período")
    plt.tight_layout()
    plt.savefig(nome_arquivo)
    plt.close()
    return nome_arquivo

def filtrar_contas_repetidas(df):
    return df["nome_da_conta"].value_counts()[lambda x: x > 1].index.tolist()

def agrupar_por_mes(df):
    df["chave"] = df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)
    return df.groupby(["ano", "mes"]).apply(lambda g: g.to_dict(orient="records")).to_dict()



# =====================================================
# 📄 Geração do Relatório Financeiro em PDF
# =====================================================
def gerar_relatorio_pdf(df_atual, nome_mes, ano):
    """
    Gera um relatório financeiro em PDF baseado nos dados fornecidos para o mês atual.
    O relatório inclui:
    - Gráfico de pizza com distribuição por categoria
    - Comparativo com o mês anterior e mesmo mês do ano anterior
    - Resumo financeiro (por pagador, saldo, contas divididas)
    - Lista detalhada das contas pagas

    Parâmetros:
        df_atual (pd.DataFrame): Dados das contas do mês atual.
        nome_mes (str): Nome do mês (ex: 'Abril').
        ano (int): Ano de referência.

    Retorno:
        BytesIO: Objeto de buffer contendo o PDF gerado.
    """
    # -----------------------------
    # 🧾 Validação dos dados
    # -----------------------------
    if df_atual.empty:
        return None

    # -----------------------------
    # 🔄 Carregamento de meses de referência
    # -----------------------------
    df_mes_anterior = carregar_mes_referente(
        df_atual.iloc[0]['mes'], df_atual.iloc[0]['ano'], delta_meses=-1
    )
    df_ano_passado = carregar_mes_referente(
        df_atual.iloc[0]['mes'], df_atual.iloc[0]['ano'], delta_anos=-1
    )
    
    # -----------------------------
    # 🧹 Pré-processamento dos dados
    # -----------------------------
    df = df_atual.copy()
    df['dividida'] = df['dividida'].astype(bool)
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.0)

    # -----------------------------
    # 💰 Cálculo dos totais
    # -----------------------------
    totais = df.groupby('quem_pagou')['valor'].sum().to_dict()
    total_roman = totais.get('Roman', 0.0)
    total_tati = totais.get('Tati', 0.0)
    total_outros = totais.get('Outro', 0.0)
    categorias = df.groupby('nome_da_conta')['valor'].sum().sort_values(ascending=False)
    total_gastos = categorias.sum()

    # -----------------------------
    # 🔄 Cálculo dos débitos em contas divididas
    # -----------------------------
    df_divididas = df[df['dividida'] == True]
    debitos = {'Roman': 0.0, 'Tati': 0.0}
    for _, row in df_divididas.iterrows():
        metade = row['valor'] / 2
        if row['quem_pagou'] == 'Roman':
            debitos['Tati'] += metade
        elif row['quem_pagou'] == 'Tati':
            debitos['Roman'] += metade

    saldo = debitos['Tati'] - debitos['Roman']


    # -----------------------------
    # 📊 Geração do gráfico de pizza por categoria
    grafico_path = "grafico_pizza.png"
    gerar_grafico_pizza_periodo(df, grafico_path)



    # -----------------------------
    # 📊 Geração do gráfico comparativo duplo
    # -----------------------------
    comparativo_path = "comparativo_duplo.png"
    gerar_grafico_comparativo_duplo(df, df_mes_anterior, df_ano_passado, comparativo_path)

    # -----------------------------
    # 📄 Inicialização do PDF e capa
    # -----------------------------
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Relatório Financeiro - {nome_mes}/{ano}", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Gerado em {datetime.now().strftime('%d/%m/%Y')}", ln=True, align="C")

    # -----------------------------
    # 📎 Inserção do gráfico de pizza na primeira página
    # -----------------------------
    pdf.image(grafico_path, x=10, y=30, w=180)
    if pdf.get_y() < 190:
        pdf.set_y(200)

     # -----------------------------
    # 📋 Resumo geral no PDF
    # -----------------------------
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Resumo Geral:", ln=True)

    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Total gasto: R$ {total_gastos:,.2f}".replace('.', ','), ln=True)
    pdf.cell(
        0, 8,
        f"Roman: R$ {total_roman:,.2f} | Tati: R$ {total_tati:,.2f} | Outros: R$ {total_outros:,.2f}".replace('.', ','),
        ln=True
    )
    pdf.cell(0, 8, f"Contas divididas: {len(df_divididas)}", ln=True)

    ajuste_escola = 929.00
    saldo_ajustado = saldo + ajuste_escola

    # -----------------------------
    # 💳 Linha 1: Saldo original
    # -----------------------------
    if saldo < 0:
        pdf.cell(0, 8, f"Roman deve R$ {abs(saldo):,.2f} para Tati".replace('.', ','), ln=True)
    elif saldo > 0:
        pdf.cell(0, 8, f"Tati deve R$ {abs(saldo):,.2f} para Roman".replace('.', ','), ln=True)
    else:
        pdf.cell(0, 8, "Balanço equilibrado entre Roman e Tati", ln=True)

    # -----------------------------
    # 🏫 Linha 2: Saldo ajustado com atividades da escola
    # -----------------------------
    if saldo_ajustado < 0:
        pdf.cell(
            0, 8,
            f"Roman deve R$ {abs(saldo_ajustado):,.2f} para Tati (após abater R$ {ajuste_escola:,.2f} das atividades extras da escola)".replace('.', ','),
            ln=True
        )
    elif saldo_ajustado > 0:
        pdf.cell(
            0, 8,
            f"Tati deve R$ {abs(saldo_ajustado):,.2f} para Roman (após abater R$ {ajuste_escola:,.2f} das atividades extras da escola)".replace('.', ','),
            ln=True
        )
    else:
        pdf.cell(
            0, 8,
            f"Balanço ajustado: Tati deve R$ {ajuste_escola:,.2f} para Roman (atividades extras da escola)".replace('.', ','),
            ln=True
        )

    # -----------------------------
    # 📊 Página com gráfico comparativo duplo
    # -----------------------------
    pdf.add_page()
    pdf.image(comparativo_path, x=10, w=190)

    # -----------------------------
    # 🧾 Listagem de contas por pagador
    # -----------------------------
    pdf.add_page()
    for pagador in ['Roman', 'Tati', 'Outro']:
        df_pagador = df[df['quem_pagou'] == pagador]
        if df_pagador.empty:
            continue

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Contas pagas por {pagador}:", ln=True)
        pdf.set_font("Arial", size=10)

        for _, row in df_pagador.iterrows():
            valor_fmt = f"R$ {row['valor']:,.2f}".replace('.', ',')
            dividida = 'Sim' if row['dividida'] else 'Não'
            nome = row['nome_da_conta']
            instancia = row.get('instancia', '')
            nome_completo = f"{nome} ({instancia})" if instancia else nome

            pdf.set_font("Arial", style="", size=10)
            pdf.cell(80, 6, nome_completo, border=0)
            pdf.cell(30, 6, valor_fmt, border=0)
            pdf.cell(25, 6, f"Dividida: {dividida}", border=0)

            if row.get('link_boleto') and isinstance(row['link_boleto'], str):
                pdf.write_link_inline("Boleto", row['link_boleto'])

            if row.get('link_comprovante') and isinstance(row['link_comprovante'], str):
                pdf.write_link_inline("Comprovante", row['link_comprovante'])

            pdf.ln(6)
        pdf.ln(3)

    # -----------------------------
    # 💾 Exportação para buffer de memória (BytesIO)
    # -----------------------------
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)

    # -----------------------------
    # 🧹 Limpeza de arquivos temporários
    # -----------------------------
    for path in [grafico_path, comparativo_path]:
        if os.path.exists(path):
            os.remove(path)

    return buffer

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
# 📈 Gerar gráfico de linha comparativo de conta por período
# =====================================================

def gerar_grafico_comparativo_linha(df, nome_conta, mes_inicio, ano_inicio, mes_fim, ano_fim):
    """
    Gera um gráfico de linha visualmente limpo para exibir a variação de uma conta específica
    ao longo de um intervalo de meses, com escala ajustada automaticamente e estética minimalista.
    """
    import matplotlib.pyplot as plt

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
# 📄 Gerar PDF comparativo de uma conta no tempo
# =====================================================

def gerar_pdf_comparativo_conta(df, nome_conta, mes_inicio, ano_inicio, mes_fim, ano_fim):
    """
    Gera um PDF contendo o gráfico de linha da variação de uma conta específica
    ao longo de um intervalo de meses, além de resumo geral do valor total acumulado.

    Parâmetros:
    - df (pd.DataFrame): DataFrame com colunas ['ano', 'mes', 'valor_total']
    - nome_conta (str): Nome da conta (ex: 'Luz')
    - mes_inicio (int): Mês inicial (1 a 12)
    - ano_inicio (int): Ano inicial
    - mes_fim (int): Mês final (1 a 12)
    - ano_fim (int): Ano final

    Retorno:
    - BytesIO: Buffer contendo o PDF pronto para download
    """

    # -----------------------------
    # 📊 Gerar gráfico e salvar temporariamente
    # -----------------------------
    fig = gerar_grafico_comparativo_linha(df, nome_conta, mes_inicio, ano_inicio, mes_fim, ano_fim)
    caminho_img = "grafico_comparativo_temp.png"
    fig.savefig(caminho_img)
    plt.close(fig)

    # -----------------------------
    # 📄 Iniciar PDF
    # -----------------------------
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    titulo = f"Comparativo - {nome_conta}: {mes_inicio:02d}/{ano_inicio} a {mes_fim:02d}/{ano_fim}"
    pdf.cell(0, 10, titulo, ln=True, align="C")

    # -----------------------------
    # 🖼️ Inserir imagem do gráfico
    # -----------------------------
    pdf.image(caminho_img, x=10, y=30, w=190)
    pdf.set_y(110)

    # -----------------------------
    # 🧾 Inserir resumo geral
    # -----------------------------
    valor_total = df["valor_total"].sum()
    pdf.set_font("Arial", "", 12)
    pdf.ln(85)
    pdf.cell(0, 10, f"Valor total acumulado no período: R$ {valor_total:,.2f}".replace(".", ","), ln=True)

    # -----------------------------
    # 💾 Exportar para buffer de memória
    # -----------------------------
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)

    # Limpar imagem temporária
    if os.path.exists(caminho_img):
        os.remove(caminho_img)

    return buffer

def gerar_relatorio_periodo_pdf(df, mes_inicio, ano_inicio, mes_fim, ano_fim):
    """
    Gera um PDF contendo o resumo financeiro de um período completo, incluindo:
    - Gráfico de pizza com distribuição por categoria (maiores contas + "Outros")
    - Gráficos de linha por conta (apenas as que aparecem mais de uma vez, até 3 por página)
    - Listagem de contas agrupadas por mês com valores, pagador e links clicáveis

    Parâmetros:
        df (pd.DataFrame): DataFrame contendo as contas do período
        mes_inicio (int): Mês inicial do intervalo
        ano_inicio (int): Ano inicial do intervalo
        mes_fim (int): Mês final do intervalo
        ano_fim (int): Ano final do intervalo

    Retorno:
        BytesIO: PDF final gerado, pronto para download
    """
    if df.empty:
        return None

    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.0)
    df = df.copy()

    arquivos_temp = []

    # Gráfico de pizza
    grafico_pizza_path = "pizza_periodo.png"
    gerar_grafico_pizza_periodo(df, grafico_pizza_path)
    arquivos_temp.append(grafico_pizza_path)

    # PDF inicial
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Resumo Financeiro: {mes_inicio:02d}/{ano_inicio} a {mes_fim:02d}/{ano_fim}", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Gerado em {pd.Timestamp.now().strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.image(grafico_pizza_path, x=10, y=40, w=180)
    pdf.set_y(130)

    # Gráficos de linha para contas recorrentes (até 3 por página)
    contas_validas = filtrar_contas_repetidas(df)
    graficos_por_pagina = 3
    imagens = []

    for conta in contas_validas:
        df_conta = df[df["nome_da_conta"] == conta]
        df_conta = (
            df_conta.groupby(["ano", "mes"])["valor"]
            .sum()
            .reset_index()
            .rename(columns={"valor": "valor_total"})
            .sort_values(by=["ano", "mes"])
        )
        fig = gerar_grafico_comparativo_linha(df_conta, conta, mes_inicio, ano_inicio, mes_fim, ano_fim)
        caminho_img = f"linha_{conta}.png"
        fig.savefig(caminho_img)
        plt.close(fig)
        imagens.append(caminho_img)
        arquivos_temp.append(caminho_img)

    for i in range(0, len(imagens), graficos_por_pagina):
        pdf.add_page()
        for j, img_path in enumerate(imagens[i:i+graficos_por_pagina]):
            y_pos = 30 + j * 85
            pdf.image(img_path, x=10, y=y_pos, w=190)

    # Listagem agrupada por mês
    agrupado = agrupar_por_mes(df)
    for (ano, mes) in sorted(agrupado.keys()):
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        nome_mes = pd.Timestamp(year=ano, month=mes, day=1).strftime("%B").capitalize()
        pdf.cell(0, 10, f"{nome_mes}/{ano}", ln=True)

        pdf.set_font("Arial", size=9)
        for row in agrupado[(ano, mes)]:
            nome = row["nome_da_conta"]
            instancia = row.get("instancia", "")
            quem_pagou = row.get("quem_pagou", "")
            valor_fmt = f"R$ {row['valor']:,.2f}".replace(".", ",")
            nome_exibido = f"{nome} ({instancia})" if instancia else nome

            pdf.cell(80, 6, nome_exibido, border=0)
            pdf.cell(26, 6, valor_fmt, border=0)
            pdf.cell(30, 6, f"Pagador: {quem_pagou}", border=0)

            if row.get("link_boleto"):
                pdf.write_link_inline("Boleto", row["link_boleto"])
            if row.get("link_comprovante"):
                pdf.write_link_inline("Comprovante", row["link_comprovante"])

            pdf.ln(6)
        pdf.ln(3)

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)

    # Limpa os arquivos temporários criados
    for path in arquivos_temp:
        if os.path.exists(path):
            os.remove(path)

    return buffer














