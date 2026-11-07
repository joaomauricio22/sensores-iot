"""Cliente HTTP da interface gráfica.

Encapsula a comunicação com a API REST usando a biblioteca `requests`.
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


class ApiClient:

    BASE_URL = "http://localhost:8080/telemetria"

    def __init__(self, base_url: str = None):
        self.__base_url = base_url or self.BASE_URL
        self.usuario_id = None

    def _url(self, resource, resource_id=None, extra=None):
        url = f"{self.__base_url}/{resource}"
        if resource_id is not None:
            url += f"/{resource_id}"
        if extra:
            url += f"/{extra}"
        return url

    # ---- Autenticação ----
    def registrar(self, nome, senha):
        return requests.post(self._url("usuarios"), json={"nome": nome, "senha": senha})

    def login(self, nome, senha):
        resp = requests.post(
            self._url("usuarios", extra="login"), json={"nome": nome, "senha": senha}
        )
        if resp.status_code == 200:
            self.usuario_id = resp.json().get("id")
        return resp

    # ---- Rotas ----
    def list_rotas(self):
        return requests.get(self._url("rotas"), params={"usuario_id": self.usuario_id})

    def importar_csv(self, nome, arquivo_origem, conteudo_csv):
        return requests.post(
            self._url("rotas", extra="importar"),
            json={
                "usuario_id": self.usuario_id,
                "nome": nome,
                "arquivo_origem": arquivo_origem,
                "conteudo_csv": conteudo_csv,
            },
        )

    def renomear_rota(self, rota_id, nome):
        return requests.put(
            self._url("rotas", rota_id), json={"usuario_id": self.usuario_id, "nome": nome}
        )

    def excluir_rota(self, rota_id):
        return requests.delete(self._url("rotas", rota_id))

    def analisar_rota(self, rota_id):
        return requests.post(self._url("rotas", rota_id, "analisar"))

    def grafico_rota(self, rota_id):
        return requests.get(self._url("rotas", rota_id, "grafico"))

    def resumo_rota(self, rota_id):
        return requests.get(self._url("rotas", rota_id, "resumo"))

    def comparar_rotas(self, rota_ids):
        return requests.post(self._url("rotas", extra="comparar"), json={"rota_ids": rota_ids})

    # ---- Eventos ----
    def list_eventos(self, rota_id, tipo=None):
        params = {"rota_id": rota_id}
        if tipo:
            params["tipo"] = tipo
        return requests.get(self._url("eventos-risco"), params=params)

    # ---- Configurações (limiares) ----
    def get_limiares(self):
        return requests.get(self._url("configuracoes", extra="limiares"))

    def set_limiares(self, limiares):
        return requests.put(self._url("configuracoes", extra="limiares"), json=limiares)
