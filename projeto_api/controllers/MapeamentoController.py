from flask_restful import Resource, abort
from flask_apispec import marshal_with, use_kwargs
from flask_apispec.views import MethodResource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from controllers.schemas import MapeamentoRequestSchema, MapeamentoResponseSchema
from services.MapeamentoParametroService import MapeamentoParametroService


class MapeamentoList(MethodResource, Resource):

    def __init__(self):
        self.__service = MapeamentoParametroService()

    @marshal_with(MapeamentoResponseSchema(many=True))
    def get(self):
        try:
            return self.__service.get_all(), 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(MapeamentoRequestSchema, location="json")
    @marshal_with(MapeamentoResponseSchema)
    def post(self, **kwargs):
        try:
            return self.__service.add(**kwargs), 201
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Violação de integridade no banco de dados.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class MapeamentoItem(MethodResource, Resource):

    def __init__(self):
        self.__service = MapeamentoParametroService()

    @marshal_with(MapeamentoResponseSchema)
    def get(self, mapeamento_id):
        try:
            mapeamento = self.__service.get_by_id(mapeamento_id)
            if not mapeamento:
                abort(404, message="Mapeamento não encontrado.")
            return mapeamento, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(MapeamentoRequestSchema, location="json")
    @marshal_with(MapeamentoResponseSchema)
    def put(self, mapeamento_id, **kwargs):
        try:
            mapeamento = self.__service.update(mapeamento_id, **kwargs)
            if not mapeamento:
                abort(404, message="Mapeamento não encontrado.")
            return mapeamento, 200
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Violação de integridade no banco de dados.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    def delete(self, mapeamento_id):
        try:
            mapeamento = self.__service.delete(mapeamento_id)
            if not mapeamento:
                abort(404, message="Mapeamento não encontrado.")
            return {"message": "Mapeamento excluído com sucesso."}, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")
