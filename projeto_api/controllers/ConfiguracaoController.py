from flask_restful import Resource, abort
from flask_apispec import marshal_with, use_kwargs
from flask_apispec.views import MethodResource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from controllers.schemas import (
    ConfiguracaoRequestSchema,
    ConfiguracaoResponseSchema,
    ConfiguracaoUpdateSchema,
    LimiaresRequestSchema,
)
from services.AnaliseService import AnaliseService
from services.ConfiguracaoService import ConfiguracaoService


class ConfiguracaoList(MethodResource, Resource):

    def __init__(self):
        self.__service = ConfiguracaoService()

    @marshal_with(ConfiguracaoResponseSchema(many=True))
    def get(self):
        try:
            return self.__service.get_all(), 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(ConfiguracaoRequestSchema, location="json")
    @marshal_with(ConfiguracaoResponseSchema)
    def post(self, **kwargs):
        try:
            return self.__service.add(kwargs["chave"], kwargs["valor"]), 201
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Já existe uma configuração com essa chave.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class ConfiguracaoItem(MethodResource, Resource):

    def __init__(self):
        self.__service = ConfiguracaoService()

    @marshal_with(ConfiguracaoResponseSchema)
    def get(self, config_id):
        try:
            config = self.__service.get_by_id(config_id)
            if not config:
                abort(404, message="Configuração não encontrada.")
            return config, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(ConfiguracaoUpdateSchema, location="json")
    @marshal_with(ConfiguracaoResponseSchema)
    def put(self, config_id, **kwargs):
        try:
            config = self.__service.update(
                config_id, chave=kwargs.get("chave"), valor=kwargs.get("valor")
            )
            if not config:
                abort(404, message="Configuração não encontrada.")
            return config, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    def delete(self, config_id):
        try:
            config = self.__service.delete(config_id)
            if not config:
                abort(404, message="Configuração não encontrada.")
            return {"message": "Configuração excluída com sucesso."}, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class ConfiguracaoLimiares(MethodResource, Resource):
    """Leitura e atualização em lote dos limiares de detecção de risco."""

    def __init__(self):
        self.__service = ConfiguracaoService()
        self.__analise = AnaliseService()

    def get(self):
        try:
            return self.__service.get_limiares(), 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(LimiaresRequestSchema, location="json")
    def put(self, **kwargs):
        try:
            atualizados = self.__service.set_limiares(
                {k: v for k, v in kwargs.items() if v is not None}
            )
            # Reanalisa as rotas com os novos limiares (remove e recria os eventos).
            rotas_reanalisadas = self.__analise.reanalisar_todas()
            return {
                "message": "Limiares atualizados e rotas reanalisadas.",
                "limiares": atualizados,
                "rotas_reanalisadas": rotas_reanalisadas,
            }, 200
        except ValidationError as e:
            abort(400, message=str(e))
        except OperationalError:
            abort(500, message="Erro interno do servidor.")
