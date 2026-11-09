"""Ponto de entrada da interface gráfica (Tkinter).

A interface é separada da API: toda operação passa por HTTP (ApiClient).
Navegação lateral:
  Dados (Rotas / Leituras / Eventos) · Visão Geral · Gráfico · Sensores · Comparar

Executar: python main.py
"""
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import requests

from api_client import ApiClient
from tabs import (
    BG,
    BORDA,
    CINZA,
    CompararTab,
    DadosTab,
    DashboardTab,
    GraficoTab,
    SensorTab,
    TEXTO,
    _rotulo_rota,
)

COR_SIDEBAR = "#2d3436"
COR_ATIVO = "#0984e3"
COR_HOVER = "#3d4446"


class App:
    """Janela principal com barra lateral e área de conteúdo."""

    def __init__(self, root, api):
        self.root = root
        self.api = api
        self.rotas = []
        self.rota_atual_id = None
        self.secoes = {}
        self.botoes = {}
        self.secao_atual = None

        self.root.title("Telemetria Veicular — Detecção de Eventos de Risco")
        self.root.minsize(1080, 680)
        self.root.configure(bg=BG)
        self.__centralizar(1280, 800)

        # Fila usada para entregar, na thread principal, os resultados das
        # tarefas executadas em segundo plano (análise/consultas).
        self._fila = queue.Queue()
        self._agendar_consumidor()

        self._construir()
        self.recarregar_rotas()
        self.mostrar("dados")

    def __centralizar(self, largura, altura):
        """Posiciona a janela no centro da tela, mantendo o tamanho inicial.

        Sem ``+X+Y`` no geometry, o gerenciador de janelas abre a aplicação no
        canto superior esquerdo. Aqui calculamos o deslocamento a partir da
        resolução da tela para centralizá-la.
        """
        self.root.update_idletasks()  # garante dimensões reais da tela
        pos_x = max(0, (self.root.winfo_screenwidth() - largura) // 2)
        pos_y = max(0, (self.root.winfo_screenheight() - altura) // 2)
        self.root.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

    # ------------------------------------------------------------------ #
    # Construção da interface
    # ------------------------------------------------------------------ #
    def _construir(self):
        self.sidebar = tk.Frame(self.root, bg=COR_SIDEBAR, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="Telemetria", font=("Segoe UI", 16, "bold"),
                 bg=COR_SIDEBAR, fg="white").pack(pady=(22, 0))
        tk.Label(self.sidebar, text="Veicular", font=("Segoe UI", 11),
                 bg=COR_SIDEBAR, fg="#b2bec3").pack(pady=(0, 18))

        for chave, rotulo in [
            ("dados", "Dados"),
            ("visao", "Visão Geral"),
            ("grafico", "Gráfico"),
            ("sensores", "Sensores"),
            ("comparar", "Comparar"),
        ]:
            botao = tk.Button(
                self.sidebar, text=rotulo, anchor="w", padx=18,
                font=("Segoe UI", 11, "bold"), bg=COR_SIDEBAR, fg="white",
                activebackground=COR_ATIVO, activeforeground="white",
                relief="flat", bd=0, cursor="hand2",
                command=lambda c=chave: self.mostrar(c),
            )
            botao.pack(fill="x", pady=1)
            self.botoes[chave] = botao

        tk.Label(self.sidebar, text="Limiares em config/limiares.json",
                 font=("Segoe UI", 8), bg=COR_SIDEBAR, fg="#636e72",
                 wraplength=180, justify="left").pack(side="bottom", padx=12, pady=12)

        self.area = tk.Frame(self.root, bg=BG)
        self.area.pack(side="left", fill="both", expand=True)

        topo = tk.Frame(self.area, bg=BG, highlightbackground=BORDA, highlightthickness=1)
        topo.pack(fill="x")
        tk.Label(topo, text="Rota em análise:", font=("Segoe UI", 10, "bold"),
                 bg=BG, fg=TEXTO).pack(side="left", padx=(15, 6), pady=8)
        self.combo_rota = ttk.Combobox(topo, state="readonly", width=42)
        self.combo_rota.pack(side="left", pady=8)
        self.combo_rota.bind("<<ComboboxSelected>>", self._trocar_rota)
        self.lbl_status = tk.Label(topo, text="", font=("Segoe UI", 9),
                                   bg=BG, fg=CINZA)
        self.lbl_status.pack(side="right", padx=15)

        self.conteudo = tk.Frame(self.area, bg=BG)
        self.conteudo.pack(fill="both", expand=True)

        self.secoes = {
            "dados": DadosTab(self.conteudo, self),
            "visao": DashboardTab(self.conteudo, self),
            "grafico": GraficoTab(self.conteudo, self),
            "sensores": SensorTab(self.conteudo, self),
            "comparar": CompararTab(self.conteudo, self),
        }

    # ------------------------------------------------------------------ #
    # Navegação
    # ------------------------------------------------------------------ #
    def mostrar(self, chave):
        for nome, secao in self.secoes.items():
            if nome == chave:
                secao.pack(fill="both", expand=True)
            else:
                secao.pack_forget()

        for nome, botao in self.botoes.items():
            botao.configure(bg=COR_ATIVO if nome == chave else COR_SIDEBAR)

        self.secao_atual = chave
        secao = self.secoes[chave]
        if chave == "grafico":
            secao.plotar()
        elif hasattr(secao, "atualizar"):
            secao.atualizar()

    # ------------------------------------------------------------------ #
    # Rotas / seleção global
    # ------------------------------------------------------------------ #
    def recarregar_rotas(self, selecionar=None):
        try:
            resp = self.api.list_rotas()
        except requests.exceptions.RequestException:
            self.lbl_status.configure(text="API indisponível")
            return
        if resp.status_code != 200:
            self.lbl_status.configure(text="Erro ao carregar rotas")
            return

        self.rotas = resp.json()
        self.lbl_status.configure(text=f"{len(self.rotas)} rota(s) cadastrada(s)")
        nomes = ["Todas"] + [_rotulo_rota(r) for r in self.rotas]
        self.combo_rota["values"] = nomes

        if selecionar is not None and any(r["id"] == selecionar for r in self.rotas):
            self.definir_rota(selecionar)
        elif self.rota_atual_id is not None and any(
            r["id"] == self.rota_atual_id for r in self.rotas
        ):
            self.definir_rota(self.rota_atual_id)
        elif self.rotas:
            self.definir_rota(self.rotas[0]["id"])
        else:
            self.rota_atual_id = None
            self.combo_rota.set("Todas")

        # Atualiza as listas que dependem do cadastro de rotas.
        self.secoes["dados"].atualizar()
        self.secoes["comparar"].atualizar()
        if self.secao_atual in ("visao", "grafico", "sensores"):
            self.secoes[self.secao_atual].atualizar()

    def definir_rota(self, rota_id):
        self.rota_atual_id = rota_id
        for indice, rota in enumerate(self.rotas):
            if rota["id"] == rota_id:
                self.combo_rota.current(indice + 1)
                break
        else:
            self.combo_rota.set("Todas")
            self.rota_atual_id = None
        self.refresh_detalhes()

    def _trocar_rota(self, _event):
        indice = self.combo_rota.current()
        if indice <= 0:
            self.rota_atual_id = None
        else:
            self.rota_atual_id = self.rotas[indice - 1]["id"]
        self.refresh_detalhes()
        if self.secao_atual in ("visao", "grafico", "sensores"):
            self.secoes[self.secao_atual].atualizar()

    def refresh_detalhes(self):
        """Atualiza as seções que dependem da rota selecionada."""
        self.secoes["visao"].atualizar()
        self.secoes["grafico"].plotar()
        self.secoes["sensores"].atualizar()

    def carregar_async(self, funcao, ao_concluir):
        """Executa `funcao()` em uma thread e entrega o resultado na thread principal.

        Evita que a análise (ML) e as consultas pesadas congelem a interface.
        O resultado chega por uma fila, consumida pelo `_agendar_consumidor`
        (agendado na thread principal via `after`), que chama `ao_concluir`.
        """
        def trabalho():
            try:
                resultado = funcao()
            except requests.exceptions.RequestException as erro:
                resultado = {"__erro__": str(erro)}
            self._fila.put((ao_concluir, resultado))

        threading.Thread(target=trabalho, daemon=True).start()

    def _agendar_consumidor(self):
        """Drena a fila periodicamente na thread principal."""
        self._drenar_fila()
        self.root.after(100, self._agendar_consumidor)

    def _drenar_fila(self):
        while True:
            try:
                callback, resultado = self._fila.get_nowait()
            except queue.Empty:
                break
            try:
                callback(resultado)
            except Exception as erro:  # noqa: BLE001 — mantém o loop vivo
                print("Erro ao atualizar a interface:", erro)


def main():
    root = tk.Tk()
    api = ApiClient()
    try:
        App(root, api)
    except Exception as erro:  # noqa: BLE001
        messagebox.showerror("Erro ao iniciar", str(erro))
        root.destroy()
        raise
    root.mainloop()


if __name__ == "__main__":
    main()
