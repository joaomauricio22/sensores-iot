"""Captura as telas da interface gráfica (para inserir nos slides).

Abre a janela Tkinter com dados de exemplo criados pela API, fotografa cada
seção e remove a rota de exemplo ao final.
As imagens são salvas em ../apresentacao/imgs/*.png

Executar (com a API no ar):
    python capturar_telas.py
"""
import os
import sys
import time
import tkinter as tk

from PIL import ImageGrab

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import ApiClient
from main import App

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

    # Cria uma rota de exemplo para as capturas.
    resp = api.importar_csv("Rota de Exemplo", "exemplo.csv", CSV)
    if resp.status_code not in (200, 201):
        print("Não foi possível criar a rota de exemplo:", resp.text)
        return
    rota_id = resp.json()["rota_id"]
    api.analisar_rota(rota_id)

    root = tk.Tk()
    app = App(root, api)
    app.definir_rota(rota_id)
    root.update()

    # Dados → Rotas / Leituras / Eventos
    app.mostrar("dados")
    app.secoes["dados"].notebook.select(app.secoes["dados"].rota_tab)
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
        ("comparar", "comparar.png", 0.4),
    ]:
        app.mostrar(chave)
        root.update()
        capture(root, nome, delay)

    root.destroy()

    # Remove a rota de exemplo para deixar o banco como estava.
    api.excluir_rota(rota_id)
    print("Capturas concluídas.")


if __name__ == "__main__":
    main()
