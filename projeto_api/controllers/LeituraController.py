from flask_restful import Resource, abort
from flask_apispec import marshal_with, use_kwargs
from flask_apispec.views import MethodResource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from controllers.schemas import AnomaliaResponseSchema, LeituraRequestSchema, LeituraResponseSchema
from services.AnaliseService import AnaliseService
from services.LeituraService import LeituraService


class LeituraList(MethodResource, Resource):

    def __init__(self):
        self.__service = LeituraService()

    @marshal_with(LeituraResponseSchema(many=True))
    def get(self):
        try:
            return self.__service.get_all(), 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(LeituraRequestSchema, location="json")
    @marshal_with(LeituraResponseSchema)
    def post(self, **kwargs):
        try:
            return self.__service.add(**kwargs), 201
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Já existe uma leitura idêntica para este sensor.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class LeituraItem(MethodResource, Resource):

    def __init__(self):
        self.__service = LeituraService()

    @marshal_with(LeituraResponseSchema)
    def get(self, leitura_id):
        try:
            leitura = self.__service.get_by_id(leitura_id)
            if not leitura:
                abort(404, message="Leitura não encontrada.")
            return leitura, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(LeituraRequestSchema, location="json")
    @marshal_with(LeituraResponseSchema)
    def put(self, leitura_id, **kwargs):
        try:
            leitura = self.__service.update(leitura_id, **kwargs)
            if not leitura:
                abort(404, message="Leitura não encontrada.")
            return leitura, 200
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Já existe uma leitura idêntica para este sensor.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    def delete(self, leitura_id):
        try:
            leitura = self.__service.delete(leitura_id)
            if not leitura:
                abort(404, message="Leitura não encontrada.")
            return {"message": "Leitura excluída com sucesso."}, 200
        except IntegrityError:
            abort(409, message="Não é possível excluir: existem anomalias vinculadas a esta leitura.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class LeituraAnalise(MethodResource, Resource):
    """Executa os detectores de anomalia sobre uma leitura (regras 7 e 9)."""

    def __init__(self):
        self.__analise_service = AnaliseService()

    @marshal_with(AnomaliaResponseSchema(many=True))
    def post(self, leitura_id):
        try:
            anomalias = self.__analise_service.analisar_leitura(leitura_id)
            if anomalias is None:
                abort(404, message="Leitura não encontrada.")
            return anomalias, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class LeituraClassificacao(MethodResource, Resource):
    """Classifica uma leitura com o modelo de ML (regra 8)."""

    def __init__(self):
        self.__analise_service = AnaliseService()

    @marshal_with(LeituraResponseSchema)
    def post(self, leitura_id):
        try:
            leitura = self.__analise_service.classificar_ml(leitura_id)
            if not leitura:
                abort(404, message="Leitura não encontrada.")
            return leitura, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")
