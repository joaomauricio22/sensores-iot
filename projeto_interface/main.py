"""Ponto de entrada da interface gráfica (Tkinter).

Executar: python main.py
A interface se comunica com a API REST (que deve estar em execução).
"""
import tkinter as tk
from tkinter import ttk

from api_client import ApiClient
from tabs import EventoRiscoTab, LeituraTab, MapeamentoTab, ParametroTab, VeiculoTab


def main():
    root = tk.Tk()
    root.title("Telemetria Veicular — Detecção de Eventos de Risco")
    root.geometry("1100x680")
    root.configure(bg="#f5f6fa")

    api = ApiClient()

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    notebook.add(VeiculoTab(notebook, api), text="Veículos")
    notebook.add(ParametroTab(notebook, api), text="Parâmetros")
    notebook.add(MapeamentoTab(notebook, api), text="Mapeamentos")
    notebook.add(LeituraTab(notebook, api), text="Leituras")
    notebook.add(EventoRiscoTab(notebook, api), text="Eventos de Risco")

    root.mainloop()


if __name__ == "__main__":
    main()
