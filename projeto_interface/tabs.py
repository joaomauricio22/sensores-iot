"""Telas da interface gráfica (Tkinter).

Organização:
  - Dados: Rotas, Leituras e Eventos de Risco, com CRUD completo.
  - Visão Geral: resumo + score de segurança da rota + exportação CSV.
  - Gráfico: velocidade, Força G e RPM, com limiares do JSON e tooltip.
  - Análise por Sensor: estatísticas e % de leituras fora do limiar.
  - Comparar: compara o resumo de duas rotas.
"""
import csv
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import requests
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
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
      chave, rotulo, tipo ("texto", "numero", "combo", "datahora", "arquivo"),
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
            container = None
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
            elif tipo == "arquivo":
                # Campo com botão "Selecionar…" que abre o seletor de arquivo
                # (mesma função do fluxo de importação de CSV). O valor salvo é
                # apenas o nome do arquivo (arquivo_origem).
                container = tk.Frame(form, bg=BG)
                widget = tk.Entry(container, width=34, font=("Segoe UI", 10))
                widget.pack(side="left", fill="x", expand=True)
                atual = self.valores.get(chave)
                if atual is not None:
                    widget.insert(0, str(atual))
                tk.Button(
                    container, text="Selecionar…", font=("Segoe UI", 9),
                    cursor="hand2", command=lambda w=widget: self._escolher_arquivo(w),
                ).pack(side="left", padx=(6, 0))
            else:
                widget = tk.Entry(form, width=40, font=("Segoe UI", 10))
                atual = self.valores.get(chave)
                if atual is not None:
                    if tipo == "datahora":
                        atual = _para_exibicao(atual)
                    widget.insert(0, str(atual))
            (container or widget).grid(row=linha, column=1, sticky="ew", pady=5)
            self.widgets[chave] = widget

    def _escolher_arquivo(self, entrada):
        """Abre o seletor e preenche a entrada com o nome do arquivo escolhido."""
        caminho = filedialog.askopenfilename(
            title="Selecionar arquivo de origem",
            filetypes=[("CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        )
        if caminho:
            entrada.delete(0, "end")
            entrada.insert(0, os.path.basename(caminho))

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
        self.lbl_status = tk.Label(self, text="", bg=BG, fg=CINZA,
                                   font=("Segoe UI", 9))
        self.lbl_status.pack(anchor="w", padx=20)

        botoes = tk.Frame(self, bg=BG)
        botoes.pack(anchor="w", padx=20, pady=6)
        _botao(botoes, "Nova Rota", "#0984e3", self.nova).pack(side="left", padx=(0, 5))
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
        self.lbl_status.configure(text="Carregando…")

        def carregar():
            return self.app.api.list_rotas()

        self.app.carregar_async(carregar, self._render)

    def _render(self, resultado):
        if isinstance(resultado, dict) and "__erro__" in resultado:
            self.lbl_status.configure(text="Erro ao carregar as rotas.")
            return
        resp = resultado
        if resp.status_code != 200:
            self.lbl_status.configure(text="Erro ao carregar as rotas.")
            return
        self.rotas = resp.json()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for rota in self.rotas:
            self.tree.insert("", "end", values=(
                rota["id"], rota["nome"], rota.get("arquivo_origem") or "",
                _para_exibicao(rota.get("data_importacao")),
            ))
        self.lbl_status.configure(text=f"{len(self.rotas)} rota(s)")

    def nova(self):
        # "Nova rota" = importar um ou mais CSVs de telemetria. Cada arquivo
        # vira uma rota (cadastro em lote), conforme o fluxo do sistema.
        caminhos = filedialog.askopenfilenames(
            title="Selecionar arquivo(s) de telemetria",
            filetypes=[("CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        )
        if not caminhos:
            return

        caminhos = list(caminhos)
        self.lbl_status.configure(text=f"Importando 0/{len(caminhos)}…")

        def importar_todos():
            resultados = []
            for indice, caminho in enumerate(caminhos, start=1):
                nome = os.path.splitext(os.path.basename(caminho))[0]
                try:
                    with open(caminho, encoding="utf-8-sig", errors="replace") as arquivo:
                        conteudo = arquivo.read()
                except OSError as erro:
                    resultados.append((nome, False, f"Não foi possível ler: {erro}"))
                    continue
                try:
                    resp = self.app.api.importar_csv(
                        nome, os.path.basename(caminho), conteudo
                    )
                except requests.exceptions.RequestException as erro:
                    resultados.append((nome, False, f"Erro de comunicação: {erro}"))
                    continue
                if resp.status_code in (200, 201):
                    dados = resp.json()
                    limpeza = dados.get("limpeza", {})
                    resultados.append((
                        nome, True,
                        f"{dados.get('total_leituras', 0)} leituras · "
                        f"{limpeza.get('total_removido', 0)} descartadas",
                    ))
                else:
                    resultados.append((nome, False, extract_error(resp)))
            return resultados

        self.app.carregar_async(importar_todos, self._render_importacao)

    def _render_importacao(self, resultados):
        if isinstance(resultados, dict) and "__erro__" in resultados:
            self.lbl_status.configure(text="Erro ao importar.")
            return
        criadas = [r for r in resultados if r[1]]
        falhas = [r for r in resultados if not r[1]]
        self.lbl_status.configure(text=f"{len(criadas)} rota(s) criada(s)")

        linhas = [f"{len(criadas)} rota(s) criada(s) com sucesso:"]
        linhas += [f"  • {nome} — {detalhe}" for nome, _ok, detalhe in criadas]
        if falhas:
            linhas.append("")
            linhas.append(f"{len(falhas)} falha(s):")
            linhas += [f"  • {nome} — {detalhe}" for nome, _ok, detalhe in falhas]
        messagebox.showinfo("Importação concluída", "\n".join(linhas))

        self.app.recarregar_rotas()

    def editar(self):
        rota_id = self._get_selecionada()
        if rota_id is None:
            return
        rota = next((r for r in self.rotas if r["id"] == rota_id), None)
        if rota is None:
            return
        dialogo = FormDialog(self, "Editar rota", [
            {"chave": "nome", "rotulo": "Nome da rota", "tipo": "texto", "obrigatorio": True},
            {"chave": "arquivo_origem", "rotulo": "Arquivo de origem", "tipo": "arquivo"},
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
        self.lbl_status = tk.Label(self, text="", bg=BG, fg=CINZA,
                                   font=("Segoe UI", 9))
        self.lbl_status.pack(anchor="w", padx=20)

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
        self.lbl_status.configure(text="Carregando…")

        filtro = self._rota_filtro()

        def carregar():
            return self.app.api.list_leituras(filtro)

        self.app.carregar_async(carregar, self._render)

    def _render(self, resultado):
        if isinstance(resultado, dict) and "__erro__" in resultado:
            self.lbl_status.configure(text="Erro ao carregar as leituras.")
            return
        resp = resultado
        if resp.status_code != 200:
            self.lbl_status.configure(text="Erro ao carregar as leituras.")
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
        self.lbl_status.configure(text=f"{len(self.leituras)} leitura(s)")

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
        self.lbl_status = tk.Label(self, text="", bg=BG, fg=CINZA,
                                   font=("Segoe UI", 9))
        self.lbl_status.pack(anchor="w", padx=20)

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
        self.lbl_status.configure(text="Carregando…")

        def carregar():
            resp = self.app.api.list_eventos(filtro, tipo)
            resp_sensores = self.app.api.get_sensores()
            # Carrega as leituras apenas da rota filtrada (evita trazer todas).
            resp_leituras = self.app.api.list_leituras(filtro) if filtro is not None else None
            return resp, resp_sensores, resp_leituras

        self.app.carregar_async(carregar, self._render)

    def _render(self, resultado):
        if isinstance(resultado, dict) and "__erro__" in resultado:
            self.lbl_status.configure(text="Erro ao carregar os eventos.")
            return
        resp, resp_sensores, resp_leituras = resultado
        if resp.status_code != 200:
            self.lbl_status.configure(text="Erro ao carregar os eventos.")
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
        self.lbl_status.configure(text=f"{len(self.eventos)} evento(s)")

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
                "Linhas tracejadas = limiares configurados. Use a barra abaixo para dar zoom.")
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(5, 0))
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.toolbar.pack(fill="x", padx=15, pady=(0, 8))
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.plotar()

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
            # Busca os limiares em background para não travar a thread principal.
            resp_limiares = self.app.api.get_limiares()
            return rota_id, resp, resp_limiares

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
        rota_id, resp, resp_limiares = resultado
        if rota_id != self.app.rota_atual_id:
            return
        # Limpa os eixos para remover a mensagem "Analisando a rota…" (que
        # ficaria como marca d'água atrás das linhas).
        for eixo in (self.ax_vel, self.ax_fg, self.ax_rpm):
            eixo.clear()
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
        limiares = resp_limiares.json() if resp_limiares.status_code == 200 else {}

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
            zorder=20, annotation_clip=False,
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
# Análise por Sensor
# =========================================================================
class SensorTab(tk.Frame):

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.figure = Figure(figsize=(7.0, 3.4), dpi=100, facecolor=BG)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self._build()

    def _build(self):
        _titulo(self, "Análise por Sensor",
                "Estatísticas dos sensores e % de leituras fora do limiar configurado.")
        self.lbl_status = tk.Label(self, text="", bg=BG, fg=CINZA,
                                   font=("Segoe UI", 9))
        self.lbl_status.pack(anchor="w", padx=20)

        tabela = tk.Frame(self, bg=BG)
        tabela.pack(fill="both", expand=False, padx=20, pady=(5, 4))
        cols = ("sensor", "min", "max", "media", "limiar", "fora_n", "fora_pct")
        self.tree = ttk.Treeview(tabela, columns=cols, show="headings", height=4)
        for chave, rotulo, largura, ancora in [
            ("sensor", "Sensor", 210, "w"),
            ("min", "Mín", 90, "center"),
            ("max", "Máx", 90, "center"),
            ("media", "Média", 90, "center"),
            ("limiar", "Limiar", 130, "center"),
            ("fora_n", "Fora (n)", 90, "center"),
            ("fora_pct", "Fora (%)", 90, "center"),
        ]:
            self.tree.heading(chave, text=rotulo)
            self.tree.column(chave, width=largura, anchor=ancora)
        self.tree.pack(fill="both", expand=True)

        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 0))
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.toolbar.pack(fill="x", padx=20, pady=(0, 10))

    def atualizar(self):
        rota_id = self.app.rota_atual_id
        if not rota_id:
            self.lbl_status.configure(text="Selecione uma rota para ver a análise por sensor.")
            self._limpar()
            return
        self.lbl_status.configure(text="Carregando…")

        def carregar():
            # grafico_rota já dispara a análise (idempotente) no servidor.
            resp = self.app.api.grafico_rota(rota_id)
            resp_limiares = self.app.api.get_limiares()
            return rota_id, resp, resp_limiares

        self.app.carregar_async(carregar, self._render)

    def _limpar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.ax.clear()
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()

    def _render(self, resultado):
        if isinstance(resultado, dict) and "__erro__" in resultado:
            self.lbl_status.configure(text="Erro ao carregar a análise por sensor.")
            self._limpar()
            return
        rota_id, resp, resp_limiares = resultado
        if rota_id != self.app.rota_atual_id:
            return
        if resp.status_code != 200:
            self.lbl_status.configure(text=extract_error(resp))
            self._limpar()
            return

        dados = resp.json()
        pontos = dados["pontos"]
        limiares = resp_limiares.json() if resp_limiares.status_code == 200 else {}
        limiares = limiares.get("limiares", limiares)  # compatibilidade

        if not pontos:
            self.lbl_status.configure(text="Esta rota não possui leituras.")
            self._limpar()
            return

        metricas = self._calcular(pontos, limiares)

        for item in self.tree.get_children():
            self.tree.delete(item)
        for m in metricas:
            self.tree.insert("", "end", values=(
                m["rotulo"], _fmt_num(m["min"], m["casas"]),
                _fmt_num(m["max"], m["casas"]), _fmt_num(m["media"], m["casas"]),
                m["limiar_texto"], m["fora_n"], f"{m['fora_pct']:.1f}%",
            ))

        self._desenhar_barras(metricas)
        self.lbl_status.configure(text=f"{len(pontos)} leitura(s) analisadas.")

    def _calcular(self, pontos, limiares):
        def serie(campo):
            return [p[campo] for p in pontos]

        def stats(valores):
            valores = [v for v in valores if v is not None]
            if not valores:
                return {"min": None, "max": None, "media": None}
            return {
                "min": min(valores),
                "max": max(valores),
                "media": sum(valores) / len(valores),
            }

        def fora(valores, lo=None, hi=None):
            n = 0
            for v in valores:
                if v is None:
                    continue
                if (lo is not None and v < lo) or (hi is not None and v > hi):
                    n += 1
            return n

        total = len(pontos)

        def pct(n):
            return (n / total * 100.0) if total else 0.0

        v_max = limiares.get("velocidade_max")
        g_max = limiares.get("lateral_max")
        r_max = limiares.get("rpm_max")
        a_max = limiares.get("aceleracao_max")
        f_max = limiares.get("frenagem_max")

        vel = serie("velocidade")
        fg = serie("forca_g")
        rpm = serie("rpm")
        acel = serie("acel_longitudinal")

        def rotulo_limiar(lo, hi, casas=1):
            if lo is None and hi is None:
                return "—"
            if lo is not None and hi is not None:
                return f"{_fmt_num(lo, casas)} / {_fmt_num(hi, casas)}"
            return _fmt_num(hi if hi is not None else lo, casas)

        return [
            {"rotulo": "Velocidade (km/h)", "casas": 1,
             **stats(vel), "limiar_texto": rotulo_limiar(None, v_max),
             "fora_n": fora(vel, hi=v_max), "fora_pct": pct(fora(vel, hi=v_max))},
            {"rotulo": "Força G (m/s²)", "casas": 2,
             **stats(fg), "limiar_texto": rotulo_limiar(None, g_max),
             "fora_n": fora(fg, hi=g_max), "fora_pct": pct(fora(fg, hi=g_max))},
            {"rotulo": "RPM", "casas": 0,
             **stats(rpm), "limiar_texto": rotulo_limiar(None, r_max, 0),
             "fora_n": fora(rpm, hi=r_max), "fora_pct": pct(fora(rpm, hi=r_max))},
            {"rotulo": "Aceleração long. (m/s²)", "casas": 2,
             **stats(acel), "limiar_texto": rotulo_limiar(f_max, a_max, 1),
             "fora_n": fora(acel, lo=f_max, hi=a_max),
             "fora_pct": pct(fora(acel, lo=f_max, hi=a_max))},
        ]

    def _desenhar_barras(self, metricas):
        self.ax.clear()
        nomes = ["Velocidade", "Força G", "RPM", "Acel. long."]
        valores = [m["fora_pct"] for m in metricas]
        cores = ["#0984e3", "#e17055", "#6c5ce7", "#00b894"]
        barras = self.ax.bar(nomes, valores, color=cores[:len(nomes)])
        self.ax.set_ylabel("% de leituras fora do limiar")
        topo = max(valores) * 1.15 if valores else 0
        self.ax.set_ylim(0, max(topo, 10))
        for barra, v in zip(barras, valores):
            self.ax.text(barra.get_x() + barra.get_width() / 2,
                         barra.get_height() + max(topo, 10) * 0.02,
                         f"{v:.1f}%", ha="center", va="bottom", fontsize=9)
        self.ax.grid(axis="y", linestyle="--", alpha=0.4)
        self.figure.tight_layout()
        self.canvas.draw()


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
