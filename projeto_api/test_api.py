"""Script de teste manual da API (valida endpoints e regras de negócio).

Executar com a API em execução:  python test_api.py
"""
import requests

BASE = "http://localhost:8080/iot"


def show(titulo, ok, detalhe=""):
    status = "OK" if ok else "FALHOU"
    print(f"[{status}] {titulo}" + (f" -> {detalhe}" if detalhe else ""))


def main():
    # ---- Tipos de sensor ----
    r = requests.get(f"{BASE}/tipos-sensor")
    show("GET /tipos-sensor (200)", r.status_code == 200)

    r = requests.post(f"{BASE}/tipos-sensor", json={"nome": "Temperatura", "unidade": "°C"})
    show("POST tipo duplicado (400)", r.status_code == 400, f"{r.status_code} {r.text[:70]}")

    r = requests.post(f"{BASE}/tipos-sensor", json={"nome": "Pressão", "unidade": "hPa"})
    show("POST tipo novo (201)", r.status_code == 201)

    # ---- Sensores ----
    r = requests.get(f"{BASE}/sensores")
    sensores = r.json() if r.status_code == 200 else []
    show("GET /sensores (200)", r.status_code == 200 and len(sensores) == 2)

    # Resolve dinamicamente o sensor de temperatura
    sensor_temp = next((s for s in sensores if s["identificador"] == "SENSOR-001"), None)
    sensor_id = sensor_temp["id"] if sensor_temp else 1

    r = requests.post(f"{BASE}/sensores", json={
        "identificador": "SENSOR-001", "tipo_sensor_id": 1,
        "limite_min": 10, "limite_max": 40,
    })
    show("POST sensor duplicado (400)", r.status_code == 400, f"{r.status_code}")

    r = requests.post(f"{BASE}/sensores", json={
        "identificador": "SENSOR-X", "tipo_sensor_id": 999,
        "limite_min": 10, "limite_max": 40,
    })
    show("POST sensor tipo inexistente (400)", r.status_code == 400, f"{r.status_code}")

    r = requests.post(f"{BASE}/sensores", json={
        "identificador": "SENSOR-X", "tipo_sensor_id": 1,
        "limite_min": 50, "limite_max": 40,
    })
    show("POST sensor limite_min>max (400)", r.status_code == 400, f"{r.status_code}")

    # ---- Leituras ----
    r = requests.post(f"{BASE}/leituras", json={
        "sensor_id": 999, "valor": 25.0, "data_hora": "2026-10-30T16:00:00",
    })
    show("POST leitura sensor inexistente (400)", r.status_code == 400, f"{r.status_code}")

    r = requests.post(f"{BASE}/leituras", json={
        "sensor_id": sensor_id, "valor": "abc", "data_hora": "2026-10-30T16:00:00",
    })
    show("POST leitura valor nao numerico (422)", r.status_code == 422, f"{r.status_code}")

    r = requests.post(f"{BASE}/leituras", json={
        "sensor_id": sensor_id, "valor": 27.7, "data_hora": "2026-10-30T16:00:00",
    })
    show("POST leitura valida (201)", r.status_code == 201, f"{r.status_code}")
    nova_leitura_id = r.json().get("id") if r.status_code == 201 else None

    r = requests.post(f"{BASE}/leituras", json={
        "sensor_id": sensor_id, "valor": 27.7, "data_hora": "2026-10-30T16:00:00",
    })
    show("POST leitura duplicada (400)", r.status_code == 400, f"{r.status_code}")

    # ---- Análise de anomalias ----
    r = requests.get(f"{BASE}/leituras")
    leituras = r.json()
    anomalia_para_analisar = next((l for l in leituras if l["valor"] == 75.0), None)
    if anomalia_para_analisar:
        lid = anomalia_para_analisar["id"]
        r = requests.post(f"{BASE}/leituras/{lid}/analisar")
        metodos = [a["metodo"] for a in r.json()] if r.status_code == 200 else []
        show("POST analisar leitura anômala (200 + métodos)",
             r.status_code == 200 and len(metodos) >= 1, f"metodos={metodos}")

    # ---- Classificação ML ----
    if nova_leitura_id:
        r = requests.post(f"{BASE}/leituras/{nova_leitura_id}/classificar")
        show("POST classificar ML (200)", r.status_code == 200,
             f"classificacao={r.json().get('classificacao')}")

    # ---- Estatísticas ----
    r = requests.get(f"{BASE}/sensores/{sensor_id}/estatisticas")
    show("GET estatisticas sensor (200)", r.status_code == 200 and "media" in r.json(),
         f"{r.status_code}")

    # ---- Anomalias registradas ----
    r = requests.get(f"{BASE}/anomalias")
    show("GET /anomalias (200)", r.status_code == 200, f"total={len(r.json())}")

    print("\nTestes concluídos.")


if __name__ == "__main__":
    main()
