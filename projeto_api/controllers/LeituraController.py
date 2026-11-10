from flask_restful import Resource, abort, request
from flask_apispec import marshal_with, use_kwargs
from flask_apispec.views import MethodResource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from controllers.schemas import LeituraRequestSchema, LeituraResponseSchema
from services.LeituraService import LeituraService


class LeituraList(MethodResource, Resource):

    def __init__(self):
        self.__service = LeituraService()

    @marshal_with(LeituraResponseSchema(many=True))
    def get(self):
        try:
            rota_id = self.__extrair_rota_id()
            if rota_id is not None:
                return self.__service.get_by_rota(rota_id), 200
            return self.__service.get_all(), 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @staticmethod
    def __extrair_rota_id():
        """Lê o filtro ``rota_id``; valor não numérico responde 400 (não ignora)."""
        bruto = request.args.get("rota_id")
        if bruto is None:
            return None
        try:
            return int(bruto)
        except (TypeError, ValueError):
            abort(400, message="O parâmetro 'rota_id' deve ser um número inteiro.")

    @use_kwargs(LeituraRequestSchema, location="json")
    @marshal_with(LeituraResponseSchema)
    def post(self, **kwargs):
        try:
            return self.__service.add(**kwargs), 201
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Já existe uma leitura para esta rota nesse instante.")
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
            abort(409, message="Já existe uma leitura para esta rota nesse instante.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    def delete(self, leitura_id):
        try:
            leitura = self.__service.delete(leitura_id)
            if not leitura:
                abort(404, message="Leitura não encontrada.")
            return {"message": "Leitura excluída com sucesso."}, 200
        except IntegrityError:
            abort(409, message="Não é possível excluir: há eventos vinculados a esta leitura.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")
