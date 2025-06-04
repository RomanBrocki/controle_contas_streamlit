# 📁 Módulo `relatorio/`

Este módulo é responsável pela geração de relatórios financeiros no formato PDF e gráficos, baseando-se nos dados de contas do Supabase.

---

## 📦 Estrutura dos arquivos

### `graficos.py`
Contém funções de visualização com `matplotlib`, incluindo:
- `gerar_grafico_pizza_periodo`
- `gerar_grafico_comparativo_linha`
- `gerar_grafico_comparativo_duplo`

### `pdf.py`
Contém funções que geram arquivos PDF com base nos dados e gráficos:
- `gerar_relatorio_pdf`
- `gerar_pdf_comparativo_conta`
- `gerar_relatorio_periodo_pdf`

### `utils.py`
Funções auxiliares de cálculo e agregação:
- `carregar_dados_conta_periodo`
- `calcular_saldo_entre_pagadores`
- `agrupar_por_mes`
- `filtrar_contas_repetidas`

### `__init__.py`
Facilita a importação direta dos recursos do módulo:
```python
from relatorio import gerar_relatorio_pdf, gerar_pdf_comparativo_conta
```
Essas importações concentram as funções principais do pacote em um único
lugar, evitando a necessidade de referenciar cada submódulo separadamente.
