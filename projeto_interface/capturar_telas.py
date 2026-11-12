"""Captura as telas da interface gráfica (para inserir nos slides).

Abre a janela Tkinter com dados sintéticos de telemetria, fotografa cada
seção e deixa duas rotas de exemplo no banco para facilitar a demonstração.

Executar (com a API no ar):
    python capturar_telas.py          # pede confirmação antes de apagar rotas
    python capturar_telas.py --sim    # pula a confirmação (útil em CI)
"""
import os
import sys
import time
import tkinter as tk
from tkinter import messagebox

from PIL import ImageGrab

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import ApiClient
from dados_sinteticos import JANELAS_AGRESSIVO, JANELAS_DEFENSIVO, gerar_csv
from main import App

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apresentacao", "imgs")


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
    # Os perfis vivem em dados_sinteticos.PERFIS (fonte única de verdade).
    rotas = [
        ("Condução Agressiva", gerar_csv(1, 70.0, JANELAS_AGRESSIVO)),
        ("Condução Defensiva", gerar_csv(2, 70.0, JANELAS_DEFENSIVO)),
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
    # Captura em tela cheia: maximiza a janela (mantém a barra de título) antes
    # de fotografar cada seção. No Windows, 'zoomed' ocupa toda a área útil.
    root.state("zoomed")
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
