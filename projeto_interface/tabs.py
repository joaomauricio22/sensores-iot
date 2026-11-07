"""Telas da interface gráfica (centrada no usuário).

Abas:
  - RotaTab: lista as rotas, cadastra via CSV, renomeia e exclui.
  - DashboardTab: resumo + score de segurança da rota + exportação CSV.
  - EventosTab: lista detalhada dos eventos de risco, com filtro por tipo.
  - GraficoTab: gráfico em painel (velocidade, Força G e RPM) com trechos de risco.
  - MapaTab: trajeto no mapa (GPS) com os trechos de risco.
  - CompararTab: compara o resumo de duas rotas.
  - ConfiguracaoTab: ajusta os limiares de detecção de risco.
"""
import csv
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import requests
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from api_client import extract_error

BG = "#f5f6fa"

TIPOS_RISCO = [
    "Frenagem brusca",
    "Aceleração brusca",
    "Curva em alta velocidade",
    "Excesso de velocidade",
    "RPM excessivo",
    "Acelerador brusco",
    "Comportamento atípico",
]

CORES_TIPO = {
    "Frenagem brusca": "#d63031",
    "Aceleração brusca": "#e17055",
    "Curva em alta velocidade": "#6c5ce7",
    "Excesso de velocidade": "#f39c12",
    "RPM excessivo": "#e84393",
    "Acelerador brusco": "#00b894",
    "Comportamento atípico": "#636e72",
}

ORDEM_SEVERIDADE = TIPOS_RISCO

# Metadados dos limiares (chave -> rótulo) para a aba de Configurações.
LIMIARES_INFO = [
    ("velocidade_max", "Velocidade máxima (km/h)"),
    ("rpm_max", "RPM máximo (RPM)"),
    ("aceleracao_max", "Aceleração máxima (m/s²)"),
    ("frenagem_max", "Frenagem máxima (m/s²)"),
    ("lateral_max", "Aceleração lateral (m/s²)"),
    ("curva_velocidade_min", "Velocidade mínima p/ curva (km/h)"),
    ("acelerador_delta_max", "Variação do acelerador (%/s)"),
]


def _botao(parent, texto, cor, comando, width=20):
    return tk.Button(
        parent, text=texto, command=comando, font=("Segoe UI", 10, "bold"),
        bg=cor, fg="white", activebackground=cor, activeforeground="white",
        relief="flat", cursor="hand2", width=width, height=1, bd=0,
    )


def _titulo(parent, texto):
    return tk.Label(parent, text=texto, font=("Segoe UI", 20, "bold"),
                    bg=BG, fg="#2d3436").pack(pady=(15, 8))


def tipo_principal(classificacoes):
    """Escolhe o tipo mais severo para colorir um ponto com vários eventos."""
    if not classificacoes:
        return None
    for t in ORDEM_SEVERIDADE:
        if t in classificacoes:
            return t
    return classificacoes[0]


def cor_score(score):
    if score >= 80:
        return "#00b894"
    if score >= 50:
        return "#f39c12"
    return "#d63031"


def formatar_duracao(segundos):
    s = int(segundos)
    h, resto = divmod(s, 3600)
    m, s = divmod(resto, 60)
    if h:
        return f"{h}h {m:02d}min {s:02d}s"
    if m:
        return f"{m}min {s:02d}s"
    return f"{s}s"


def _so_hora(data_hora):
    if not data_hora:
        return ""
    if "T" in data_hora:
        return data_hora.split("T")[1].split("+")[0].split(".")[0]
    return data_hora


# =========================================================================
# RotaTab
# =========================================================================
class RotaTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.tree = None
        self._build()

    def _build(self):
        _titulo(self, "Minhas Rotas")

        btns = tk.Frame(self, bg=BG)
        btns.pack(pady=6)
        _botao(btns, "Cadastrar Rota (CSV)", "#0984e3", self.cadastrar_rota).pack(side="left", padx=4)
        _botao(btns, "Renomear", "#e17055", self.renomear, width=14).pack(side="left", padx=4)
        _botao(btns, "Excluir", "#d63031", self.excluir, width=14).pack(side="left", padx=4)

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        cols = ["id", "nome", "arquivo", "data"]
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for key, label, width in [
            ("id", "ID", 50), ("nome", "Nome", 200),
            ("arquivo", "Arquivo de origem", 300), ("data", "Data", 120),
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
            self.app.refresh_detalhes()
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
                self.app.refresh_detalhes()
        else:
            messagebox.showerror("Erro", extract_error(resp))


# =========================================================================
# DashboardTab
# =========================================================================
class DashboardTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.resumo = None
        self.eventos = []
        self.var_score = tk.StringVar(value="—")
        self.var_det = tk.StringVar(value="—")
        self.vars = {}
        self._build()

    def _build(self):
        _titulo(self, "Dashboard da Rota")

        topo = tk.Frame(self, bg=BG)
        topo.pack(fill="x", padx=20, pady=5)

        # Cartão do score
        score_card = tk.Frame(topo, bg="white", highlightbackground="#dfe6e9",
                              highlightthickness=1)
        score_card.pack(side="left", padx=(0, 10))
        tk.Label(score_card, text="Score de segurança", font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#636e72").pack(padx=18, pady=(12, 0))
        self.lbl_score = tk.Label(score_card, textvariable=self.var_score,
                                  font=("Segoe UI", 42, "bold"), bg="white", fg="#2d3436")
        self.lbl_score.pack(padx=18, pady=(0, 12))

        # Cartões de estatísticas
        self.cards = tk.Frame(topo, bg=BG)
        self.cards.pack(side="left", fill="both", expand=True)
        metricas = [
            ("duracao", "Duração"), ("distancia", "Distância (km)"),
            ("vmedia", "Velocidade média"), ("vmax", "Velocidade máxima"),
            ("rpmax", "RPM máximo"), ("total", "Total de eventos"),
        ]
        for i, (key, label) in enumerate(metricas):
            var = tk.StringVar(value="—")
            self.vars[key] = var
            card = tk.Frame(self.cards, bg="white", highlightbackground="#dfe6e9",
                            highlightthickness=1, width=120)
            card.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="nsew")
            tk.Label(card, text=label, font=("Segoe UI", 9), bg="white",
                     fg="#636e72").pack(pady=(8, 0))
            tk.Label(card, textvariable=var, font=("Segoe UI", 15, "bold"),
                     bg="white", fg="#2d3436").pack(pady=(0, 8))

        # Eventos por tipo
        lbl = tk.Label(self, text="Eventos por tipo", font=("Segoe UI", 13, "bold"),
                       bg=BG, fg="#2d3436")
        lbl.pack(anchor="w", padx=20, pady=(12, 4))
        self.tipos_frame = tk.Frame(self, bg=BG)
        self.tipos_frame.pack(fill="both", expand=True, padx=20)

        rodape = tk.Frame(self, bg=BG)
        rodape.pack(fill="x", padx=20, pady=(5, 15))
        _botao(rodape, "Exportar Relatório (CSV)", "#00b894",
               self.exportar_relatorio, width=24).pack(side="left")

    def atualizar(self):
        rota_id = self.app.rota_atual_id
        self.resumo = None
        self.eventos = []
        if not rota_id:
            self.var_score.set("—")
            self.lbl_score.configure(fg="#2d3436")
            for var in self.vars.values():
                var.set("—")
            self._limpar_tipos()
            return
        try:
            self.app.api.analisar_rota(rota_id)
            resp = self.app.api.resumo_rota(rota_id)
        except requests.exceptions.RequestException:
            return
        if resp.status_code != 200:
            return
        resumo = resp.json()
        self.resumo = resumo

        score = resumo.get("score", 0)
        self.var_score.set(str(score))
        self.lbl_score.configure(fg=cor_score(score))

        self.vars["duracao"].set(formatar_duracao(resumo.get("duracao_segundos", 0)))
        self.vars["distancia"].set(f"{resumo.get('distancia_km', 0):.2f}")
        self.vars["vmedia"].set(f"{resumo.get('velocidade_media', 0):.1f} km/h")
        self.vars["vmax"].set(f"{resumo.get('velocidade_maxima', 0):.1f} km/h")
        self.vars["rpmax"].set(f"{resumo.get('rpm_maximo', 0):.0f} RPM")
        self.vars["total"].set(str(resumo.get("total_eventos", 0)))

        self._exibir_tipos(resumo.get("eventos_por_tipo", {}))

        try:
            r = self.app.api.list_eventos(rota_id)
            if r.status_code == 200:
                self.eventos = r.json()
        except requests.exceptions.RequestException:
            pass

    def _limpar_tipos(self):
        for w in self.tipos_frame.winfo_children():
            w.destroy()
        tk.Label(self.tipos_frame, text="Nenhum evento registrado.",
                 bg=BG, fg="#636e72").pack(anchor="w")

    def _exibir_tipos(self, eventos_por_tipo):
        for w in self.tipos_frame.winfo_children():
            w.destroy()
        if not eventos_por_tipo:
            tk.Label(self.tipos_frame, text="Nenhum evento de risco detectado.",
                     bg=BG, fg="#636e72").pack(anchor="w")
            return
        for tipo, qtd in sorted(eventos_por_tipo.items(), key=lambda x: -x[1]):
            linha = tk.Frame(self.tipos_frame, bg=BG)
            linha.pack(fill="x", pady=2)
            cor = CORES_TIPO.get(tipo, "#636e72")
            tk.Label(linha, text="●", fg=cor, bg=BG, font=("Segoe UI", 11)).pack(side="left")
            tk.Label(linha, text=tipo, bg=BG, fg="#2d3436",
                     font=("Segoe UI", 11)).pack(side="left", padx=6)
            tk.Label(linha, text=str(qtd), bg=BG, fg="#2d3436",
                     font=("Segoe UI", 11, "bold")).pack(side="left")

    def exportar_relatorio(self):
        if not self.resumo:
            messagebox.showwarning("Aviso", "Selecione uma rota para exportar o relatório.")
            return
        caminho = filedialog.asksaveasfilename(
            title="Salvar relatório", defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not caminho:
            return
        resumo = self.resumo
        try:
            with open(caminho, "w", newline="", encoding="utf-8-sig") as fh:
                w = csv.writer(fh, delimiter=";")
                w.writerow(["Relatório de Telemetria Veicular"])
                w.writerow([])
                w.writerow(["Rota", resumo.get("nome")])
                w.writerow(["Score de segurança", resumo.get("score")])
                w.writerow(["Duração (s)", resumo.get("duracao_segundos")])
                w.writerow(["Distância (km)", resumo.get("distancia_km")])
                w.writerow(["Velocidade média (km/h)", resumo.get("velocidade_media")])
                w.writerow(["Velocidade máxima (km/h)", resumo.get("velocidade_maxima")])
                w.writerow(["RPM máximo", resumo.get("rpm_maximo")])
                w.writerow(["Total de eventos", resumo.get("total_eventos")])
                w.writerow([])
                w.writerow(["Eventos por tipo"])
                for tipo, qtd in (resumo.get("eventos_por_tipo") or {}).items():
                    w.writerow([tipo, qtd])
                w.writerow([])
                w.writerow(["Detalhe dos eventos"])
                w.writerow(["Tipo", "Método", "Hora", "Força G", "Instabilidade", "Descrição"])
                for e in self.eventos:
                    w.writerow([
                        e.get("classificacao"), e.get("metodo"), _so_hora(e.get("data_hora")),
                        e.get("forca_g"), e.get("instabilidade"), e.get("descricao"),
                    ])
        except OSError as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")
            return
        messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{caminho}")


# =========================================================================
# EventosTab
# =========================================================================
class EventosTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.tree = None
        self._build()

    def _build(self):
        _titulo(self, "Eventos de Risco")

        filtro = tk.Frame(self, bg=BG)
        filtro.pack(pady=6)
        tk.Label(filtro, text="Filtrar por tipo:", bg=BG,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=4)
        self.combo_tipo = ttk.Combobox(filtro, state="readonly", width=26,
                                       values=["Todos"] + TIPOS_RISCO)
        self.combo_tipo.current(0)
        self.combo_tipo.pack(side="left", padx=4)
        self.combo_tipo.bind("<<ComboboxSelected>>", lambda e: self.atualizar())

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        cols = ["id", "tipo", "metodo", "hora", "forca_g", "instab"]
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for key, label, width in [
            ("id", "ID", 50), ("tipo", "Tipo", 180), ("metodo", "Método", 110),
            ("hora", "Hora", 90), ("forca_g", "Força G", 80), ("instab", "Instab.", 80),
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
        tipo = self.combo_tipo.get()
        if tipo == "Todos":
            tipo = None
        try:
            self.app.api.analisar_rota(rota_id)
            resp = self.app.api.list_eventos(rota_id, tipo)
        except requests.exceptions.RequestException:
            return
        if resp.status_code != 200:
            return
        for e in resp.json():
            fg = e.get("forca_g")
            self.tree.insert("", "end", values=(
                e["id"], e.get("classificacao"), e.get("metodo"),
                _so_hora(e.get("data_hora")),
                f"{fg:.2f}" if fg is not None else "",
                f"{e.get('instabilidade'):.2f}" if e.get("instabilidade") is not None else "",
            ))


# =========================================================================
# GraficoTab (painel: velocidade + Força G + RPM)
# =========================================================================
class GraficoTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.figure = Figure(figsize=(7.2, 6.2), dpi=100, facecolor=BG)
        self.ax_vel = self.figure.add_subplot(311)
        self.ax_fg = self.figure.add_subplot(312, sharex=self.ax_vel)
        self.ax_rpm = self.figure.add_subplot(313, sharex=self.ax_vel)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self._build()

    def _build(self):
        _titulo(self, "Comportamento da Rota")
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(5, 15))
        self.plotar()

    def plotar(self):
        rota_id = self.app.rota_atual_id
        for ax in (self.ax_vel, self.ax_fg, self.ax_rpm):
            ax.clear()
        if not rota_id:
            self.ax_vel.text(0.5, 0.5, "Cadastre uma rota para visualizar o gráfico.",
                             ha="center", va="center", fontsize=12, color="#636e72",
                             transform=self.ax_vel.transAxes)
            self.ax_vel.set_xticks([])
            self.ax_vel.set_yticks([])
            self.ax_fg.set_visible(False)
            self.ax_rpm.set_visible(False)
            self.canvas.draw()
            return
        self.ax_fg.set_visible(True)
        self.ax_rpm.set_visible(True)

        try:
            self.app.api.analisar_rota(rota_id)
            resp = self.app.api.grafico_rota(rota_id)
        except requests.exceptions.RequestException:
            self.canvas.draw()
            return
        if resp.status_code != 200:
            self.ax_vel.text(0.5, 0.5, extract_error(resp), ha="center", va="center",
                             fontsize=12, color="#d63031", transform=self.ax_vel.transAxes)
            self.ax_vel.set_xticks([])
            self.ax_vel.set_yticks([])
            self.canvas.draw()
            return

        dados = resp.json()
        pontos = dados["pontos"]
        tempos = [p["tempo"] for p in pontos]
        velocidades = [p["velocidade"] if p["velocidade"] is not None else 0.0 for p in pontos]
        fgs = [p["forca_g"] if p["forca_g"] is not None else 0.0 for p in pontos]
        rpms = [p["rpm"] if p["rpm"] is not None else 0.0 for p in pontos]

        # Painel 1 — velocidade com pontos de risco coloridos
        self.ax_vel.plot(tempos, velocidades, color="#0984e3", linewidth=1.3,
                         label="Velocidade (km/h)")
        por_tipo = {}
        for p in pontos:
            if p["risco"] and p["classificacoes"]:
                t = tipo_principal(p["classificacoes"])
                por_tipo.setdefault(t, []).append((p["tempo"], p["velocidade"]))
        for tipo, pts in por_tipo.items():
            if pts:
                t, v = zip(*pts)
                self.ax_vel.scatter(t, v, color=CORES_TIPO.get(tipo, "#d63031"),
                                    s=28, zorder=5, label=tipo)
        self.ax_vel.set_ylabel("Velocidade (km/h)")
        self.ax_vel.set_title(dados["nome"], fontsize=11)
        self.ax_vel.legend(loc="upper right", fontsize="x-small")
        self.ax_vel.grid(True, linestyle="--", alpha=0.5)

        # Painel 2 — Força G resultante com limites CTB
        self.ax_fg.plot(tempos, fgs, color="#e17055", linewidth=1.2, label="Força G (m/s²)")
        self.ax_fg.axhline(y=2.5, color="#f39c12", linestyle="--", linewidth=1.1)
        self.ax_fg.axhline(y=-3.0, color="#d63031", linestyle="--", linewidth=1.1)
        self.ax_fg.set_ylabel("Força G (m/s²)")
        self.ax_fg.legend(loc="upper right", fontsize="x-small")
        self.ax_fg.grid(True, linestyle="--", alpha=0.5)

        # Painel 3 — RPM
        self.ax_rpm.plot(tempos, rpms, color="#6c5ce7", linewidth=1.2, label="RPM")
        self.ax_rpm.set_ylabel("RPM")
        self.ax_rpm.set_xlabel("Tempo (s)")
        self.ax_rpm.legend(loc="upper right", fontsize="x-small")
        self.ax_rpm.grid(True, linestyle="--", alpha=0.5)

        self.figure.tight_layout()
        self.canvas.draw()


# =========================================================================
# MapaTab
# =========================================================================
class MapaTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.mapa = None
        self._build()

    def _build(self):
        _titulo(self, "Trajeto no Mapa")

        self.msg = tk.Label(self, text="Carregando...", bg=BG, fg="#636e72",
                            font=("Segoe UI", 11))
        self.msg.pack(pady=4)

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        try:
            from tkintermapview import TkinterMapView
            self.mapa = TkinterMapView(self.container, width=800, height=520, corner_radius=0)
            self.mapa.pack(fill="both", expand=True)
            self.mapa.set_position(-22.58, -43.28)
            self.mapa.set_zoom(14)
            self.msg.configure(text="Mapa do OpenStreetMap — requer conexão com a internet.")
        except ImportError:
            self.mapa = None
            self.msg.configure(text="Biblioteca 'tkintermapview' não instalada. "
                                    "Instale com: pip install tkintermapview")

    def atualizar(self):
        if self.mapa is None:
            return
        rota_id = self.app.rota_atual_id
        self.mapa.delete_all_path()
        self.mapa.delete_all_marker()
        if not rota_id:
            self.msg.configure(text="Cadastre uma rota com GPS para visualizar o trajeto.")
            return
        try:
            self.app.api.analisar_rota(rota_id)
            resp = self.app.api.grafico_rota(rota_id)
        except requests.exceptions.RequestException:
            return
        if resp.status_code != 200:
            return
        pontos = resp.json()["pontos"]
        coord = [(p["latitude"], p["longitude"]) for p in pontos
                 if p.get("latitude") is not None and p.get("longitude") is not None]
        if not coord:
            self.msg.configure(text="Esta rota não possui dados de GPS (latitude/longitude).")
            return

        self.mapa.set_position(coord[0][0], coord[0][1])
        self.mapa.set_path(coord, color="#0984e3", width=4)

        n_risco = 0
        for p in pontos:
            if p["risco"] and p.get("latitude") is not None and p.get("longitude") is not None:
                t = tipo_principal(p["classificacoes"])
                self.mapa.set_marker(
                    p["latitude"], p["longitude"], text="⚠",
                    marker_color_circle=CORES_TIPO.get(t, "#d63031"),
                    marker_color_outside=CORES_TIPO.get(t, "#d63031"),
                    text_color="white",
                )
                n_risco += 1
        self.msg.configure(text=f"{len(coord)} pontos de GPS · {n_risco} trecho(s) de risco.")


# =========================================================================
# CompararTab
# =========================================================================
class CompararTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.rotas = []
        self.tree = None
        self._build()

    def _build(self):
        _titulo(self, "Comparar Rotas")

        sel = tk.Frame(self, bg=BG)
        sel.pack(pady=6)
        tk.Label(sel, text="Rota A:", bg=BG, font=("Segoe UI", 10, "bold")).pack(side="left", padx=4)
        self.combo_a = ttk.Combobox(sel, state="readonly", width=28)
        self.combo_a.pack(side="left", padx=4)
        tk.Label(sel, text="Rota B:", bg=BG, font=("Segoe UI", 10, "bold")).pack(side="left", padx=4)
        self.combo_b = ttk.Combobox(sel, state="readonly", width=28)
        self.combo_b.pack(side="left", padx=4)
        _botao(sel, "Comparar", "#6c5ce7", self.comparar, width=12).pack(side="left", padx=6)

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        cols = ["metrica", "a", "b"]
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        self.tree.heading("metrica", text="Métrica")
        self.tree.heading("a", text="Rota A")
        self.tree.heading("b", text="Rota B")
        self.tree.column("metrica", width=220, anchor="w")
        self.tree.column("a", width=180, anchor="center")
        self.tree.column("b", width=180, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

    def atualizar(self):
        try:
            resp = self.app.api.list_rotas()
        except requests.exceptions.RequestException:
            return
        if resp.status_code != 200:
            return
        self.rotas = resp.json()
        nomes = [f"#{r['id']} — {r['nome']}" for r in self.rotas]
        self.combo_a["values"] = nomes
        self.combo_b["values"] = nomes
        if nomes:
            self.combo_a.current(0)
            if len(nomes) > 1:
                self.combo_b.current(1)

    def _rota_id_do_combo(self, combo):
        idx = combo.current()
        if idx < 0 or idx >= len(self.rotas):
            return None
        return self.rotas[idx]["id"]

    def comparar(self):
        ida = self._rota_id_do_combo(self.combo_a)
        idb = self._rota_id_do_combo(self.combo_b)
        if ida is None or idb is None:
            messagebox.showwarning("Aviso", "Selecione as duas rotas para comparar.")
            return
        try:
            resp = self.app.api.comparar_rotas([ida, idb])
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro de comunicação com a API:\n{e}")
            return
        if resp.status_code != 200:
            messagebox.showerror("Erro", extract_error(resp))
            return
        rotas = resp.json()["rotas"]
        if len(rotas) < 2:
            return

        for i in self.tree.get_children():
            self.tree.delete(i)

        def fmt(v, sufixo="", casas=1):
            if v is None:
                return "—"
            return f"{v:.{casas}f}{sufixo}" if isinstance(v, (int, float)) else str(v)

        linhas = [
            ("Score de segurança", lambda r: r["score"], ""),
            ("Duração", lambda r: formatar_duracao(r.get("duracao_segundos", 0)), ""),
            ("Distância (km)", lambda r: fmt(r.get("distancia_km"), "", 2), ""),
            ("Velocidade média (km/h)", lambda r: fmt(r.get("velocidade_media"), "", 1), ""),
            ("Velocidade máxima (km/h)", lambda r: fmt(r.get("velocidade_maxima"), "", 1), ""),
            ("RPM máximo", lambda r: fmt(r.get("rpm_maximo"), "", 0), ""),
            ("Total de eventos", lambda r: str(r.get("total_eventos", 0)), ""),
        ]
        for label, fn, _ in linhas:
            self.tree.insert("", "end", values=(label, fn(rotas[0]), fn(rotas[1])))

        melhor = "Rota A" if rotas[0]["score"] >= rotas[1]["score"] else "Rota B"
        messagebox.showinfo(
            "Comparação",
            f"{melhor} apresentou o maior score de segurança "
            f"({max(rotas[0]['score'], rotas[1]['score'])} vs "
            f"{min(rotas[0]['score'], rotas[1]['score'])}).",
        )


# =========================================================================
# ConfiguracaoTab
# =========================================================================
class ConfiguracaoTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.entries = {}
        self._build()

    def _build(self):
        _titulo(self, "Configurações de Detecção")

        tk.Label(self, text="Ajuste os limiares usados para classificar os eventos de risco.",
                 bg=BG, fg="#636e72", font=("Segoe UI", 10)).pack(pady=(0, 10))

        form = tk.Frame(self, bg=BG)
        form.pack(pady=5)
        self.entries = {}
        for i, (chave, label) in enumerate(LIMIARES_INFO):
            tk.Label(form, text=label, bg=BG, font=("Segoe UI", 10, "bold")).grid(
                row=i, column=0, sticky="w", pady=6)
            entry = tk.Entry(form, width=14, font=("Segoe UI", 11))
            entry.grid(row=i, column=1, pady=6, padx=10)
            self.entries[chave] = entry

        btns = tk.Frame(self, bg=BG)
        btns.pack(pady=16)
        _botao(btns, "Salvar", "#00b894", self.salvar, width=14).pack(side="left", padx=6)
        _botao(btns, "Recarregar", "#636e72", self.atualizar, width=14).pack(side="left", padx=6)

    def atualizar(self):
        try:
            resp = self.app.api.get_limiares()
        except requests.exceptions.RequestException:
            return
        if resp.status_code != 200:
            return
        limiares = resp.json()
        for chave, entry in self.entries.items():
            valor = limiares.get(chave)
            entry.delete(0, tk.END)
            if valor is not None:
                entry.insert(0, str(valor))

    def salvar(self):
        dados = {}
        for chave, entry in self.entries.items():
            texto = entry.get().strip().replace(",", ".")
            if texto == "":
                continue
            try:
                dados[chave] = float(texto)
            except ValueError:
                messagebox.showerror("Erro", f"Valor inválido para '{chave}': {texto}")
                return
        try:
            resp = self.app.api.set_limiares(dados)
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro de comunicação com a API:\n{e}")
            return
        if resp.status_code == 200:
            messagebox.showinfo("Sucesso", "Limiares atualizados com sucesso.")
        else:
            messagebox.showerror("Erro", extract_error(resp))
