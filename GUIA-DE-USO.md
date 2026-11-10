# Guia de Uso — Sentinela (Telemetria Veicular OBD-II)

Este guia explica como usar o sistema como um produto real: cadastrar rotas de
telemetria, gerenciar leituras e eventos, e explorar o dashboard, o gráfico, a
análise por sensor e a comparação.

---

## Visão geral

```
Cadastrar Rota (CSV) → Análise automática → Visão Geral / Eventos / Gráfico / Sensores
```

- **API** (`projeto_api`): recebe, padroniza, armazena e analisa os dados.
- **Banco** (PostgreSQL): persiste tudo. Começa **vazio**.
- **Interface** (`projeto_interface`): tela para operar o sistema (cliente da API).

---

## 1. Subir o sistema

```bash
cd projeto_api
docker compose up --build -d   # sobe API (8080) + banco (5432)
```

A API fica em `http://localhost:8080/telemetria`.

```bash
cd projeto_interface
python main.py
```

---

## 2. Cadastrar uma rota (o "cadastro" em lote)

Na seção **Dados → Rotas**:

1. Clique em **Nova Rota** e selecione o arquivo `.csv` de telemetria.
2. Dê um nome para a rota (ex.: "Rota 1").
3. O sistema importa as leituras, **padroniza os nomes das colunas** e **limpa** os dados
   (spikes de acelerômetro, velocidades implausíveis e excesso de leituras paradas).

> Colunas não reconhecidas são ignoradas; frames duplicados são descartados.
> A análise é feita **automaticamente** (não há botão "Analisar").
> O botão **Nova Rota** faz o cadastro importando o CSV (o "cadastro" em lote).

---

## 3. Gerenciar os dados (CRUD por tabela)

Na seção **Dados**, as três tabelas do sistema têm operações de **criar, ler, editar e excluir**:

| Sub-aba | O que permite |
|---|---|
| **Rotas** | criar (via CSV), editar nome/origem e excluir |
| **Leituras** | criar/editar um frame (rota, data/hora e valores dos sensores) e excluir |
| **Eventos** | criar/editar/excluir um evento de risco (canal, valor, método, classificação) |

> Excluir uma rota remove, em cascata, suas leituras e eventos (o sistema avisa antes).

---

## 4. Explorar os resultados

Ao selecionar uma rota na barra superior, cada seção se atualiza:

| Seção | O que mostra |
|---|---|
| **Dados** | CRUD das tabelas rota, leitura e evento_risco |
| **Visão Geral** | score de segurança (0–100), duração, distância, velocidades, RPM, eventos por tipo e **exportação CSV** |
| **Gráfico** | painel com velocidade, Força G e RPM; linhas tracejadas = limiares do JSON; passe o mouse para ver os valores |
| **Sensores** | estatísticas (mín/máx/média) e % de leituras fora do limiar por sensor |
| **Comparar** | compara o resumo (score e estatísticas) de duas rotas |

> Na **Visão Geral**, use **Exportar Relatório (CSV)** para gerar um arquivo com as
> estatísticas e os eventos da rota.

---

## 5. Ajustar os limiares (fora da interface)

Os limiares de detecção e o catálogo de sensores ficam no arquivo
`projeto_api/config/limiares.json` (fonte única, somente leitura pela API).

Para ver os valores atuais:

```bash
curl http://localhost:8080/telemetria/limiares
curl http://localhost:8080/telemetria/sensores
```

Após editar o JSON, **reanalise** as rotas para aplicar os novos limites:

```bash
cd projeto_api
python reanalisar.py
```

---

## 6. Comandos úteis

```bash
# Parar / subir os containers
docker compose down
docker compose up -d

# Rebuild (se mudou o código)
docker compose up --build -d

# Popular com os CSVs de exemplo (opcional; exige banco vazio)
cd projeto_api && python seed.py

# Reanalisar com os limiares atuais
python reanalisar.py

# Avaliar o detector de ML
python avaliar_ml.py

# Rodar os testes
python test_api.py
python test_limpeza.py
```
