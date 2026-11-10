# Roteiro da Apresentação — Sentinela (Telemetria Veicular)

Mapeamento dos 10 itens exigidos ao que foi implementado.

1. **Contexto** — sistema de telemetria veicular via OBD-II para detectar e classificar eventos de risco.
2. **Problema** — monitorar condutores e identificar manobras de risco automaticamente.
3. **Requisitos** — 10 regras de negócio no domínio veicular.
4. **Modelo do banco** — 3 tabelas (rota, leitura, evento_risco), limiares em JSON.
5. **Arquitetura** — camadas: entities → repositories → services → controllers → routes.
6. **Principais classes** — `DetectorAnomalia` + 3 detectores, `ImportadorService`, `AnaliseService`, `LimiaresService`.
7. **Endpoints** — CRUD das 3 tabelas + `/rotas/<id>/analisar`, `/rotas/<id>/grafico`, `/rotas/<id>/resumo`, `/rotas/comparar`, `/limiares`, `/sensores`.
8. **Interface gráfica** — Tkinter, navegação lateral (Dados, Visão Geral, Gráfico, Sensores, Comparar).
9. **Demonstração** — importação real, CRUD, ≥3 regras, análise (classificações), score, análise por sensor.
10. **Dificuldades** — padronização, performance, compatibilidade de versões, ML.

> O roteiro detalhado de defesa está em `ROTEIRO-DEFESA.md` (na raiz do projeto).
