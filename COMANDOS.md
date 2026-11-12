# Comandos do Sentinela

> Atalhos de execução do projeto. Atualizado para a versão atual do código.

## 0. Antes de começar

- **Abra o Docker Desktop** e espere ficar "Running".
- Terminal: **CMD** ou PowerShell, partindo de `C:\Users\jo22m\Documents\Trabalho_PAV`.
- Dependências Python já instaladas (requests, matplotlib, pillow, flask, sqlalchemy, psycopg2, scikit-learn, python-pptx).

---

## 1. Subir a API + banco (Terminal 1)

```cmd
cd projeto_api
docker compose up --build -d
```

- `--build` **só** quando alterar código Python da API. No dia a dia basta `docker compose up -d`.
- API: `http://localhost:8080/telemetria`
- Conferir se subiu: `docker compose ps` (api e db como `running` / `healthy`)
- Teste rápido (PowerShell): `Invoke-RestMethod http://localhost:8080/telemetria/rotas`

## 2. Abrir a interface (Terminal 2)

```cmd
cd projeto_interface
python main.py
```

## 3. Parar

```cmd
cd projeto_api
docker compose down       # para os containers, MANTÉM os dados
docker compose down -v    # para e APAGA o banco (volume pgdata) → próxima rota volta a ser id 1
```

---

## 4. Comandos auxiliares — `cd projeto_api`

| Comando | O que faz |
|---|---|
| `python seed.py` | Importa os CSVs de `dados/` (exige banco vazio; `dados/` não é versionado) |
| `python seed.py --reset` | Apaga tudo (reinicia ids em 1) e reimporta |
| `python reanalisar.py` | Reanalisa todas as rotas com os limiares atuais (preserva eventos `MANUAL`) |
| `python avaliar_ml.py` | Métricas do detector de ML (precisão/recall/F1/silhouette) |
| `python test_api.py` | Testes de integração — **exige a API no ar**; cria e apaga rotas de teste |
| `python test_limpeza.py` | Testes unitários da limpeza — **não** precisa de API |

## 5. Apresentação / relatório — `cd projeto_interface`

```cmd
python gerar_relatorio.py 162                    # HTML em apresentacao/relatorios/
python gerar_relatorio.py 162 -t "Rota 1 - demo" -o "C:\temp\rel.html"
python gerar_dados_teste.py                      # gera os CSVs sintéticos em apresentacao/dados_teste
python capturar_telas.py --sim                   # recria rotas demo + capturas em apresentacao/imgs
```

## 6. Slides — `cd apresentacao`

```cmd
python gerar_slides.py    # regenera slides_pav.pptx (19 slides)
```

---

## 7. Roteiro completo da demo (ordem que funciona)

```cmd
cd projeto_api
docker compose up --build -d
cd ..\projeto_interface
python main.py                                  :: importar CSVs de apresentacao\dados_teste
:: (na GUI) Dados -> Rotas -> Nova Rota -> escolher os CSVs
:: (na GUI) Visao Geral -> Relatorio visual (HTML) -> nomear -> salvar
```

Se quiser recriar tudo do zero para apresentar:

```cmd
cd projeto_api
docker compose down -v
docker compose up -d
cd ..\projeto_interface
python gerar_dados_teste.py
python main.py
```

---

## 8. Pegadinhas que vale anotar

- **`docker compose` e `git push` escrevem em stderr** → o PowerShell mostra "Exited with code 1" mesmo quando deu certo. Confie no texto, não no código de saída.
- **Feche o PowerPoint** antes de `gerar_slides.py`, senão dá `PermissionError`.
- **`capturar_telas.py --sim`** apaga e recria as rotas demo (invalida análises) → depois rode `gerar_slides.py`.
- **`config/limiares.json`** é montado como read-only no container: editar **não** exige rebuild, mas exige `python reanalisar.py` para os eventos refletirem os novos limites.
- **`seed.py`** depende de `projeto_api/dados/*.csv`, que **não está no git** — em outra máquina, use os CSVs de `apresentacao/dados_teste` importando pela interface.
- O banco **inicia vazio**; `seed.py` é opcional.
