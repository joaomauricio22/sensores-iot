"""Teste manual da API (endpoints e regras de negócio) — domínio veicular.

Executar com a API em execução:  python test_api.py
"""
import requests

BASE = "http://localhost:8080/telemetria"


def show(titulo, ok, detalhe=""):
    print(f"[{'OK' if ok else 'FALHOU'}] {titulo}" + (f" -> {detalhe}" if detalhe else ""))


def main():
    # ---- Veículos ----
    r = requests.get(f"{BASE}/veiculos")
    show("GET /veiculos (200 e 4 veículos)", r.status_code == 200 and len(r.json()) == 4)

    r = requests.post(f"{BASE}/veiculos", json={"identificador": "VEICULO-001"})
    show("POST veículo duplicado (400)", r.status_code == 400, f"{r.status_code}")

    r = requests.post(f"{BASE}/veiculos", json={"identificador": "VEICULO-TESTE", "modelo": "Teste"})
    show("POST veículo novo (201)", r.status_code == 201)
    novo_veiculo_id = r.json().get("id") if r.status_code == 201 else None

    # ---- Parâmetros ----
    r = requests.get(f"{BASE}/parametros")
    show("GET /parametros (200 e 8 parâmetros)", r.status_code == 200 and len(r.json()) == 8)

    # ---- Mapeamentos ----
    r = requests.get(f"{BASE}/mapeamentos")
    show("GET /mapeamentos (200 e 14 mapeamentos)", r.status_code == 200 and len(r.json()) == 14)

    # ---- Leituras ----
    r = requests.post(f"{BASE}/leituras", json={
        "veiculo_id": 999, "data_hora": "2026-11-06T10:00:00",
    })
    show("POST leitura veículo inexistente (400)", r.status_code == 400, f"{r.status_code}")

    r = requests.post(f"{BASE}/leituras", json={
        "veiculo_id": novo_veiculo_id, "data_hora": "2026-11-06T10:00:00",
        "velocidade": 60, "rpm": 2000, "accel_x": 1.0, "accel_y": 0.5, "accel_z": 9.8,
    })
    show("POST leitura válida (201)", r.status_code == 201, f"{r.status_code}")
    nova_leitura_id = r.json().get("id") if r.status_code == 201 else None

    r = requests.post(f"{BASE}/leituras", json={
        "veiculo_id": novo_veiculo_id, "data_hora": "2026-11-06T10:00:00",
    })
    show("POST leitura duplicada (400)", r.status_code == 400, f"{r.status_code}")

    r = requests.post(f"{BASE}/leituras", json={
        "veiculo_id": novo_veiculo_id, "data_hora": "2026-11-06T10:05:00",
        "velocidade": "abc",
    })
    show("POST leitura valor não numérico (422)", r.status_code == 422, f"{r.status_code}")

    # ---- Análise ----
    r = requests.post(f"{BASE}/veiculos/{novo_veiculo_id}/analisar")
    show("POST analisar veículo (200)", r.status_code == 200, f"{r.status_code}")

    r = requests.get(f"{BASE}/veiculos/1/estatisticas")
    show("GET estatísticas veículo 1 (200)", r.status_code == 200 and "forca_g_media" in r.json())

    # ---- Eventos ----
    r = requests.get(f"{BASE}/eventos-risco")
    show("GET /eventos-risco (200)", r.status_code == 200, f"total={len(r.json())}")

    # ---- 404 e integridade ----
    r = requests.get(f"{BASE}/leituras/999999")
    show("GET leitura inexistente (404)", r.status_code == 404)

    r = requests.delete(f"{BASE}/veiculos/1")
    show("DELETE veículo com leituras (409)", r.status_code == 409, f"{r.status_code}")

    print("\nTestes concluídos.")


if __name__ == "__main__":
    main()
