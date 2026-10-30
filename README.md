# Trabalho PAV — Análise de Dados de Sensores IoT

Sistema para **receber, armazenar e consultar dados produzidos por sensores IoT**,
realizando o tratamento e a análise dos dados para **identificar valores anormais**.

- **Aluno:** João Maurício Araújo Leitão
- **Modalidade:** Individual
- **Tecnologias:** Python, Flask (Flask-RESTful), SQLAlchemy, PostgreSQL, scikit-learn, Tkinter, Docker

## Estrutura do projeto

```
Trabalho_PAV/
├── projeto_api/            # Partes 2, 3 e 5 (modelos, API e Docker)
│   ├── entities/           # Classes de modelo (SQLAlchemy)
│   ├── repositories/       # Operações no banco de dados
│   ├── services/           # Regras de negócio + detectores de anomalia + ML
│   ├── controllers/        # Recebimento das requisições HTTP (schemas + Resources)
│   ├── routes/             # Mapeamento de URLs
│   ├── config/             # Configuração (conexão com o banco)
│   ├── app.py              # Ponto de entrada da API
│   ├── init.sql            # Script de criação do banco
│   ├── seed.py             # Carga de dados de exemplo
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
    ├── slides_pav.pptx     # Slides prontos
    ├── gerar_slides.py     # Script que gera os slides
    ├── roteiro-apresentacao.md
    └── imgs/               # Capturas das telas
```

## Documentação de apoio

- **`ROTEIRO-DEFESA.md`** — guia de estudo para a apresentação/arguição: onde cada requisito foi implementado e respostas para as perguntas prováveis do professor.
- **`GUIA-DE-USO.md`** — como usar o sistema no dia a dia (configuração inicial + operação contínua).
- **`AUTOAVALIACAO.md`** — questionário com respostas para treinar a explicação do código.

## Modelo de dados (4 tabelas)

```
TipoSensor 1 ──── N Sensor 1 ──── N Leitura 1 ──── N Anomalia
```

| Tabela | Descrição |
|---|---|
| `tipo_sensor` | Tipo de dado produzido (nome, unidade, descrição) |
| `sensor` | Sensor com identificador único e limites mín/máx |
| `leitura` | Medição (sensor, valor, data/hora, classificação) |
| `anomalia` | Registro de anomalia (sensor, valor, data/hora, método) |

## Regras de negócio (10)

1. Sensor com identificador único.
2. Leitura exige sensor, valor e data/hora.
3. Leitura apenas para sensor cadastrado.
4. Valor numérico e finito.
5. Sem leituras duplicadas (sensor + valor + instante).
6. Limites mínimo/máximo por sensor.
7. Anomalia = fora dos limites ou desvio do histórico.
8. Classificação pelo modelo de ML.
9. Registro da anomalia com o método de identificação.
10. Análise histórica (padrões estatísticos).

## Como executar (com Docker — Parte 5)

```bash
cd projeto_api
docker compose up --build
```

- API: http://localhost:8080/iot
- Banco: PostgreSQL na porta 5432 (script `init.sql` aplicado automaticamente).

A interface gráfica roda **fora** do container:

```bash
cd projeto_interface
python main.py
```

## Como executar (sem Docker, para desenvolvimento)

1. Crie o banco PostgreSQL e aplique o script:
   ```bash
   psql -U postgres -c "CREATE DATABASE iot_sensores;"
   psql -U postgres -d iot_sensores -f init.sql
   ```
2. Instale as dependências e suba a API:
   ```bash
   cd projeto_api
   pip install -r requirements.txt
   python app.py
   ```
3. (Opcional) Popule dados de exemplo:
   ```bash
   python seed.py
   ```

## Endpoints principais

| Método | Rota | Descrição |
|---|---|---|
| GET/POST | `/iot/tipos-sensor` | Listar / cadastrar tipos |
| GET/PUT/DELETE | `/iot/tipos-sensor/<id>` | Selecionar / editar / excluir tipo |
| GET/POST | `/iot/sensores` | Listar / cadastrar sensores |
| GET/PUT/DELETE | `/iot/sensores/<id>` | Selecionar / editar / excluir sensor |
| GET | `/iot/sensores/<id>/estatisticas` | Padrões estatísticos (regra 10) |
| GET/POST | `/iot/leituras` | Listar / cadastrar leituras |
| GET/PUT/DELETE | `/iot/leituras/<id>` | Selecionar / editar / excluir leitura |
| POST | `/iot/leituras/<id>/analisar` | Detecção de anomalias (regra 7 e 9) |
| POST | `/iot/leituras/<id>/classificar` | Classificação pelo ML (regra 8) |
| GET/POST | `/iot/anomalias` | Listar / cadastrar anomalias |
| GET/PUT/DELETE | `/iot/anomalias/<id>` | Selecionar / editar / excluir anomalia |

## Detecção de anomalias (3 métodos)

- **LIMITE** — valor fora dos limites mínimo/máximo.
- **ESTATISTICO** — z-score (|z| > 3) em relação ao histórico.
- **MODELO_ML** — `IsolationForest` (scikit-learn) treinado com o histórico.
