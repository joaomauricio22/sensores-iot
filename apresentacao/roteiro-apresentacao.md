# Roteiro da Apresentação — Sensores IoT (Parte 6)

Este roteiro mapeia os 10 itens exigidos na apresentação ao que foi implementado.

## 1. Contexto do sistema
Sistema para **receber, armazenar e consultar** dados produzidos por sensores
IoT, realizando o tratamento e a **análise** dos dados para **identificar valores
anormais** (detecção de anomalias).

## 2. Problema que o sistema resolve
- Sensores geram grande volume de dados; identificar manualmente valores fora do
  padrão é inviável.
- O sistema automatiza: validação dos dados, armazenamento, análise estatística e
  classificação por Machine Learning das leituras anômalas.

## 3. Requisitos principais (10 regras de negócio)
1. Identificador único do sensor.
2. Leitura exige sensor, valor e data/hora.
3. Leitura apenas para sensor cadastrado.
4. Valor numérico (e finito).
5. Sem leituras duplicadas (sensor + valor + instante).
6. Limites mínimo/máximo por sensor.
7. Anomalia = fora dos limites **ou** desvio do histórico.
8. Classificação pelo modelo de ML.
9. Registro da anomalia (sensor, valor, data/hora, método).
10. Análise histórica (padrões estatísticos).

## 4. Modelo do banco de dados
- 4 tabelas com relacionamentos coerentes:

```
TipoSensor 1 ── N Sensor 1 ── N Leitura 1 ── N Anomalia
```
- Restrições de integridade: `UNIQUE(identificador)`, `UNIQUE(sensor_id, valor, data_hora)`, `UNIQUE(leitura_id, metodo)`.

## 5. Arquitetura da aplicação
Arquitetura em camadas (separação de responsabilidades):

```
entities → repositories → services → controllers → routes
```

- **entities**: classes que mapeiam as tabelas (SQLAlchemy).
- **repositories**: operações no banco (SELECT/INSERT/UPDATE/DELETE).
- **services**: regras de negócio e análise (detecção de anomalias + ML).
- **controllers**: recebem as requisições HTTP (Flask-RESTful + Marshmallow).
- **routes**: mapeamento de URLs.
- **config**: conexão com o banco.

## 6. Principais classes
- `TipoSensor`, `Sensor`, `Leitura`, `Anomalia` (entidades/ORM).
- `DetectorAnomalia` (abstrata) + `LimiteDetector`, `EstatisticoDetector`, `ModeloMLDetector` (herança/polimorfismo).
- `AnaliseService` (orquestra a análise).
- `*Service`, `*Repository`, `*Controller` de cada entidade.

## 7. Endpoints da API
- CRUD completo por entidade: `/iot/tipos-sensor`, `/iot/sensores`, `/iot/leituras`, `/iot/anomalias`.
- `POST /iot/leituras/<id>/analisar` — detecção de anomalias.
- `POST /iot/leituras/<id>/classificar` — classificação ML.
- `GET /iot/sensores/<id>/estatisticas` — análise histórica.

## 8. Interface gráfica
Tkinter, projeto separado, com abas (Notebook) para cada entidade:
cadastro, busca, edição, exclusão e listagem + botões de análise.

## 9. Demonstração (na prática)
- Cadastro, consulta, edição e exclusão (CRUD).
- **Pelo menos 3 regras de negócio** (ex.: sensor duplicado, leitura para sensor
  inexistente, leitura duplicada).
- Comunicação interface ↔ API.
- Persistência no banco.
- **Pelo menos 2 casos de erro/validação.**

## 10. Principais dificuldades
Sugestões de pontos a relatar:
- Compatibilidade de versões (Flask-RESTful, flask-apispec, Marshmallow 3 vs 4).
- Configuração do PostgreSQL + Docker.
- Treinamento do modelo de ML com dados históricos (quantidade mínima de amostras).
