"""Cliente HTTP da interface gráfica.

Encapsula a comunicação com a API REST usando a biblioteca `requests`.
Separar essa responsabilidade facilita a manutenção e demonstra
ENCAPSULAMENTO (os detalhes de URL/HTTP ficam escondidos das telas).
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
    """Transforma estruturas de erro (dict/list) em texto legível."""
    if isinstance(errors, dict):
        partes = []
        for campo, msgs in errors.items():
            if isinstance(msgs, list):
                msgs = "; ".join(str(m) for m in msgs)
            partes.append(f"{campo}: {msgs}")
        return "\n".join(partes)
    if isinstance(errors, list):
        return "; ".join(str(e) for e in errors)
    return str(errors)


class ApiClient:

    BASE_URL = "http://localhost:8080/iot"

    def __init__(self, base_url: str = None):
        self.__base_url = base_url or self.BASE_URL

    def _url(self, resource, resource_id=None, extra=None):
        url = f"{self.__base_url}/{resource}"
        if resource_id is not None:
            url += f"/{resource_id}"
        if extra:
            url += f"/{extra}"
        return url

    # Operações de CRUD genéricas
    def list(self, resource):
        return requests.get(self._url(resource))

    def get(self, resource, resource_id):
        return requests.get(self._url(resource, resource_id))

    def create(self, resource, data: dict):
        return requests.post(self._url(resource), json=data)

    def update(self, resource, resource_id, data: dict):
        return requests.put(self._url(resource, resource_id), json=data)

    def delete(self, resource, resource_id):
        return requests.delete(self._url(resource, resource_id))

    # Endpoints de análise
    def analisar_leitura(self, leitura_id):
        return requests.post(self._url("leituras", leitura_id, "analisar"))

    def classificar_leitura(self, leitura_id):
        return requests.post(self._url("leituras", leitura_id, "classificar"))

    def estatisticas_sensor(self, sensor_id):
        return requests.get(self._url("sensores", sensor_id, "estatisticas"))
