# 🧩 Módulo `interface/`

Este módulo contém as funções relacionadas à interface e controle visual do app principal de Controle de Contas.

---

## 📁 Arquivos

### `app_utils.py`

Agrupa os componentes visuais e formulários:

* `exibir_cabecalho_mes()`
* `exibir_formulario_conta()`
* `exibir_contas_mes()`

### `navegacao.py`

Controla a navegação entre telas do app:

* `ir_para_mes_vigente()`
* `ir_para_historico()`
* `voltar_tela_inicial()`

### `app_vars.py`

Inicializa variáveis de controle da sessão do Streamlit:

* `inicializar_sessao()`

---

## 🔁 Como importar no `app.py`

```python
from interface import (
    inicializar_sessao,
    ir_para_mes_vigente,
    ir_para_historico,
    voltar_tela_inicial,
    exibir_cabecalho_mes,
    exibir_formulario_conta,
    exibir_contas_mes,
)
```

### 📁 assets/README.md

Contém recursos visuais estáticos, como a imagem de fundo da tela inicial.

---

Pronto para ser executado diretamente na nuvem com visual moderno, funcionalidade prática e histórico persistente.
