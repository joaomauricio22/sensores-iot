# Trabalho PAV — Telemetria Veicular (OBD-II) e Detecção de Eventos de Risco

Sistema para **receber, padronizar, armazenar e analisar dados de telemetria veicular**
coletados via interface **OBD-II**, identificando e **classificando** eventos de condução
de risco (frenagens bruscas, acelerações intensas, curvas em alta velocidade, excesso de
velocidade, RPM excessivo e acelerador brusco), com **score de segurança** do condutor.

- **Aluno:** João Maurício Araújo Leitão
- **Modalidade:** Individual
- **Tecnologias:** Python, Flask (Flask-RESTful), SQLAlchemy, PostgreSQL, scikit-learn, matplotlib, tkintermapview, Tkinter, Docker

## Estrutura do projeto

```
Trabalho_PAV/
├── projeto_api/            # Modelos, API, análise e Docker
│   ├── entities/           # Classes de modelo (SQLAlchemy)
│   ├── repositories/       # Operações no banco de dados
│   ├── services/           # Regras de negócio + importação + análise
│   │   ├── detectors/      # Detectores de risco (herança/polimorfismo)
│   │   ├── features.py     # Extração de atributos (Força G, aceleração, instabilidade)
│   │   ├── ImportadorService.py   # Importação, padronização e limpeza dos CSVs
│   │   ├── LimiaresService.py     # Leitura/validação de config/limiares.json
│   │   └── limpeza.py             # Regras de limpeza dos dados brutos
│   ├── controllers/        # Recebimento das requisições HTTP
│   ├── routes/             # Mapeamento de URLs
│   ├── config/             # limiares.json (fonte única dos limites e sensores)
│   ├── app.py              # Ponto de entrada da API
│   ├── settings.py         # Configuração da conexão com o banco
│   ├── init.sql            # Script de criação do banco
│   ├── seed.py             # Importa os CSVs (opcional; o banco começa vazio)
│   ├── reanalisar.py       # Reanalisa as rotas com os limiares atuais
│   ├── avaliar_ml.py       # Métricas do detector de ML (precisão/recall/F1/silhouette)
│   ├── test_api.py         # Testes dos endpoints e regras
│   ├── test_limpeza.py     # Testes unitários da limpeza
│   ├── dados/              # Arquivos CSV de telemetria (não versionados)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── projeto_interface/      # Interface gráfica Tkinter (separada da API)
│   ├── main.py             # Janela principal com navegação lateral
│   ├── tabs.py             # Seções: Dados (Rotas/Leituras/Eventos), Visão Geral, Gráfico, Mapa, Comparar
│   ├── api_client.py       # Cliente HTTP
│   └── capturar_telas.py   # Gera as capturas para os slides
│
└── apresentacao/           # Apresentação (slides)
    └── slides_pav.pptx
```

## Modelo de dados (3 tabelas)

```
rota 1 ── N leitura 1 ── N evento_risco
```

| Tabela | Descrição |
|---|---|
| `rota` | Uma viagem monitorada (nome + arquivo de origem + data de importação) |
| `leitura` | Frame de telemetria: valores dos sensores em um instante (velocidade, RPM, aceleração X/Y/Z, acelerador, GPS) |
| `evento_risco` | Evento de risco detectado (canal/sensor, valor, Força G, instabilidade, classificação, método, instante) |

- **Integridade:** chaves estrangeiras com `ON DELETE CASCADE` (excluir uma rota remove
  leituras e eventos; excluir uma leitura remove seus eventos).
- **Restrições únicas:** `leitura (rota_id, data_hora)` evita frames duplicados;
  `evento_risco (leitura_id, metodo, classificacao, canal)` evita eventos repetidos.
- Os **limiares de detecção** e o **catálogo de sensores** ficam em `config/limiares.json`
  (fonte única, versionada), não em uma tabela.

## Regras de negócio (10)

> Neste domínio, cada **sensor** corresponde a um canal de medição do veículo
> (velocidade, RPM, aceleração X/Y/Z, ...), e cada **leitura** é um frame de telemetria.

1. **Identificação do sensor:** cada sensor possui um identificador único no sistema
   (`config/limiares.json` → seção `sensores` → ids `S01`...`S08`).
2. **Dados obrigatórios da leitura:** uma leitura só é registrada se possuir rota,
   data/hora e ao menos um valor medido (`LeituraService.add`).
3. **Sensor cadastrado:** não se registra leitura/evento para um canal que não esteja no
   catálogo (`LimiaresService` + `EventoRiscoService.__validar_canal`).
4. **Valores válidos:** o sistema rejeita valores não numéricos/não finitos
   (`fields.Float` + `__validar_numero`).
5. **Leituras duplicadas:** `UniqueConstraint(rota_id, data_hora)` + deduplicação no importador.
6. **Limites de operação:** cada sensor tem `min`/`max` de referência no JSON
   (`sensores`) e limiares de risco na seção `limiares`.
7. **Identificação de anomalias:** leitura fora dos limites (`LimiteDetector`) ou com
   desvio significativo do histórico (`EstatisticoDetector`, `ModeloMLDetector`).
8. **Classificação pelo modelo:** o modelo de ML classifica cada leitura como normal ou
   anômala; somente as anômalas são persistidas (`ModeloMLDetector`).
9. **Registro das anomalias:** `evento_risco` guarda canal, valor, data/hora e método.
10. **Análise histórica:** o modelo de ML treina com as leituras das **outras rotas** e o
    detector estatístico usa o desvio padrão do histórico (z-score).

## Detecção de risco (3 métodos, 6 classificações)

**Métodos de detecção** (herança/polimorfismo em `services/detectors/`):

- **LIMITE** — compara cada leitura com os limiares de referência (do JSON).
- **ESTATISTICO** — z-score da Força G em relação ao histórico da rota (`|z| > zscore_max`).
- **MODELO_ML** — DBSCAN (pseudo-rótulos) + RandomForest, treinado com as outras rotas
  (fallback para a própria rota quando o histórico é pequeno).

**Classificações** (atribuídas conforme a física do veículo):

| Classificação | Critério (limiar padrão) |
|---|---|
| Frenagem brusca | aceleração longitudinal < -3,0 m/s² |
| Aceleração brusca | aceleração longitudinal > +2,5 m/s² |
| Curva em alta velocidade | aceleração lateral > 3,0 m/s² e velocidade > 30 km/h |
| Excesso de velocidade | velocidade > 100 km/h |
| RPM excessivo | RPM > 5000 |
| Acelerador brusco | variação do acelerador > 15 %/s |
| Comportamento atípico | z-score / modelo de ML |

A Força G resultante é `√(ax² + ay²)`; a instabilidade é o desvio padrão da aceleração
numa janela de ~3 s. O **score de segurança** (0–100) desconta pontos conforme a
severidade dos eventos detectados.

### Limpeza na importação

Antes de persistir, o importador:
- limita a aceleração de cada eixo a ±5 m/s² (spikes fisicamente improváveis);
- descarta leituras com velocidade acima de 200 km/h;
- mantém no máximo 3 leituras consecutivas com o veículo parado.

A rota **não é dividida** por intervalos de tempo: é a viagem inteira.

## Como executar

```bash
cd projeto_api
docker compose up --build -d    # sobe API (8080) + banco (5432)
```

A API fica em `http://localhost:8080/telemetria`. O banco **inicia vazio**: a primeira
rota cadastrada recebe o **id 1**.

Interface gráfica (roda fora do container; instale `tkintermapview` para o mapa):

```bash
cd projeto_interface
pip install tkintermapview
python main.py
```

Na interface: **Dados → Rotas → Importar CSV** (ou criar manualmente) → o sistema
**analisa automaticamente** e exibe **Visão Geral (score)**, **Gráfico**, **Mapa (GPS)**,
permite **comparar rotas** e fazer o **CRUD completo** de rotas, leituras e eventos.

### Comandos auxiliares

```bash
cd projeto_api
python seed.py            # importa os CSVs de dados/ (opcional; exige banco vazio)
python seed.py --reset    # apaga tudo e reimporta
python reanalisar.py      # reanalisa as rotas com os limiares atuais do JSON
python avaliar_ml.py      # métricas do detector de ML
python test_api.py        # testes de integração (com a API no ar)
python test_limpeza.py    # testes unitários da limpeza
```

## Endpoints principais

| Método | Rota | Descrição |
|---|---|---|
| GET / POST | `/telemetria/rotas` | Listar / cadastrar rotas |
| POST | `/telemetria/rotas/importar` | Importar CSV como rota |
| GET / PUT / DELETE | `/telemetria/rotas/<id>` | Selecionar / editar / excluir |
| POST | `/telemetria/rotas/<id>/analisar` | Detecção de eventos de risco |
| GET | `/telemetria/rotas/<id>/grafico` | Dados para o gráfico (e mapa) |
| GET | `/telemetria/rotas/<id>/resumo` | Dashboard (score + estatísticas) |
| POST | `/telemetria/rotas/comparar` | Comparar resumos de rotas |
| GET / POST | `/telemetria/leituras` | Listar (por rota) / cadastrar leituras |
| GET / PUT / DELETE | `/telemetria/leituras/<id>` | Selecionar / editar / excluir leitura |
| GET / POST | `/telemetria/eventos-risco` | Listar (filtros) / cadastrar eventos |
| GET / PUT / DELETE | `/telemetria/eventos-risco/<id>` | Selecionar / editar / excluir evento |
| GET | `/telemetria/limiares` | Ler os limiares (somente leitura) |
| GET | `/telemetria/sensores` | Catálogo de sensores/canais |

## Arquitetura em camadas

`routes` → `controllers` → `services` → `repositories` → `entities` → banco de dados.

- **Herança/polimorfismo:** `DetectorAnomalia` (abstrata) → `LimiteDetector`,
  `EstatisticoDetector`, `ModeloMLDetector` (cada um implementa `detectar`).
- **Encapsulamento:** atributos privados (`self.__repository`, `self.__service`).
- **Programação estruturada:** condições (validações), repetições (janelas/laços),
  listas e dicionários (padronização e payloads).
