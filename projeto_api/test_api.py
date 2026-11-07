"""Teste da API — domínio de telemetria veicular (rotas por usuário).

Executar com a API em execução:  python test_api.py
"""
import requests

BASE = "http://localhost:8080/telemetria"


def show(titulo, ok, detalhe=""):
    print(f"[{'OK' if ok else 'FALHOU'}] {titulo}" + (f" -> {detalhe}" if detalhe else ""))


# CSV de exemplo (com StartTime e colunas mínimas).
CSV_EXEMPLO = """# StartTime = 01/21/2026 08:00:00.0000 AM
Time (sec), Vehicle speed (km/h), Engine RPM (RPM), Accel X (m/s²), Accel Y (m/s²), Accel Z (m/s²)
0.0, 0, 800, 0.1, 0.1, 0.1
1.0, 10, 1000, 0.2, 0.1, 0.1
2.0, 25, 1500, 0.3, 0.2, 0.1
3.0, 45, 2200, 0.5, 0.3, 0.2
4.0, 60, 2600, 0.4, 0.2, 0.1
5.0, 55, 2300, -0.5, -0.2, 0.1
6.0, 40, 1800, -0.3, -0.1, 0.1
7.0, 20, 1200, -0.2, 0.0, 0.1
8.0, 0, 800, 0.0, 0.0, 0.1
"""


def main():
    # ---- Cadastro e login ----
    r = requests.post(f"{BASE}/usuarios", json={"nome": "teste_api", "senha": "123"})
    show("POST usuário (201)", r.status_code == 201, f"{r.status_code}")
    usuario_id = r.json().get("id") if r.status_code == 201 else None

    r = requests.post(f"{BASE}/usuarios", json={"nome": "teste_api", "senha": "123"})
    show("POST usuário duplicado (400)", r.status_code == 400, f"{r.status_code}")

    r = requests.post(f"{BASE}/usuarios/login", json={"nome": "teste_api", "senha": "errada"})
    show("POST login senha errada (401)", r.status_code == 401, f"{r.status_code}")

    r = requests.post(f"{BASE}/usuarios/login", json={"nome": "teste_api", "senha": "123"})
    show("POST login correto (200)", r.status_code == 200, f"{r.status_code}")

    # ---- Importar CSV como rota ----
    r = requests.post(f"{BASE}/rotas/importar", json={
        "usuario_id": usuario_id, "nome": "Rota de Teste",
        "arquivo_origem": "teste.csv", "conteudo_csv": CSV_EXEMPLO,
    })
    show("POST importar CSV (201)", r.status_code == 201, f"{r.status_code} {r.text[:80]}")
    rota_id = r.json().get("rota_id") if r.status_code == 201 else None

    # ---- Rotas do usuário ----
    r = requests.get(f"{BASE}/rotas", params={"usuario_id": usuario_id})
    show("GET rotas do usuário (200)", r.status_code == 200 and len(r.json()) >= 1)

    # ---- Análise e gráfico ----
    if rota_id:
        r = requests.post(f"{BASE}/rotas/{rota_id}/analisar")
        show("POST analisar rota (200)", r.status_code == 200, f"{r.status_code}")

        r = requests.get(f"{BASE}/rotas/{rota_id}/grafico")
        show("GET gráfico da rota (200)", r.status_code == 200 and "pontos" in r.json())

        r = requests.get(f"{BASE}/eventos-risco", params={"rota_id": rota_id})
        show("GET eventos da rota (200)", r.status_code == 200)

    # ---- Regras de negócio ----
    if rota_id:
        r = requests.post(f"{BASE}/leituras", json={
            "rota_id": 999999, "data_hora": "2026-11-06T10:00:00",
        })
        show("POST leitura rota inexistente (400)", r.status_code == 400, f"{r.status_code}")

    r = requests.get(f"{BASE}/rotas/999999")
    show("GET rota inexistente (404)", r.status_code == 404)

    r = requests.delete(f"{BASE}/usuarios/{usuario_id}")
    show("DELETE usuário com rotas (409)", r.status_code == 409, f"{r.status_code}")

    print("\nTestes concluídos.")


if __name__ == "__main__":
    main()
