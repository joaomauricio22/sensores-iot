"""Testes de integração da API — modelo de 3 tabelas.

Pré-requisito: containers em execução (docker compose up -d).
Executar:  python test_api.py
"""
import concurrent.futures
import uuid

import requests

BASE = "http://localhost:8080/telemetria"
SUFIXO = uuid.uuid4().hex[:8]

falhas = 0


def show(titulo, ok, detalhe=""):
    global falhas
    if not ok:
        falhas += 1
    print(f"[{'OK' if ok else 'FALHOU'}] {titulo}" + (f" -> {detalhe}" if detalhe else ""))


# CSV de exemplo (com StartTime, colunas mínimas e GPS).
CSV_EXEMPLO = """# StartTime = 01/21/2026 08:00:00.0000 AM
Time (sec), Vehicle speed (km/h), Engine RPM (RPM), Accel X (m/s²), Accel Y (m/s²), Accel Z (m/s²), Absolute throttle position (%), Latitude (deg), Longitude (deg)
0.0, 0, 800, 0.1, 0.1, 0.1, 5, -22.588833, -43.284300
1.0, 30, 1500, 0.2, 0.1, 0.1, 10, -22.588900, -43.284300
2.0, 60, 2500, 0.3, 0.2, 0.1, 20, -22.589000, -43.284300
3.0, 90, 3500, 0.4, 3.5, 0.2, 30, -22.589100, -43.284300
4.0, 120, 4500, 0.3, 0.3, 0.2, 40, -22.589200, -43.284300
5.0, 130, 6000, 0.2, 0.3, 0.2, 60, -22.589300, -43.284300
6.0, 100, 5000, -0.5, -0.2, 0.1, 40, -22.589400, -43.284300
7.0, 70, 4000, -0.4, -0.1, 0.1, 30, -22.589500, -43.284300
8.0, 40, 3000, -0.3, 0.0, 0.1, 20, -22.589600, -43.284300
9.0, 20, 2000, -0.2, 0.0, 0.1, 10, -22.589700, -43.284300
10.0, 0, 900, 0.0, 0.0, 0.1, 5, -22.589800, -43.284300
"""


def main():
    rota_id = None
    leitura_id = None
    evento_id = None
    rotas_criadas = []

    try:
        # ---------------------------------------------------------------- #
        # Configuração somente leitura (JSON)
        # ---------------------------------------------------------------- #
        r = requests.get(f"{BASE}/limiares")
        show("GET limiares (200)", r.status_code == 200 and "velocidade_max" in r.json())
        r = requests.get(f"{BASE}/sensores")
        show("GET sensores (200, 8 canais)",
             r.status_code == 200 and len(r.json()) == 8,
             f"{r.status_code} {len(r.json()) if r.status_code == 200 else ''}")
        r = requests.put(f"{BASE}/limiares", json={"velocidade_max": 120})
        show("PUT limiares bloqueado (405)", r.status_code == 405, f"{r.status_code}")

        # ---------------------------------------------------------------- #
        # CRUD de Rota
        # ---------------------------------------------------------------- #
        r = requests.post(f"{BASE}/rotas", json={"nome": ""})
        show("POST rota sem nome (400)", r.status_code == 400, f"{r.status_code}")

        r = requests.post(f"{BASE}/rotas", json={"nome": "n" * 120})
        show("POST rota nome longo (400)", r.status_code == 400, f"{r.status_code}")

        r = requests.post(f"{BASE}/rotas", json={
            "nome": f"Rota teste {SUFIXO}",
            "arquivo_origem": "teste.csv",
        })
        show("POST rota (201)", r.status_code == 201, f"{r.status_code} {r.text[:80]}")
        if r.status_code == 201:
            rota_id = r.json()["id"]
            rotas_criadas.append(rota_id)

        r = requests.get(f"{BASE}/rotas/{rota_id}")
        show("GET rota (200)", r.status_code == 200)

        r = requests.put(f"{BASE}/rotas/{rota_id}", json={
            "nome": f"Rota teste {SUFIXO} (editada)",
            "arquivo_origem": "teste.csv",
        })
        show("PUT rota (200)", r.status_code == 200 and "editada" in r.json().get("nome", ""))

        r = requests.get(f"{BASE}/rotas/999999")
        show("GET rota inexistente (404)", r.status_code == 404)

        # ---------------------------------------------------------------- #
        # CRUD de Leitura + regras de negócio
        # ---------------------------------------------------------------- #
        r = requests.post(f"{BASE}/leituras", json={
            "rota_id": 999999, "data_hora": "2026-01-21T10:00:00", "velocidade": 50,
        })
        show("POST leitura rota inexistente (400)", r.status_code == 400, f"{r.status_code}")

        r = requests.post(f"{BASE}/leituras", json={
            "rota_id": rota_id, "data_hora": "2026-01-21T10:00:00",
        })
        show("POST leitura sem valor medido (400)", r.status_code == 400, f"{r.status_code}")

        r = requests.post(f"{BASE}/leituras", json={
            "rota_id": rota_id, "data_hora": "2026-01-21T10:00:00",
            "velocidade": 80, "rpm": 2500, "accel_x": 1.0, "accel_y": 0.5,
            "accel_z": 9.8, "posicao_acelerador": 30, "latitude": -23.5,
            "longitude": -46.6,
        })
        show("POST leitura (201)", r.status_code == 201, f"{r.status_code} {r.text[:80]}")
        if r.status_code == 201:
            leitura_id = r.json()["id"]

        r = requests.post(f"{BASE}/leituras", json={
            "rota_id": rota_id, "data_hora": "2026-01-21T10:00:00", "velocidade": 90,
        })
        show("POST leitura duplicada (400)", r.status_code == 400, f"{r.status_code}")

        r = requests.get(f"{BASE}/leituras", params={"rota_id": rota_id})
        show("GET leituras da rota (200)", r.status_code == 200 and len(r.json()) == 1)

        r = requests.put(f"{BASE}/leituras/{leitura_id}", json={
            "rota_id": rota_id, "data_hora": "2026-01-21T10:00:00",
            "velocidade": 85, "rpm": 2600,
        })
        show("PUT leitura (200)", r.status_code == 200 and r.json().get("velocidade") == 85)

        r = requests.put(f"{BASE}/leituras/{leitura_id}", json={
            "rota_id": rota_id, "data_hora": "2026-01-21T10:00:00",
        })
        show("PUT leitura sem valor medido (400)", r.status_code == 400, f"{r.status_code}")

        # ---------------------------------------------------------------- #
        # CRUD de EventoRisco
        # ---------------------------------------------------------------- #
        r = requests.post(f"{BASE}/eventos-risco", json={
            "leitura_id": leitura_id, "metodo": "INVALIDO",
        })
        show("POST evento método inválido (400)", r.status_code == 400, f"{r.status_code}")

        r = requests.post(f"{BASE}/eventos-risco", json={
            "leitura_id": leitura_id, "metodo": "LIMITE", "canal": "inexistente",
        })
        show("POST evento canal inválido (400)", r.status_code == 400, f"{r.status_code}")

        r = requests.post(f"{BASE}/eventos-risco", json={
            "leitura_id": 999999, "metodo": "LIMITE",
        })
        show("POST evento leitura inexistente (400)", r.status_code == 400, f"{r.status_code}")

        r = requests.post(f"{BASE}/eventos-risco", json={
            "leitura_id": leitura_id, "metodo": "LIMITE", "canal": "velocidade",
            "classificacao": "x" * 50,
        })
        show("POST evento classificação longa (400)", r.status_code == 400, f"{r.status_code}")

        r = requests.post(f"{BASE}/eventos-risco", json={
            "leitura_id": leitura_id, "metodo": "LIMITE", "canal": "velocidade",
            "valor": 130, "classificacao": "Excesso de velocidade",
        })
        show("POST evento (201)", r.status_code == 201, f"{r.status_code} {r.text[:80]}")
        if r.status_code == 201:
            evento_id = r.json()["id"]
            show("Evento deriva rota/data da leitura",
                 r.json()["rota_id"] == rota_id and r.json()["data_hora"] is not None)

        r = requests.get(f"{BASE}/eventos-risco", params={"rota_id": rota_id})
        show("GET eventos da rota (200)", r.status_code == 200 and len(r.json()) == 1)

        r = requests.get(f"{BASE}/eventos-risco",
                         params={"rota_id": rota_id, "tipo": "Excesso de velocidade"})
        show("GET eventos filtro por tipo (200)", r.status_code == 200 and len(r.json()) == 1)

        r = requests.put(f"{BASE}/eventos-risco/{evento_id}", json={
            "leitura_id": leitura_id, "metodo": "LIMITE", "canal": "velocidade",
            "valor": 140, "classificacao": "Excesso de velocidade",
        })
        show("PUT evento (200)", r.status_code == 200 and r.json().get("valor") == 140)

        # ---------------------------------------------------------------- #
        # Importação de CSV e análise
        # ---------------------------------------------------------------- #
        r = requests.post(f"{BASE}/rotas/importar", json={
            "nome": f"Rota CSV {SUFIXO}", "arquivo_origem": "teste.csv",
            "conteudo_csv": CSV_EXEMPLO,
        })
        show("POST importar CSV (201)", r.status_code == 201, f"{r.status_code} {r.text[:80]}")
        rota_csv_id = r.json().get("rota_id") if r.status_code == 201 else None
        if r.status_code == 201:
            rotas_criadas.append(rota_csv_id)
            show("Importação informa limpeza",
                 "limpeza" in r.json() and r.json()["total_leituras"] == 11,
                 str(r.json().get("limpeza")))

        if rota_csv_id:
            r = requests.post(f"{BASE}/rotas/{rota_csv_id}/analisar")
            show("POST analisar rota (200)", r.status_code == 200, f"{r.status_code}")
            r = requests.get(f"{BASE}/rotas/{rota_csv_id}/grafico")
            show("GET gráfico da rota (200)",
                 r.status_code == 200 and "pontos" in r.json())
            r = requests.get(f"{BASE}/rotas/{rota_csv_id}/resumo")
            show("GET resumo com score (200)",
                 r.status_code == 200 and "score" in r.json())
            r = requests.post(f"{BASE}/rotas/comparar",
                              json={"rota_ids": [rota_csv_id, rota_id]})
            show("POST comparar rotas (200)",
                 r.status_code == 200 and len(r.json().get("rotas", [])) == 2)
            r = requests.post(f"{BASE}/rotas/comparar", json={})
            show("POST comparar sem rota_ids (400)", r.status_code == 400, f"{r.status_code}")

        # Regressão: uma leitura criada APÓS a análise deve ser reanalisada.
        if rota_csv_id:
            r = requests.get(f"{BASE}/rotas/{rota_csv_id}/resumo")
            total_antes = r.json().get("total_eventos", 0)
            r = requests.post(f"{BASE}/leituras", json={
                "rota_id": rota_csv_id, "data_hora": "2026-01-21T08:00:11",
                "velocidade": 135, "rpm": 6000,
            })
            show("POST leitura pós-análise (201)", r.status_code == 201, f"{r.status_code}")
            if r.status_code == 201:
                r = requests.get(f"{BASE}/rotas/{rota_csv_id}/resumo")
                total_depois = r.json().get("total_eventos", 0)
                show("Reanálise detecta a leitura nova",
                     total_depois > total_antes, f"{total_antes} -> {total_depois}")

        # ---------------------------------------------------------------- #
        # Regressões (bugs corrigidos na varredura)
        # ---------------------------------------------------------------- #

        # R1: filtro rota_id inválido não é ignorado.
        r = requests.get(f"{BASE}/leituras", params={"rota_id": "abc"})
        show("GET leituras rota_id inválido (400)", r.status_code == 400, f"{r.status_code}")
        r = requests.get(f"{BASE}/eventos-risco", params={"rota_id": "abc"})
        show("GET eventos rota_id inválido (400)", r.status_code == 400, f"{r.status_code}")

        # R2: comparar com rota_ids inválidos.
        r = requests.post(f"{BASE}/rotas/comparar", json={"rota_ids": ["abc"]})
        show("POST comparar rota_ids texto (400)", r.status_code == 400, f"{r.status_code}")
        r = requests.post(f"{BASE}/rotas/comparar", json={"rota_ids": [1, 2.5]})
        show("POST comparar rota_ids float (400)", r.status_code == 400, f"{r.status_code}")
        r = requests.post(f"{BASE}/rotas/comparar", json={"rota_ids": [1]})
        show("POST comparar rota_ids único (400)", r.status_code == 400, f"{r.status_code}")

        # R3: StartTime inválido retorna 400 (não 500).
        r = requests.post(f"{BASE}/rotas/importar", json={
            "nome": f"CSV inválido {SUFIXO}", "arquivo_origem": "ruim.csv",
            "conteudo_csv": "# StartTime = data-invalida\nTime (sec), Vehicle speed (km/h)\n0, 10\n",
        })
        show("POST importar StartTime inválido (400)", r.status_code == 400, f"{r.status_code}")

        # R4: CSV com nan/inf tem as linhas descartadas pela limpeza.
        csv_nan = (
            "# StartTime = 01/21/2026 08:00:00.0000 AM\n"
            "Time (sec), Vehicle speed (km/h), Engine RPM (RPM)\n"
            "0, nan, 2000\n"
            "1, 50, inf\n"
            "2, 60, 2500\n"
        )
        r = requests.post(f"{BASE}/rotas/importar", json={
            "nome": f"Rota nan {SUFIXO}", "arquivo_origem": "nan.csv", "conteudo_csv": csv_nan,
        })
        show("POST importar nan/inf (201)", r.status_code == 201, f"{r.status_code}")
        rota_nan = r.json().get("rota_id") if r.status_code == 201 else None
        if rota_nan:
            rotas_criadas.append(rota_nan)
            limpeza = r.json().get("limpeza", {})
            show("nan/inf contabilizados em valores_invalidos",
                 limpeza.get("valores_invalidos", 0) == 2, str(limpeza))
            show("nan/inf reduzem total de leituras",
                 r.json().get("total_leituras") == 1, str(r.json().get("total_leituras")))
            r = requests.get(f"{BASE}/rotas/{rota_nan}/resumo")
            show("resumo de rota com nan descartado (200)",
                 r.status_code == 200, f"{r.status_code}")

        # R5: mapeamento em português (Aceleração Y).
        csv_pt = (
            "# StartTime = 01/21/2026 08:00:00.0000 AM\n"
            "Time (sec), Velocidade do veículo (km/h), RPM do motor (RPM), Aceleração Y (m/s²)\n"
            "0, 50, 2000, 2.5\n"
            "1, 60, 2200, 3.5\n"
        )
        r = requests.post(f"{BASE}/rotas/importar", json={
            "nome": f"Rota PT {SUFIXO}", "arquivo_origem": "pt.csv", "conteudo_csv": csv_pt,
        })
        show("POST importar CSV PT (201)", r.status_code == 201, f"{r.status_code}")
        rota_pt = r.json().get("rota_id") if r.status_code == 201 else None
        if rota_pt:
            rotas_criadas.append(rota_pt)
            leituras_pt = requests.get(f"{BASE}/leituras", params={"rota_id": rota_pt}).json()
            show("Aceleração Y mapeada (accel_y não nulo)",
                 bool(leituras_pt) and leituras_pt[0].get("accel_y") is not None,
                 str(leituras_pt[0].get("accel_y") if leituras_pt else None))

        # R5b: alias do typo "Acelere Y" (localização pt-BR do software OBD).
        csv_typo = (
            "# StartTime = 01/21/2026 08:00:00.0000 AM\n"
            "Time (sec), Velocidade do veículo (km/h), Aceleração X (m/s²), Acelere Y (m/s²)\n"
            "0, 50, 1.0, 2.0\n"
            "1, 60, 1.5, 2.5\n"
        )
        r = requests.post(f"{BASE}/rotas/importar", json={
            "nome": f"Rota typo {SUFIXO}", "arquivo_origem": "typo.csv", "conteudo_csv": csv_typo,
        })
        show("POST importar CSV 'Acelere Y' (201)", r.status_code == 201, f"{r.status_code}")
        rota_typo = r.json().get("rota_id") if r.status_code == 201 else None
        if rota_typo:
            rotas_criadas.append(rota_typo)
            leituras_typo = requests.get(f"{BASE}/leituras", params={"rota_id": rota_typo}).json()
            show("Acelere Y mapeada (accel_y não nulo)",
                 bool(leituras_typo) and leituras_typo[0].get("accel_y") is not None,
                 str(leituras_typo[0].get("accel_y") if leituras_typo else None))

        # R6: editar leitura remove o evento obsoleto.
        r = requests.post(f"{BASE}/rotas", json={"nome": f"Rota editar {SUFIXO}"})
        rota_ed = r.json().get("id") if r.status_code == 201 else None
        if rota_ed:
            rotas_criadas.append(rota_ed)
            r = requests.post(f"{BASE}/leituras", json={
                "rota_id": rota_ed, "data_hora": "2026-02-01T10:00:00",
                "velocidade": 150, "rpm": 3000,
            })
            leitura_ed = r.json()["id"]
            requests.get(f"{BASE}/rotas/{rota_ed}/resumo")
            antes = requests.get(f"{BASE}/eventos-risco", params={"rota_id": rota_ed}).json()
            tem_excesso = any(e["classificacao"] == "Excesso de velocidade" for e in antes)
            r = requests.put(f"{BASE}/leituras/{leitura_ed}", json={
                "rota_id": rota_ed, "data_hora": "2026-02-01T10:00:00",
                "velocidade": 50, "rpm": 3000,
            })
            show("PUT leitura corrigida (200)", r.status_code == 200, f"{r.status_code}")
            requests.get(f"{BASE}/rotas/{rota_ed}/resumo")
            depois = requests.get(f"{BASE}/eventos-risco", params={"rota_id": rota_ed}).json()
            show("Editar leitura remove evento obsoleto",
                 tem_excesso and not any(e["classificacao"] == "Excesso de velocidade" for e in depois),
                 f"{len(antes)} -> {len(depois)}")

        # R7: mover leitura para outra rota.
        r = requests.post(f"{BASE}/rotas", json={"nome": f"Rota A mover {SUFIXO}"})
        rota_a = r.json().get("id") if r.status_code == 201 else None
        r = requests.post(f"{BASE}/rotas", json={"nome": f"Rota B mover {SUFIXO}"})
        rota_b = r.json().get("id") if r.status_code == 201 else None
        if rota_a and rota_b:
            rotas_criadas.extend([rota_a, rota_b])
            r = requests.post(f"{BASE}/leituras", json={
                "rota_id": rota_a, "data_hora": "2026-03-01T10:00:00",
                "velocidade": 150, "rpm": 3000,
            })
            leitura_mv = r.json()["id"]
            requests.get(f"{BASE}/rotas/{rota_a}/resumo")
            r = requests.put(f"{BASE}/leituras/{leitura_mv}", json={
                "rota_id": rota_b, "data_hora": "2026-03-01T10:00:00",
                "velocidade": 150, "rpm": 3000,
            })
            show("PUT move leitura (200)", r.status_code == 200, f"{r.status_code}")
            r = requests.get(f"{BASE}/rotas/{rota_b}/resumo")
            show("resumo rota destino após mover (200)", r.status_code == 200, f"{r.status_code}")
            eventos_b = requests.get(f"{BASE}/eventos-risco", params={"rota_id": rota_b}).json()
            show("evento segue a leitura (rota_id correto)",
                 any(e["rota_id"] == rota_b for e in eventos_b),
                 str([(e["rota_id"], e["classificacao"]) for e in eventos_b]))
            eventos_a = requests.get(f"{BASE}/eventos-risco", params={"rota_id": rota_a}).json()
            show("rota origem sem eventos órfãos", len(eventos_a) == 0, str(len(eventos_a)))

        # R8: evento MANUAL sobrevive à reanálise forçada.
        r = requests.post(f"{BASE}/rotas", json={"nome": f"Rota manual {SUFIXO}"})
        rota_manual = r.json().get("id") if r.status_code == 201 else None
        if rota_manual:
            rotas_criadas.append(rota_manual)
            r = requests.post(f"{BASE}/leituras", json={
                "rota_id": rota_manual, "data_hora": "2026-04-01T10:00:00",
                "velocidade": 50, "rpm": 2000,
            })
            leitura_m = r.json()["id"]
            r = requests.post(f"{BASE}/eventos-risco", json={
                "leitura_id": leitura_m, "metodo": "MANUAL", "canal": "velocidade",
                "classificacao": "Evento manual", "valor": 50,
            })
            show("POST evento MANUAL (201)", r.status_code == 201, f"{r.status_code}")
            r = requests.post(f"{BASE}/rotas/{rota_manual}/analisar")
            show("POST reanalisar (200)", r.status_code == 200, f"{r.status_code}")
            eventos_m = requests.get(f"{BASE}/eventos-risco", params={"rota_id": rota_manual}).json()
            show("Reanálise preserva evento MANUAL",
                 any(e["metodo"] == "MANUAL" for e in eventos_m),
                 str([(e["metodo"], e["classificacao"]) for e in eventos_m]))

        # R9: timestamp com fração de segundo no PUT.
        if rota_csv_id:
            r = requests.post(f"{BASE}/leituras", json={
                "rota_id": rota_csv_id, "data_hora": "2026-01-21T08:00:00.500000",
                "velocidade": 55,
            })
            if r.status_code == 201:
                leitura_frac = r.json()["id"]
                r = requests.put(f"{BASE}/leituras/{leitura_frac}", json={
                    "rota_id": rota_csv_id, "data_hora": "2026-01-21T08:00:00.500000",
                    "velocidade": 60,
                })
                show("PUT leitura com fração de segundo (200)",
                     r.status_code == 200, f"{r.status_code}")
            else:
                show("POST leitura com fração de segundo (201)", False, f"{r.status_code}")

        # R10: concorrência na primeira análise (sem 500).
        linhas = [
            "# StartTime = 01/21/2026 08:00:00.0000 AM",
            "Time (sec), Vehicle speed (km/h), Engine RPM (RPM), Accel X (m/s²), Accel Y (m/s²)",
        ]
        for i in range(400):
            v = 120 if i % 50 == 0 else 60
            linhas.append(f"{i * 0.5}, {v}, {3000 if i % 50 else 6000}, 0.2, {4.0 if i % 40 == 0 else 0.1}")
        r = requests.post(f"{BASE}/rotas/importar", json={
            "nome": f"Rota conc {SUFIXO}", "arquivo_origem": "c.csv",
            "conteudo_csv": "\n".join(linhas),
        })
        rota_conc = r.json().get("rota_id") if r.status_code == 201 else None
        if rota_conc:
            rotas_criadas.append(rota_conc)

            def chama(caminho):
                try:
                    return requests.get(
                        f"{BASE}/rotas/{rota_conc}/{caminho}", timeout=60
                    ).status_code
                except requests.exceptions.RequestException:
                    return 0

            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
                status = list(ex.map(chama, ["resumo", "grafico", "resumo",
                                             "grafico", "resumo", "grafico"]))
            show("Análise concorrente sem 500", all(s == 200 for s in status), str(status))

        # ---------------------------------------------------------------- #
        # Exclusões e cascade
        # ---------------------------------------------------------------- #
        if evento_id:
            r = requests.delete(f"{BASE}/eventos-risco/{evento_id}")
            show("DELETE evento (200)", r.status_code == 200, f"{r.status_code}")

        if leitura_id:
            r = requests.delete(f"{BASE}/leituras/{leitura_id}")
            show("DELETE leitura (200)", r.status_code == 200, f"{r.status_code}")

        if rota_csv_id:
            r = requests.delete(f"{BASE}/rotas/{rota_csv_id}")
            show("DELETE rota remove leituras/eventos (200)", r.status_code == 200)
            r = requests.get(f"{BASE}/leituras", params={"rota_id": rota_csv_id})
            show("Cascade: leituras removidas", r.status_code == 200 and r.json() == [])
            r = requests.get(f"{BASE}/eventos-risco", params={"rota_id": rota_csv_id})
            show("Cascade: eventos removidos", r.status_code == 200 and r.json() == [])

        if rota_id:
            r = requests.delete(f"{BASE}/rotas/{rota_id}")
            show("DELETE rota de teste (200)", r.status_code == 200, f"{r.status_code}")
            r = requests.get(f"{BASE}/rotas/{rota_id}")
            show("Rota excluída não existe (404)", r.status_code == 404)

    finally:
        # Garante que o banco volte ao estado vazio mesmo se um teste falhar.
        for rid in dict.fromkeys(rotas_criadas):
            try:
                requests.delete(f"{BASE}/rotas/{rid}", timeout=15)
            except requests.exceptions.RequestException:
                pass

    print("\nTestes concluídos.")
    if falhas:
        print(f"FALHAS: {falhas}")
        raise SystemExit(1)
    print("Todos os testes passaram.")


if __name__ == "__main__":
    main()
