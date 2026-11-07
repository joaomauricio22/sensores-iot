"""Captura as telas da interface gráfica (para inserir nos slides).

Abre a janela Tkinter com os dados reais da API e fotografa cada aba.
As imagens são salvas em ../apresentacao/imgs/*.png

Executar (com a API no ar e um usuário/rota criados):
    python capturar_telas.py
"""
import os
import sys
import time
import tkinter as tk

from PIL import ImageGrab

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import ApiClient
from main import App, LoginWindow

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apresentacao", "imgs")

CSV = """# StartTime = 01/21/2026 08:00:00.0000 AM
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


def capture(widget, name, delay=0.4):
    widget.update_idletasks()
    widget.update()
    time.sleep(delay)
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

    # Prepara um usuário e uma rota de exemplo.
    r = api.registrar("joao", "123456")
    if r.status_code in (200, 201):
        api.usuario_id = r.json().get("id")
    else:
        api.login("joao", "123456")
    import requests
    r = requests.post(f"{ApiClient.BASE_URL}/rotas/importar", json={
        "usuario_id": api.usuario_id, "nome": "Rota de Exemplo",
        "arquivo_origem": "exemplo.csv", "conteudo_csv": CSV,
    })
    rota_id = r.json()["rota_id"]

    # Tela de login.
    root = tk.Tk()
    LoginWindow(root, api)
    root.update()
    capture(root, "login.png")
    root.destroy()

    # Janela principal.
    root = tk.Tk()
    app = App(root, api)
    app.rota_atual_id = rota_id
    app.refresh_detalhes()
    root.update()

    capturas = [
        (app.rota_tab, "rotas.png", 0.4),
        (app.dashboard_tab, "dashboard.png", 0.4),
        (app.eventos_tab, "eventos.png", 0.4),
        (app.grafico_tab, "grafico.png", 0.6),
        (app.mapa_tab, "mapa.png", 2.5),
        (app.config_tab, "config.png", 0.4),
    ]
    for tab, nome, delay in capturas:
        app.notebook.select(tab)
        root.update()
        time.sleep(0.4)
        capture(root, nome, delay)

    root.destroy()
    print("Capturas concluídas.")


if __name__ == "__main__":
    main()
