from flask_restful import Resource, abort
from flask_apispec import marshal_with, use_kwargs
from flask_apispec.views import MethodResource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from controllers.schemas import TipoSensorRequestSchema, TipoSensorResponseSchema
from services.TipoSensorService import TipoSensorService


class TipoSensorList(MethodResource, Resource):

    def __init__(self):
        self.__service = TipoSensorService()

    @marshal_with(TipoSensorResponseSchema(many=True))
    def get(self):
        try:
            return self.__service.get_all(), 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(TipoSensorRequestSchema, location="json")
    @marshal_with(TipoSensorResponseSchema)
    def post(self, **kwargs):
        try:
            return self.__service.add(**kwargs), 201
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Violação de integridade no banco de dados.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class TipoSensorItem(MethodResource, Resource):

    def __init__(self):
        self.__service = TipoSensorService()

    @marshal_with(TipoSensorResponseSchema)
    def get(self, tipo_sensor_id):
        try:
            tipo_sensor = self.__service.get_by_id(tipo_sensor_id)
            if not tipo_sensor:
                abort(404, message="Tipo de sensor não encontrado.")
            return tipo_sensor, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(TipoSensorRequestSchema, location="json")
    @marshal_with(TipoSensorResponseSchema)
    def put(self, tipo_sensor_id, **kwargs):
        try:
            tipo_sensor = self.__service.update(tipo_sensor_id, **kwargs)
            if not tipo_sensor:
                abort(404, message="Tipo de sensor não encontrado.")
            return tipo_sensor, 200
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Violação de integridade no banco de dados.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    def delete(self, tipo_sensor_id):
        try:
            tipo_sensor = self.__service.delete(tipo_sensor_id)
            if not tipo_sensor:
                abort(404, message="Tipo de sensor não encontrado.")
            return {"message": "Tipo de sensor excluído com sucesso."}, 200
        except IntegrityError:
            abort(409, message="Não é possível excluir: existem sensores vinculados a este tipo.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")
