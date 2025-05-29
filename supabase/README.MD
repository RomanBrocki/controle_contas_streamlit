# 🔌 Módulo `supabase/`

Este módulo centraliza a comunicação com a API REST do Supabase utilizada no projeto.

---

## Arquivos

### `supabase_config.py`

Contém:

* `SUPABASE_URL`
* `SUPABASE_KEY`
* `TABELA`
* `HEADERS`

Essas variáveis são lidas de `st.secrets[...]` (no ambiente Streamlit Cloud ou local via `.streamlit/secrets.toml`).

---

### `supabase_utils.py`

Funções de interação com o Supabase, incluindo:

* `carregar_tabela`
* `salvar_conta` (insere ou edita)
* `excluir_conta`
* `get_nomes_conta_unicos`
* `carregar_mes_referente`
* `get_anos_meses_disponiveis`

---

## Importação recomendada

```python
from supabase import carregar_tabela, salvar_conta
```

Responsável pela comunicação com o Supabase:

* `supabase_utils.py`: funções REST para carregar, salvar e excluir contas
* `supabase_config.py`: configuração de acesso via URL e chave

### 📁 assets/README.md

Contém recursos visuais estáticos, como a imagem de fundo da tela inicial.

---

Pronto para ser executado diretamente na nuvem com visual moderno, funcionalidade prática e histórico persistente.
