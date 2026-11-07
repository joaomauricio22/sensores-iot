"""Telas da interface gráfica (centrada no usuário).

- RotaTab: lista as rotas do usuário, importa CSV, renomeia, exclui e analisa.
- EventoRiscoTab: lista os eventos de risco da rota selecionada.
- GraficoTab: gráfico da Força G ao longo do tempo, com os trechos de risco.
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import requests
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from api_client import extract_error

BG = "#f5f6fa"


def _botao(parent, texto, cor, comando):
    return tk.Button(
        parent, text=texto, command=comando, font=("Segoe UI", 10, "bold"),
        bg=cor, fg="white", activebackground=cor, activeforeground="white",
        relief="flat", cursor="hand2", width=13, height=1, bd=0,
    )


class RotaTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.tree = None
        self._build()
        self.atualizar()

    def _build(self):
        tk.Label(self, text="Minhas Rotas", font=("Segoe UI", 20, "bold"),
                 bg=BG, fg="#2d3436").pack(pady=(15, 10))

        btns = tk.Frame(self, bg=BG)
        btns.pack(pady=6)
        _botao(btns, "Importar CSV", "#0984e3", self.importar_csv).pack(side="left", padx=4)
        _botao(btns, "Renomear", "#e17055", self.renomear).pack(side="left", padx=4)
        _botao(btns, "Excluir", "#d63031", self.excluir).pack(side="left", padx=4)
        _botao(btns, "Analisar", "#6c5ce7", self.analisar).pack(side="left", padx=4)
        _botao(btns, "Atualizar", "#00b894", self.atualizar).pack(side="left", padx=4)

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        cols = ["id", "nome", "arquivo", "data_importacao"]
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        for key, label, width in [
            ("id", "ID", 50), ("nome", "Nome", 180),
            ("arquivo", "Arquivo de origem", 240), ("data_importacao", "Importação", 180),
        ]:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, anchor="center")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, _event):
        sel = self.tree.selection()
        if sel:
            self.app.rota_atual_id = int(self.tree.item(sel[0])["values"][0])

    def _get_selecionada(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma rota na lista.")
            return None
        return int(self.tree.item(sel[0])["values"][0])

    def atualizar(self):
        try:
            resp = self.app.api.list_rotas()
        except requests.exceptions.RequestException:
            return
        for i in self.tree.get_children():
            self.tree.delete(i)
        if resp.status_code != 200:
            return
        for r in resp.json():
            self.tree.insert("", "end", values=(
                r["id"], r["nome"], r.get("arquivo_origem") or "", r["data_importacao"],
            ))

    def importar_csv(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar arquivo de telemetria", filetypes=[("CSV", "*.csv")],
        )
        if not caminho:
            return
        nome = simpledialog.askstring("Nome da rota", "Dê um nome para a rota:")
        if not nome:
            return
        try:
            with open(caminho, encoding="utf-8-sig", errors="replace") as fh:
                conteudo = fh.read()
        except OSError as e:
            messagebox.showerror("Erro", f"Não foi possível ler o arquivo:\n{e}")
            return
        try:
            resp = self.app.api.importar_csv(nome, os.path.basename(caminho), conteudo)
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro de comunicação com a API:\n{e}")
            return
        if resp.status_code in (200, 201):
            dados = resp.json()
            messagebox.showinfo("Sucesso", f"Rota '{nome}' importada com {dados['total_leituras']} leituras.")
            self.atualizar()
        else:
            messagebox.showerror("Erro", extract_error(resp))

    def renomear(self):
        rota_id = self._get_selecionada()
        if rota_id is None:
            return
        nome = simpledialog.askstring("Renomear", "Novo nome da rota:")
        if not nome:
            return
        resp = self.app.api.renomear_rota(rota_id, nome)
        if resp.status_code == 200:
            messagebox.showinfo("Sucesso", "Rota renomeada.")
            self.atualizar()
        else:
            messagebox.showerror("Erro", extract_error(resp))

    def excluir(self):
        rota_id = self._get_selecionada()
        if rota_id is None:
            return
        if not messagebox.askyesno("Confirmar", "Excluir a rota selecionada?"):
            return
        resp = self.app.api.excluir_rota(rota_id)
        if resp.status_code == 200:
            messagebox.showinfo("Sucesso", "Rota excluída.")
            self.atualizar()
        else:
            messagebox.showerror("Erro", extract_error(resp))

    def analisar(self):
        rota_id = self._get_selecionada()
        if rota_id is None:
            return
        try:
            resp = self.app.api.analisar_rota(rota_id)
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro de comunicação com a API:\n{e}")
            return
        if resp.status_code == 200:
            eventos = resp.json()
            if eventos:
                messagebox.showwarning("Análise", f"{len(eventos)} novo(s) evento(s) de risco detectado(s).")
            else:
                messagebox.showinfo("Análise", "Nenhum novo evento de risco detectado.")
        else:
            messagebox.showerror("Erro", extract_error(resp))


class EventoRiscoTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.tree = None
        self._build()

    def _build(self):
        tk.Label(self, text="Eventos de Risco", font=("Segoe UI", 20, "bold"),
                 bg=BG, fg="#2d3436").pack(pady=(15, 10))
        _botao(self, "Atualizar", "#00b894", self.atualizar).pack(pady=6)

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        cols = ["data_hora", "metodo", "forca_g", "classificacao"]
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        for key, label, width in [
            ("data_hora", "Data/Hora", 180), ("metodo", "Método", 120),
            ("forca_g", "Força G (m/s²)", 130), ("classificacao", "Classificação", 110),
        ]:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, anchor="center")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def atualizar(self):
        rota_id = self.app.rota_atual_id
        for i in self.tree.get_children():
            self.tree.delete(i)
        if not rota_id:
            return
        try:
            resp = self.app.api.list_eventos(rota_id)
        except requests.exceptions.RequestException:
            return
        if resp.status_code != 200:
            return
        for e in resp.json():
            fg = f"{e['forca_g']:.2f}" if e.get("forca_g") is not None else ""
            self.tree.insert("", "end", values=(
                e["data_hora"], e["metodo"], fg, e.get("classificacao") or "",
            ))


class GraficoTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.figure = Figure(figsize=(7, 4.2), dpi=100, facecolor=BG)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self._build()

    def _build(self):
        tk.Label(self, text="Comportamento da Rota", font=("Segoe UI", 20, "bold"),
                 bg=BG, fg="#2d3436").pack(pady=(15, 5))
        _botao(self, "Plotar Gráfico", "#0984e3", self.plotar).pack(pady=6)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(5, 15))

    def plotar(self):
        rota_id = self.app.rota_atual_id
        if not rota_id:
            messagebox.showwarning("Aviso", "Selecione uma rota na aba 'Rotas'.")
            return
        try:
            resp = self.app.api.grafico_rota(rota_id)
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro de comunicação com a API:\n{e}")
            return
        if resp.status_code != 200:
            messagebox.showerror("Erro", extract_error(resp))
            return

        dados = resp.json()
        pontos = dados["pontos"]
        tempos = [p["tempo"] for p in pontos]
        fgs = [p["forca_g"] if p["forca_g"] is not None else 0.0 for p in pontos]
        riscos = [
            (p["tempo"], p["forca_g"])
            for p in pontos if p["risco"] and p["forca_g"] is not None
        ]

        ax = self.figure.add_subplot(111)
        ax.clear()
        ax.plot(tempos, fgs, color="#0984e3", linewidth=1.0, label="Força G resultante")
        if riscos:
            rt, rf = zip(*riscos)
            ax.scatter(rt, rf, color="#d63031", s=28, zorder=5, label="Evento de risco")
        ax.axhline(y=2.5, color="#f39c12", linestyle="--", linewidth=1.2, label="Limite CTB (2,5 m/s²)")
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Força G resultante (m/s²)")
        ax.set_title(dados["nome"])
        ax.legend(loc="upper right", fontsize="small")
        ax.grid(True, linestyle="--", alpha=0.5)
        self.figure.tight_layout()
        self.canvas.draw()
