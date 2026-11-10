# Sentinela — Telemetria Veicular (OBD-II) e Detecção de Eventos de Risco

> **Trabalho PAV**

Sistema para **receber, padronizar, armazenar e analisar dados de telemetria veicular**
coletados via interface **OBD-II**, identificando e **classificando** eventos de condução
de risco (frenagens bruscas, acelerações intensas, curvas em alta velocidade, excesso de
velocidade, RPM excessivo e acelerador brusco), com **score de segurança** do condutor.

- **Aluno:** João Maurício Araújo Leitão
- **Modalidade:** Individual
- **Tecnologias:** Python, Flask (Flask-RESTful), SQLAlchemy, PostgreSQL, scikit-learn, matplotlib, Tkinter, Docker

## Estrutura do projeto

```
Trabalho_PAV/
├── README.md               # Este documento
├── GUIA-DE-USO.md          # Guia de uso passo a passo (demonstração)
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
│   ├── tabs.py             # Seções: Dados (Rotas/Leituras/Eventos), Visão Geral, Gráfico, Sensores, Comparar
│   ├── api_client.py       # Cliente HTTP
│   ├── assets/             # Logo e ícone do Sentinela (PNG/ICO)
│   └── capturar_telas.py   # Captura as telas (exige API no ar) → apresentacao/imgs/
│
└── apresentacao/           # Apresentação (slides)
    ├── gerar_slides.py     # Gera o arquivo slides_pav.pptx
    ├── roteiro-apresentacao.md
    ├── imgs/               # Capturas de tela usadas nos slides
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
> (velocidade, RPM, aceleração X/Y/Z, ...), e cada **leitura** é um frame de telemetria
> com os valores desses sensores em um mesmo instante.

As 10 regras (texto original, conforme enviadas na Parte 1):

1. **Identificação do sensor:** cada sensor deve possuir um identificador único no sistema.
2. **Dados obrigatórios da leitura:** uma leitura só poderá ser registrada se possuir
   sensor, valor medido e data/hora da coleta.
3. **Sensor cadastrado:** o sistema não deve permitir o registro de uma leitura associada
   a um sensor que não esteja cadastrado.
4. **Valores válidos:** o sistema não deve armazenar leituras com valores que não sejam
   numéricos ou incompatíveis com o tipo de dado produzido pelo sensor.
5. **Leituras duplicadas:** o sistema não deve considerar como nova leitura duas medições
   do mesmo sensor com o mesmo valor e o mesmo instante de coleta.
6. **Limites de operação:** cada sensor deve possuir limites mínimo e máximo de referência
   para suas medições, de acordo com seu tipo.
7. **Identificação de anomalias:** uma leitura que ultrapasse os limites de referência ou
   apresente comportamento significativamente diferente do padrão histórico deve ser
   identificada como potencialmente anômala.
8. **Classificação pelo modelo:** as leituras submetidas ao modelo de Machine Learning
   devem receber uma classificação indicando comportamento normal ou potencialmente anômalo.
9. **Registro das anomalias:** toda anomalia identificada deve manter informações sobre o
   sensor, valor, data/hora e método utilizado para sua identificação.
10. **Análise histórica:** o sistema deve utilizar dados históricos dos sensores para
    calcular padrões estatísticos e fornecer informações utilizadas na identificação de
    comportamentos anormais.

### Onde cada regra está implementada

| Regra | Implementação |
|---|---|
| 1 | `config/limiares.json` → `sensores.*.id` (`S01`...`S08`) |
| 2 | `LeituraService.add` (exige rota + data/hora + ao menos um valor medido, sendo os valores os sensores/canais) |
| 3 | `LimiaresService.get_sensores` + `EventoRiscoService.__validar_canal` (validação por nome) |
| 4 | `fields.Float` (Marshmallow) + `LeituraService.__validar_numero` |
| 5 | `UniqueConstraint(rota_id, data_hora)` + deduplicação no importador |
| 6 | `config/limiares.json` → `sensores.*.min/max` e `limiares.*` |
| 7 | `LimiteDetector` + `EstatisticoDetector` + `ModeloMLDetector` |
| 8 | `ModeloMLDetector` (DBSCAN + RandomForest) — classifica normal × anômalo; só as anômalas são persistidas |
| 9 | `EventoRisco` (canal, valor, data/hora, método) |
| 10 | `ModeloMLDetector` (histórico das outras rotas) + `EstatisticoDetector` (z-score) |

> **Notas de interpretação:**
> - **Regra 3:** a leitura é um frame com colunas fixas, e cada coluna corresponde a um
>   sensor do catálogo — um canal não cadastrado não possui coluna e, portanto, não pode
>   ser persistido na leitura. A validação **por nome** acontece nos eventos
>   (`EventoRiscoService.__validar_canal`), que referenciam canais livremente.
> - **Regra 8:** o modelo classifica **todas** as leituras como normal ou anômala
>   internamente; por eficiência e pela regra 9, apenas as anômalas são persistidas.
> - **Regra 6:** os limites `min`/`max` são de **referência** (não rejeitam leituras);
>   a detecção de risco usa os limiares da seção `limiares`.

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

> **Limitação do score:** a penalidade é contada por evento (não normalizada por
> distância/duração). Rotas muito longas tendem a acumular mais eventos e, portanto, a
> score menor que rotas curtas. A comparação entre rotas deve considerar isso.

### Análise idempotente e reanálise

Cada rota guarda o instante da última análise (`rota.data_analise`). A análise é
executada automaticamente quando a rota é criada (importação) e **reagendada** sempre que
uma leitura é criada, editada ou excluída (o campo é invalidado por
`LeituraService.__invalidar_analise`).

- **Análise automática** (`resumo`/`gráfico`): acrescenta apenas os eventos novos,
  preservando os já existentes — inclusive os cadastrados manualmente via CRUD.
- **Reanálise forçada** (`POST /rotas/<id>/analisar`, botão "Reanalisar" ou
  `python reanalisar.py`): apaga os eventos e os regenera do zero — útil após editar
  `config/limiares.json` ou corrigir uma leitura.

### Limpeza na importação

Antes de persistir, o importador:
- limita a aceleração de cada eixo a ±5 m/s² (spikes fisicamente improváveis);
- descarta leituras com velocidade acima de 200 km/h;
- mantém no máximo 3 leituras consecutivas com o veículo parado.

A rota **não é dividida** por intervalos de tempo: é a viagem inteira.

## Como executar

> No Windows, abra o **Docker Desktop** antes e rode os comandos no **CMD** (ou PowerShell).

```bash
cd projeto_api
docker compose up --build -d    # sobe API (8080) + banco (5432)
```

A API fica em `http://localhost:8080/telemetria`. O banco **inicia vazio**: a primeira
rota cadastrada recebe o **id 1**.

Interface gráfica (roda fora do container; instale as dependências uma vez):

```bash
cd projeto_interface
pip install requests matplotlib pillow
python main.py
```

Na interface: **Dados → Rotas → Nova Rota** (importa um ou mais CSVs) → o sistema
**analisa automaticamente** e exibe **Visão Geral (score)**, **Gráfico**,
**Análise por Sensor**, permite **comparar rotas** e fazer o **CRUD completo**
de rotas, leituras e eventos.

Comportamentos da interface:

- **Nova Rota** aceita **vários CSVs de uma vez**; cada arquivo vira uma rota
  com o nome do próprio arquivo.
- As tabelas de **Dados** carregam na primeira visita a cada aba e, depois disso,
  são atualizadas **manualmente** pelo botão **Atualizar** (ou após criar/editar/excluir).
- O seletor **"Rota em análise"** (barra superior) aparece apenas em
  **Visão Geral**, **Gráfico** e **Sensores**.
- **Gráfico** e **Sensores** têm barra de **zoom/pan** (matplotlib).
- Se a API estiver fora do ar, a interface mostra **"API offline"** com o botão
  **"Tentar novamente"** e tenta reconectar sozinha.

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
| POST | `/telemetria/rotas/<id>/analisar` | (Re)executa a detecção de eventos de risco |
| GET | `/telemetria/rotas/<id>/grafico` | Dados para o gráfico (e análise por sensor) |
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

## Documentação

- **[Guia de uso](GUIA-DE-USO.md)** — passo a passo da demonstração (subir, cadastrar rota, CRUD, análise).
- **[Roteiro da apresentação](apresentacao/roteiro-apresentacao.md)** — mapeamento dos 10 itens exigidos.
- **Slides** — gere com `cd apresentacao && python gerar_slides.py` (saída `slides_pav.pptx`).
