# Trabalho PAV — Telemetria Veicular (OBD-II) e Detecção de Eventos de Risco

Sistema para **receber, padronizar, armazenar e analisar dados de telemetria veicular**
coletados via interface **OBD-II**, identificando **eventos de condução de risco**
(frenagens bruscas, acelerações intensas, curvas fechadas).

O pipeline de análise integra aprendizagem **não supervisionada (DBSCAN)** e
**supervisionada (RandomForest)**, inspirado em pesquisa de Iniciação Científica
desenvolvida no INMETRO.

- **Aluno:** João Maurício Araújo Leitão
- **Modalidade:** Individual
- **Tecnologias:** Python, Flask (Flask-RESTful), SQLAlchemy, PostgreSQL, scikit-learn, Tkinter, Docker

## Estrutura do projeto

```
Trabalho_PAV/
├── projeto_api/            # Partes 2, 3 e 5 (modelos, API e Docker)
│   ├── entities/           # Classes de modelo (SQLAlchemy)
│   ├── repositories/       # Operações no banco de dados
│   ├── services/           # Regras de negócio + importação + análise
│   │   ├── detectors/      # Detectores de risco (herança/polimorfismo)
│   │   ├── features.py     # Extração de atributos (Força G, instabilidade)
│   │   └── ImportadorService.py  # Padronização de parâmetros dos CSVs
│   ├── controllers/        # Recebimento das requisições HTTP
│   ├── routes/             # Mapeamento de URLs
│   ├── config/             # Configuração (conexão com o banco)
│   ├── app.py              # Ponto de entrada da API
│   ├── init.sql            # Script de criação do banco
│   ├── seed.py             # Cria catálogo/mapa e importa os CSVs reais
│   ├── test_api.py         # Testes dos endpoints e regras
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── projeto_interface/      # Parte 4 (interface gráfica Tkinter)
│   ├── main.py
│   ├── tabs.py
│   ├── api_client.py
│   └── README.md
│
└── apresentacao/           # Parte 6 (apresentação)
    └── slides_pav.pptx
```

## Modelo de dados (5 tabelas)

```
Parametro 1 ── N MapeamentoParametro
Veiculo 1 ── N Leitura 1 ── N EventoRisco
```

| Tabela | Descrição |
|---|---|
| `veiculo` | Veículo monitorado (identificador único, modelo) |
| `parametro` | Catálogo de parâmetros canônicos (nome, unidade, limites) |
| `mapeamento_parametro` | Padronização: nome bruto da coluna → parâmetro canônico |
| `leitura` | Frame de telemetria (velocidade, rpm, acelerações, ...) |
| `evento_risco` | Evento de risco detectado (Força G, instabilidade, método) |

## Padronização de parâmetros

Fontes diferentes nomeiam a mesma grandeza de formas distintas (ex.: `Vehicle speed
(km/h)` e `Velocidade do veículo (km/h)`). A tabela `mapeamento_parametro` traduz cada
nome bruto para um parâmetro canônico; colunas não mapeadas são ignoradas na importação.

## Regras de negócio (10)

1. Veículo com identificador único.
2. Leitura (frame) exige veículo e data/hora.
3. Leitura apenas para veículo cadastrado.
4. Valores numéricos e finitos.
5. Sem frames duplicados (mesmo veículo + instante).
6. Limites de referência por parâmetro.
7. Evento de risco = Força G acima do limiar **ou** desvio do histórico.
8. Classificação pelo modelo de ML.
9. Registro do evento (veículo, valores, data/hora, método).
10. Análise histórica (estatísticas de condução).

## Detecção de risco (3 métodos)

- **LIMITE** — Força G resultante acima do limiar físico (0,5 g).
- **ESTATISTICO** — z-score da Força G em relação ao histórico.
- **MODELO_ML** — DBSCAN (pseudo-rótulos) + RandomForest.

A Força G resultante é `√(ax² + ay² + az²) / 9,81`; a instabilidade é o desvio padrão
da aceleração numa janela de ~3 s.

## Como executar (com Docker)

```bash
cd projeto_api
docker compose up --build -d        # sobe API (8080) + banco (5432)
python seed.py                      # cria catálogo/mapa e importa os CSVs
```

- API: http://localhost:8080/telemetria

Interface gráfica (roda fora do container):

```bash
cd projeto_interface
python main.py
```

## Endpoints principais

| Método | Rota | Descrição |
|---|---|---|
| GET/POST | `/telemetria/veiculos` | Listar / cadastrar veículos |
| GET/PUT/DELETE | `/telemetria/veiculos/<id>` | Selecionar / editar / excluir |
| GET | `/telemetria/veiculos/<id>/estatisticas` | Estatísticas de condução (regra 10) |
| POST | `/telemetria/veiculos/<id>/analisar` | Detecção de eventos de risco (7, 8, 9) |
| GET/POST | `/telemetria/parametros` | Listar / cadastrar parâmetros |
| GET/POST | `/telemetria/mapeamentos` | Listar / cadastrar mapeamentos |
| GET/POST | `/telemetria/leituras` | Listar / cadastrar leituras |
| GET/POST | `/telemetria/eventos-risco` | Listar / cadastrar eventos |
