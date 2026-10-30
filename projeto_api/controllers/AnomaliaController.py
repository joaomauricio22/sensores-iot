from flask_restful import Resource, abort
from flask_apispec import marshal_with, use_kwargs
from flask_apispec.views import MethodResource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from controllers.schemas import AnomaliaRequestSchema, AnomaliaResponseSchema
from services.AnomaliaService import AnomaliaService


class AnomaliaList(MethodResource, Resource):

    def __init__(self):
        self.__service = AnomaliaService()

    @marshal_with(AnomaliaResponseSchema(many=True))
    def get(self):
        try:
            return self.__service.get_all(), 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(AnomaliaRequestSchema, location="json")
    @marshal_with(AnomaliaResponseSchema)
    def post(self, **kwargs):
        try:
            return self.__service.add(**kwargs), 201
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Violação de integridade no banco de dados.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class AnomaliaItem(MethodResource, Resource):

    def __init__(self):
        self.__service = AnomaliaService()

    @marshal_with(AnomaliaResponseSchema)
    def get(self, anomalia_id):
        try:
            anomalia = self.__service.get_by_id(anomalia_id)
            if not anomalia:
                abort(404, message="Anomalia não encontrada.")
            return anomalia, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(AnomaliaRequestSchema, location="json")
    @marshal_with(AnomaliaResponseSchema)
    def put(self, anomalia_id, **kwargs):
        try:
            anomalia = self.__service.update(anomalia_id, **kwargs)
            if not anomalia:
                abort(404, message="Anomalia não encontrada.")
            return anomalia, 200
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Violação de integridade no banco de dados.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    def delete(self, anomalia_id):
        try:
            anomalia = self.__service.delete(anomalia_id)
            if not anomalia:
                abort(404, message="Anomalia não encontrada.")
            return {"message": "Anomalia excluída com sucesso."}, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")
