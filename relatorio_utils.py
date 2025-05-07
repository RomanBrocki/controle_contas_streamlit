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
        ax.legend(loc='lower right')

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
        cor_ref="#1f77b4", cor_atual="#ff7f0e",
        label_atual=atual_label, label_ref=mes_ano_anterior,
    )

    plot_duplo(
        ax2, df_ano,
        col_ref="Ano Passado", col_atual="Atual",
        titulo=f"Comparativo com {ano_anterior}",
        cor_ref="#1f77b4", cor_atual="#ff7f0e",
        label_atual=atual_label, label_ref=ano_anterior
    )

    plt.tight_layout()
    plt.savefig(nome_arquivo)
    plt.close()
    return nome_arquivo



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
    # 💰 Cálculo dos totais por pagador
    # -----------------------------
    totais = df.groupby('quem_pagou')['valor'].sum().to_dict()
    total_roman = totais.get('Roman', 0.0)
    total_tati = totais.get('Tati', 0.0)
    total_outros = totais.get('Outro', 0.0)

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
    # -----------------------------
    categorias = df.groupby('nome_da_conta')['valor'].sum().sort_values(ascending=False)
    total_gastos = categorias.sum()

    # Agrupar categorias menores como 'Outros'
    if len(categorias) > 6:
        top5 = categorias.head(5)
        outros = categorias.iloc[5:].sum()
        categorias_ordenadas = pd.concat([top5, pd.Series({'Outros': outros})])
    else:
        categorias_ordenadas = categorias

    # Criar figura de gráfico de pizza
    fig, ax = plt.subplots(figsize=(7, 6))
    explode = [0.1 if v == categorias_ordenadas.max() else 0 for v in categorias_ordenadas]
    categorias_ordenadas.plot(
        kind="pie",
        startangle=90,
        ax=ax,
        explode=explode,
        label=""
    )
    ax.legend(
        labels=[f"{cat} (R$ {val:,.2f})".replace('.', ',') for cat, val in categorias_ordenadas.items()],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=2
    )

    plt.title(f"Gastos por Categoria - {nome_mes}/{ano}")
    grafico_path = "grafico_pizza.png"
    plt.tight_layout()
    plt.savefig(grafico_path)
    plt.close()

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
    Carrega os dados de uma conta específica ao longo de um intervalo de meses,
    filtrando diretamente na API Supabase e agrupando os resultados por mês e ano.

    Parâmetros:
    - mes_inicio (int): Mês inicial (1–12)
    - ano_inicio (int): Ano inicial (ex: 2024)
    - mes_fim (int): Mês final (1–12)
    - ano_fim (int): Ano final (ex: 2025)
    - nome_da_conta (str): Nome da conta a ser filtrada

    Retorno:
    - pd.DataFrame: DataFrame com colunas ['ano', 'mes', 'valor_total']
    """
    # Garante que a data inicial seja anterior à final
    data_inicio = datetime(ano_inicio, mes_inicio, 1)
    data_fim = datetime(ano_fim, mes_fim, 1)

    if data_inicio > data_fim:
        data_inicio, data_fim = data_fim, data_inicio  # Inverte se necessário

    # Lista todas as combinações de mês/ano no intervalo
    data_atual = data_inicio
    registros = []

    while data_atual <= data_fim:
        mes = data_atual.month
        ano = data_atual.year

        df_mes = carregar_tabela(mes, ano)

        if not df_mes.empty:
            df_filtrado = df_mes[df_mes["nome_da_conta"] == nome_da_conta].copy()
            df_filtrado["mes"] = mes
            df_filtrado["ano"] = ano
            registros.append(df_filtrado)

        # Avança um mês
        data_atual += relativedelta(months=1)

    if not registros:
        return pd.DataFrame(columns=["ano", "mes", "valor_total"])

    df_todos = pd.concat(registros, ignore_index=True)
    df_todos["valor"] = pd.to_numeric(df_todos["valor"], errors="coerce").fillna(0)

    df_agrupado = (
        df_todos.groupby(["ano", "mes"])["valor"]
        .sum()
        .reset_index()
        .rename(columns={"valor": "valor_total"})
        .sort_values(by=["ano", "mes"])
    )

    return df_agrupado

# =====================================================
# 📈 Gerar gráfico de linha comparativo de conta por período
# =====================================================

def gerar_grafico_comparativo_linha(df, nome_conta, mes_inicio, ano_inicio, mes_fim, ano_fim):
    """
    Gera um gráfico de linha com pontos para visualização da variação do valor total
    de uma conta específica ao longo de um intervalo de meses.

    Parâmetros:
    - df (pd.DataFrame): DataFrame com colunas ['ano', 'mes', 'valor_total']
    - nome_conta (str): Nome da conta (ex: 'Luz')
    - mes_inicio (int): Mês inicial (1 a 12)
    - ano_inicio (int): Ano inicial
    - mes_fim (int): Mês final (1 a 12)
    - ano_fim (int): Ano final

    Retorno:
    - matplotlib.figure.Figure: Objeto da figura com o gráfico pronto
    """

    
    if df.empty or "mes" not in df.columns or "ano" not in df.columns or "valor_total" not in df.columns:
        raise ValueError("DataFrame de entrada está vazio ou incompleto.")

    # Conversões necessárias
    df["mes"] = df["mes"].astype(int)
    df["ano"] = df["ano"].astype(int)

    # Cria coluna de rótulo do eixo X no formato MM/AAAA
    df["periodo"] = df.apply(lambda row: f"{int(row['mes']):02d}/{int(row['ano'])}", axis=1)

    # Início do gráfico
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["periodo"], df["valor_total"], marker="o", linestyle="-", color="#4FC3F7")

    # Rótulos de valor sobre cada ponto
    for i, valor in enumerate(df["valor_total"]):
        ax.text(i, valor + 1, f"R$ {valor:.2f}", ha='center', va='bottom', fontsize=9)

    # Título dinâmico
    titulo = f"Comparativo de conta '{nome_conta}' - {mes_inicio:02d}/{ano_inicio} a {mes_fim:02d}/{ano_fim}"
    ax.set_title(titulo, fontsize=14)
    ax.set_ylabel("Valor (R$)")
    ax.set_xlabel("Período")
    ax.grid(True, linestyle="--", alpha=0.4)

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
    import os
    from io import BytesIO
    from fpdf import FPDF

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














