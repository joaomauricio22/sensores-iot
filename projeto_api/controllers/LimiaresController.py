from flask_restful import Resource, abort
from flask_apispec.views import MethodResource
from marshmallow import ValidationError

from services.LimiaresService import LimiaresService


class Limiares(MethodResource, Resource):
    """Leitura dos limiares de detecção (somente leitura)."""

    def __init__(self):
        self.__service = LimiaresService()

    def get(self):
        try:
            return self.__service.get_limiares(), 200
        except ValidationError as e:
            abort(500, message=str(e))


class Sensores(MethodResource, Resource):
    """Catálogo de sensores (canais) cadastrados no sistema."""

    def __init__(self):
        self.__service = LimiaresService()

    def get(self):
        try:
            return self.__service.get_sensores(), 200
        except ValidationError as e:
            abort(500, message=str(e))
