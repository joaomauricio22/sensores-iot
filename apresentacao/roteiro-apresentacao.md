# Roteiro da Apresentação — Telemetria Veicular (Parte 6)

Mapeamento dos 10 itens exigidos ao que foi implementado.

1. **Contexto** — sistema de telemetria veicular via OBD-II para detectar eventos de risco.
2. **Problema** — monitorar condutores e identificar manobras de risco automaticamente.
3. **Requisitos** — 10 regras de negócio no domínio veicular.
4. **Modelo do banco** — 5 tabelas (veiculo, parametro, mapeamento_parametro, leitura, evento_risco).
5. **Arquitetura** — camadas: entities → repositories → services → controllers → routes.
6. **Principais classes** — `DetectorAnomalia` + 3 detectores, `ImportadorService`, `AnaliseService`.
7. **Endpoints** — CRUD + `/veiculos/<id>/analisar` e `/veiculos/<id>/estatisticas`.
8. **Interface gráfica** — Tkinter, 5 abas.
9. **Demonstração** — importação real (18.943 leituras), CRUD, ≥3 regras, análise (532 eventos).
10. **Dificuldades** — padronização, performance, compatibilidade de versões, ML.

> O roteiro detalhado de defesa está em `ROTEIRO-DEFESA.md` (na raiz do projeto).
