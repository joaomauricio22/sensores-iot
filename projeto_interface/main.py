"""Ponto de entrada da interface gráfica (Tkinter).

Fluxo: tela de login (entrar / criar conta) → tela principal com as abas
Rotas e Gráfico (o gráfico é gerado automaticamente após importar uma rota).

Executar: python main.py
"""
import tkinter as tk
from tkinter import messagebox, ttk

import requests

from api_client import ApiClient, extract_error
from tabs import GraficoTab, RotaTab


class CadastroWindow(tk.Toplevel):
    """Tela de cadastro de usuário (nome, senha e confirmação)."""

    def __init__(self, master, api):
        super().__init__(master)
        self.api = api
        self.title("Criar conta")
        self.geometry("360x280")
        self.configure(bg="#f5f6fa")
        self.resizable(False, False)
        self._build()

    def _build(self):
        tk.Label(self, text="Criar conta", font=("Segoe UI", 16, "bold"),
                 bg="#f5f6fa", fg="#2d3436").pack(pady=(18, 8))

        form = tk.Frame(self, bg="#f5f6fa")
        form.pack(pady=5)
        self.entry_nome = self._campo(form, 0, "Nome de usuário:")
        self.entry_senha = self._campo(form, 1, "Senha:", show="*")
        self.entry_confirmar = self._campo(form, 2, "Confirmar senha:", show="*")

        tk.Button(self, text="Cadastrar", bg="#00b894", fg="white", width=14,
                  font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                  command=self.cadastrar).pack(pady=16)

    def _campo(self, parent, row, label, show=None):
        tk.Label(parent, text=label, bg="#f5f6fa", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=5)
        entry = tk.Entry(parent, width=26, font=("Segoe UI", 11), show=show)
        entry.grid(row=row, column=1, pady=5, padx=8)
        return entry

    def cadastrar(self):
        nome = self.entry_nome.get().strip()
        senha = self.entry_senha.get()
        confirmar = self.entry_confirmar.get()
        if not nome:
            messagebox.showwarning("Aviso", "Informe um nome de usuário.")
            return
        if not senha:
            messagebox.showwarning("Aviso", "Informe uma senha.")
            return
        if senha != confirmar:
            messagebox.showerror("Erro", "As senhas não conferem.")
            return
        try:
            resp = self.api.registrar(nome, senha)
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Não foi possível conectar à API:\n{e}")
            return
        if resp.status_code in (200, 201):
            messagebox.showinfo("Sucesso", "Conta criada. Agora entre com seu usuário.")
            self.destroy()
        else:
            messagebox.showerror("Erro", extract_error(resp))


class LoginWindow:

    def __init__(self, root, api):
        self.root = root
        self.api = api
        self.root.title("Login — Telemetria Veicular")
        self.root.geometry("380x250")
        self.root.configure(bg="#f5f6fa")
        self.root.resizable(False, False)
        self._build()

    def _build(self):
        tk.Label(self.root, text="Telemetria Veicular", font=("Segoe UI", 18, "bold"),
                 bg="#f5f6fa", fg="#2d3436").pack(pady=(22, 5))
        tk.Label(self.root, text="Entre com seu usuário (ou crie uma conta)",
                 font=("Segoe UI", 10), bg="#f5f6fa", fg="#636e72").pack(pady=(0, 12))

        form = tk.Frame(self.root, bg="#f5f6fa")
        form.pack(pady=5)
        tk.Label(form, text="Usuário:", bg="#f5f6fa", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=5)
        self.entry_nome = tk.Entry(form, width=28, font=("Segoe UI", 11))
        self.entry_nome.grid(row=0, column=1, pady=5, padx=8)
        tk.Label(form, text="Senha:", bg="#f5f6fa", font=("Segoe UI", 10, "bold")).grid(
            row=1, column=0, sticky="w", pady=5)
        self.entry_senha = tk.Entry(form, width=28, show="*", font=("Segoe UI", 11))
        self.entry_senha.grid(row=1, column=1, pady=5, padx=8)

        btns = tk.Frame(self.root, bg="#f5f6fa")
        btns.pack(pady=16)
        tk.Button(btns, text="Entrar", bg="#0984e3", fg="white", width=11,
                  font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                  command=self.entrar).pack(side="left", padx=6)
        tk.Button(btns, text="Criar conta", bg="#00b894", fg="white", width=12,
                  font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                  command=self.criar_conta).pack(side="left", padx=6)

    def entrar(self):
        nome = self.entry_nome.get().strip()
        senha = self.entry_senha.get().strip()
        if not nome or not senha:
            messagebox.showwarning("Aviso", "Preencha usuário e senha.")
            return
        try:
            resp = self.api.login(nome, senha)
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Não foi possível conectar à API:\n{e}")
            return
        if resp.status_code == 200:
            self._abrir_principal()
        else:
            messagebox.showerror("Erro", extract_error(resp))

    def criar_conta(self):
        CadastroWindow(self.root, self.api)

    def _abrir_principal(self):
        self.root.destroy()
        root = tk.Tk()
        App(root, self.api)
        root.mainloop()


class App:

    def __init__(self, root, api):
        self.root = root
        self.api = api
        self.rota_atual_id = None
        self.root.title("Telemetria Veicular — Detecção de Eventos de Risco")
        self.root.geometry("1100x700")
        self.root.configure(bg="#f5f6fa")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.rota_tab = RotaTab(self.notebook, self)
        self.grafico_tab = GraficoTab(self.notebook, self)
        self.notebook.add(self.rota_tab, text="Rotas")
        self.notebook.add(self.grafico_tab, text="Gráfico")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _on_tab_change(self, _event):
        # ao abrir a aba Gráfico, plota automaticamente a rota selecionada.
        if self.notebook.index(self.notebook.select()) == 1:
            self.grafico_tab.plotar()

    def mostrar_grafico(self):
        self.notebook.select(1)
        self.grafico_tab.plotar()


def main():
    root = tk.Tk()
    api = ApiClient()
    LoginWindow(root, api)
    root.mainloop()


if __name__ == "__main__":
    main()
