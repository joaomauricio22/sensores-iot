"""Telas da interface gráfica (Tkinter).

Organização:
  - Dados: Rotas, Leituras e Eventos de Risco, com CRUD completo.
  - Visão Geral: resumo + score de segurança da rota + exportação CSV.
  - Gráfico: velocidade, Força G e RPM, com limiares do JSON e tooltip.
  - Mapa: trajeto GPS com os trechos de risco.
  - Comparar: compara o resumo de duas rotas.
"""
import csv
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import requests
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from api_client import extract_error

BG = "#f5f6fa"
CARD = "white"
TEXTO = "#2d3436"
CINZA = "#636e72"
BORDA = "#dfe6e9"

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

METODOS = ["LIMITE", "ESTATISTICO", "MODELO_ML"]
CANAIS_ESPECIAIS = ["geral", "forca_g", "multivariado"]


# =========================================================================
# Funções auxiliares
# =========================================================================
def _botao(parent, texto, cor, comando, width=18):
    return tk.Button(
        parent, text=texto, command=comando, font=("Segoe UI", 10, "bold"),
        bg=cor, fg="white", activebackground=cor, activeforeground="white",
        relief="flat", cursor="hand2", width=width, height=1, bd=0,
    )


def _titulo(parent, texto, subtitulo=None):
    tk.Label(parent, text=texto, font=("Segoe UI", 19, "bold"),
             bg=BG, fg=TEXTO).pack(anchor="w", padx=20, pady=(14, 2))
    if subtitulo:
        tk.Label(parent, text=subtitulo, font=("Segoe UI", 10),
                 bg=BG, fg=CINZA).pack(anchor="w", padx=20, pady=(0, 8))


def tipo_principal(classificacoes):
    """Escolhe o tipo mais severo para colorir um ponto com vários eventos."""
    if not classificacoes:
        return None
    for tipo in TIPOS_RISCO:
        if tipo in classificacoes:
            return tipo
    return classificacoes[0]


def cor_score(score):
    if score >= 80:
        return "#00b894"
    if score >= 50:
        return "#f39c12"
    return "#d63031"


def formatar_duracao(segundos):
    s = int(segundos or 0)
    h, resto = divmod(s, 3600)
    m, s = divmod(resto, 60)
    if h:
        return f"{h}h {m:02d}min {s:02d}s"
    if m:
        return f"{m}min {s:02d}s"
    return f"{s}s"


def _para_iso(texto):
    """Converte o texto digitado para o formato ISO aceito pela API."""
    texto = (texto or "").strip()
    for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(texto, formato).isoformat()
        except ValueError:
            continue
    raise ValueError("Use o formato AAAA-MM-DD HH:MM:SS.")


def _para_exibicao(data_hora):
    if not data_hora:
        return ""
    return data_hora.replace("T", " ").split(".")[0].split("+")[0]


def _so_hora(data_hora):
    texto = _para_exibicao(data_hora)
    return texto.split(" ")[1] if " " in texto else texto


def _rotulo_rota(rota):
    return f"#{rota['id']} — {rota['nome']}"


def _fmt_num(valor, casas=1):
    if valor is None:
        return ""
    return f"{valor:.{casas}f}"


def _erro_api(resp):
    messagebox.showerror("Erro", extract_error(resp))


def _erro_conexao(erro):
    messagebox.showerror("Erro", f"Erro de comunicação com a API:\n{erro}")


# =========================================================================
# Formulário genérico (usado pelo CRUD das três tabelas)
# =========================================================================
class FormDialog(tk.Toplevel):
    """Janela modal com campos validados.

    Cada campo é um dict:
      chave, rotulo, tipo ("texto", "numero", "combo", "datahora"),
      obrigatorio (bool), valores (lista de (rótulo, valor) para combo).
    """

    def __init__(self, master, titulo, campos, valores=None):
        super().__init__(master)
        self.title(titulo)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.resultado = None
        self.campos = campos
        self.valores = valores or {}
        self.widgets = {}
        self._build()
        self.grab_set()
        self.wait_window(self)

    def _build(self):
        tk.Label(self, text=self.title(), font=("Segoe UI", 14, "bold"),
                 bg=BG, fg=TEXTO).pack(pady=(14, 8))

        form = tk.Frame(self, bg=BG)
        form.pack(padx=20, pady=5, fill="x")

        for linha, campo in enumerate(self.campos):
            chave = campo["chave"]
            tk.Label(form, text=campo["rotulo"], bg=BG, fg=TEXTO,
                     font=("Segoe UI", 10, "bold")).grid(
                row=linha, column=0, sticky="w", pady=5, padx=(0, 8))

            tipo = campo.get("tipo", "texto")
            if tipo == "combo":
                widget = ttk.Combobox(form, state="readonly", width=38)
                opcoes = campo.get("valores", [])
                widget["values"] = [rotulo for rotulo, _ in opcoes]
                atual = self.valores.get(chave)
                for rotulo, valor in opcoes:
                    if valor == atual:
                        widget.set(rotulo)
                        break
                else:
                    if opcoes and campo.get("obrigatorio"):
                        widget.current(0)
            else:
                widget = tk.Entry(form, width=40, font=("Segoe UI", 10))
                atual = self.valores.get(chave)
                if atual is not None:
                    if tipo == "datahora":
                        atual = _para_exibicao(atual)
                    widget.insert(0, str(atual))
            widget.grid(row=linha, column=1, sticky="ew", pady=5)
            self.widgets[chave] = widget

        botoes = tk.Frame(self, bg=BG)
        botoes.pack(pady=14)
        _botao(botoes, "Salvar", "#00b894", self._salvar, width=12).pack(side="left", padx=5)
        _botao(botoes, "Cancelar", CINZA, self.destroy, width=12).pack(side="left", padx=5)

    def _salvar(self):
        dados = {}
        for campo in self.campos:
            chave = campo["chave"]
            tipo = campo.get("tipo", "texto")
            widget = self.widgets[chave]

            if tipo == "combo":
                rotulo = widget.get()
                mapa = dict(campo.get("valores", []))
                valor = mapa.get(rotulo)
            else:
                valor = widget.get().strip()

            if campo.get("obrigatorio") and (valor is None or valor == ""):
                messagebox.showwarning("Aviso", f"Preencha o campo '{campo['rotulo']}'.")
                return

            if valor in ("", None):
                dados[chave] = None
                continue

            try:
                if tipo == "numero":
                    dados[chave] = float(str(valor).replace(",", "."))
                elif tipo == "datahora":
                    dados[chave] = _para_iso(str(valor))
                else:
                    dados[chave] = valor
            except ValueError as erro:
                messagebox.showerror("Erro", f"Valor inválido em '{campo['rotulo']}':\n{erro}")
                return

        self.resultado = dados
        self.destroy()


# =========================================================================
# Dados → Rotas
# =========================================================================
class RotaTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.rotas = []
        self.tree = None
        self._build()

    def _build(self):
        _titulo(self, "Rotas", "Cada rota representa uma viagem monitorada.")

        botoes = tk.Frame(self, bg=BG)
        botoes.pack(anchor="w", padx=20, pady=6)
        _botao(botoes, "Nova Rota", "#0984e3", self.nova).pack(side="left", padx=(0, 5))
        _botao(botoes, "Importar CSV", "#6c5ce7", self.importar).pack(side="left", padx=5)
        _botao(botoes, "Editar", "#e17055", self.editar).pack(side="left", padx=5)
        _botao(botoes, "Excluir", "#d63031", self.excluir).pack(side="left", padx=5)
        _botao(botoes, "Atualizar", CINZA, self.atualizar, width=12).pack(side="left", padx=5)

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        cols = ("id", "nome", "arquivo", "data")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for chave, rotulo, largura, ancora in [
            ("id", "ID", 50, "center"),
            ("nome", "Nome", 260, "w"),
            ("arquivo", "Arquivo de origem", 300, "w"),
            ("data", "Data de importação", 150, "center"),
        ]:
            self.tree.heading(chave, text=rotulo)
            self.tree.column(chave, width=largura, anchor=ancora)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._selecionar)

    def _selecionar(self, _event):
        rota_id = self._get_selecionada(silencioso=True)
        if rota_id is not None:
            self.app.definir_rota(rota_id)

    def _get_selecionada(self, silencioso=False):
        selecao = self.tree.selection()
        if not selecao:
            if not silencioso:
                messagebox.showwarning("Aviso", "Selecione uma rota na lista.")
            return None
        return int(self.tree.item(selecao[0])["values"][0])

    def atualizar(self):
        try:
            resp = self.app.api.list_rotas()
        except requests.exceptions.RequestException:
            return
        if resp.status_code != 200:
            return
        self.rotas = resp.json()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for rota in self.rotas:
            self.tree.insert("", "end", values=(
                rota["id"], rota["nome"], rota.get("arquivo_origem") or "",
                _para_exibicao(rota.get("data_importacao")),
            ))

    def nova(self):
        dialogo = FormDialog(self, "Nova rota", [
            {"chave": "nome", "rotulo": "Nome da rota", "tipo": "texto", "obrigatorio": True},
            {"chave": "arquivo_origem", "rotulo": "Arquivo de origem", "tipo": "texto"},
        ])
        if dialogo.resultado is None:
            return
        try:
            resp = self.app.api.criar_rota(**dialogo.resultado)
        except requests.exceptions.RequestException as erro:
            _erro_conexao(erro)
            return
        if resp.status_code in (200, 201):
            self.app.recarregar_rotas(selecionar=resp.json().get("id"))
        else:
            _erro_api(resp)

    def importar(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar arquivo de telemetria", filetypes=[("CSV", "*.csv")],
        )
        if not caminho:
            return
        dialogo = FormDialog(self, "Importar CSV", [
            {"chave": "nome", "rotulo": "Nome da rota", "tipo": "texto", "obrigatorio": True},
        ], valores={"nome": os.path.splitext(os.path.basename(caminho))[0]})
        if dialogo.resultado is None:
            return
        try:
            with open(caminho, encoding="utf-8-sig", errors="replace") as arquivo:
                conteudo = arquivo.read()
        except OSError as erro:
            messagebox.showerror("Erro", f"Não foi possível ler o arquivo:\n{erro}")
            return
        try:
            resp = self.app.api.importar_csv(
                dialogo.resultado["nome"], os.path.basename(caminho), conteudo
            )
        except requests.exceptions.RequestException as erro:
            _erro_conexao(erro)
            return
        if resp.status_code in (200, 201):
            dados = resp.json()
            limpeza = dados.get("limpeza", {})
            messagebox.showinfo(
                "Importação concluída",
                f"{dados.get('total_leituras', 0)} leituras importadas.\n"
                f"Leituras descartadas: {limpeza.get('total_removido', 0)}\n"
                f"Spikes ajustados: {limpeza.get('acelerometro_ajustado', 0)}",
            )
            self.app.recarregar_rotas(selecionar=dados.get("rota_id"))
        else:
            _erro_api(resp)

    def editar(self):
        rota_id = self._get_selecionada()
        if rota_id is None:
            return
        rota = next((r for r in self.rotas if r["id"] == rota_id), None)
        if rota is None:
            return
        dialogo = FormDialog(self, "Editar rota", [
            {"chave": "nome", "rotulo": "Nome da rota", "tipo": "texto", "obrigatorio": True},
            {"chave": "arquivo_origem", "rotulo": "Arquivo de origem", "tipo": "texto"},
        ], valores=rota)
        if dialogo.resultado is None:
            return
        try:
            resp = self.app.api.atualizar_rota(rota_id, **dialogo.resultado)
        except requests.exceptions.RequestException as erro:
            _erro_conexao(erro)
            return
        if resp.status_code == 200:
            self.app.recarregar_rotas(selecionar=rota_id)
        else:
            _erro_api(resp)

    def excluir(self):
        rota_id = self._get_selecionada()
        if rota_id is None:
            return
        if not messagebox.askyesno(
            "Confirmar",
            "Excluir a rota selecionada?\nAs leituras e os eventos vinculados também serão excluídos.",
        ):
            return
        try:
            resp = self.app.api.excluir_rota(rota_id)
        except requests.exceptions.RequestException as erro:
            _erro_conexao(erro)
            return
        if resp.status_code == 200:
            self.app.recarregar_rotas()
        else:
            _erro_api(resp)


# =========================================================================
# Dados → Leituras
# =========================================================================
class LeituraTab(tk.Frame):

    CAMPOS_NUMEROS = [
        ("velocidade", "Velocidade (km/h)"),
        ("rpm", "RPM"),
        ("accel_x", "Aceleração X (m/s²)"),
        ("accel_y", "Aceleração Y (m/s²)"),
        ("accel_z", "Aceleração Z (m/s²)"),
        ("posicao_acelerador", "Posição do acelerador (%)"),
        ("latitude", "Latitude"),
        ("longitude", "Longitude"),
    ]

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.leituras = []
        self.tree = None
        self._build()

    def _build(self):
        _titulo(self, "Leituras", "Frames de telemetria: valores dos sensores em um instante.")

        filtro = tk.Frame(self, bg=BG)
        filtro.pack(anchor="w", padx=20, pady=4)
        tk.Label(filtro, text="Rota:", bg=BG, fg=TEXTO,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 4))
        self.combo_rota = ttk.Combobox(filtro, state="readonly", width=32)
        self.combo_rota.pack(side="left", padx=(0, 10))
        self.combo_rota.bind("<<ComboboxSelected>>", lambda _e: self.atualizar())

        botoes = tk.Frame(self, bg=BG)
        botoes.pack(anchor="w", padx=20, pady=4)
        _botao(botoes, "Nova Leitura", "#0984e3", self.nova).pack(side="left", padx=(0, 5))
        _botao(botoes, "Editar", "#e17055", self.editar).pack(side="left", padx=5)
        _botao(botoes, "Excluir", "#d63031", self.excluir).pack(side="left", padx=5)
        _botao(botoes, "Atualizar", CINZA, self.atualizar, width=12).pack(side="left", padx=5)

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        cols = ("id", "rota", "data", "vel", "rpm", "ax", "ay", "az", "acel", "lat", "lon")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=13)
        for chave, rotulo, largura in [
            ("id", "ID", 45), ("rota", "Rota", 60), ("data", "Data/hora", 140),
            ("vel", "Veloc.", 60), ("rpm", "RPM", 65), ("ax", "Accel X", 65),
            ("ay", "Accel Y", 65), ("az", "Accel Z", 65), ("acel", "Acelerador", 75),
            ("lat", "Latitude", 85), ("lon", "Longitude", 85),
        ]:
            self.tree.heading(chave, text=rotulo)
            self.tree.column(chave, width=largura, anchor="center")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _rota_filtro(self):
        indice = self.combo_rota.current()
        if indice <= 0:
            return None
        return self.app.rotas[indice - 1]["id"]

    def atualizar(self):
        nomes = ["Todas"] + [_rotulo_rota(r) for r in self.app.rotas]
        self.combo_rota["values"] = nomes
        if self.combo_rota.current() < 0:
            self.combo_rota.current(0)

        try:
            resp = self.app.api.list_leituras(self._rota_filtro())
        except requests.exceptions.RequestException:
            return
        if resp.status_code != 200:
            return
        self.leituras = resp.json()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for leitura in self.leituras:
            self.tree.insert("", "end", values=(
                leitura["id"], leitura["rota_id"],
                _para_exibicao(leitura.get("data_hora")),
                _fmt_num(leitura.get("velocidade")), _fmt_num(leitura.get("rpm"), 0),
                _fmt_num(leitura.get("accel_x"), 2), _fmt_num(leitura.get("accel_y"), 2),
                _fmt_num(leitura.get("accel_z"), 2), _fmt_num(leitura.get("posicao_acelerador")),
                _fmt_num(leitura.get("latitude"), 6), _fmt_num(leitura.get("longitude"), 6),
            ))

    def _get_selecionada(self):
        selecao = self.tree.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione uma leitura na lista.")
            return None
        return int(self.tree.item(selecao[0])["values"][0])

    def _campos(self):
        opcoes_rota = [(_rotulo_rota(r), r["id"]) for r in self.app.rotas]
        campos = [
            {"chave": "rota_id", "rotulo": "Rota", "tipo": "combo",
             "valores": opcoes_rota, "obrigatorio": True},
            {"chave": "data_hora", "rotulo": "Data/hora (AAAA-MM-DD HH:MM:SS)",
             "tipo": "datahora", "obrigatorio": True},
        ]
        for chave, rotulo in self.CAMPOS_NUMEROS:
            campos.append({"chave": chave, "rotulo": rotulo, "tipo": "numero"})
        return campos

    def nova(self):
        if not self.app.rotas:
            messagebox.showwarning("Aviso", "Cadastre uma rota antes de criar leituras.")
            return
        dialogo = FormDialog(self, "Nova leitura", self._campos())
        if dialogo.resultado is None:
            return
        try:
            resp = self.app.api.criar_leitura(dialogo.resultado)
        except requests.exceptions.RequestException as erro:
            _erro_conexao(erro)
            return
        if resp.status_code in (200, 201):
            self.atualizar()
            self.app.refresh_detalhes()
        else:
            _erro_api(resp)

    def editar(self):
        leitura_id = self._get_selecionada()
        if leitura_id is None:
            return
        leitura = next((l for l in self.leituras if l["id"] == leitura_id), None)
        if leitura is None:
            return
        dialogo = FormDialog(self, "Editar leitura", self._campos(), valores=leitura)
        if dialogo.resultado is None:
            return
        try:
            resp = self.app.api.atualizar_leitura(leitura_id, dialogo.resultado)
        except requests.exceptions.RequestException as erro:
            _erro_conexao(erro)
            return
        if resp.status_code == 200:
            self.atualizar()
            self.app.refresh_detalhes()
        else:
            _erro_api(resp)

    def excluir(self):
        leitura_id = self._get_selecionada()
        if leitura_id is None:
            return
        if not messagebox.askyesno(
            "Confirmar",
            "Excluir a leitura selecionada?\nOs eventos vinculados a ela também serão excluídos.",
        ):
            return
        try:
            resp = self.app.api.excluir_leitura(leitura_id)
        except requests.exceptions.RequestException as erro:
            _erro_conexao(erro)
            return
        if resp.status_code == 200:
            self.atualizar()
            self.app.refresh_detalhes()
        else:
            _erro_api(resp)


# =========================================================================
# Dados → Eventos de risco
# =========================================================================
class EventoRiscoTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.eventos = []
        self.leituras = []
        self.sensores = []
        self.tree = None
        self._build()

    def _build(self):
        _titulo(self, "Eventos de Risco",
                "Anomalias detectadas: canal, valor, método e classificação.")

        filtro = tk.Frame(self, bg=BG)
        filtro.pack(anchor="w", padx=20, pady=4)
        tk.Label(filtro, text="Rota:", bg=BG, fg=TEXTO,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 4))
        self.combo_rota = ttk.Combobox(filtro, state="readonly", width=30)
        self.combo_rota.pack(side="left", padx=(0, 10))
        self.combo_rota.bind("<<ComboboxSelected>>", lambda _e: self.atualizar())
        tk.Label(filtro, text="Tipo:", bg=BG, fg=TEXTO,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 4))
        self.combo_tipo = ttk.Combobox(filtro, state="readonly", width=26,
                                       values=["Todos"] + TIPOS_RISCO)
        self.combo_tipo.current(0)
        self.combo_tipo.pack(side="left")
        self.combo_tipo.bind("<<ComboboxSelected>>", lambda _e: self.atualizar())

        botoes = tk.Frame(self, bg=BG)
        botoes.pack(anchor="w", padx=20, pady=4)
        _botao(botoes, "Novo Evento", "#0984e3", self.novo).pack(side="left", padx=(0, 5))
        _botao(botoes, "Editar", "#e17055", self.editar).pack(side="left", padx=5)
        _botao(botoes, "Excluir", "#d63031", self.excluir).pack(side="left", padx=5)
        _botao(botoes, "Atualizar", CINZA, self.atualizar, width=12).pack(side="left", padx=5)

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        cols = ("id", "leitura", "rota", "data", "tipo", "metodo", "canal", "valor", "fg", "inst")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        for chave, rotulo, largura in [
            ("id", "ID", 45), ("leitura", "Leitura", 60), ("rota", "Rota", 55),
            ("data", "Data/hora", 140), ("tipo", "Classificação", 180),
            ("metodo", "Método", 105), ("canal", "Canal", 110), ("valor", "Valor", 70),
            ("fg", "Força G", 70), ("inst", "Instab.", 70),
        ]:
            self.tree.heading(chave, text=rotulo)
            self.tree.column(chave, width=largura, anchor="center")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _rota_filtro(self):
        indice = self.combo_rota.current()
        if indice <= 0:
            return None
        return self.app.rotas[indice - 1]["id"]

    def atualizar(self):
        nomes = ["Todas"] + [_rotulo_rota(r) for r in self.app.rotas]
        self.combo_rota["values"] = nomes
        if self.combo_rota.current() < 0:
            self.combo_rota.current(0)

        tipo = self.combo_tipo.get()
        if tipo == "Todos":
            tipo = None

        filtro = self._rota_filtro()
        try:
            resp = self.app.api.list_eventos(filtro, tipo)
            resp_sensores = self.app.api.get_sensores()
            # Carrega as leituras apenas da rota filtrada (evita trazer todas).
            resp_leituras = self.app.api.list_leituras(filtro) if filtro is not None else None
        except requests.exceptions.RequestException:
            return
        if resp.status_code != 200:
            return
        self.eventos = resp.json()
        self.leituras = (
            resp_leituras.json()
            if resp_leituras is not None and resp_leituras.status_code == 200
            else []
        )
        if resp_sensores.status_code == 200:
            self.sensores = list(resp_sensores.json().keys())

        for item in self.tree.get_children():
            self.tree.delete(item)
        for evento in self.eventos:
            self.tree.insert("", "end", values=(
                evento["id"], evento["leitura_id"], evento["rota_id"],
                _para_exibicao(evento.get("data_hora")),
                evento.get("classificacao"), evento.get("metodo"),
                evento.get("canal"), _fmt_num(evento.get("valor"), 2),
                _fmt_num(evento.get("forca_g"), 2),
                _fmt_num(evento.get("instabilidade"), 2),
            ))

    def _get_selecionada(self):
        selecao = self.tree.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um evento na lista.")
            return None
        return int(self.tree.item(selecao[0])["values"][0])

    def _campos(self):
        opcoes_leitura = [
            (f"#{l['id']} — rota {l['rota_id']} — {_para_exibicao(l['data_hora'])}", l["id"])
            for l in self.leituras
        ]
        canais = self.sensores + [c for c in CANAIS_ESPECIAIS if c not in self.sensores]
        return [
            {"chave": "leitura_id", "rotulo": "Leitura", "tipo": "combo",
             "valores": opcoes_leitura, "obrigatorio": True},
            {"chave": "metodo", "rotulo": "Método", "tipo": "combo",
             "valores": [(m, m) for m in METODOS], "obrigatorio": True},
            {"chave": "canal", "rotulo": "Canal (sensor)", "tipo": "combo",
             "valores": [(c, c) for c in canais], "obrigatorio": True},
            {"chave": "classificacao", "rotulo": "Classificação", "tipo": "combo",
             "valores": [(t, t) for t in TIPOS_RISCO], "obrigatorio": True},
            {"chave": "valor", "rotulo": "Valor medido", "tipo": "numero"},
            {"chave": "forca_g", "rotulo": "Força G (m/s²)", "tipo": "numero"},
            {"chave": "instabilidade", "rotulo": "Instabilidade", "tipo": "numero"},
            {"chave": "descricao", "rotulo": "Descrição", "tipo": "texto"},
        ]

    def novo(self):
        if not self.leituras:
            messagebox.showwarning(
                "Aviso",
                "Selecione uma rota no filtro acima para escolher a leitura do evento.",
            )
            return
        dialogo = FormDialog(self, "Novo evento de risco", self._campos())
        if dialogo.resultado is None:
            return
        try:
            resp = self.app.api.criar_evento(dialogo.resultado)
        except requests.exceptions.RequestException as erro:
            _erro_conexao(erro)
            return
        if resp.status_code in (200, 201):
            self.atualizar()
            self.app.refresh_detalhes()
        else:
            _erro_api(resp)

    def editar(self):
        evento_id = self._get_selecionada()
        if evento_id is None:
            return
        if not self.leituras:
            messagebox.showwarning(
                "Aviso",
                "Selecione uma rota no filtro acima para editar o evento.",
            )
            return
        evento = next((e for e in self.eventos if e["id"] == evento_id), None)
        if evento is None:
            return
        dialogo = FormDialog(self, "Editar evento de risco", self._campos(), valores=evento)
        if dialogo.resultado is None:
            return
        try:
            resp = self.app.api.atualizar_evento(evento_id, dialogo.resultado)
        except requests.exceptions.RequestException as erro:
            _erro_conexao(erro)
            return
        if resp.status_code == 200:
            self.atualizar()
            self.app.refresh_detalhes()
        else:
            _erro_api(resp)

    def excluir(self):
        evento_id = self._get_selecionada()
        if evento_id is None:
            return
        if not messagebox.askyesno("Confirmar", "Excluir o evento selecionado?"):
            return
        try:
            resp = self.app.api.excluir_evento(evento_id)
        except requests.exceptions.RequestException as erro:
            _erro_conexao(erro)
            return
        if resp.status_code == 200:
            self.atualizar()
            self.app.refresh_detalhes()
        else:
            _erro_api(resp)


# =========================================================================
# Seção Dados (notebook com as três tabelas)
# =========================================================================
class DadosTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.rota_tab = RotaTab(self.notebook, app)
        self.leitura_tab = LeituraTab(self.notebook, app)
        self.evento_tab = EventoRiscoTab(self.notebook, app)

        self.notebook.add(self.rota_tab, text="Rotas")
        self.notebook.add(self.leitura_tab, text="Leituras")
        self.notebook.add(self.evento_tab, text="Eventos")
        self.notebook.bind("<<NotebookTabChanged>>", self._trocar)

    def _trocar(self, _event):
        indice = self.notebook.index(self.notebook.select())
        [self.rota_tab, self.leitura_tab, self.evento_tab][indice].atualizar()

    def atualizar(self):
        indice = self.notebook.index(self.notebook.select())
        [self.rota_tab, self.leitura_tab, self.evento_tab][indice].atualizar()


# =========================================================================
# Visão Geral (dashboard + score + exportação)
# =========================================================================
class DashboardTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.resumo = None
        self.eventos = []
        self.var_score = tk.StringVar(value="—")
        self.vars = {}
        self._build()

    def _build(self):
        _titulo(self, "Visão Geral da Rota", "Resumo, score de segurança e relatório.")

        topo = tk.Frame(self, bg=BG)
        topo.pack(fill="x", padx=20, pady=5)

        score_card = tk.Frame(topo, bg=CARD, highlightbackground=BORDA, highlightthickness=1)
        score_card.pack(side="left", padx=(0, 10))
        tk.Label(score_card, text="Score de segurança", font=("Segoe UI", 11, "bold"),
                 bg=CARD, fg=CINZA).pack(padx=18, pady=(12, 0))
        self.lbl_score = tk.Label(score_card, textvariable=self.var_score,
                                  font=("Segoe UI", 42, "bold"), bg=CARD, fg=TEXTO)
        self.lbl_score.pack(padx=18, pady=(0, 12))

        self.cards = tk.Frame(topo, bg=BG)
        self.cards.pack(side="left", fill="both", expand=True)
        metricas = [
            ("duracao", "Duração"), ("distancia", "Distância (km)"),
            ("vmedia", "Velocidade média"), ("vmax", "Velocidade máxima"),
            ("rpmax", "RPM máximo"), ("total", "Total de eventos"),
        ]
        for i, (chave, rotulo) in enumerate(metricas):
            var = tk.StringVar(value="—")
            self.vars[chave] = var
            card = tk.Frame(self.cards, bg=CARD, highlightbackground=BORDA,
                            highlightthickness=1, width=120)
            card.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="nsew")
            tk.Label(card, text=rotulo, font=("Segoe UI", 9), bg=CARD,
                     fg=CINZA).pack(pady=(8, 0))
            tk.Label(card, textvariable=var, font=("Segoe UI", 15, "bold"),
                     bg=CARD, fg=TEXTO).pack(pady=(0, 8))

        tk.Label(self, text="Eventos por tipo", font=("Segoe UI", 13, "bold"),
                 bg=BG, fg=TEXTO).pack(anchor="w", padx=20, pady=(12, 4))
        self.tipos_frame = tk.Frame(self, bg=BG)
        self.tipos_frame.pack(fill="both", expand=True, padx=20)

        rodape = tk.Frame(self, bg=BG)
        rodape.pack(fill="x", padx=20, pady=(5, 15))
        _botao(rodape, "Reanalisar", "#0984e3", self.reanalisar, width=16).pack(side="left", padx=(0, 8))
        _botao(rodape, "Exportar Relatório (CSV)", "#00b894",
               self.exportar_relatorio, width=24).pack(side="left")

    def atualizar(self):
        rota_id = self.app.rota_atual_id
        self.resumo = None
        self.eventos = []
        if not rota_id:
            self._mostrar_vazio("Selecione uma rota na barra superior.")
            return

        self.var_score.set("…")
        self.lbl_score.configure(fg=TEXTO)
        self._limpar_tipos("Analisando a rota…")

        def carregar():
            # resumo_rota dispara a análise no servidor (idempotente).
            resp = self.app.api.resumo_rota(rota_id)
            resp_eventos = self.app.api.list_eventos(rota_id)
            return rota_id, resp, resp_eventos

        self.app.carregar_async(carregar, self._render)

    def reanalisar(self):
        """Força a reanálise da rota atual (apaga e reexecuta os detectores)."""
        rota_id = self.app.rota_atual_id
        if not rota_id:
            return
        self.var_score.set("…")
        self.lbl_score.configure(fg=TEXTO)
        self._limpar_tipos("Reanalisando a rota…")

        def carregar():
            # POST /analisar agora força a reanálise no servidor.
            self.app.api.analisar_rota(rota_id)
            resp = self.app.api.resumo_rota(rota_id)
            resp_eventos = self.app.api.list_eventos(rota_id)
            return rota_id, resp, resp_eventos

        self.app.carregar_async(carregar, self._render)

    def _render(self, resultado):
        if isinstance(resultado, dict) and "__erro__" in resultado:
            self._limpar_tipos(resultado["__erro__"])
            return
        rota_id, resp, resp_eventos = resultado
        if rota_id != self.app.rota_atual_id:
            return  # a rota mudou enquanto carregava
        if resp.status_code != 200:
            self._limpar_tipos(extract_error(resp))
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

        if resp_eventos.status_code == 200:
            self.eventos = resp_eventos.json()

    def _mostrar_vazio(self, mensagem):
        self.var_score.set("—")
        self.lbl_score.configure(fg=TEXTO)
        for var in self.vars.values():
            var.set("—")
        self._limpar_tipos(mensagem)

    def _limpar_tipos(self, mensagem):
        for widget in self.tipos_frame.winfo_children():
            widget.destroy()
        tk.Label(self.tipos_frame, text=mensagem, bg=BG, fg=CINZA).pack(anchor="w")

    def _exibir_tipos(self, eventos_por_tipo):
        for widget in self.tipos_frame.winfo_children():
            widget.destroy()
        if not eventos_por_tipo:
            self._limpar_tipos("Nenhum evento de risco detectado.")
            return
        for tipo, quantidade in sorted(eventos_por_tipo.items(), key=lambda x: -x[1]):
            linha = tk.Frame(self.tipos_frame, bg=BG)
            linha.pack(fill="x", pady=2)
            tk.Label(linha, text="●", fg=CORES_TIPO.get(tipo, CINZA),
                     bg=BG, font=("Segoe UI", 11)).pack(side="left")
            tk.Label(linha, text=tipo, bg=BG, fg=TEXTO,
                     font=("Segoe UI", 11)).pack(side="left", padx=6)
            tk.Label(linha, text=str(quantidade), bg=BG, fg=TEXTO,
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
            with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
                escritor = csv.writer(arquivo, delimiter=";")
                escritor.writerow(["Relatório de Telemetria Veicular"])
                escritor.writerow([])
                escritor.writerow(["Rota", resumo.get("nome")])
                escritor.writerow(["Score de segurança", resumo.get("score")])
                escritor.writerow(["Duração (s)", resumo.get("duracao_segundos")])
                escritor.writerow(["Distância (km)", resumo.get("distancia_km")])
                escritor.writerow(["Velocidade média (km/h)", resumo.get("velocidade_media")])
                escritor.writerow(["Velocidade máxima (km/h)", resumo.get("velocidade_maxima")])
                escritor.writerow(["RPM máximo", resumo.get("rpm_maximo")])
                escritor.writerow(["Total de eventos", resumo.get("total_eventos")])
                escritor.writerow([])
                escritor.writerow(["Eventos por tipo"])
                for tipo, quantidade in (resumo.get("eventos_por_tipo") or {}).items():
                    escritor.writerow([tipo, quantidade])
                escritor.writerow([])
                escritor.writerow(["Detalhe dos eventos"])
                escritor.writerow([
                    "Tipo", "Método", "Canal", "Valor", "Hora",
                    "Força G", "Instabilidade", "Descrição",
                ])
                for evento in self.eventos:
                    escritor.writerow([
                        evento.get("classificacao"), evento.get("metodo"),
                        evento.get("canal"), evento.get("valor"),
                        _so_hora(evento.get("data_hora")),
                        evento.get("forca_g"), evento.get("instabilidade"),
                        evento.get("descricao"),
                    ])
        except OSError as erro:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{erro}")
            return
        messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{caminho}")


# =========================================================================
# Gráfico (velocidade + Força G + RPM, com limiares do JSON e tooltip)
# =========================================================================
class GraficoTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self._pontos = []
        self.figure = Figure(figsize=(7.2, 6.0), dpi=100, facecolor=BG)
        self.ax_vel = self.figure.add_subplot(311)
        self.ax_fg = self.figure.add_subplot(312, sharex=self.ax_vel)
        self.ax_rpm = self.figure.add_subplot(313, sharex=self.ax_vel)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self._tooltip = None
        self._build()

    def _build(self):
        _titulo(self, "Comportamento da Rota",
                "Linhas tracejadas = limiares configurados. Passe o mouse para ver os valores.")
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(5, 15))
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.plotar()

    def _limiares(self):
        try:
            resp = self.app.api.get_limiares()
            if resp.status_code == 200:
                return resp.json()
        except requests.exceptions.RequestException:
            pass
        return {}

    def plotar(self):
        rota_id = self.app.rota_atual_id
        for eixo in (self.ax_vel, self.ax_fg, self.ax_rpm):
            eixo.clear()
        self._pontos = []
        self._tooltip = None

        if not rota_id:
            self._mostrar_mensagem("Selecione uma rota para visualizar o gráfico.", CINZA)
            return

        self._mostrar_mensagem("Analisando a rota…", CINZA)

        def carregar():
            # grafico_rota já dispara a análise (idempotente) no servidor.
            resp = self.app.api.grafico_rota(rota_id)
            return rota_id, resp

        self.app.carregar_async(carregar, self._render)

    def _mostrar_mensagem(self, texto, cor):
        self.ax_fg.set_visible(False)
        self.ax_rpm.set_visible(False)
        self.ax_vel.text(0.5, 0.5, texto, ha="center", va="center", fontsize=12,
                         color=cor, transform=self.ax_vel.transAxes)
        self.ax_vel.set_xticks([])
        self.ax_vel.set_yticks([])
        self.canvas.draw()

    def _render(self, resultado):
        if isinstance(resultado, dict) and "__erro__" in resultado:
            self._mostrar_mensagem(resultado["__erro__"], "#d63031")
            return
        rota_id, resp = resultado
        if rota_id != self.app.rota_atual_id:
            return
        self.ax_fg.set_visible(True)
        self.ax_rpm.set_visible(True)
        if resp.status_code != 200:
            self._mostrar_mensagem(extract_error(resp), "#d63031")
            return

        dados = resp.json()
        pontos = dados["pontos"]
        self._pontos = pontos
        tempos = [p["tempo"] for p in pontos]
        velocidades = [p["velocidade"] if p["velocidade"] is not None else 0.0 for p in pontos]
        forcas = [p["forca_g"] if p["forca_g"] is not None else 0.0 for p in pontos]
        rpms = [p["rpm"] if p["rpm"] is not None else 0.0 for p in pontos]
        limiares = self._limiares()

        # Painel 1 — velocidade + pontos de risco coloridos.
        self.ax_vel.plot(tempos, velocidades, color="#0984e3", linewidth=1.3,
                         label="Velocidade (km/h)")
        if limiares.get("velocidade_max") is not None:
            self.ax_vel.axhline(y=limiares["velocidade_max"], color="#f39c12",
                                linestyle="--", linewidth=1.1,
                                label=f"Limite {limiares['velocidade_max']:.0f} km/h")
        por_tipo = {}
        for ponto in pontos:
            if ponto["risco"] and ponto["classificacoes"]:
                tipo = tipo_principal(ponto["classificacoes"])
                por_tipo.setdefault(tipo, []).append((ponto["tempo"], ponto["velocidade"]))
        for tipo, lista in por_tipo.items():
            if lista:
                t, v = zip(*lista)
                self.ax_vel.scatter(t, v, color=CORES_TIPO.get(tipo, "#d63031"),
                                    s=28, zorder=5, label=tipo)
        self.ax_vel.set_ylabel("Velocidade (km/h)")
        self.ax_vel.set_title(dados["nome"], fontsize=11)
        self.ax_vel.legend(loc="upper right", fontsize="x-small", ncol=2)
        self.ax_vel.grid(True, linestyle="--", alpha=0.4)

        # Painel 2 — Força G resultante + limiar lateral.
        self.ax_fg.plot(tempos, forcas, color="#e17055", linewidth=1.2,
                        label="Força G resultante (m/s²)")
        if limiares.get("lateral_max") is not None:
            self.ax_fg.axhline(y=limiares["lateral_max"], color="#d63031",
                               linestyle="--", linewidth=1.1,
                               label=f"Limite lateral {limiares['lateral_max']:.1f} m/s²")
        self.ax_fg.set_ylabel("Força G (m/s²)")
        self.ax_fg.legend(loc="upper right", fontsize="x-small")
        self.ax_fg.grid(True, linestyle="--", alpha=0.4)

        # Painel 3 — RPM + limiar.
        self.ax_rpm.plot(tempos, rpms, color="#6c5ce7", linewidth=1.2, label="RPM")
        if limiares.get("rpm_max") is not None:
            self.ax_rpm.axhline(y=limiares["rpm_max"], color="#e84393",
                                linestyle="--", linewidth=1.1,
                                label=f"Limite {limiares['rpm_max']:.0f} RPM")
        self.ax_rpm.set_ylabel("RPM")
        self.ax_rpm.set_xlabel("Tempo (s)")
        self.ax_rpm.legend(loc="upper right", fontsize="x-small")
        self.ax_rpm.grid(True, linestyle="--", alpha=0.4)

        self._tooltip = self.ax_vel.annotate(
            "", xy=(0, 0), xytext=(10, 10), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=BORDA),
            fontsize=8, arrowprops=dict(arrowstyle="->", color=CINZA),
        )
        self._tooltip.set_visible(False)

        self.figure.tight_layout()
        self.canvas.draw()

    def _on_hover(self, event):
        if self._tooltip is None or not self._pontos or event.inaxes is not self.ax_vel:
            if self._tooltip is not None and self._tooltip.get_visible():
                self._tooltip.set_visible(False)
                self.canvas.draw_idle()
            return
        if event.xdata is None:
            return
        ponto = min(self._pontos, key=lambda p: abs(p["tempo"] - event.xdata))
        texto = (
            f"t = {ponto['tempo']:.1f} s\n"
            f"Velocidade: {_fmt_num(ponto['velocidade']) or '—'} km/h\n"
            f"Força G: {_fmt_num(ponto['forca_g'], 2) or '—'} m/s²\n"
            f"RPM: {_fmt_num(ponto['rpm'], 0) or '—'}"
        )
        if ponto["classificacoes"]:
            texto += "\nRisco: " + ", ".join(sorted(set(ponto["classificacoes"])))
        self._tooltip.xy = (ponto["tempo"], ponto["velocidade"] or 0)
        self._tooltip.set_text(texto)
        self._tooltip.set_visible(True)
        self.canvas.draw_idle()


# =========================================================================
# Mapa
# =========================================================================
class MapaTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.mapa = None
        self._build()

    def _build(self):
        _titulo(self, "Trajeto no Mapa", "Pontos de GPS e trechos com eventos de risco.")
        self.msg = tk.Label(self, text="Carregando...", bg=BG, fg=CINZA,
                            font=("Segoe UI", 10))
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
            self.msg.configure(text="Selecione uma rota com GPS para visualizar o trajeto.")
            return
        self.msg.configure(text="Analisando a rota…")

        def carregar():
            # grafico_rota já dispara a análise (idempotente) no servidor.
            resp = self.app.api.grafico_rota(rota_id)
            return rota_id, resp

        self.app.carregar_async(carregar, self._render)

    def _render(self, resultado):
        if isinstance(resultado, dict) and "__erro__" in resultado:
            self.msg.configure(text=resultado["__erro__"])
            return
        rota_id, resp = resultado
        if rota_id != self.app.rota_atual_id:
            return
        if resp.status_code != 200:
            self.msg.configure(text=extract_error(resp))
            return
        pontos = resp.json()["pontos"]
        coordenadas = [(p["latitude"], p["longitude"]) for p in pontos
                       if p.get("latitude") is not None and p.get("longitude") is not None]
        if not coordenadas:
            self.msg.configure(text="Esta rota não possui dados de GPS (latitude/longitude).")
            return

        self.mapa.set_position(coordenadas[0][0], coordenadas[0][1])
        if len(coordenadas) >= 2:
            self.mapa.set_path(coordenadas, color="#0984e3", width=4)

        n_risco = 0
        for ponto in pontos:
            if ponto["risco"] and ponto.get("latitude") is not None and ponto.get("longitude") is not None:
                tipo = tipo_principal(ponto["classificacoes"])
                cor = CORES_TIPO.get(tipo, "#d63031")
                self.mapa.set_marker(
                    ponto["latitude"], ponto["longitude"],
                    text=tipo or "Risco",
                    marker_color_circle=cor, marker_color_outside=cor,
                    text_color="white",
                )
                n_risco += 1
        self.msg.configure(
            text=f"{len(coordenadas)} pontos de GPS · {n_risco} trecho(s) de risco."
        )


# =========================================================================
# Comparar
# =========================================================================
class CompararTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.rotas = []
        self.tree = None
        self._build()

    def _build(self):
        _titulo(self, "Comparar Rotas", "Compare o score e as métricas de duas viagens.")

        selecao = tk.Frame(self, bg=BG)
        selecao.pack(anchor="w", padx=20, pady=6)
        tk.Label(selecao, text="Rota A:", bg=BG, fg=TEXTO,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=4)
        self.combo_a = ttk.Combobox(selecao, state="readonly", width=28)
        self.combo_a.pack(side="left", padx=4)
        tk.Label(selecao, text="Rota B:", bg=BG, fg=TEXTO,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=4)
        self.combo_b = ttk.Combobox(selecao, state="readonly", width=28)
        self.combo_b.pack(side="left", padx=4)
        _botao(selecao, "Comparar", "#6c5ce7", self.comparar, width=12).pack(
            side="left", padx=6)

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        cols = ("metrica", "a", "b")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=11)
        self.tree.heading("metrica", text="Métrica")
        self.tree.heading("a", text="Rota A")
        self.tree.heading("b", text="Rota B")
        self.tree.column("metrica", width=240, anchor="w")
        self.tree.column("a", width=200, anchor="center")
        self.tree.column("b", width=200, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

    def atualizar(self):
        self.rotas = self.app.rotas
        nomes = [_rotulo_rota(r) for r in self.rotas]
        self.combo_a["values"] = nomes
        self.combo_b["values"] = nomes
        if nomes:
            self.combo_a.current(0)
            self.combo_b.current(1 if len(nomes) > 1 else 0)

    def _rota_id(self, combo):
        indice = combo.current()
        if indice < 0 or indice >= len(self.rotas):
            return None
        return self.rotas[indice]["id"]

    def comparar(self):
        ida = self._rota_id(self.combo_a)
        idb = self._rota_id(self.combo_b)
        if ida is None or idb is None:
            messagebox.showwarning("Aviso", "Selecione as duas rotas para comparar.")
            return
        try:
            resp = self.app.api.comparar_rotas([ida, idb])
        except requests.exceptions.RequestException as erro:
            _erro_conexao(erro)
            return
        if resp.status_code != 200:
            _erro_api(resp)
            return
        rotas = resp.json()["rotas"]
        if len(rotas) < 2:
            messagebox.showwarning("Aviso", "Selecione duas rotas válidas.")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        def fmt(valor, casas=1):
            if valor is None:
                return "—"
            return f"{valor:.{casas}f}" if isinstance(valor, (int, float)) else str(valor)

        linhas = [
            ("Score de segurança", lambda r: str(r["score"])),
            ("Duração", lambda r: formatar_duracao(r.get("duracao_segundos", 0))),
            ("Distância (km)", lambda r: fmt(r.get("distancia_km"), 2)),
            ("Velocidade média (km/h)", lambda r: fmt(r.get("velocidade_media"))),
            ("Velocidade máxima (km/h)", lambda r: fmt(r.get("velocidade_maxima"))),
            ("RPM máximo", lambda r: fmt(r.get("rpm_maximo"), 0)),
            ("Total de eventos", lambda r: str(r.get("total_eventos", 0))),
            ("Comportamento atípico",
             lambda r: str((r.get("eventos_por_tipo") or {}).get("Comportamento atípico", 0))),
        ]
        for rotulo, funcao in linhas:
            self.tree.insert("", "end", values=(rotulo, funcao(rotas[0]), funcao(rotas[1])))

        melhor = "Rota A" if rotas[0]["score"] >= rotas[1]["score"] else "Rota B"
        messagebox.showinfo(
            "Comparação",
            f"{melhor} apresentou o maior score de segurança "
            f"({max(rotas[0]['score'], rotas[1]['score'])} vs "
            f"{min(rotas[0]['score'], rotas[1]['score'])}).",
        )
