from flask_restful import Resource, abort, request
from flask_apispec import marshal_with, use_kwargs
from flask_apispec.views import MethodResource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from controllers.schemas import EventoRiscoRequestSchema, EventoRiscoResponseSchema
from services.EventoRiscoService import EventoRiscoService


class EventoRiscoList(MethodResource, Resource):

    def __init__(self):
        self.__service = EventoRiscoService()

    @marshal_with(EventoRiscoResponseSchema(many=True))
    def get(self):
        try:
            rota_id = request.args.get("rota_id", type=int)
            tipo = request.args.get("tipo")
            if rota_id is not None:
                return self.__service.get_by_rota(rota_id, tipo), 200
            return self.__service.get_all(tipo), 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(EventoRiscoRequestSchema, location="json")
    @marshal_with(EventoRiscoResponseSchema)
    def post(self, **kwargs):
        try:
            return self.__service.add(**kwargs), 201
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Já existe um evento igual para esta leitura.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class EventoRiscoItem(MethodResource, Resource):

    def __init__(self):
        self.__service = EventoRiscoService()

    @marshal_with(EventoRiscoResponseSchema)
    def get(self, evento_id):
        try:
            evento = self.__service.get_by_id(evento_id)
            if not evento:
                abort(404, message="Evento não encontrado.")
            return evento, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(EventoRiscoRequestSchema, location="json")
    @marshal_with(EventoRiscoResponseSchema)
    def put(self, evento_id, **kwargs):
        try:
            evento = self.__service.update(evento_id, **kwargs)
            if not evento:
                abort(404, message="Evento não encontrado.")
            return evento, 200
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Já existe um evento igual para esta leitura.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    def delete(self, evento_id):
        try:
            evento = self.__service.delete(evento_id)
            if not evento:
                abort(404, message="Evento não encontrado.")
            return {"message": "Evento excluído com sucesso."}, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")
