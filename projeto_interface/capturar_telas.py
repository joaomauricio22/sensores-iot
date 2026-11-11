"""Captura as telas da interface gráfica (para inserir nos slides).

Abre a janela Tkinter com dados sintéticos de telemetria, fotografa cada
seção e deixa duas rotas de exemplo no banco para facilitar a demonstração.

Executar (com a API no ar):
    python capturar_telas.py          # pede confirmação antes de apagar rotas
    python capturar_telas.py --sim    # pula a confirmação (útil em CI)
"""
import math
import os
import random
import sys
import time
import tkinter as tk
from tkinter import messagebox

from PIL import ImageGrab

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import ApiClient
from main import App

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apresentacao", "imgs")


def _gerar_csv(seed, base_vel, janelas):
    """Gera um CSV sintético de telemetria com anomalias curtas e isoladas.

    ``janelas`` é uma lista de tuplas ``(tipo, início, duração)`` que descreve
    cada evento (frenagem/aceleração brusca, curva, excesso de velocidade,
    RPM excessivo e acelerador brusco). O restante é um cruzeiro suave.
    """
    rng = random.Random(seed)
    dt = 0.5
    n = 720
    linhas = [
        "# StartTime = 01/21/2026 08:00:00.0000 AM",
        "Time (sec), Vehicle speed (km/h), Engine RPM (RPM), Accel X (m/s²), "
        "Accel Y (m/s²), Accel Z (m/s²), Absolute throttle position (%), "
        "Latitude (deg), Longitude (deg)",
    ]
    lat0, lon0 = -22.588833, -43.284300
    lat, lon = lat0, lon0
    rumo = math.radians(40.0)  # direção fixa (nordeste) da rota sintética
    speed = base_vel
    rpm = 850.0 + base_vel * 30.0
    throttle = 10.0 + base_vel * 0.35

    ativo = {}
    for tipo, inicio, duracao in janelas:
        for j in range(duracao):
            ativo[inicio + j] = tipo

    for i in range(n):
        t = i * dt
        k = ativo.get(i)
        prev = speed

        if k == "fren":
            speed = max(15.0, speed - 13.0)
        elif k == "acel":
            speed = min(115.0, speed + 11.0)
        elif k == "curva":
            speed = base_vel + 5.0
        elif k == "excesso":
            # Sobe gradualmente até ultrapassar o limite (aceleração ~0,23 g,
            # abaixo do limiar de "aceleração brusca", para não gerar cascata).
            speed = min(108.0, speed + 4.0)
        elif k == "rpm":
            speed = base_vel + 4.0
        elif k == "acelerador":
            speed = base_vel - 8.0
        else:
            # Cruzeiro quase constante, com deriva bem suave.
            alvo = base_vel + 2.0 * math.sin(i / 60.0)
            speed += (alvo - speed) * 0.08
            speed = max(0.0, min(115.0, speed))
        speed = round(speed, 1)

        if k in ("fren", "acel"):
            ax = (speed - prev) / 3.6 / dt
        else:
            ax = rng.gauss(0.0, 0.04)

        if k == "curva":
            ay = 4.0 * (1 if i % 2 == 0 else -1)
        else:
            ay = rng.gauss(0.0, 0.05)

        az = rng.gauss(0.1, 0.03)

        if k == "rpm":
            rpm = 6100.0
        else:
            rpm = 850.0 + speed * 30.0 + rng.gauss(0, 40)
        rpm = round(rpm, 0)

        if k == "acelerador":
            throttle = 75.0
        else:
            throttle = 10.0 + speed * 0.35 + rng.gauss(0, 0.5)
        throttle = round(max(0.0, min(100.0, throttle)), 1)

        # GPS integrado a partir da velocidade (coerente com o painel):
        # desloca-se na direção fixa pela distância percorrida no passo.
        vm = (prev + speed) / 2.0  # km/h médio do passo
        passo_km = vm / 3.6 * dt / 1000.0
        lat += passo_km * math.cos(rumo) / 111.32
        lon += passo_km * math.sin(rumo) / (111.32 * math.cos(math.radians(lat)))
        linhas.append(
            f"{t:.1f}, {speed:.1f}, {rpm:.0f}, {ax:.2f}, {ay:.2f}, "
            f"{az:.2f}, {throttle:.1f}, {lat:.6f}, {lon:.6f}"
        )
    return "\n".join(linhas)


def capture(widget, name, delay=0.4):
    widget.update_idletasks()
    # Bombeia o event loop para concluir os carregamentos assíncronos
    # (análise, gráfico, sensores) antes de fotografar.
    fim = time.time() + delay
    while time.time() < fim:
        widget.update()
        time.sleep(0.03)
    x = widget.winfo_rootx()
    y = widget.winfo_rooty()
    w = widget.winfo_width()
    h = widget.winfo_height()
    if w <= 0 or h <= 0:
        return
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img.save(os.path.join(OUT_DIR, name))
    print("saved", name)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    api = ApiClient()

    # Estado de demonstração consistente: remove rotas antigas e importa duas
    # rotas sintéticas com perfis de condução distintos. Como apagar é uma ação
    # destrutiva, pede confirmação (a menos que --sim seja passado).
    # Remove apenas as rotas de demonstração (nomes fixos), preservando qualquer
    # rota real importada pelo usuário. Como apagar é uma ação destrutiva, pede
    # confirmação (a menos que --sim seja passado).
    resp = api.list_rotas()
    rotas_existentes = resp.json() if resp.status_code == 200 else []
    nomes_demo = {"Condução Agressiva", "Condução Defensiva"}
    demos = [r for r in rotas_existentes if r.get("nome") in nomes_demo]
    outras = [r for r in rotas_existentes if r.get("nome") not in nomes_demo]
    if demos and "--sim" not in sys.argv:
        print(f"Atenção: {len(demos)} rota(s) de demonstração serão EXCLUÍDAS "
              f"({len(outras)} rota(s) sua(s) serão preservadas).")
        if input("Digite 'sim' para continuar (ou Ctrl+C para cancelar): ").strip().lower() != "sim":
            print("Cancelado.")
            return
    for rota in demos:
        api.excluir_rota(rota["id"])

    # Ambos os trajetos compartilham os mesmos tipos de evento (para que o
    # modelo de ML os considere "típicos" entre si), variando a intensidade.
    janelas_agressivo = [
        ("fren", 60, 1),
        ("acel", 90, 1),
        ("curva", 140, 2),
        ("fren", 200, 1),
        ("acel", 230, 1),
        ("acelerador", 270, 1),
        ("curva", 320, 2),
        ("fren", 380, 1),
        ("acel", 410, 1),
        ("curva", 460, 2),
        ("excesso", 520, 11),
        ("rpm", 560, 1),
        ("acelerador", 590, 1),
        ("fren", 640, 1),
        ("acel", 670, 1),
    ]
    janelas_defensivo = [
        ("curva", 400, 2),
        ("excesso", 510, 11),
        ("rpm", 560, 1),
    ]

    rotas = [
        ("Condução Agressiva", _gerar_csv(1, 70.0, janelas_agressivo)),
        ("Condução Defensiva", _gerar_csv(2, 70.0, janelas_defensivo)),
    ]
    ids = []
    for nome, csv_texto in rotas:
        resp = api.importar_csv(nome, f"{nome}.csv", csv_texto)
        if resp.status_code not in (200, 201):
            print(f"Não foi possível criar '{nome}':", resp.text)
            return
        ids.append(resp.json()["rota_id"])
    rota_a, rota_b = ids
    api.analisar_rota(rota_a)
    api.analisar_rota(rota_b)

    root = tk.Tk()
    root.attributes("-topmost", True)
    app = App(root, api)
    app.definir_rota(rota_a)
    root.update()
    root.lift()
    root.focus_force()

    # Dados → Rotas / Leituras / Eventos
    app.mostrar("dados")
    app.secoes["dados"].notebook.select(app.secoes["dados"].rota_tab)
    app.secoes["dados"].rota_tab.atualizar()
    root.update()
    capture(root, "rotas.png")

    app.secoes["dados"].notebook.select(app.secoes["dados"].leitura_tab)
    app.secoes["dados"].leitura_tab.atualizar()
    root.update()
    capture(root, "leituras.png")

    app.secoes["dados"].notebook.select(app.secoes["dados"].evento_tab)
    app.secoes["dados"].evento_tab.atualizar()
    root.update()
    capture(root, "eventos.png")

    # Demais seções
    for chave, nome, delay in [
        ("visao", "dashboard.png", 0.5),
        ("grafico", "grafico.png", 0.7),
        ("sensores", "sensores.png", 0.6),
    ]:
        app.mostrar(chave)
        root.update()
        capture(root, nome, delay)

    # Comparar: duas rotas, sem caixas de diálogo bloqueando a captura.
    app.mostrar("comparar")
    root.update()
    comp = app.secoes["comparar"]
    comp.combo_a.current(0)
    comp.combo_b.current(1)
    original = messagebox.showinfo
    messagebox.showinfo = lambda *a, **k: None
    try:
        comp.comparar()
    finally:
        messagebox.showinfo = original
    capture(root, "comparar.png", delay=0.6)

    root.destroy()
    print("Capturas concluídas.")


if __name__ == "__main__":
    main()
