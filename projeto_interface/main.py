"""Ponto de entrada da interface gráfica (Tkinter).

A interface é separada da API: toda operação passa por HTTP (ApiClient).
Navegação lateral:
  Dados (Rotas / Leituras / Eventos) · Visão Geral · Gráfico · Sensores · Comparar

Executar: python main.py
"""
import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import requests

from api_client import ApiClient, mensagem_conexao
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")


def aplicar_icone(root):
    """Define o ícone da janela (PNG para o Tk e ICO para o Windows)."""
    try:
        root.iconbitmap(default=os.path.join(ASSETS, "sentinela_icon.ico"))
    except tk.TclError:
        pass
    try:
        icone = tk.PhotoImage(file=os.path.join(ASSETS, "sentinela_icon.png"))
        root.iconphoto(True, icone)
        root._icone = icone  # mantém a referência viva
    except tk.TclError:
        pass


class Splash(tk.Toplevel):
    """Tela de carregamento exibida enquanto a interface inicia."""

    def __init__(self, master, logo_path, largura=560, altura=310):
        super().__init__(master)
        self.overrideredirect(True)
        self.configure(bg="#0d1b2a")
        self.attributes("-topmost", True)

        try:
            logo = tk.PhotoImage(file=logo_path).subsample(2)
            lbl = tk.Label(self, image=logo, bg="#0d1b2a", bd=0)
            lbl.image = logo
            lbl.pack(pady=(42, 6))
        except tk.TclError:
            tk.Label(self, text="SENTINELA", font=("Segoe UI", 24, "bold"),
                     bg="#0d1b2a", fg="white").pack(pady=(60, 6))

        tk.Label(self, text="Telemetria e Segurança Veicular",
                 font=("Segoe UI", 10), bg="#0d1b2a", fg="#b2bec3").pack()
        tk.Label(self, text="Carregando…", font=("Segoe UI", 9),
                 bg="#0d1b2a", fg="#636e72").pack(pady=(18, 6))
        barra = ttk.Progressbar(self, mode="indeterminate", length=260)
        barra.pack()
        barra.start(12)
        self._barra = barra

        self.update_idletasks()
        x = (self.winfo_screenwidth() - largura) // 2
        y = (self.winfo_screenheight() - altura) // 2
        self.geometry(f"{largura}x{altura}+{x}+{y}")
        self.update()


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

        self.root.title("Sentinela — Telemetria e Segurança Veicular")
        self.root.configure(bg=BG)
        self.__centralizar(1280, 800)

        # Fila usada para entregar, na thread principal, os resultados das
        # tarefas executadas em segundo plano (análise/consultas).
        self._fila = queue.Queue()
        self._retry_job = None
        self._agendar_consumidor()

        self._construir()
        self.recarregar_rotas()
        self.mostrar("dados")

    def __centralizar(self, largura, altura):
        """Posiciona a janela no centro da tela, reduzindo-a se for maior que a tela.

        Sem ``+X+Y`` no geometry, o gerenciador de janelas abre a aplicação no
        canto superior esquerdo. Aqui calculamos o deslocamento a partir da
        resolução da tela para centralizá-la e evitamos uma janela maior que a
        área visível (ex.: notebooks 1366×768).
        """
        self.root.update_idletasks()  # garante dimensões reais da tela
        tela_l = self.root.winfo_screenwidth()
        tela_a = self.root.winfo_screenheight()
        largura = min(largura, tela_l - 60)
        altura = min(altura, tela_a - 120)
        self.root.minsize(min(1080, largura), min(680, altura))
        pos_x = max(0, (tela_l - largura) // 2)
        pos_y = max(0, (tela_a - altura) // 2)
        self.root.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

    # ------------------------------------------------------------------ #
    # Construção da interface
    # ------------------------------------------------------------------ #
    def _construir(self):
        self.sidebar = tk.Frame(self.root, bg=COR_SIDEBAR, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        try:
            logo = tk.PhotoImage(
                file=os.path.join(ASSETS, "sentinela_logo.png")
            ).subsample(5)
            lbl_logo = tk.Label(self.sidebar, image=logo, bg=COR_SIDEBAR, bd=0)
            lbl_logo.image = logo
            lbl_logo.pack(pady=(18, 2))
        except tk.TclError:
            tk.Label(self.sidebar, text="Sentinela", font=("Segoe UI", 16, "bold"),
                     bg=COR_SIDEBAR, fg="white").pack(pady=(22, 0))
        tk.Label(self.sidebar, text="Telemetria e Segurança Veicular",
                 font=("Segoe UI", 8), bg=COR_SIDEBAR, fg="#b2bec3",
                 wraplength=180).pack(pady=(0, 18))

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
        self.filtro_rota = tk.Frame(topo, bg=BG)
        self.filtro_rota.pack(side="left", pady=8)
        tk.Label(self.filtro_rota, text="Rota em análise:",
                 font=("Segoe UI", 10, "bold"), bg=BG, fg=TEXTO
                 ).pack(side="left", padx=(15, 6))
        self.combo_rota = ttk.Combobox(self.filtro_rota, state="readonly", width=42)
        self.combo_rota.pack(side="left")
        self.combo_rota.bind("<<ComboboxSelected>>", self._trocar_rota)
        self.lbl_status = tk.Label(topo, text="", font=("Segoe UI", 9),
                                   bg=BG, fg=CINZA)
        self.lbl_status.pack(side="right", padx=(0, 15))
        self.btn_reconectar = tk.Button(
            topo, text="Tentar novamente", font=("Segoe UI", 9, "bold"),
            bg=COR_ATIVO, fg="white", relief="flat", bd=0, cursor="hand2",
            activebackground="#0a6bb5", activeforeground="white",
            command=self.recarregar_rotas,
        )
        self.btn_reconectar.pack(side="right", padx=(0, 6))
        self.btn_reconectar.pack_forget()

        self.conteudo = tk.Frame(self.area, bg=BG)
        self.conteudo.pack(fill="both", expand=True)

        self.secoes = {
            "dados": DadosTab(self.conteudo, self),
            "visao": DashboardTab(self.conteudo, self),
            "grafico": GraficoTab(self.conteudo, self),
            "sensores": SensorTab(self.conteudo, self),
            "comparar": CompararTab(self.conteudo, self),
        }
        for secao in self.secoes.values():
            self._aplicar_marca_dagua(secao)

    def _aplicar_marca_dagua(self, secao):
        """Coloca a logo como marca d'água discreta no fundo da seção."""
        try:
            img = tk.PhotoImage(
                file=os.path.join(ASSETS, "sentinela_watermark.png")
            )
        except tk.TclError:
            return
        marca = tk.Label(secao, image=img, bg=BG, bd=0)
        marca.image = img
        marca.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")
        marca.lower()
        secao._marca_dagua = marca

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

        # O seletor "Rota em análise" só faz sentido nas seções de análise;
        # Dados e Comparar têm seus próprios seletores/filtros.
        if chave in ("dados", "comparar"):
            self.filtro_rota.pack_forget()
        else:
            self.filtro_rota.pack(side="left", pady=8)

        if chave == "grafico":
            secao.plotar()
        elif chave != "dados" and hasattr(secao, "atualizar"):
            secao.atualizar()

    # ------------------------------------------------------------------ #
    # Rotas / seleção global
    # ------------------------------------------------------------------ #
    def recarregar_rotas(self, selecionar=None):
        try:
            resp = self.api.list_rotas()
        except requests.exceptions.RequestException:
            self._marcar_offline()
            return
        if resp.status_code != 200:
            self._marcar_offline()
            return

        self.rotas = resp.json()
        self._marcar_online(len(self.rotas))
        nomes = [_rotulo_rota(r) for r in self.rotas]
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
            self.combo_rota.set("")

        # Atualiza as listas que dependem do cadastro de rotas.
        self.secoes["dados"].atualizar()
        self.secoes["comparar"].atualizar()

    # ------------------------------------------------------------------ #
    # Estado da conexão com a API (status do topo + reconexão automática)
    # ------------------------------------------------------------------ #
    def _marcar_offline(self):
        self.lbl_status.configure(
            text="API offline — inicie o Docker (docker compose up -d)",
            fg="#d63031",
        )
        self.btn_reconectar.pack(side="right", padx=(0, 6))
        self._agendar_reconexao()

    def _marcar_online(self, quantidade):
        self.lbl_status.configure(
            text=f"{quantidade} rota(s) cadastrada(s)", fg=CINZA,
        )
        self.btn_reconectar.pack_forget()
        self._cancelar_reconexao()

    def _agendar_reconexao(self):
        self._cancelar_reconexao()
        self._retry_job = self.root.after(5000, self._tentar_reconexao)

    def _cancelar_reconexao(self):
        if getattr(self, "_retry_job", None) is not None:
            try:
                self.root.after_cancel(self._retry_job)
            except Exception:  # noqa: BLE001 — o timer já pode ter disparado
                pass
            self._retry_job = None

    def _tentar_reconexao(self):
        self._retry_job = None
        if self.api.disponivel():
            self.recarregar_rotas()
        else:
            self._agendar_reconexao()

    def definir_rota(self, rota_id):
        self.rota_atual_id = rota_id
        for indice, rota in enumerate(self.rotas):
            if rota["id"] == rota_id:
                self.combo_rota.current(indice)
                break
        else:
            self.combo_rota.set("")
            self.rota_atual_id = None
        self.refresh_detalhes()

    def _trocar_rota(self, _event):
        indice = self.combo_rota.current()
        if indice < 0 or indice >= len(self.rotas):
            self.rota_atual_id = None
        else:
            self.rota_atual_id = self.rotas[indice]["id"]
        self.refresh_detalhes()

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
                resultado = {"__erro__": mensagem_conexao(erro)}
            except Exception as erro:  # noqa: BLE001 — a thread não pode morrer
                print("Falha inesperada ao carregar dados:", erro)
                resultado = {"__erro__": "Falha inesperada ao carregar os dados. Tente novamente."}
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
    root.withdraw()
    aplicar_icone(root)
    splash = Splash(root, os.path.join(ASSETS, "sentinela_logo.png"))

    api = ApiClient()
    try:
        App(root, api)
    except Exception as erro:  # noqa: BLE001
        splash.destroy()
        root.deiconify()
        messagebox.showerror("Erro ao iniciar", str(erro))
        root.destroy()
        raise

    def finalizar():
        splash.destroy()
        root.deiconify()
        root.lift()
        root.focus_force()

    root.after(1200, finalizar)
    root.mainloop()


if __name__ == "__main__":
    main()
