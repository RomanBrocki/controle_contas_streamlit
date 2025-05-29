### README.md (raiz do projeto)

# 💸 Controle de Contas Pessoais

Aplicativo desenvolvido com **Streamlit Cloud**, pensado para controle doméstico de despesas mensais com visual moderno, geração de relatórios e integração ao Supabase.
---
# Repositório github:
https://github.com/RomanBrocki/controle_contas_streamlit
---
## ✨ Funcionalidades

* 📅 Registro de contas mensais com nome, valor, data, pagador, se é dividida, instância e links
* 📊 Relatório mensal em PDF com:

  * Gráfico de pizza por categoria
  * Comparativo com mês anterior e mesmo mês do ano anterior
  * Saldo entre pagadores (com ajuste escolar)
  * Lista clicável com links de comprovantes e boletos
* 📈 Comparativo por conta com gráfico de linha e PDF
* 🧾 Resumo de múltiplos meses com pizza consolidada, gráficos de linha e listagem agrupada
* 📌 Lembrete com contas não pagas comparando com o mês anterior
* 🌐 Interface organizada com cabeçalho fixo e formulários colapsáveis

---

## 🚀 Como Usar na Streamlit Cloud

1. Suba o projeto no GitHub
2. Vá para [streamlit.io/cloud](https://streamlit.io/cloud) e conecte sua conta
3. Aponte o app principal: `app.py`
4. Configure os segredos no menu `Settings > Secrets`:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_KEY = "sua-chave"
```

5. Clique em Deploy

---

## 📁 Estrutura

```bash
controle-contas/
├── app.py                 # App principal e roteamento
├── estilo.py              # Estilos visuais globais
├── assets/                # Imagem de fundo
│
├── interface/
│   ├── app_utils.py       # Formulários, cabeçalho, lembretes
│   ├── app_vars.py        # Inicialização do session_state
│   ├── navegacao.py       # Troca de tela
│   └── __init__.py        # Pacote de interface
│
├── relatorio/
│   ├── graficos.py        # Geração de gráficos
│   ├── pdf.py             # Relatórios em PDF
│   ├── utils.py           # Cálculos auxiliares e carregamento por período
│   └── __init__.py        # Pacote de relatórios
│
├── supabase/
│   ├── supabase_utils.py  # CRUD e integração REST
│   ├── supabase_config.py # Variáveis de acesso
│   └── __init__.py        # Pacote supabase
```

---

## 📦 Requisitos

```txt
streamlit
pandas
openpyxl
fpdf
matplotlib
numpy
requests
python-dateutil
```

---

### 📁 interface/README.md

Módulo responsável pela interface visual do usuário:

* `app_utils.py`: cabeçalho, formulários, lembretes e exibição de contas
* `app_vars.py`: controle de estado da sessão
* `navegacao.py`: troca de telas

### 📁 relatorio/README.md

Responsável pela geração de relatórios:

* `graficos.py`: gráficos de pizza e linha
* `pdf.py`: exportação de relatórios mensais e por período
* `utils.py`: cálculo de saldo, agrupamento e carregamento de dados históricos

### 📁 supabase/README.md

Responsável pela comunicação com o Supabase:

* `supabase_utils.py`: funções REST para carregar, salvar e excluir contas
* `supabase_config.py`: configuração de acesso via URL e chave

### 📁 assets/README.md

Contém recursos visuais estáticos, como a imagem de fundo da tela inicial.

---

Pronto para ser executado diretamente na nuvem com visual moderno, funcionalidade prática e histórico persistente.





