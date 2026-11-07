"""Telas da interface gráfica (centrada no usuário).

- RotaTab: lista as rotas, cadastra via CSV, renomeia e exclui.
- GraficoTab: gráfico automático da velocidade (km/h) com os trechos de risco,
  coloridos conforme o tipo do evento.
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import requests
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from api_client import extract_error

BG = "#f5f6fa"

CORES_TIPO = {
    "Frenagem brusca": "#d63031",
    "Aceleração brusca": "#e17055",
    "Curva em alta velocidade": "#6c5ce7",
    "Evento de risco": "#d63031",
}


def _botao(parent, texto, cor, comando):
    return tk.Button(
        parent, text=texto, command=comando, font=("Segoe UI", 10, "bold"),
        bg=cor, fg="white", activebackground=cor, activeforeground="white",
        relief="flat", cursor="hand2", width=20, height=1, bd=0,
    )


class RotaTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.tree = None
        self._build()

    def _build(self):
        tk.Label(self, text="Minhas Rotas", font=("Segoe UI", 20, "bold"),
                 bg=BG, fg="#2d3436").pack(pady=(15, 10))

        btns = tk.Frame(self, bg=BG)
        btns.pack(pady=6)
        _botao(btns, "Cadastrar Rota (CSV)", "#0984e3", self.cadastrar_rota).pack(side="left", padx=4)
        _botao(btns, "Renomear", "#e17055", self.renomear).pack(side="left", padx=4)
        _botao(btns, "Excluir", "#d63031", self.excluir).pack(side="left", padx=4)

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        cols = ["id", "nome", "arquivo", "data"]
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        for key, label, width in [
            ("id", "ID", 50), ("nome", "Nome", 200),
            ("arquivo", "Arquivo de origem", 260), ("data", "Data", 120),
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
            data = (r.get("data_importacao") or "").split("T")[0]
            self.tree.insert("", "end", values=(
                r["id"], r["nome"], r.get("arquivo_origem") or "", data,
            ))

    def cadastrar_rota(self):
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
            self.app.rota_atual_id = dados["rota_id"]
            self.atualizar()
            # gera o gráfico automaticamente (sem trocar de aba)
            self.app.grafico_tab.plotar()
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
            self.atualizar()
        else:
            messagebox.showerror("Erro", extract_error(resp))

    def excluir(self):
        rota_id = self._get_selecionada()
        if rota_id is None:
            return
        if not messagebox.askyesno("Confirmar", "Excluir a rota selecionada?"):
            return
        try:
            resp = self.app.api.excluir_rota(rota_id)
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro de comunicação com a API:\n{e}")
            return
        if resp.status_code == 200:
            self.atualizar()
            if self.app.rota_atual_id == rota_id:
                self.app.rota_atual_id = None
                self.app.grafico_tab.plotar()
        else:
            messagebox.showerror("Erro", extract_error(resp))


class GraficoTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.figure = Figure(figsize=(7, 4.4), dpi=100, facecolor=BG)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self._build()

    def _build(self):
        tk.Label(self, text="Comportamento da Rota", font=("Segoe UI", 20, "bold"),
                 bg=BG, fg="#2d3436").pack(pady=(15, 5))
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(5, 15))
        self.plotar()

    def plotar(self):
        rota_id = self.app.rota_atual_id
        self.ax.clear()
        if not rota_id:
            self.ax.text(0.5, 0.5, "Cadastre uma rota para visualizar o gráfico.",
                         ha="center", va="center", fontsize=12, color="#636e72")
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.canvas.draw()
            return

        # análise automática (idempotente) + dados do gráfico
        try:
            self.app.api.analisar_rota(rota_id)
            resp = self.app.api.grafico_rota(rota_id)
        except requests.exceptions.RequestException:
            self.canvas.draw()
            return
        if resp.status_code != 200:
            self.ax.text(0.5, 0.5, extract_error(resp), ha="center", va="center",
                         fontsize=12, color="#d63031")
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.canvas.draw()
            return

        dados = resp.json()
        pontos = dados["pontos"]
        tempos = [p["tempo"] for p in pontos]
        velocidades = [p["velocidade"] if p["velocidade"] is not None else 0.0 for p in pontos]

        self.ax.plot(tempos, velocidades, color="#0984e3", linewidth=1.2, label="Velocidade (km/h)")

        # pontos de risco, coloridos conforme o tipo
        for tipo, cor in CORES_TIPO.items():
            pts = [
                (p["tempo"], p["velocidade"])
                for p in pontos
                if p["risco"] and p["classificacao"] == tipo and p["velocidade"] is not None
            ]
            if pts:
                t, v = zip(*pts)
                self.ax.scatter(t, v, color=cor, s=30, zorder=5, label=tipo)

        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Velocidade (km/h)")
        self.ax.set_title(dados["nome"])
        self.ax.legend(loc="upper right", fontsize="small")
        self.ax.grid(True, linestyle="--", alpha=0.5)
        self.figure.tight_layout()
        self.canvas.draw()
