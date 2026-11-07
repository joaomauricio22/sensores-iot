# Guia de Uso — Telemetria Veicular (OBD-II)

Este guia explica como usar o sistema **como um produto real**: criar conta, importar
rotas de telemetria e visualizar o comportamento de risco no gráfico.

---

## Visão geral

```
Login → Importar CSV (rota) → Analisar → Gráfico com trechos de risco
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
python main.py
```

---

## 2. Primeiro acesso (cadastro e login)

1. Na tela de login, clique em **Criar conta**.
2. Digite um usuário e uma senha.
3. Entre com essas credenciais.

> O primeiro usuário é criado por você (nenhum usuário é pré-cadastrado).

---

## 3. Importar uma rota (o "cadastro")

Na aba **Rotas**, clique em **Importar CSV**:
1. Selecione o arquivo `.csv` de telemetria.
2. Dê um nome para a rota (ex.: "Rota 1").
3. O sistema importa as leituras, padronizando os nomes das colunas.

> Colunas não reconhecidas são ignoradas; frames duplicados são descartados.

---

## 4. Analisar e visualizar

1. Na aba **Rotas**, selecione a rota e clique em **Analisar**.
2. Os eventos de risco aparecem na aba **Eventos de Risco**.
3. Na aba **Gráfico**, clique em **Plotar Gráfico** para ver a **Força G ao longo
   do tempo**, com a linha do limite (CTB) e os **trechos de risco em vermelho**.

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
