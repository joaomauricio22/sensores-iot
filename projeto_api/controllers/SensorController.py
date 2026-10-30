from flask_restful import Resource, abort
from flask_apispec import marshal_with, use_kwargs
from flask_apispec.views import MethodResource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from controllers.schemas import SensorRequestSchema, SensorResponseSchema
from services.AnaliseService import AnaliseService
from services.SensorService import SensorService


class SensorList(MethodResource, Resource):

    def __init__(self):
        self.__service = SensorService()

    @marshal_with(SensorResponseSchema(many=True))
    def get(self):
        try:
            return self.__service.get_all(), 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(SensorRequestSchema, location="json")
    @marshal_with(SensorResponseSchema)
    def post(self, **kwargs):
        try:
            return self.__service.add(**kwargs), 201
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Violação de integridade no banco de dados.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class SensorItem(MethodResource, Resource):

    def __init__(self):
        self.__service = SensorService()

    @marshal_with(SensorResponseSchema)
    def get(self, sensor_id):
        try:
            sensor = self.__service.get_by_id(sensor_id)
            if not sensor:
                abort(404, message="Sensor não encontrado.")
            return sensor, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(SensorRequestSchema, location="json")
    @marshal_with(SensorResponseSchema)
    def put(self, sensor_id, **kwargs):
        try:
            sensor = self.__service.update(sensor_id, **kwargs)
            if not sensor:
                abort(404, message="Sensor não encontrado.")
            return sensor, 200
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Violação de integridade no banco de dados.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    def delete(self, sensor_id):
        try:
            sensor = self.__service.delete(sensor_id)
            if not sensor:
                abort(404, message="Sensor não encontrado.")
            return {"message": "Sensor excluído com sucesso."}, 200
        except IntegrityError:
            abort(409, message="Não é possível excluir: existem leituras ou anomalias vinculadas.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class SensorEstatisticas(MethodResource, Resource):
    """Retorna os padrões estatísticos do histórico de um sensor (regra 10)."""

    def __init__(self):
        self.__analise_service = AnaliseService()

    def get(self, sensor_id):
        try:
            estatisticas = self.__analise_service.estatisticas_sensor(sensor_id)
            if not estatisticas:
                abort(404, message="Sensor não encontrado.")
            return estatisticas, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")
