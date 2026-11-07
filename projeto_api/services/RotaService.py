from marshmallow import ValidationError

from entities.Rota import Rota
from repositories.RotaRepository import RotaRepository
from repositories.UsuarioRepository import UsuarioRepository


# Camada de serviço: regras de negócio da Rota.
class RotaService:

    def __init__(self):
        self.__repository = RotaRepository()
        self.__usuario_repository = UsuarioRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, rota_id):
        return self.__repository.get_by_id(rota_id)

    def get_by_usuario(self, usuario_id):
        return self.__repository.get_by_usuario(usuario_id)

    def add(self, usuario_id: int, nome: str, arquivo_origem: str = None) -> Rota:
        if not nome or not str(nome).strip():
            raise ValidationError("O nome da rota é obrigatório.")
        if self.__usuario_repository.get_by_id(usuario_id) is None:
            raise ValidationError("O usuário informado não está cadastrado.")
        rota = Rota(usuario_id=usuario_id, nome=nome, arquivo_origem=arquivo_origem)
        return self.__repository.add(rota)

    def update(self, rota_id: int, nome: str):
        rota = self.__repository.get_by_id(rota_id)
        if not rota:
            return None
        if not nome or not str(nome).strip():
            raise ValidationError("O nome da rota é obrigatório.")
        rota.nome = nome
        return self.__repository.update(rota)

    def delete(self, rota_id: int):
        rota = self.__repository.get_by_id(rota_id)
        if not rota:
            return None
        return self.__repository.delete(rota)
