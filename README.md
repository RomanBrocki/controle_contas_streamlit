# 💸 Controle de Contas Pessoais

Aplicativo desenvolvido com **Streamlit Cloud**, pensado para ser executado diretamente no navegador, sem necessidade de instalação local. Ele permite controlar contas domésticas pagas mensalmente, incluindo geração de relatórios financeiros completos e integração com Supabase.

---

## ✨ Funcionalidades

* 📅 Registro mensal de contas com:
  * Nome, valor, data, instância, pagador, se é dividida e links (boleto e comprovante)
* 📊 Relatório em PDF mensal com:
  * Gráfico de pizza por categoria
  * Comparativo com mês anterior e mesmo mês do ano anterior
  * Saldo entre as partes (incluindo ajuste escolar)
  * Lista detalhada com links clicáveis
* 📈 Comparativo de conta por período com gráfico de linha e PDF
* 🧾 Relatório do período com:
  * Gráfico de pizza consolidado
  * Gráficos de linha para contas recorrentes (até 3 por página)
  * Listagem agrupada por mês com valor, pagador e links clicáveis
* 📂 Interface organizada com formulários colapsáveis e cabeçalho fixo
* 🔄 Campos dinâmicos obtidos do banco de dados (nome da conta, quem pagou)
* 🌐 Datas e nomes de mês formatados para pt-BR nos relatórios
* 🔐 Integração segura com Supabase via secrets ou variáveis de ambiente

---

## 🚀 Como Usar (via Streamlit Cloud)

1. **Suba os arquivos para um repositório no GitHub.**

2. **Acesse:** [streamlit.io/cloud](https://streamlit.io/cloud) e conecte com seu GitHub

3. **Escolha o repositório e o arquivo principal:** `app.py`

4. **Configure os secrets em Settings > Secrets:**

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_KEY = "sua-chave"
```

> Alternativamente, você pode configurar essas variáveis como variáveis de ambiente no painel da Streamlit Cloud.

5. **Clique em Deploy.** Pronto!

---

## 🧑‍💻 Como Funciona o Uso no Navegador

### Tela Inicial

* Possui um fundo visual personalizado e três botões:
  * **Mês Vigente**: exibe as contas do mês atual.
  * **Histórico**: permite navegar por qualquer mês e ano para consultar contas anteriores.
  * **Relatórios**: acesso à análise por período com gráficos e PDFs.

### Modo "Mês Vigente" ou "Histórico"

* Exibe um cabeçalho com o nome do mês, ano e total pago.
* Há botões para:
  * **Nova Conta**: abre um formulário para registrar uma nova despesa.
  * **Gerar Relatório 📄**: cria um relatório PDF detalhado daquele mês.

### Cadastro ou Edição de Contas

* Os dados preenchidos incluem:
  * Nome da conta (baseado no banco)
  * Valor
  * Data de pagamento
  * Instância (ex: cartão, conta específica)
  * Quem pagou (valores dinâmicos baseados no banco)
  * Checkbox para "Conta dividida?"
  * Link do boleto e comprovante (se houver)

* As contas já registradas aparecem em caixas colapsadas (expander), onde é possível:
  * Editar e salvar alterações
  * Excluir conta existente

### Relatório em PDF do mês

* Gerado automaticamente com:
  * Gráfico de pizza por categoria
  * Comparativos com mês anterior e mesmo mês do ano anterior
  * Resumo de quem pagou, saldo entre as partes e ajuste escolar
  * Lista detalhada com links clicáveis para boletos e comprovantes

### Relatórios por período

* Dois tipos:
  * **Comparativo de conta específica por período:** gráfico de linha + PDF com valor total
  * **Resumo de todas as contas por período:**
    * Pizza consolidada
    * Gráficos de linha (contas recorrentes)
    * Listagem mês a mês
    * PDF com download imediato

---

## 📁 Estrutura do Projeto

```plaintext
controle-contas/
├── app.py                        # Aplicativo principal (interface e navegação)
├── estilo.py                     # Estilo visual customizado (fundo, cabeçalho flutuante)
│
├── interface/                    # Componentes da interface
│   ├── app_utils.py              # Formulários, cabeçalho e visualização de contas
│   ├── app_vars.py               # Inicialização do estado de sessão
│   ├── navegacao.py              # Funções de troca de tela
│   └── __init__.py
│
├── relatorio/                    # Geração de relatórios, gráficos e PDFs
│   ├── graficos.py
│   ├── pdf.py
│   ├── utils.py
│   └── __init__.py
│
├── supabase/                     # Comunicação com o Supabase (REST API)
│   ├── supabase_config.py
│   ├── supabase_utils.py
│   └── __init__.py
│
├── assets/
│   └── bg_1.png                  # Imagem de fundo da tela inicial
│
├── requirements.txt              # Dependências do projeto
└── mockupstreamlit.html          # Protótipo HTML da interface (opcional)
```

---

## 📦 Dependências Necessárias

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

Essas bibliotecas são carregadas automaticamente na Streamlit Cloud com base no `requirements.txt`.




