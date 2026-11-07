# Roteiro da Apresentação — Telemetria Veicular (Parte 6)

Mapeamento dos 10 itens exigidos ao que foi implementado.

1. **Contexto** — sistema de telemetria veicular via OBD-II para detectar e classificar eventos de risco.
2. **Problema** — monitorar condutores e identificar manobras de risco automaticamente.
3. **Requisitos** — 10 regras de negócio no domínio veicular.
4. **Modelo do banco** — 5 tabelas (usuario, rota, leitura, evento_risco, configuracao).
5. **Arquitetura** — camadas: entities → repositories → services → controllers → routes.
6. **Principais classes** — `DetectorAnomalia` + 3 detectores, `ImportadorService`, `AnaliseService`, `ConfiguracaoService`.
7. **Endpoints** — CRUD + `/rotas/<id>/analisar`, `/rotas/<id>/grafico`, `/rotas/<id>/resumo`, `/rotas/comparar`, `/configuracoes/limiares`.
8. **Interface gráfica** — Tkinter, 7 abas (Rotas, Dashboard, Eventos, Gráfico, Mapa, Comparar, Configurações).
9. **Demonstração** — importação real, CRUD, ≥3 regras, análise (classificações), score, mapa.
10. **Dificuldades** — padronização, performance, compatibilidade de versões, ML.

> O roteiro detalhado de defesa está em `ROTEIRO-DEFESA.md` (na raiz do projeto).
