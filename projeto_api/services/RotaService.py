from marshmallow import ValidationError

from entities.Rota import Rota
from repositories.RotaRepository import RotaRepository


# Camada de serviço: regras de negócio da Rota.
class RotaService:

    def __init__(self):
        self.__repository = RotaRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, rota_id):
        return self.__repository.get_by_id(rota_id)

    def add(self, nome: str, arquivo_origem: str = None) -> Rota:
        if not nome or not str(nome).strip():
            raise ValidationError("O nome da rota é obrigatório.")
        nome = str(nome).strip()
        self.__validar_tamanhos(nome, arquivo_origem)
        rota = Rota(nome=nome, arquivo_origem=arquivo_origem)
        return self.__repository.add(rota)

    def update(self, rota_id: int, nome: str, arquivo_origem: str = None):
        rota = self.__repository.get_by_id(rota_id)
        if not rota:
            return None
        if not nome or not str(nome).strip():
            raise ValidationError("O nome da rota é obrigatório.")
        nome = str(nome).strip()
        self.__validar_tamanhos(nome, arquivo_origem)
        rota.nome = nome
        rota.arquivo_origem = arquivo_origem or None
        return self.__repository.update(rota)

    def __validar_tamanhos(self, nome, arquivo_origem):
        if len(nome) > 100:
            raise ValidationError("O nome da rota deve ter no máximo 100 caracteres.")
        if arquivo_origem is not None and len(arquivo_origem) > 200:
            raise ValidationError("O arquivo de origem deve ter no máximo 200 caracteres.")

    def delete(self, rota_id: int):
        rota = self.__repository.get_by_id(rota_id)
        if not rota:
            return None
        # O banco está configurado com ON DELETE CASCADE: as leituras e os
        # eventos vinculados são removidos automaticamente.
        resultado = self.__repository.delete(rota)
        # Remover uma rota muda o histórico de ML das demais (que treinam com as
        # leituras das outras rotas), então todas ficam pendentes de reanálise.
        self.__repository.invalidar_analises()
        return resultado
