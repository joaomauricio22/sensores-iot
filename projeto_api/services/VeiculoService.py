from marshmallow import ValidationError

from entities.Veiculo import Veiculo
from repositories.VeiculoRepository import VeiculoRepository


# Camada de serviço: regras de negócio do Veículo.
class VeiculoService:

    def __init__(self):
        self.__repository = VeiculoRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, veiculo_id):
        return self.__repository.get_by_id(veiculo_id)

    def add(self, identificador: str, modelo: str = None) -> Veiculo:
        # Regra 1: identificador obrigatório e único.
        if not identificador or not str(identificador).strip():
            raise ValidationError("O identificador do veículo é obrigatório.")
        if self.__repository.get_by_identificador(identificador):
            raise ValidationError("Já existe um veículo com esse identificador.")
        veiculo = Veiculo(identificador=identificador, modelo=modelo)
        return self.__repository.add(veiculo)

    def update(self, veiculo_id: int, identificador: str, modelo: str = None):
        veiculo = self.__repository.get_by_id(veiculo_id)
        if not veiculo:
            return None
        if not identificador or not str(identificador).strip():
            raise ValidationError("O identificador do veículo é obrigatório.")
        existente = self.__repository.get_by_identificador(identificador)
        if existente and existente.id != veiculo.id:
            raise ValidationError("Já existe um veículo com esse identificador.")
        veiculo.identificador = identificador
        veiculo.modelo = modelo
        return self.__repository.update(veiculo)

    def delete(self, veiculo_id: int):
        veiculo = self.__repository.get_by_id(veiculo_id)
        if not veiculo:
            return None
        return self.__repository.delete(veiculo)
