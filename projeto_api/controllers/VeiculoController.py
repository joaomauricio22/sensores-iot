from flask_restful import Resource, abort
from flask_apispec import marshal_with, use_kwargs
from flask_apispec.views import MethodResource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from controllers.schemas import EventoRiscoResponseSchema, VeiculoRequestSchema, VeiculoResponseSchema
from services.AnaliseService import AnaliseService
from services.VeiculoService import VeiculoService


class VeiculoList(MethodResource, Resource):

    def __init__(self):
        self.__service = VeiculoService()

    @marshal_with(VeiculoResponseSchema(many=True))
    def get(self):
        try:
            return self.__service.get_all(), 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(VeiculoRequestSchema, location="json")
    @marshal_with(VeiculoResponseSchema)
    def post(self, **kwargs):
        try:
            return self.__service.add(**kwargs), 201
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Violação de integridade no banco de dados.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class VeiculoItem(MethodResource, Resource):

    def __init__(self):
        self.__service = VeiculoService()

    @marshal_with(VeiculoResponseSchema)
    def get(self, veiculo_id):
        try:
            veiculo = self.__service.get_by_id(veiculo_id)
            if not veiculo:
                abort(404, message="Veículo não encontrado.")
            return veiculo, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(VeiculoRequestSchema, location="json")
    @marshal_with(VeiculoResponseSchema)
    def put(self, veiculo_id, **kwargs):
        try:
            veiculo = self.__service.update(veiculo_id, **kwargs)
            if not veiculo:
                abort(404, message="Veículo não encontrado.")
            return veiculo, 200
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Violação de integridade no banco de dados.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    def delete(self, veiculo_id):
        try:
            veiculo = self.__service.delete(veiculo_id)
            if not veiculo:
                abort(404, message="Veículo não encontrado.")
            return {"message": "Veículo excluído com sucesso."}, 200
        except IntegrityError:
            abort(409, message="Não é possível excluir: há leituras ou eventos vinculados.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class VeiculoEstatisticas(MethodResource, Resource):
    """Indicadores do histórico de condução de um veículo (regra 10)."""

    def __init__(self):
        self.__analise_service = AnaliseService()

    def get(self, veiculo_id):
        try:
            estatisticas = self.__analise_service.estatisticas_veiculo(veiculo_id)
            if not estatisticas:
                abort(404, message="Veículo não encontrado.")
            return estatisticas, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class VeiculoAnalise(MethodResource, Resource):
    """Executa a detecção de eventos de risco sobre o histórico do veículo (regras 7, 8 e 9)."""

    def __init__(self):
        self.__analise_service = AnaliseService()

    @marshal_with(EventoRiscoResponseSchema(many=True))
    def post(self, veiculo_id):
        try:
            eventos = self.__analise_service.analisar_veiculo(veiculo_id)
            if eventos is None:
                abort(404, message="Veículo não encontrado.")
            return eventos, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")
