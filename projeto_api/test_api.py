"""Teste da API — domínio de telemetria veicular (rotas por usuário).

Executar com a API em execução:  python test_api.py
"""
import time

import requests

BASE = "http://localhost:8080/telemetria"
NOME_TESTE = f"teste_api_{int(time.time())}"


def show(titulo, ok, detalhe=""):
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
    # ---- Cadastro e login ----
    r = requests.post(f"{BASE}/usuarios", json={"nome": NOME_TESTE, "senha": "123"})
    show("POST usuário senha curta (400)", r.status_code == 400, f"{r.status_code}")

    r = requests.post(f"{BASE}/usuarios", json={"nome": NOME_TESTE, "senha": "123456"})
    show("POST usuário (201)", r.status_code == 201, f"{r.status_code}")
    usuario_id = r.json().get("id") if r.status_code == 201 else None

    r = requests.post(f"{BASE}/usuarios", json={"nome": NOME_TESTE, "senha": "123456"})
    show("POST usuário duplicado (400)", r.status_code == 400, f"{r.status_code}")

    r = requests.post(f"{BASE}/usuarios/login", json={"nome": NOME_TESTE, "senha": "errada"})
    show("POST login senha errada (401)", r.status_code == 401, f"{r.status_code}")

    r = requests.post(f"{BASE}/usuarios/login", json={"nome": NOME_TESTE, "senha": "123456"})
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

    # ---- Análise, gráfico, resumo e eventos ----
    if rota_id:
        r = requests.post(f"{BASE}/rotas/{rota_id}/analisar")
        show("POST analisar rota (200)", r.status_code == 200, f"{r.status_code}")

        r = requests.get(f"{BASE}/rotas/{rota_id}/grafico")
        show("GET gráfico da rota (200)", r.status_code == 200 and "pontos" in r.json())

        r = requests.get(f"{BASE}/rotas/{rota_id}/resumo")
        show("GET resumo da rota (200, com score)",
             r.status_code == 200 and "score" in r.json())

        r = requests.get(f"{BASE}/eventos-risco", params={"rota_id": rota_id})
        show("GET eventos da rota (200)", r.status_code == 200)

        r = requests.get(f"{BASE}/eventos-risco",
                         params={"rota_id": rota_id, "tipo": "Frenagem brusca"})
        show("GET eventos filtro por tipo (200)", r.status_code == 200)

    # ---- Configurações (limiares) ----
    r = requests.get(f"{BASE}/configuracoes/limiares")
    show("GET limiares (200)", r.status_code == 200 and "velocidade_max" in r.json())
    velocidade_original = r.json().get("velocidade_max", 100)

    r = requests.put(f"{BASE}/configuracoes/limiares",
                     json={"velocidade_max": velocidade_original + 5})
    show("PUT limiares reanalisa rotas (200)",
         r.status_code == 200 and "rotas_reanalisadas" in r.json(),
         f"{r.status_code} {r.text[:80]}")

    # Restaura o limiar original para não deixar a configuração alterada.
    requests.put(f"{BASE}/configuracoes/limiares",
                 json={"velocidade_max": velocidade_original})

    # ---- CRUD de configurações ----
    r = requests.post(f"{BASE}/configuracoes", json={"chave": "teste_config", "valor": "abc"})
    show("POST configuração (201)", r.status_code == 201, f"{r.status_code}")
    config_id = r.json().get("id") if r.status_code == 201 else None

    r = requests.post(f"{BASE}/configuracoes", json={"chave": "teste_config", "valor": "xyz"})
    show("POST configuração duplicada (400)", r.status_code == 400, f"{r.status_code}")

    if config_id:
        r = requests.put(f"{BASE}/configuracoes/{config_id}", json={"valor": "def"})
        show("PUT configuração (200)",
             r.status_code == 200 and r.json().get("valor") == "def")

        r = requests.delete(f"{BASE}/configuracoes/{config_id}")
        show("DELETE configuração (200)", r.status_code == 200)

    # ---- Comparação ----
    if rota_id:
        r = requests.post(f"{BASE}/rotas/comparar", json={"rota_ids": [rota_id]})
        show("POST comparar rotas (200)", r.status_code == 200)

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

    # Limpeza: exclui a rota (cascata em leituras/eventos) e depois o usuário.
    if rota_id:
        r = requests.delete(f"{BASE}/rotas/{rota_id}")
        show("DELETE rota com leituras (200)", r.status_code == 200, f"{r.status_code}")

    r = requests.delete(f"{BASE}/usuarios/{usuario_id}")
    show("DELETE usuário sem rotas (200)", r.status_code == 200, f"{r.status_code}")

    print("\nTestes concluídos.")


if __name__ == "__main__":
    main()
