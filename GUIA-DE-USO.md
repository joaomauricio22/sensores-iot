# Guia de Uso — Análise de Dados de Sensores IoT

Este guia explica como usar o sistema **como uma ferramenta real do dia a dia**,
desde a configuração inicial até a operação contínua de monitoramento.

---

## Visão geral do sistema

O sistema tem 3 partes que trabalham juntas:

```
Sensores IoT ──(leituras)──▶ API REST ──▶ PostgreSQL
                                ▲
                                │
                      Interface Gráfica (Tkinter)
```

- **API** (`projeto_api`): recebe, valida, armazena e analisa os dados.
- **Banco** (PostgreSQL): persiste tudo.
- **Interface** (`projeto_interface`): tela para o usuário operar.

---

## 1. Subir o sistema (1 vez por sessão)

```bash
# Na pasta projeto_api — sobe API + banco em containers
docker compose up -d

# Ver se está tudo no ar
docker ps
```

A API fica em `http://localhost:8080/iot` e o banco na porta `5432`.

Depois, abra a interface em **outro terminal**:

```bash
# Na pasta projeto_interface
python main.py
```

---

## 2. Configuração inicial (feita 1 vez)

É o "cadastro mestre". Antes de qualquer leitura, o sistema precisa saber:

### 2.1 Cadastrar os tipos de medição
Na aba **Tipos de Sensor** → preencha e clique **Cadastrar**:
- **Temperatura** — unidade `°C`
- **Umidade** — unidade `%`

### 2.2 Cadastrar os sensores
Na aba **Sensores** → preencha e clique **Cadastrar**:
- `SENSOR-001` (Temperatura), limites **10** a **40**
- `SENSOR-002` (Umidade), limites **20** a **80**

> O sistema já impede: identificador duplicado, tipo inexistente e limite mínimo maior que o máximo.

---

## 3. Operação diária (o que acontece todo dia)

### 3.1 Receber as leituras
Na prática, um dispositivo IoT (ou um script) envia as medições para a API.
Cada leitura é **validada automaticamente**; se estiver errada, é recusada.

Exemplo de leitura (o que o sensor manda):
```json
{ "sensor_id": 1, "valor": 25.4, "data_hora": "2026-10-30T14:00:00" }
```

Na interface, isso equivale a: aba **Leituras** → preencher → **Cadastrar**.

O que o sistema faz sozinho (sem você perceber):
- recusa valor não numérico;
- recusa leitura de sensor não cadastrado;
- recusa leitura duplicada (mesmo sensor + valor + instante).

### 3.2 Rodar a análise
De tempos em tempos (ou quando algo parece estranho):

- Aba **Leituras** → digite o ID da leitura → **Detectar Anomalias** → o sistema roda os 3 métodos e grava o resultado.
- Aba **Leituras** → **Classificar (ML)** → o modelo diz se é `NORMAL` ou `ANOMALO`.

### 3.3 Monitorar
- Aba **Anomalias** → veja tudo o que saiu do padrão e **qual método** detectou.
- Aba **Sensores** → digite o ID → **Estatísticas** → veja média, desvio padrão, mín/máx e total de anomalias do histórico.

### 3.4 Agir
Quando uma anomalia aparece (ex.: leitura de 75 °C num sensor cujo limite é 40), você vai verificar o equipamento físico. O sistema **aponta o problema**, você **toma a decisão**.

---

## 4. Fluxo completo de exemplo

Cenário: o sensor de temperatura da "Sala A" está com defeito.

1. **Receber** a leitura `{sensor 1, valor 75, 16:05}`.
2. **Analisar** essa leitura → o sistema detecta:
   - `LIMITE` (75 > 40);
   - `ESTATÍSTICO` (z-score alto);
   - `MODELO_ML` (IsolationForest marca como anômalo).
3. **Consultar** a aba Anomalias → vejo as 3 ocorrências.
4. **Verificar** o sensor fisicamente → estava coberto de poeira.

---

## 5. Comandos úteis de manutenção

```bash
# Parar os containers
docker compose down

# Subir de novo (sem rebuild)
docker compose up -d

# Rebuild (se mudou o código)
docker compose up --build -d

# Ver logs da API
docker compose logs api

# Popular dados de exemplo
cd projeto_api && python seed.py

# Preparar dados para demonstração (análise + classificação)
python preparar_demo.py

# Rodar os testes da API
python test_api.py
```

---

## 6. Como funciona sem Docker (desenvolvimento)

```bash
# 1. Instalar dependências
cd projeto_api
pip install -r requirements.txt

# 2. Subir um PostgreSQL (qualquer um) e criar o banco + tabelas
psql -U postgres -c "CREATE DATABASE iot_sensores;"
psql -U postgres -d iot_sensores -f init.sql

# 3. Subir a API (porta 8080)
python app.py

# 4. Em outro terminal, abrir a interface
cd ../projeto_interface
python main.py
```

> A variável de ambiente `DATABASE_URI` permite apontar para outro banco, se precisar.
