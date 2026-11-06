"""Telas da interface gráfica.

Contém a classe base `CrudTab` (com toda a estrutura comum de uma tela CRUD)
e as subclasses específicas de cada entidade. O uso de herança permite
reaproveitar o código e personalizar apenas o que muda em cada tela.
"""
import tkinter as tk
from tkinter import ttk, messagebox

import requests

from api_client import extract_error


class CrudTab(tk.Frame):
    """Estrutura comum: formulário (ID + campos), botões e tabela de registros."""

    RESOURCE = ""        # caminho da API (ex.: "veiculos")
    TITLE = ""           # título exibido na tela
    FIELDS = []          # [{"key", "label", "required"}]
    COLUMNS = []         # [("key", "label", "width")]

    BG = "#f5f6fa"

    def __init__(self, master, api):
        super().__init__(master, bg=self.BG)
        self.api = api
        self.entries = {}
        self.tree = None
        self._build()
        self.atualizar(silent=True)

    # ---------------------------------------------------------------- UI
    def _build(self):
        tk.Label(self, text=self.TITLE, font=("Segoe UI", 20, "bold"),
                 bg=self.BG, fg="#2d3436").pack(pady=(15, 10))

        form = tk.Frame(self, bg=self.BG)
        form.pack(fill="x", padx=20)

        self.entries["id"] = self._field(form, 0, "ID (buscar/editar/excluir):")

        row = 1
        for field in self.FIELDS:
            self.entries[field["key"]] = self._field(form, row, field["label"] + ":")
            row += 1

        btns = tk.Frame(self, bg=self.BG)
        btns.pack(pady=10)
        self._button(btns, "Cadastrar", "#0984e3", self.cadastrar)
        self._button(btns, "Buscar", "#6c5ce7", self.buscar)
        self._button(btns, "Editar", "#e17055", self.editar)
        self._button(btns, "Excluir", "#d63031", self.excluir)
        self._button(btns, "Limpar", "#636e72", self.limpar)
        self._button(btns, "Atualizar", "#00b894", self.atualizar)
        self._extra_buttons(btns)

        self._build_tree()

    def _field(self, parent, row, label_text):
        tk.Label(parent, text=label_text, font=("Segoe UI", 10, "bold"),
                 bg=self.BG, fg="#2d3436").grid(row=row, column=0, sticky="w", pady=3)
        entry = tk.Entry(parent, font=("Segoe UI", 11), relief="solid", bd=1, width=40)
        entry.grid(row=row, column=1, pady=3, ipady=4, padx=10, sticky="w")
        return entry

    def _button(self, parent, text, color, command):
        tk.Button(parent, text=text, command=command, font=("Segoe UI", 10, "bold"),
                  bg=color, fg="white", activebackground=color, activeforeground="white",
                  relief="flat", cursor="hand2", width=11, height=1, bd=0
                  ).pack(side="left", padx=4)

    def _build_tree(self):
        frame = tk.Frame(self, bg=self.BG)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        cols = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        for key, label, width in self.COLUMNS:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, anchor="center")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _extra_buttons(self, parent):
        """Ponto de extensão para telas com botões adicionais."""

    # ------------------------------------------------------- helpers
    def _on_select(self, _event):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0])["values"]
        record = dict(zip([c[0] for c in self.COLUMNS], values))
        self._fill_form(record)

    def _get_id(self):
        raw = self.entries["id"].get().strip()
        if not raw:
            messagebox.showwarning("Aviso", "Informe o ID do registro.")
            return None
        try:
            return int(raw)
        except ValueError:
            messagebox.showwarning("Aviso", "O ID deve ser um número inteiro.")
            return None

    def _get_payload(self):
        return {f["key"]: self.entries[f["key"]].get().strip() for f in self.FIELDS}

    def _check_required(self):
        for field in self.FIELDS:
            if field.get("required") and not self.entries[field["key"]].get().strip():
                messagebox.showwarning("Aviso", f"O campo '{field['label']}' é obrigatório.")
                return False
        return True

    def _fill_form(self, record):
        self.limpar()
        if "id" in record and record["id"] is not None:
            self.entries["id"].insert(0, str(record["id"]))
        for field in self.FIELDS:
            key = field["key"]
            if key in record and record[key] is not None:
                self.entries[key].insert(0, str(record[key]))

    def _populate_tree(self, items):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for item in items:
            values = [item.get(c[0], "") for c in self.COLUMNS]
            self.tree.insert("", "end", values=values)

    def _safe_call(self, func):
        try:
            return func()
        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Erro",
                "Não foi possível conectar à API.\nVerifique se o servidor está em execução.",
            )
            return None
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro de comunicação com a API:\n{e}")
            return None

    # ------------------------------------------------------- ações CRUD
    def atualizar(self, silent=False):
        try:
            resp = self.api.list(self.RESOURCE)
        except requests.exceptions.RequestException:
            if not silent:
                messagebox.showerror(
                    "Erro",
                    "Não foi possível conectar à API.\nVerifique se o servidor está em execução.",
                )
            return
        if resp.status_code == 200:
            self._populate_tree(resp.json())
        elif not silent:
            messagebox.showerror("Erro", extract_error(resp))

    def buscar(self):
        registro_id = self._get_id()
        if registro_id is None:
            return
        resp = self._safe_call(lambda: self.api.get(self.RESOURCE, registro_id))
        if resp is None:
            return
        if resp.status_code == 200:
            self._fill_form(resp.json())
        else:
            messagebox.showerror("Erro", extract_error(resp))

    def cadastrar(self):
        if not self._check_required():
            return
        resp = self._safe_call(lambda: self.api.create(self.RESOURCE, self._get_payload()))
        if resp is None:
            return
        if resp.status_code in (200, 201):
            messagebox.showinfo("Sucesso", "Registro cadastrado com sucesso.")
            self.limpar()
            self.atualizar()
        else:
            messagebox.showerror("Erro", extract_error(resp))

    def editar(self):
        registro_id = self._get_id()
        if registro_id is None:
            return
        if not self._check_required():
            return
        resp = self._safe_call(
            lambda: self.api.update(self.RESOURCE, registro_id, self._get_payload())
        )
        if resp is None:
            return
        if resp.status_code == 200:
            messagebox.showinfo("Sucesso", "Registro atualizado com sucesso.")
            self.limpar()
            self.atualizar()
        else:
            messagebox.showerror("Erro", extract_error(resp))

    def excluir(self):
        registro_id = self._get_id()
        if registro_id is None:
            return
        if not messagebox.askyesno("Confirmar", f"Excluir o registro de ID {registro_id}?"):
            return
        resp = self._safe_call(lambda: self.api.delete(self.RESOURCE, registro_id))
        if resp is None:
            return
        if resp.status_code == 200:
            messagebox.showinfo("Sucesso", "Registro excluído com sucesso.")
            self.limpar()
            self.atualizar()
        else:
            messagebox.showerror("Erro", extract_error(resp))

    def limpar(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)


# ======================================================================
# Telas específicas
# ======================================================================

class VeiculoTab(CrudTab):
    RESOURCE = "veiculos"
    TITLE = "Veículos"
    FIELDS = [
        {"key": "identificador", "label": "Identificador (placa)", "required": True},
        {"key": "modelo", "label": "Modelo", "required": False},
    ]
    COLUMNS = [
        ("id", "ID", 60),
        ("identificador", "Identificador", 140),
        ("modelo", "Modelo", 140),
        ("data_cadastro", "Cadastro", 170),
    ]

    def _extra_buttons(self, parent):
        self._button(parent, "Estatísticas", "#f39c12", self.ver_estatisticas)
        self._button(parent, "Detectar Riscos", "#d63031", self.analisar)

    def ver_estatisticas(self):
        veiculo_id = self._get_id()
        if veiculo_id is None:
            return
        resp = self._safe_call(lambda: self.api.estatisticas_veiculo(veiculo_id))
        if resp is None:
            return
        if resp.status_code == 200:
            dados = resp.json()
            linhas = [f"{chave}: {valor}" for chave, valor in dados.items()]
            messagebox.showinfo("Estatísticas do Veículo", "\n".join(linhas))
        else:
            messagebox.showerror("Erro", extract_error(resp))

    def analisar(self):
        veiculo_id = self._get_id()
        if veiculo_id is None:
            return
        resp = self._safe_call(lambda: self.api.analisar_veiculo(veiculo_id))
        if resp is None:
            return
        if resp.status_code == 200:
            eventos = resp.json()
            if eventos:
                messagebox.showwarning(
                    "Eventos de risco",
                    f"{len(eventos)} novo(s) evento(s) de risco detectado(s).",
                )
            else:
                messagebox.showinfo("Resultado", "Nenhum novo evento de risco detectado.")
        else:
            messagebox.showerror("Erro", extract_error(resp))


class ParametroTab(CrudTab):
    RESOURCE = "parametros"
    TITLE = "Parâmetros"
    FIELDS = [
        {"key": "nome", "label": "Nome (canônico)", "required": True},
        {"key": "unidade", "label": "Unidade", "required": True},
        {"key": "limite_min", "label": "Limite Mínimo", "required": True},
        {"key": "limite_max", "label": "Limite Máximo", "required": True},
    ]
    COLUMNS = [
        ("id", "ID", 60),
        ("nome", "Nome", 160),
        ("unidade", "Unidade", 90),
        ("limite_min", "Mín", 90),
        ("limite_max", "Máx", 90),
    ]


class MapeamentoTab(CrudTab):
    RESOURCE = "mapeamentos"
    TITLE = "Mapeamentos (padronização)"
    FIELDS = [
        {"key": "nome_bruto", "label": "Nome bruto (coluna)", "required": True},
        {"key": "parametro_id", "label": "ID do parâmetro", "required": True},
    ]
    COLUMNS = [
        ("id", "ID", 60),
        ("nome_bruto", "Nome bruto", 260),
        ("parametro_id", "Parâmetro", 110),
    ]


class LeituraTab(CrudTab):
    RESOURCE = "leituras"
    TITLE = "Leituras (frames de telemetria)"
    FIELDS = [
        {"key": "veiculo_id", "label": "ID do veículo", "required": True},
        {"key": "data_hora", "label": "Data/Hora (AAAA-MM-DDTHH:MM:SS)", "required": True},
        {"key": "velocidade", "label": "Velocidade", "required": False},
        {"key": "rpm", "label": "RPM", "required": False},
        {"key": "accel_x", "label": "Aceleração X", "required": False},
        {"key": "accel_y", "label": "Aceleração Y", "required": False},
        {"key": "accel_z", "label": "Aceleração Z", "required": False},
        {"key": "posicao_acelerador", "label": "Posição acelerador", "required": False},
        {"key": "latitude", "label": "Latitude", "required": False},
        {"key": "longitude", "label": "Longitude", "required": False},
    ]
    COLUMNS = [
        ("id", "ID", 55),
        ("veiculo_id", "Veíc.", 60),
        ("data_hora", "Data/Hora", 170),
        ("velocidade", "Vel.", 70),
        ("rpm", "RPM", 80),
        ("accel_x", "AX", 70),
        ("accel_y", "AY", 70),
        ("accel_z", "AZ", 70),
    ]


class EventoRiscoTab(CrudTab):
    RESOURCE = "eventos-risco"
    TITLE = "Eventos de Risco"
    FIELDS = [
        {"key": "leitura_id", "label": "ID da leitura", "required": True},
        {"key": "veiculo_id", "label": "ID do veículo", "required": True},
        {"key": "data_hora", "label": "Data/Hora (AAAA-MM-DDTHH:MM:SS)", "required": True},
        {"key": "metodo", "label": "Método", "required": True},
        {"key": "forca_g", "label": "Força G", "required": False},
        {"key": "instabilidade", "label": "Instabilidade", "required": False},
        {"key": "classificacao", "label": "Classificação", "required": False},
        {"key": "descricao", "label": "Descrição", "required": False},
    ]
    COLUMNS = [
        ("id", "ID", 55),
        ("veiculo_id", "Veíc.", 60),
        ("data_hora", "Data/Hora", 170),
        ("metodo", "Método", 110),
        ("forca_g", "Força G", 90),
        ("classificacao", "Classif.", 100),
    ]
