# Guia de Uso — Telemetria Veicular (OBD-II)

Este guia explica como usar o sistema **como um produto real**: criar conta, cadastrar
rotas de telemetria e explorar o dashboard, os eventos, o gráfico, o mapa e a comparação.

---

## Visão geral

```
Login → Cadastrar Rota (CSV) → Análise automática → Dashboard / Eventos / Gráfico / Mapa
```

- **API** (`projeto_api`): recebe, padroniza, armazena e analisa os dados.
- **Banco** (PostgreSQL): persiste tudo.
- **Interface** (`projeto_interface`): tela para o usuário operar.

---

## 1. Subir o sistema

```bash
cd projeto_api
docker compose up --build -d   # sobe API (8080) + banco (5432)
```

A API fica em `http://localhost:8080/telemetria`.

```bash
cd projeto_interface
pip install tkintermapview      # necessário para a aba Mapa
python main.py
```

---

## 2. Primeiro acesso (cadastro e login)

1. Na tela de login, clique em **Criar conta**.
2. Digite um usuário e uma senha (mínimo de **6 caracteres**), com a confirmação.
3. Entre com essas credenciais.

> O primeiro usuário é criado por você (nenhum usuário é pré-cadastrado).

---

## 3. Cadastrar uma rota (o "cadastro" em lote)

Na aba **Rotas**, clique em **Cadastrar Rota (CSV)**:
1. Selecione o arquivo `.csv` de telemetria.
2. Dê um nome para a rota (ex.: "Rota 1").
3. O sistema importa as leituras, padronizando os nomes das colunas.

> Colunas não reconhecidas são ignoradas; frames duplicados são descartados.
> A análise é feita **automaticamente** (não há botão "Analisar").

---

## 4. Explorar os resultados (abas)

Ao selecionar uma rota, cada aba se atualiza automaticamente:

| Aba | O que mostra |
|---|---|
| **Rotas** | lista de rotas; cadastrar, renomear e excluir |
| **Dashboard** | score de segurança (0–100), duração, distância, velocidades, RPM, eventos por tipo |
| **Eventos** | tabela dos eventos de risco, com **filtro por tipo** |
| **Gráfico** | painel com velocidade, Força G e RPM, e os trechos de risco coloridos por tipo |
| **Mapa** | trajeto GPS (OpenStreetMap) com os trechos de risco marcados |
| **Comparar** | compara o resumo (score e estatísticas) de duas rotas |
| **Configurações** | ajusta os limiares de detecção (velocidade, RPM, aceleração, etc.) |

> No **Dashboard**, use **Exportar Relatório (CSV)** para gerar um arquivo com as
> estatísticas e os eventos da rota.

---

## 5. Comandos úteis

```bash
# Parar / subir os containers
docker compose down
docker compose up -d

# Rebuild (se mudou o código)
docker compose up --build -d

# Popular com os CSVs de exemplo (após criar o usuário pela interface)
cd projeto_api && python seed.py

# Rodar os testes
python test_api.py
```
