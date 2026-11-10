"""Cliente HTTP da interface gráfica.

Encapsula a comunicação com a API REST usando a biblioteca `requests`.
A interface nunca acessa o banco diretamente: todo acesso passa pela API.
"""
import requests


def extract_error(response) -> str:
    """Extrai uma mensagem de erro legível a partir de uma resposta HTTP."""
    try:
        data = response.json()
    except Exception:
        return response.text or f"Erro {response.status_code}"
    if isinstance(data, dict):
        if "message" in data:
            return str(data["message"])
        for key in ("errors", "messages"):
            if key in data and data[key]:
                return _format_errors(data[key])
        return str(data)
    return str(data)


def _format_errors(errors) -> str:
    if isinstance(errors, dict):
        return "\n".join(
            f"{k}: {'; '.join(map(str, v)) if isinstance(v, list) else v}"
            for k, v in errors.items()
        )
    if isinstance(errors, list):
        return "; ".join(map(str, errors))
    return str(errors)


def mensagem_conexao(erro) -> str:
    """Traduz um erro de rede em uma instrução clara para o usuário.

    Evita exibir o texto técnico do `requests` (ex.: ``HTTPConnectionPool``
    e ``WinError 10061``) na interface.
    """
    if isinstance(erro, requests.exceptions.ConnectionError):
        return (
            "Não foi possível conectar à API do Sentinela.\n\n"
            "Abra o Docker Desktop e execute, na pasta projeto_api:\n"
            "    docker compose up -d\n\n"
            "Depois clique em \"Tentar novamente\"."
        )
    if isinstance(erro, requests.exceptions.Timeout):
        return "A API demorou para responder. Tente novamente em instantes."
    return "Falha de comunicação com a API. Tente novamente."


class ApiClient:
    """Métodos HTTP de cada recurso exposto pela API."""

    BASE_URL = "http://localhost:8080/telemetria"

    # Timeouts por tipo de operação (segundos). Evita a interface travar quando
    # a API não responde.
    TIMEOUT_PADRAO = 30
    TIMEOUT_RAPIDO = 5
    TIMEOUT_ANALISE = 120
    TIMEOUT_IMPORTACAO = 180

    def __init__(self, base_url: str = None):
        self.__base_url = base_url or self.BASE_URL

    def _url(self, resource, resource_id=None, extra=None):
        url = f"{self.__base_url}/{resource}"
        if resource_id is not None:
            url += f"/{resource_id}"
        if extra:
            url += f"/{extra}"
        return url

    def _get(self, url, **kw):
        kw.setdefault("timeout", self.TIMEOUT_PADRAO)
        return requests.get(url, **kw)

    def _post(self, url, **kw):
        kw.setdefault("timeout", self.TIMEOUT_PADRAO)
        return requests.post(url, **kw)

    def _put(self, url, **kw):
        kw.setdefault("timeout", self.TIMEOUT_PADRAO)
        return requests.put(url, **kw)

    def _delete(self, url, **kw):
        kw.setdefault("timeout", self.TIMEOUT_PADRAO)
        return requests.delete(url, **kw)

    def disponivel(self, timeout=2) -> bool:
        """Verifica rapidamente se a API está no ar (conexão e resposta 200)."""
        try:
            return requests.get(self._url("rotas"), timeout=timeout).status_code == 200
        except requests.exceptions.RequestException:
            return False

    # ---- Rotas --------------------------------------------------------- #
    def list_rotas(self):
        return self._get(self._url("rotas"), timeout=self.TIMEOUT_RAPIDO)

    def atualizar_rota(self, rota_id, nome, arquivo_origem=None):
        return self._put(
            self._url("rotas", rota_id),
            json={"nome": nome, "arquivo_origem": arquivo_origem},
        )

    def excluir_rota(self, rota_id):
        return self._delete(self._url("rotas", rota_id))

    def importar_csv(self, nome, arquivo_origem, conteudo_csv):
        return self._post(
            self._url("rotas", extra="importar"),
            json={
                "nome": nome,
                "arquivo_origem": arquivo_origem,
                "conteudo_csv": conteudo_csv,
            },
            timeout=self.TIMEOUT_IMPORTACAO,
        )

    def analisar_rota(self, rota_id):
        return self._post(
            self._url("rotas", rota_id, "analisar"), timeout=self.TIMEOUT_ANALISE
        )

    def grafico_rota(self, rota_id):
        return self._get(
            self._url("rotas", rota_id, "grafico"), timeout=self.TIMEOUT_ANALISE
        )

    def resumo_rota(self, rota_id):
        return self._get(
            self._url("rotas", rota_id, "resumo"), timeout=self.TIMEOUT_ANALISE
        )

    def comparar_rotas(self, rota_ids):
        return self._post(
            self._url("rotas", extra="comparar"), json={"rota_ids": rota_ids}
        )

    # ---- Leituras ------------------------------------------------------ #
    def list_leituras(self, rota_id=None):
        params = {}
        if rota_id is not None:
            params["rota_id"] = rota_id
        return self._get(self._url("leituras"), params=params)

    def criar_leitura(self, dados):
        return self._post(self._url("leituras"), json=dados)

    def atualizar_leitura(self, leitura_id, dados):
        return self._put(self._url("leituras", leitura_id), json=dados)

    def excluir_leitura(self, leitura_id):
        return self._delete(self._url("leituras", leitura_id))

    # ---- Eventos de risco ---------------------------------------------- #
    def list_eventos(self, rota_id=None, tipo=None):
        params = {}
        if rota_id is not None:
            params["rota_id"] = rota_id
        if tipo:
            params["tipo"] = tipo
        return self._get(self._url("eventos-risco"), params=params)

    def criar_evento(self, dados):
        return self._post(self._url("eventos-risco"), json=dados)

    def atualizar_evento(self, evento_id, dados):
        return self._put(self._url("eventos-risco", evento_id), json=dados)

    def excluir_evento(self, evento_id):
        return self._delete(self._url("eventos-risco", evento_id))

    # ---- Configuração (somente leitura) -------------------------------- #
    def get_limiares(self):
        return self._get(self._url("limiares"))

    def get_sensores(self):
        return self._get(self._url("sensores"))
