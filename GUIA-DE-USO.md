# Guia de Uso — Telemetria Veicular (OBD-II)

Este guia explica como usar o sistema **como uma ferramenta real de monitoramento de frota**,
desde a configuração até a análise dos eventos de risco.

---

## Visão geral

```
OBD-II (veículo) ──(CSV/telemetria)──▶ Importador ──▶ API REST ──▶ PostgreSQL
                                                        ▲
                                                        │
                                            Interface Gráfica (Tkinter)
```

- **API** (`projeto_api`): recebe, padroniza, armazena e analisa os dados.
- **Banco** (PostgreSQL): persiste tudo.
- **Interface** (`projeto_interface`): tela para o usuário operar.

---

## 1. Subir o sistema

```bash
cd projeto_api
docker compose up --build -d   # sobe API (8080) + banco (5432)

# Popular com os parâmetros canônicos, mapeamentos e importar os CSVs
python seed.py
```

A API fica em `http://localhost:8080/telemetria`.

Abra a interface em **outro terminal**:

```bash
cd projeto_interface
python main.py
```

---

## 2. Configuração (catálogo de parâmetros + padronização)

O `seed.py` já cria:

1. **Parâmetros canônicos** (`/parametros`): velocidade, rpm, accel_x/y/z, posição do acelerador, latitude, longitude — cada um com unidade e limites.
2. **Mapeamentos** (`/mapeamentos`): a padronização que traduz os nomes brutos das colunas
   (`Vehicle speed (km/h)`, `Velocidade do veículo (km/h)`, ...) para os parâmetros canônicos.
3. **Veículos** (`/veiculos`): um por arquivo CSV importado.

> É aqui que entra a **padronização**: se um novo arquivo usar outro nome para a mesma
> grandeza, basta adicionar um mapeamento na aba "Mapeamentos".

---

## 3. Importar novos dados (o dia a dia)

Quando chega um novo arquivo de telemetria:

```python
# Exemplo programático (ou via um script próprio)
from services.ImportadorService import ImportadorService
imp.importar_csv("novo_arquivo.csv", "VEICULO-005", "CSVLog")
```

Ou, na prática, adicione o arquivo em `seed.py` e rode `python seed.py`.

O importador:
- Lê o `StartTime` e a coluna `Time (sec)` para calcular a data/hora real de cada frame.
- Traduz cada coluna pelo mapeamento (colunas não mapeadas são **ignoradas**).
- Descarta frames duplicados (mesmo veículo + instante).

---

## 4. Analisar (detecção de eventos de risco)

- **Interface**: aba "Veículos" → digite o ID → **Detectar Riscos**.
- **API**: `POST /telemetria/veiculos/<id>/analisar`.

O sistema roda os 3 métodos e grava em "Eventos de Risco":
- `LIMITE` — Força G acima de 0,5 g.
- `ESTATISTICO` — z-score da Força G acima de 3.
- `MODELO_ML` — DBSCAN + RandomForest.

---

## 5. Monitorar

- Aba **Eventos de Risco** → veja os eventos detectados e o método de cada um.
- Aba **Veículos** → **Estatísticas** → Força G média/máxima/desvio do histórico.

---

## 6. Comandos úteis

```bash
# Parar / subir os containers
docker compose down
docker compose up -d

# Rebuild (se mudou o código)
docker compose up --build -d

# Popular/importar os CSVs
cd projeto_api && python seed.py

# Rodar os testes
python test_api.py
```
