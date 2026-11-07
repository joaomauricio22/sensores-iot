from flask_restful import Resource, abort
from flask_apispec import marshal_with, use_kwargs
from flask_apispec.views import MethodResource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from controllers.schemas import (
    LoginRequestSchema,
    UsuarioRequestSchema,
    UsuarioResponseSchema,
)
from services.UsuarioService import UsuarioService


class UsuarioList(MethodResource, Resource):

    def __init__(self):
        self.__service = UsuarioService()

    @marshal_with(UsuarioResponseSchema(many=True))
    def get(self):
        try:
            return self.__service.get_all(), 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(UsuarioRequestSchema, location="json")
    @marshal_with(UsuarioResponseSchema)
    def post(self, **kwargs):
        try:
            return self.__service.cadastrar(**kwargs), 201
        except ValidationError as e:
            abort(400, message=str(e))
        except IntegrityError:
            abort(409, message="Já existe um usuário com esse nome.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class UsuarioItem(MethodResource, Resource):

    def __init__(self):
        self.__service = UsuarioService()

    @marshal_with(UsuarioResponseSchema)
    def get(self, usuario_id):
        try:
            usuario = self.__service.get_by_id(usuario_id)
            if not usuario:
                abort(404, message="Usuário não encontrado.")
            return usuario, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    @use_kwargs(UsuarioRequestSchema, location="json")
    @marshal_with(UsuarioResponseSchema)
    def put(self, usuario_id, **kwargs):
        try:
            usuario = self.__service.update(usuario_id, senha=kwargs.get("senha"))
            if not usuario:
                abort(404, message="Usuário não encontrado.")
            return usuario, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")

    def delete(self, usuario_id):
        try:
            usuario = self.__service.delete(usuario_id)
            if not usuario:
                abort(404, message="Usuário não encontrado.")
            return {"message": "Usuário excluído com sucesso."}, 200
        except IntegrityError:
            abort(409, message="Não é possível excluir: há rotas vinculadas a este usuário.")
        except OperationalError:
            abort(500, message="Erro interno do servidor.")


class UsuarioLogin(MethodResource, Resource):
    """Autenticação: valida nome e senha."""

    def __init__(self):
        self.__service = UsuarioService()

    @use_kwargs(LoginRequestSchema, location="json")
    @marshal_with(UsuarioResponseSchema)
    def post(self, **kwargs):
        try:
            usuario = self.__service.login(kwargs["nome"], kwargs["senha"])
            if not usuario:
                abort(401, message="Usuário ou senha inválidos.")
            return usuario, 200
        except OperationalError:
            abort(500, message="Erro interno do servidor.")
