from flask_restful import Resource, abort, request
from flask_apispec import marshal_with, use_kwargs
from flask_apispec.views import MethodResource
from marshmallow import ValidationError
from sqlalchemy.exc import OperationalError

from controllers.schemas import (
    EventoRiscoResponseSchema,
    ImportarRequestSchema,
    RotaRequestSchema,
    RotaResponseSchema,
)
from services.AnaliseService import AnaliseService
from services.ImportadorService import ImportadorService
from services.RotaService import RotaService


class RotaList(MethodResource, Resource):

    def __init__(self):
        self.__service = RotaService()

    @marshal_with(RotaResponseSchema(many=True))
    def get(self):
        try:
            return self.__service.get_all(), 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(RotaRequestSchema, location="json")
    @marshal_with(RotaResponseSchema)
    def post(self, **kwargs):
        try:
            return self.__service.add(**kwargs), 201
        except ValidationError as e:
            abort(400, message=str(e))
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class RotaItem(MethodResource, Resource):

    def __init__(self):
        self.__service = RotaService()

    @marshal_with(RotaResponseSchema)
    def get(self, rota_id):
        try:
            rota = self.__service.get_by_id(rota_id)
            if not rota:
                abort(404, message="Rota não encontrada.")
            return rota, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(RotaRequestSchema, location="json")
    @marshal_with(RotaResponseSchema)
    def put(self, rota_id, **kwargs):
        try:
            rota = self.__service.update(
                rota_id,
                nome=kwargs.get("nome"),
                arquivo_origem=kwargs.get("arquivo_origem"),
            )
            if not rota:
                abort(404, message="Rota não encontrada.")
            return rota, 200
        except ValidationError as e:
            abort(400, message=str(e))
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    def delete(self, rota_id):
        try:
            rota = self.__service.delete(rota_id)
            if not rota:
                abort(404, message="Rota não encontrada.")
            return {"message": "Rota excluída com sucesso."}, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class RotaImportar(MethodResource, Resource):
    """Importa um CSV de telemetria, criando a rota e suas leituras."""

    def __init__(self):
        self.__importador = ImportadorService()

    @use_kwargs(ImportarRequestSchema, location="json")
    def post(self, **kwargs):
        try:
            resultado = self.__importador.importar_csv(
                kwargs["nome"],
                kwargs.get("arquivo_origem"),
                kwargs["conteudo_csv"],
            )
            return resultado, 201
        except ValidationError as e:
            abort(400, message=str(e))
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class RotaAnalisar(MethodResource, Resource):
    """Executa a detecção de eventos de risco sobre a rota."""

    def __init__(self):
        self.__analise = AnaliseService()

    @marshal_with(EventoRiscoResponseSchema(many=True))
    def post(self, rota_id):
        try:
            eventos = self.__analise.analisar_rota(rota_id)
            if eventos is None:
                abort(404, message="Rota não encontrada.")
            return eventos, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class RotaGrafico(MethodResource, Resource):
    """Retorna os dados para o gráfico de comportamento da rota."""

    def __init__(self):
        self.__analise = AnaliseService()

    def get(self, rota_id):
        try:
            dados = self.__analise.grafico_rota(rota_id)
            if not dados:
                abort(404, message="Rota não encontrada.")
            return dados, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class RotaResumo(MethodResource, Resource):
    """Retorna o resumo (dashboard) e o score de segurança da rota."""

    def __init__(self):
        self.__analise = AnaliseService()

    def get(self, rota_id):
        try:
            resumo = self.__analise.resumo_rota(rota_id)
            if not resumo:
                abort(404, message="Rota não encontrada.")
            return resumo, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class RotaComparar(MethodResource, Resource):
    """Compara o resumo de duas ou mais rotas."""

    def __init__(self):
        self.__analise = AnaliseService()

    def post(self):
        try:
            dados = request.get_json(silent=True) or {}
            rota_ids = dados.get("rota_ids")
            if not rota_ids or not isinstance(rota_ids, list):
                abort(400, message="Informe a lista 'rota_ids' para comparação.")
            resumos = self.__analise.comparar_rotas(rota_ids)
            return {"rotas": resumos}, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")
