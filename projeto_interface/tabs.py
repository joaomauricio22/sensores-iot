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

    RESOURCE = ""        # caminho da API (ex.: "tipos-sensor")
    TITLE = ""           # título exibido na tela
    FIELDS = []          # [{"key", "label", "required"}]
    COLUMNS = []         # [("key", "label", width)]

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

        # ---- Formulário ----
        form = tk.Frame(self, bg=self.BG)
        form.pack(fill="x", padx=20)

        self.entries["id"] = self._field(form, 0, "ID (buscar/editar/excluir):")

        row = 1
        for field in self.FIELDS:
            self.entries[field["key"]] = self._field(form, row, field["label"] + ":")
            row += 1

        # ---- Botões ----
        btns = tk.Frame(self, bg=self.BG)
        btns.pack(pady=10)
        self._button(btns, "Cadastrar", "#0984e3", self.cadastrar)
        self._button(btns, "Buscar", "#6c5ce7", self.buscar)
        self._button(btns, "Editar", "#e17055", self.editar)
        self._button(btns, "Excluir", "#d63031", self.excluir)
        self._button(btns, "Limpar", "#636e72", self.limpar)
        self._button(btns, "Atualizar", "#00b894", self.atualizar)
        self._extra_buttons(btns)

        # ---- Tabela ----
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

        # Ao clicar numa linha, preenche o formulário (facilita editar/excluir).
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

class TipoSensorTab(CrudTab):
    RESOURCE = "tipos-sensor"
    TITLE = "Tipos de Sensor"
    FIELDS = [
        {"key": "nome", "label": "Nome", "required": True},
        {"key": "unidade", "label": "Unidade", "required": True},
        {"key": "descricao", "label": "Descrição", "required": False},
    ]
    COLUMNS = [
        ("id", "ID", 60),
        ("nome", "Nome", 140),
        ("unidade", "Unidade", 80),
        ("descricao", "Descrição", 220),
    ]


class SensorTab(CrudTab):
    RESOURCE = "sensores"
    TITLE = "Sensores"
    FIELDS = [
        {"key": "identificador", "label": "Identificador", "required": True},
        {"key": "nome", "label": "Nome", "required": False},
        {"key": "tipo_sensor_id", "label": "ID do Tipo", "required": True},
        {"key": "limite_min", "label": "Limite Mínimo", "required": True},
        {"key": "limite_max", "label": "Limite Máximo", "required": True},
    ]
    COLUMNS = [
        ("id", "ID", 60),
        ("identificador", "Identificador", 130),
        ("nome", "Nome", 130),
        ("tipo_sensor_id", "Tipo", 60),
        ("limite_min", "Mín", 70),
        ("limite_max", "Máx", 70),
        ("data_cadastro", "Cadastro", 160),
    ]

    def _extra_buttons(self, parent):
        self._button(parent, "Estatísticas", "#f39c12", self.ver_estatisticas)

    def ver_estatisticas(self):
        sensor_id = self._get_id()
        if sensor_id is None:
            return
        resp = self._safe_call(lambda: self.api.estatisticas_sensor(sensor_id))
        if resp is None:
            return
        if resp.status_code == 200:
            dados = resp.json()
            linhas = [f"{chave}: {valor}" for chave, valor in dados.items()]
            messagebox.showinfo("Estatísticas do Sensor", "\n".join(linhas))
        else:
            messagebox.showerror("Erro", extract_error(resp))


class LeituraTab(CrudTab):
    RESOURCE = "leituras"
    TITLE = "Leituras"
    FIELDS = [
        {"key": "sensor_id", "label": "ID do Sensor", "required": True},
        {"key": "valor", "label": "Valor", "required": True},
        {"key": "data_hora", "label": "Data/Hora (AAAA-MM-DDTHH:MM:SS)", "required": True},
    ]
    COLUMNS = [
        ("id", "ID", 60),
        ("sensor_id", "Sensor", 70),
        ("valor", "Valor", 90),
        ("data_hora", "Data/Hora", 180),
        ("classificacao", "Classificação", 110),
    ]

    def _extra_buttons(self, parent):
        self._button(parent, "Detectar Anomalias", "#d63031", self.detectar_anomalias)
        self._button(parent, "Classificar (ML)", "#0984e3", self.classificar_ml)

    def detectar_anomalias(self):
        leitura_id = self._get_id()
        if leitura_id is None:
            return
        resp = self._safe_call(lambda: self.api.analisar_leitura(leitura_id))
        if resp is None:
            return
        if resp.status_code == 200:
            anomalias = resp.json()
            if anomalias:
                linhas = []
                for a in anomalias:
                    linhas.append(f"Método {a.get('metodo')} - valor {a.get('valor')}")
                messagebox.showwarning("Anomalias detectadas", "\n".join(linhas))
            else:
                messagebox.showinfo("Resultado", "Nenhuma anomalia detectada.")
        else:
            messagebox.showerror("Erro", extract_error(resp))

    def classificar_ml(self):
        leitura_id = self._get_id()
        if leitura_id is None:
            return
        resp = self._safe_call(lambda: self.api.classificar_leitura(leitura_id))
        if resp is None:
            return
        if resp.status_code == 200:
            dados = resp.json()
            messagebox.showinfo(
                "Classificação",
                f"Leitura {dados.get('id')}: {dados.get('classificacao')}",
            )
            self.atualizar()
        else:
            messagebox.showerror("Erro", extract_error(resp))


class AnomaliaTab(CrudTab):
    RESOURCE = "anomalias"
    TITLE = "Anomalias"
    FIELDS = [
        {"key": "leitura_id", "label": "ID da Leitura", "required": True},
        {"key": "sensor_id", "label": "ID do Sensor", "required": True},
        {"key": "valor", "label": "Valor", "required": True},
        {"key": "data_hora", "label": "Data/Hora (AAAA-MM-DDTHH:MM:SS)", "required": True},
        {"key": "metodo", "label": "Método", "required": True},
        {"key": "descricao", "label": "Descrição", "required": False},
    ]
    COLUMNS = [
        ("id", "ID", 60),
        ("leitura_id", "Leitura", 70),
        ("sensor_id", "Sensor", 70),
        ("valor", "Valor", 90),
        ("data_hora", "Data/Hora", 180),
        ("metodo", "Método", 110),
        ("descricao", "Descrição", 220),
    ]
