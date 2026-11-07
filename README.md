# Trabalho PAV — Telemetria Veicular (OBD-II) e Detecção de Eventos de Risco

Sistema para **receber, padronizar, armazenar e analisar dados de telemetria veicular**
coletados via interface **OBD-II**, identificando **eventos de condução de risco**
(frenagens bruscas, acelerações intensas, curvas fechadas).

- **Aluno:** João Maurício Araújo Leitão
- **Modalidade:** Individual
- **Tecnologias:** Python, Flask (Flask-RESTful), SQLAlchemy, PostgreSQL, scikit-learn, matplotlib, Tkinter, Docker

## Estrutura do projeto

```
Trabalho_PAV/
├── projeto_api/            # Partes 2, 3 e 5 (modelos, API e Docker)
│   ├── entities/           # Classes de modelo (SQLAlchemy)
│   ├── repositories/       # Operações no banco de dados
│   ├── services/           # Regras de negócio + importação + análise
│   │   ├── detectors/      # Detectores de risco (herança/polimorfismo)
│   │   ├── features.py     # Extração de atributos (Força G, aceleração, instabilidade)
│   │   └── ImportadorService.py  # Importação e padronização dos CSVs
│   ├── controllers/        # Recebimento das requisições HTTP
│   ├── routes/             # Mapeamento de URLs
│   ├── config/             # Configuração (conexão com o banco)
│   ├── app.py              # Ponto de entrada da API
│   ├── init.sql            # Script de criação do banco
│   ├── seed.py             # Importa os CSVs como rotas do primeiro usuário
│   ├── test_api.py         # Testes dos endpoints e regras
│   ├── dados/              # Arquivos CSV de telemetria (não versionados)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── projeto_interface/      # Parte 4 (interface gráfica Tkinter)
│   ├── main.py             # Login + janela principal
│   ├── tabs.py             # Abas: Rotas, Eventos de Risco e Gráfico
│   └── api_client.py
│
└── apresentacao/           # Parte 6 (apresentação)
    └── slides_pav.pptx
```

## Modelo de dados (4 tabelas)

```
Usuario 1 ── N Rota 1 ── N Leitura 1 ── N EventoRisco
```

| Tabela | Descrição |
|---|---|
| `usuario` | Usuário com acesso ao sistema (nome + senha) |
| `rota` | Uma viagem importada (nome, arquivo de origem) |
| `leitura` | Frame de telemetria (velocidade, rpm, acelerações, ...) |
| `evento_risco` | Evento de risco detectado (Força G, instabilidade, método) |

## Regras de negócio (10)

> Neste domínio, cada **sensor** corresponde a um canal de medição do veículo
> (velocidade, RPM, aceleração X/Y/Z), e cada **leitura** é um frame de telemetria.

1. **Identificação do sensor:** cada sensor deve possuir um identificador único no sistema.
2. **Dados obrigatórios da leitura:** uma leitura só poderá ser registrada se possuir sensor, valor medido e data/hora da coleta.
3. **Sensor cadastrado:** o sistema não deve permitir o registro de uma leitura associada a um sensor que não esteja cadastrado.
4. **Valores válidos:** o sistema não deve armazenar leituras com valores que não sejam numéricos ou que estejam incompatíveis com o tipo de dado produzido pelo sensor.
5. **Leituras duplicadas:** o sistema não deve considerar como nova leitura duas medições do mesmo sensor com o mesmo valor e o mesmo instante de coleta.
6. **Limites de operação:** cada sensor deve possuir limites mínimo e máximo de referência para suas medições, de acordo com seu tipo.
7. **Identificação de anomalias:** uma leitura que ultrapasse os limites de referência ou apresente comportamento significativamente diferente do padrão histórico deve ser identificada como potencialmente anômala.
8. **Classificação pelo modelo:** as leituras submetidas ao modelo de Machine Learning devem receber uma classificação indicando comportamento normal ou potencialmente anômalo.
9. **Registro das anomalias:** toda anomalia identificada deve manter informações sobre o sensor, valor, data/hora e método utilizado para sua identificação.
10. **Análise histórica:** o sistema deve utilizar dados históricos dos sensores para calcular padrões estatísticos e fornecer informações utilizadas na identificação de comportamentos anormais.

## Detecção de risco (3 métodos)

- **LIMITE** — aceleração longitudinal fora dos limites do CTB (+2,5 / -3,0 m/s²).
- **ESTATISTICO** — z-score da Força G em relação ao histórico.
- **MODELO_ML** — DBSCAN (pseudo-rótulos) + RandomForest.

A Força G resultante é `√(ax² + ay²)`; a instabilidade é o desvio padrão da aceleração
numa janela de ~3 s.

## Como executar

```bash
cd projeto_api
docker compose up --build -d    # sobe API (8080) + banco (5432)
```

A API fica em `http://localhost:8080/telemetria`.

Interface gráfica (roda fora do container):

```bash
cd projeto_interface
python main.py
```

Na interface: **crie uma conta** → entre → **importe um CSV** (dê um nome) → **analise** →
veja o **gráfico** da Força G com os trechos de risco.

Para popular os dados de exemplo (após criar o usuário pela interface):

```bash
cd projeto_api
python seed.py
```

## Endpoints principais

| Método | Rota | Descrição |
|---|---|---|
| GET/POST | `/telemetria/usuarios` | Listar / cadastrar usuários |
| POST | `/telemetria/usuarios/login` | Autenticação |
| GET/POST | `/telemetria/rotas` | Listar / cadastrar rotas |
| POST | `/telemetria/rotas/importar` | Importar CSV como rota |
| GET/PUT/DELETE | `/telemetria/rotas/<id>` | Selecionar / renomear / excluir |
| POST | `/telemetria/rotas/<id>/analisar` | Detecção de eventos de risco |
| GET | `/telemetria/rotas/<id>/grafico` | Dados para o gráfico |
| GET/POST | `/telemetria/leituras` | Listar / cadastrar leituras |
| GET/POST | `/telemetria/eventos-risco` | Listar / cadastrar eventos |
