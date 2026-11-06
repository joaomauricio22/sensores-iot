from flask_restful import Resource, abort
from flask_apispec import marshal_with, use_kwargs
from flask_apispec.views import MethodResource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from controllers.schemas import ParametroRequestSchema, ParametroResponseSchema
from services.ParametroService import ParametroService


class ParametroList(MethodResource, Resource):

    def __init__(self):
        self.__service = ParametroService()

    @marshal_with(ParametroResponseSchema(many=True))
    def get(self):
        try:
            return self.__service.get_all(), 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(ParametroRequestSchema, location="json")
    @marshal_with(ParametroResponseSchema)
    def post(self, **kwargs):
        try:
            return self.__service.add(**kwargs), 201
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Violação de integridade no banco de dados.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class ParametroItem(MethodResource, Resource):

    def __init__(self):
        self.__service = ParametroService()

    @marshal_with(ParametroResponseSchema)
    def get(self, parametro_id):
        try:
            parametro = self.__service.get_by_id(parametro_id)
            if not parametro:
                abort(404, message="Parâmetro não encontrado.")
            return parametro, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(ParametroRequestSchema, location="json")
    @marshal_with(ParametroResponseSchema)
    def put(self, parametro_id, **kwargs):
        try:
            parametro = self.__service.update(parametro_id, **kwargs)
            if not parametro:
                abort(404, message="Parâmetro não encontrado.")
            return parametro, 200
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Violação de integridade no banco de dados.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    def delete(self, parametro_id):
        try:
            parametro = self.__service.delete(parametro_id)
            if not parametro:
                abort(404, message="Parâmetro não encontrado.")
            return {"message": "Parâmetro excluído com sucesso."}, 200
        except IntegrityError:
            abort(409, message="Não é possível excluir: há mapeamentos vinculados a este parâmetro.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")
