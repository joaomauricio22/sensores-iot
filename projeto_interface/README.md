# Interface Gráfica — Sensores IoT

Interface gráfica em **Tkinter** (projeto separado da API) para o sistema de
análise de dados de sensores IoT.

## Requisitos
- Python 3
- `requests` (instalado com `pip install requests`)
- A API REST em execução (ver `../projeto_api`)

## Como executar
1. Suba a API (na porta 8080).
2. Execute a interface:
   ```bash
   python main.py
   ```

## Estrutura
- `main.py` — janela principal com abas (Notebook).
- `tabs.py` — classe base `CrudTab` e as telas de cada entidade.
- `api_client.py` — cliente HTTP que encapsula a comunicação com a API.

## Telas
Cada aba oferece as operações de **Cadastro, Edição, Seleção (Buscar) e
Exclusão** para a entidade correspondente, além de:
- **Sensores**: botão "Estatísticas" (análise histórica);
- **Leituras**: botões "Detectar Anomalias" e "Classificar (ML)".
