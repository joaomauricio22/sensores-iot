# Sentinela — Roteiro de apresentação

**Aluno:** João Maurício Araújo Leitão · **Data:** 13/11/2026

---

## 1. Abertura (30 s)

> "O Sentinela recebe telemetria veicular via OBD-II, padroniza e armazena em PostgreSQL e usa **três métodos** — limites do CTB, z-score histórico e Machine Learning — para detectar e classificar eventos de risco, gerando um **score de segurança por quilômetro** e relatórios visuais."

**Frase de transição:** *"Antes do código, o problema: como saber se uma viagem foi perigosa?"*

---

## 2. Antes de apresentar (5 min)

```cmd
:: 1) Abrir o Docker Desktop e esperar "Running"
cd C:\Users\jo22m\Documents\Trabalho_PAV\projeto_api
docker compose up -d
docker compose ps

:: 2) Conferir a API
powershell -c "Invoke-RestMethod http://localhost:8080/telemetria/rotas | Select-Object id,nome"

:: 3) Abrir a interface
cd ..\projeto_interface
python main.py
```

- **Backup:** PDF dos slides + 1 relatório HTML já gerado.
- **NUNCA:** `docker compose down -v` (apaga o banco).
- CSVs da demo: `apresentacao\dados_teste\`.

---

## 3. Demo (7 min)

| # | Onde | O que mostrar / dizer |
|---|---|---|
| 1 | Terminal | `docker compose ps` + `GET /rotas` → "a GUI fala HTTP, não com o banco" |
| 2 | Dados → Rotas → Nova Rota | Importar `Conducao_Agressiva.csv`; cada CSV vira uma rota |
| 3 | Visão Geral | Score 0–100 **normalizado por km** + KPIs + eventos por tipo |
| 4 | Gráfico | Zoom + seletor **Painel** (Velocidade / Força G / RPM); pontos = eventos |
| 5 | Sensores | Marcar **"Todas as rotas"** → agregado |
| 6 | Comparar | Agressiva × Defensiva |
| 7 | Visão Geral → Relatório | Gerar HTML e abrir no navegador |
| 8 | Dados → Eventos | Coluna **método**: LIMITE / ESTATISTICO / MODELO_ML |
| 9 | Slides | Arquitetura em camadas · slide 8 (classes) · slide 9 (z-score) |

**Transição:** *"Agora que vocês viram o resultado, vou mostrar como o sistema decide."*

---

## 4. Endpoints (13 caminhos)

Base: `http://localhost:8080/telemetria`

| Método | Endpoint | Função |
|---|---|---|
| GET / POST | `/rotas` | Listar / cadastrar |
| POST | `/rotas/importar` | Importar CSV (rota + leituras + limpeza) |
| GET / PUT / DELETE | `/rotas/<id>` | Detalhe / editar / excluir (cascata) |
| POST | `/rotas/<id>/analisar` | Reanálise forçada (preserva MANUAL) |
| GET | `/rotas/<id>/resumo` | Score + KPIs + eventos por tipo |
| GET | `/rotas/<id>/grafico` | Pontos do gráfico e da análise por sensor |
| POST | `/rotas/comparar` | Compara 2 a 5 rotas |
| GET / POST | `/leituras?rota_id=` | Listar / cadastrar leituras |
| GET / PUT / DELETE | `/leituras/<id>` | Detalhe / editar / excluir |
| GET / POST | `/eventos-risco?rota_id=&tipo=` | Listar / cadastrar evento |
| GET / PUT / DELETE | `/eventos-risco/<id>` | Detalhe / editar / excluir |
| GET | `/limiares` | Limiares (somente leitura) |
| GET | `/sensores` | Catálogo S01…S08 |

**Status:** 200 ok · 201 criado · 400 validação · 404 não encontrado · 409 duplicado · 405 método proibido · 500 interno.

---

## 5. Perguntas prováveis (resposta em 1 linha)

| Pergunta | Resposta |
|---|---|
| Onde está a regra X? | Tabela do README mapeia as 10 regras para arquivos |
| Por que 3 tabelas? | `rota → leitura → evento_risco`; limiares e sensores são JSON versionado |
| Por que banco vazio? | Requisito; `seed.py` é opcional |
| Como o ML decide? | StandardScaler → DBSCAN(eps=1,0; min=15) gera pseudo-rótulos → RandomForest |
| Com quais dados treina? | Com as **outras** rotas (histórico); fallback para a própria com pouco dado |
| Por que z-score 3? | Regra 3σ (~99,7%); configurável no JSON |
| Como o score funciona? | `100 − 2,0 × penalidade/km`, com pesos por tipo |
| Como evita duplicata? | `UNIQUE (rota_id, data_hora)` e `(leitura_id, metodo, classificacao, canal)` |
| E se o CSV tiver lixo? | Limpeza com relatório; se nada sobrar, 400 |
| Por que Tkinter separado? | Requisito: a GUI é só cliente HTTP |
| Onde há herança? | `DetectorAnomalia` → `LimiteDetector`, `EstatisticoDetector`, `ModeloMLDetector` |

---

## 6. Pontos fracos (admita com maturidade)

- **Rota OBDLink com score 0:** ruído no acelerador (634 eventos) → melhoria: suavização.
- **`forca_g_max` desenhado no gráfico mas não usado pelo método LIMITE:** os métodos 2 e 3 capturam; melhoria: incluir no `LimiteDetector`.
- **Agregação "Todas as rotas" é por leitura:** rotas longas pesam mais (decisão consciente).
- **ML com pseudo-rótulos:** sem ground truth; `avaliar_ml.py` mede silhouette.

**Transição:** *"Por fim, o que ficou como melhoria."*

---

## 7. Plano B

| Se falhar… | Faça |
|---|---|
| Docker não subir | Relatório HTML + slides + capturas em `apresentacao/imgs` |
| API cair | `docker compose restart`; a GUI reconecta sozinha |
| Import falhar | Usar as rotas já no banco (volume preservado) |
| PowerPoint não abrir | PDF de backup |

---

## 8. Números para citar

**3** tabelas · **3** métodos · **7** classificações · **10** regras · **13** endpoints · **19** slides · **6** rotas no banco · **18.984** leituras

---

## 9. Se sobrar tempo

- `python test_api.py` → "todos os testes passaram" (API no ar).
- `python reanalisar.py` → aplicar novos limiares.
- `python avaliar_ml.py` → métricas do modelo.
