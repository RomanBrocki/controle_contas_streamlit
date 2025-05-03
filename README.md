# 💸 Controle de Contas Pessoais

Aplicativo desenvolvido com **Streamlit Cloud**, pensado para ser executado diretamente no navegador, sem necessidade de instalação local. Ele permite controlar contas domésticas pagas mensalmente, incluindo geração de relatórios financeiros completos e integração com Supabase.

---

## ✨ Funcionalidades

* 📅 Registro mensal de contas com:

  * Nome, valor, data, instância, pagador, se é dividida e links (boleto e comprovante)
* 📊 Relatório em PDF com:

  * Gráfico de pizza por categoria
  * Comparativo com mês anterior e mesmo mês do ano anterior
  * Saldo entre as partes
* 🧾 Formulários colapsáveis e interface moderna
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

* Possui um fundo visual personalizado e dois botões:

  * **Mês Vigente**: exibe as contas do mês atual.
  * **Histórico**: permite navegar por qualquer mês e ano para consultar contas anteriores.

### Modo "Mês Vigente" ou "Histórico"

* Exibe um cabeçalho com o nome do mês, ano e total pago.
* Há botões para:

  * **Nova Conta**: abre um formulário para registrar uma nova despesa.
  * **Gerar Relatório 📄**: cria um relatório PDF detalhado daquele mês.

### Cadastro ou Edição de Contas

* Os dados preenchidos incluem:

  * Nome da conta (com opção "Outros")
  * Valor
  * Data de pagamento
  * Instância (ex: cartão, conta específica)
  * Quem pagou (Roman, Tati, Outro)
  * Checkbox para "Conta dividida?"
  * Link do boleto e comprovante (se houver)

* As contas já registradas aparecem em caixas colapsadas (expander), onde é possível:

  * Editar e salvar alterações
  * Excluir conta existente

### Relatório em PDF

* Gerado automaticamente com:

  * Gráfico de pizza por categoria
  * Comparativos com mês anterior e mesmo mês do ano anterior
  * Resumo de quem pagou, saldo entre as partes e ajuste escolar
  * Lista detalhada com links clicáveis para boletos e comprovantes

---

## 📁 Estrutura do Projeto

```
controle-contas/
├── app.py                    # App principal com lógica de interface e navegação
├── estilo.py                # Estilo visual customizado para o Streamlit
├── relatorio_utils.py       # Geração de relatórios financeiros com gráficos e PDF
├── supabase_utils.py        # Módulo de integração com Supabase (CRUD via REST API)
├── requirements.txt         # Lista de bibliotecas necessárias
├── mockupstreamlit.html     # Protótipo HTML da interface para referência visual
└── assets/
    ├── bg_1.png             # Imagem de fundo principal usada na tela inicial
    └── bg_2.png             # Imagem alternativa de fundo (opcional)
```

---

## 📦 Dependências Necessárias

```txt
streamlit
pandas
openpyxl
fpdf2
matplotlib
numpy
requests
python-dateutil
```

Essas bibliotecas são carregadas automaticamente pelo ambiente do Streamlit Cloud com base neste `requirements.txt`.


