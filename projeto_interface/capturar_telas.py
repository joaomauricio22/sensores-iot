"""Captura as telas da interface gráfica (para inserir nos slides).

Abre a janela Tkinter com os dados reais da API e fotografa cada aba.
As imagens são salvas em ../apresentacao/imgs/*.png
"""
import os
import sys
import time
import tkinter as tk
from tkinter import ttk

from PIL import ImageGrab

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import ApiClient
from tabs import AnomaliaTab, LeituraTab, SensorTab, TipoSensorTab

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apresentacao", "imgs")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    root = tk.Tk()
    root.title("Sistema de Análise de Dados de Sensores IoT")
    root.geometry("1000x640+60+60")
    root.configure(bg="#f5f6fa")
    root.attributes("-topmost", True)

    api = ApiClient()
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=10, pady=10)

    tabs = [
        ("Tipos de Sensor", TipoSensorTab(nb, api)),
        ("Sensores", SensorTab(nb, api)),
        ("Leituras", LeituraTab(nb, api)),
        ("Anomalias", AnomaliaTab(nb, api)),
    ]
    names = ["tipos_sensor", "sensores", "leituras", "anomalias"]
    for nome, tab in tabs:
        nb.add(tab, text=nome)

    root.update_idletasks()
    root.update()

    for i, name in enumerate(names):
        nb.select(i)
        root.update_idletasks()
        root.update()
        time.sleep(0.4)
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
        path = os.path.join(OUT_DIR, f"{name}.png")
        img.save(path)
        print(f"salvo: {path} ({img.size[0]}x{img.size[1]})")

    root.destroy()
    print("Captura concluída.")


if __name__ == "__main__":
    main()
