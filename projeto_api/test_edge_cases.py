"""Testes de casos-limite (edge cases) da API.

Investiga comportamentos de borda para procurar bugs:
fuso horário, valores zero/negativos, 404, integridade, etc.

Executar (com a API no ar):  python test_edge_cases.py
"""
import requests

BASE = "http://localhost:8080/iot"


def show(titulo, ok, detalhe=""):
    status = "OK" if ok else "FALHOU"
    print(f"[{status}] {titulo}" + (f" -> {detalhe}" if detalhe else ""))


def post_leituras(sensor_id, valor, data_hora):
    return requests.post(f"{BASE}/leituras", json={
        "sensor_id": sensor_id, "valor": valor, "data_hora": data_hora,
    })


def main():
    # ---- Fuso horário (suspeita de bug) ----
    r = post_leituras(1, 26.11, "2026-10-30T14:00:00Z")
    show("POST leitura data_hora com 'Z' (UTC)", r.status_code == 201, f"{r.status_code} {r.text[:80]}")

    r = post_leituras(1, 26.12, "2026-10-30T14:00:00+00:00")
    show("POST leitura data_hora com '+00:00'", r.status_code == 201, f"{r.status_code} {r.text[:80]}")

    r = post_leituras(1, 26.13, "2026-10-30T15:30:00")
    show("POST leitura data_hora sem timezone", r.status_code == 201, f"{r.status_code}")

    # ---- Valores numéricos de borda ----
    r = post_leituras(1, 0, "2026-10-30T16:00:00")
    show("POST leitura valor=0 (deve aceitar)", r.status_code == 201, f"{r.status_code} {r.text[:60]}")

    r = post_leituras(1, -3.5, "2026-10-30T16:30:00")
    show("POST leitura valor negativo", r.status_code == 201, f"{r.status_code}")

    # ---- Limites iguais ----
    r = requests.post(f"{BASE}/sensores", json={
        "identificador": "SENSOR-EDGE", "tipo_sensor_id": 1,
        "limite_min": 10, "limite_max": 10,
    })
    show("POST sensor limite_min == limite_max", r.status_code == 201, f"{r.status_code} {r.text[:60]}")
    sensor_edge_id = r.json().get("id") if r.status_code == 201 else None

    # ---- Campo obrigatório ausente / vazio ----
    r = requests.post(f"{BASE}/leituras", json={"sensor_id": 1, "valor": 30.0})
    show("POST leitura sem data_hora (422)", r.status_code == 422, f"{r.status_code}")

    r = requests.post(f"{BASE}/tipos-sensor", json={"nome": "", "unidade": "x"})
    show("POST tipo com nome vazio (400)", r.status_code == 400, f"{r.status_code} {r.text[:60]}")

    # ---- 404 (recursos inexistentes) ----
    r = requests.get(f"{BASE}/leituras/999999")
    show("GET leitura inexistente (404)", r.status_code == 404, f"{r.status_code}")

    r = requests.put(f"{BASE}/sensores/999999", json={
        "identificador": "X", "tipo_sensor_id": 1, "limite_min": 0, "limite_max": 1,
    })
    show("PUT sensor inexistente (404)", r.status_code == 404, f"{r.status_code}")

    r = requests.delete(f"{BASE}/anomalias/999999")
    show("DELETE anomalia inexistente (404)", r.status_code == 404, f"{r.status_code}")

    # ---- Integridade (exclusão proibida) ----
    r = requests.delete(f"{BASE}/sensores/1")
    show("DELETE sensor com leituras (409)", r.status_code == 409, f"{r.status_code}")

    r = requests.delete(f"{BASE}/tipos-sensor/1")
    show("DELETE tipo com sensores (409)", r.status_code == 409, f"{r.status_code}")

    # ---- Duplicidade via PUT ----
    r = requests.get(f"{BASE}/leituras")
    leituras = r.json()
    if len(leituras) >= 2:
        a, b = leituras[0], leituras[1]
        r = requests.put(f"{BASE}/leituras/{a['id']}", json={
            "sensor_id": b["sensor_id"], "valor": b["valor"], "data_hora": b["data_hora"],
        })
        show("PUT leitura gerando duplicata (400)", r.status_code == 400, f"{r.status_code} {r.text[:60]}")

    # ---- Estatísticas de sensor sem leituras ----
    if sensor_edge_id:
        r = requests.get(f"{BASE}/sensores/{sensor_edge_id}/estatisticas")
        body = r.json()
        show("GET estatisticas sensor sem leituras (sem 'media')",
             r.status_code == 200 and "media" not in body, f"{r.status_code} chaves={list(body.keys())}")

    # ---- Classificação ML com histórico insuficiente ----
    if sensor_edge_id:
        r = requests.post(f"{BASE}/leituras", json={
            "sensor_id": sensor_edge_id, "valor": 11.0, "data_hora": "2026-10-30T17:00:00",
        })
        lid = r.json().get("id") if r.status_code == 201 else None
        if lid:
            r = requests.post(f"{BASE}/leituras/{lid}/classificar")
            show("POST classificar com pouco histórico (INDETERMINADO)",
                 r.status_code == 200 and r.json().get("classificacao") == "INDETERMINADO",
                 f"classificacao={r.json().get('classificacao')}")

    print("\nTestes concluídos.")


if __name__ == "__main__":
    main()
