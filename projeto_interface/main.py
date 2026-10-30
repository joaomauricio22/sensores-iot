"""Ponto de entrada da interface gráfica (Tkinter).

Executar: python main.py
A interface se comunica com a API REST (que deve estar em execução).
"""
import tkinter as tk
from tkinter import ttk

from api_client import ApiClient
from tabs import AnomaliaTab, LeituraTab, SensorTab, TipoSensorTab


def main():
    root = tk.Tk()
    root.title("Sistema de Análise de Dados de Sensores IoT")
    root.geometry("1000x640")
    root.configure(bg="#f5f6fa")

    api = ApiClient()

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    notebook.add(TipoSensorTab(notebook, api), text="Tipos de Sensor")
    notebook.add(SensorTab(notebook, api), text="Sensores")
    notebook.add(LeituraTab(notebook, api), text="Leituras")
    notebook.add(AnomaliaTab(notebook, api), text="Anomalias")

    root.mainloop()


if __name__ == "__main__":
    main()
