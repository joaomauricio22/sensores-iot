import hashlib

from marshmallow import ValidationError

from entities.Usuario import Usuario
from repositories.UsuarioRepository import UsuarioRepository


def _hash_senha(senha: str) -> str:
    """Gera o hash SHA-256 da senha (não armazenamos a senha em texto puro)."""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


# Camada de serviço: cadastro e autenticação de usuários.
class UsuarioService:

    def __init__(self):
        self.__repository = UsuarioRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, usuario_id):
        return self.__repository.get_by_id(usuario_id)

    def cadastrar(self, nome: str, senha: str) -> Usuario:
        if not nome or not str(nome).strip():
            raise ValidationError("O nome de usuário é obrigatório.")
        if not senha or not str(senha).strip():
            raise ValidationError("A senha é obrigatória.")
        if self.__repository.get_by_nome(nome):
            raise ValidationError("Já existe um usuário com esse nome.")
        usuario = Usuario(nome=nome, senha=_hash_senha(senha))
        return self.__repository.add(usuario)

    def login(self, nome: str, senha: str):
        """Valida as credenciais; retorna o usuário se forem válidas, senão None."""
        usuario = self.__repository.get_by_nome(nome)
        if not usuario or usuario.senha != _hash_senha(senha):
            return None
        return usuario

    def update(self, usuario_id: int, senha: str = None):
        usuario = self.__repository.get_by_id(usuario_id)
        if not usuario:
            return None
        if senha and str(senha).strip():
            usuario.senha = _hash_senha(senha)
        return self.__repository.update(usuario)

    def delete(self, usuario_id: int):
        usuario = self.__repository.get_by_id(usuario_id)
        if not usuario:
            return None
        return self.__repository.delete(usuario)
