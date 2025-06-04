# ====================================
# 📄 GERAÇÃO DE RELATÓRIOS EM PDF
# ====================================

import os
from io import BytesIO
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF

from relatorio.graficos import (
    gerar_grafico_comparativo_duplo,
    gerar_grafico_comparativo_linha,
    gerar_grafico_pizza_periodo,
)
from relatorio.utils import (
    agrupar_por_mes,
    calcular_saldo_entre_pagadores,
    filtrar_contas_repetidas,
)
from supabase import carregar_mes_referente


# =====================================================
# 📄 Classe PDF customizada com links clicáveis
# =====================================================

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
# 📄 Geração do Relatório PDF do mês atual
# =====================================================

def gerar_relatorio_pdf(df_atual, nome_mes, ano):
    if df_atual.empty:
        return None

    df_mes_anterior = carregar_mes_referente(df_atual.iloc[0]['mes'], df_atual.iloc[0]['ano'], delta_meses=-1)
    df_ano_passado = carregar_mes_referente(df_atual.iloc[0]['mes'], df_atual.iloc[0]['ano'], delta_anos=-1)

    df = df_atual.copy()
    df['dividida'] = df['dividida'].astype(bool)
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.0)

    totais = df.groupby('quem_pagou')['valor'].sum().to_dict()
    total_roman = totais.get('Roman', 0.0)
    total_tati = totais.get('Tati', 0.0)
    total_outros = totais.get('Outro', 0.0)
    categorias = df.groupby('nome_da_conta')['valor'].sum().sort_values(ascending=False)
    total_gastos = categorias.sum()

    saldo, saldo_ajustado, detalhes = calcular_saldo_entre_pagadores(df)
    df_divididas = df[df['dividida'] == True]

    grafico_path = "grafico_pizza.png"
    gerar_grafico_pizza_periodo(df, grafico_path)

    comparativo_path = "comparativo_duplo.png"
    gerar_grafico_comparativo_duplo(df, df_mes_anterior, df_ano_passado, comparativo_path)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Relatório Financeiro - {nome_mes}/{ano}", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Gerado em {datetime.now().strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.image(grafico_path, x=10, y=30, w=180)
    if pdf.get_y() < 190:
        pdf.set_y(200)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Resumo Geral:", ln=True)

    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Total gasto: R$ {total_gastos:,.2f}".replace('.', ','), ln=True)
    pdf.cell(0, 8, f"Roman: R$ {total_roman:,.2f} | Tati: R$ {total_tati:,.2f} | Outros: R$ {total_outros:,.2f}".replace('.', ','), ln=True)
    pdf.ln(3)
    pdf.cell(0, 8, f"Total dividido: R$ {detalhes['total']:,.2f}".replace('.', ','), ln=True)
    pdf.cell(0, 8, f"Cada um deveria pagar: R$ {detalhes['metade']:,.2f}".replace('.', ','), ln=True)
    pdf.cell(0, 8, f"Pago por Roman: R$ {detalhes['D_R']:,.2f} | Pago por Tati: R$ {detalhes['D_T']:,.2f}".replace('.', ','), ln=True)

    if saldo > 0:
        pdf.cell(0, 8, f"Tati deve R$ {abs(saldo):,.2f} para Roman".replace('.', ','), ln=True)
    elif saldo < 0:
        pdf.cell(0, 8, f"Roman deve R$ {abs(saldo):,.2f} para Tati".replace('.', ','), ln=True)
    else:
        pdf.cell(0, 8, "Balanço equilibrado entre Roman e Tati", ln=True)

    if saldo_ajustado > 0:
        pdf.cell(0, 8, f"Tati deve R$ {abs(saldo_ajustado):,.2f} para Roman (ajustado com R$ {detalhes['ajuste']:,.2f} referentes a atividades extracurriculares)".replace('.', ','), ln=True)
    elif saldo_ajustado < 0:
        pdf.cell(0, 8, f"Roman deve R$ {abs(saldo_ajustado):,.2f} para Tati (ajustado com R$ {detalhes['ajuste']:,.2f} referentes a atividades extracurriculares)".replace('.', ','), ln=True)
    else:
        pdf.cell(0, 8, f"Balanço ajustado zerado após ajuste de R$ {detalhes['ajuste']:,.2f}".replace('.', ','), ln=True)

    pdf.add_page()
    pdf.image(comparativo_path, x=10, w=190)

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

            if row.get('link_boleto'):
                pdf.write_link_inline("Boleto", row['link_boleto'])
            if row.get('link_comprovante'):
                pdf.write_link_inline("Comprovante", row['link_comprovante'])

            pdf.ln(6)
        pdf.ln(3)

    buffer = BytesIO()
    output = pdf.output(dest="S")
    pdf_bytes = output.encode("latin1") if isinstance(output, str) else output
    buffer.write(pdf_bytes)
    buffer.seek(0)



    for path in [grafico_path, comparativo_path]:
        if os.path.exists(path):
            os.remove(path)

    return buffer

# ==================================================================
# 📄 Geração do Relatório PDF comparativo entre meses selecionados
# ==================================================================

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
        total_mes = sum(r["valor"] for r in agrupado[(ano, mes)])
        pdf.cell(0, 10, f"{nome_mes}/{ano} - Total: R$ {total_mes:,.2f}".replace('.', ','), ln=True)


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
    output = pdf.output(dest="S")
    pdf_bytes = output.encode("latin1") if isinstance(output, str) else output
    buffer.write(pdf_bytes)
    buffer.seek(0)


    # Limpa os arquivos temporários criados
    for path in arquivos_temp:
        if os.path.exists(path):
            os.remove(path)

    return buffer

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
    pdf = PDF()
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
    output = pdf.output(dest="S")
    pdf_bytes = output.encode("latin1") if isinstance(output, str) else output
    buffer.write(pdf_bytes)
    buffer.seek(0)


    # Limpar imagem temporária
    if os.path.exists(caminho_img):
        os.remove(caminho_img)

    return buffer


