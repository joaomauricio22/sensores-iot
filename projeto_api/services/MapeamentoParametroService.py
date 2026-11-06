from marshmallow import ValidationError

from entities.MapeamentoParametro import MapeamentoParametro
from repositories.MapeamentoParametroRepository import MapeamentoParametroRepository
from repositories.ParametroRepository import ParametroRepository


# Camada de serviço: regras de negócio do mapeamento (padronização de nomes).
class MapeamentoParametroService:

    def __init__(self):
        self.__repository = MapeamentoParametroRepository()
        self.__parametro_repository = ParametroRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, mapeamento_id):
        return self.__repository.get_by_id(mapeamento_id)

    def add(self, nome_bruto: str, parametro_id: int) -> MapeamentoParametro:
        if not nome_bruto or not str(nome_bruto).strip():
            raise ValidationError("O nome bruto é obrigatório.")
        if self.__repository.get_by_nome_bruto(nome_bruto):
            raise ValidationError("Já existe um mapeamento para esse nome bruto.")
        if self.__parametro_repository.get_by_id(parametro_id) is None:
            raise ValidationError("O parâmetro informado não está cadastrado.")
        mapeamento = MapeamentoParametro(nome_bruto=nome_bruto, parametro_id=parametro_id)
        return self.__repository.add(mapeamento)

    def update(self, mapeamento_id: int, nome_bruto: str, parametro_id: int):
        mapeamento = self.__repository.get_by_id(mapeamento_id)
        if not mapeamento:
            return None
        if self.__parametro_repository.get_by_id(parametro_id) is None:
            raise ValidationError("O parâmetro informado não está cadastrado.")
        mapeamento.nome_bruto = nome_bruto
        mapeamento.parametro_id = parametro_id
        return self.__repository.update(mapeamento)

    def delete(self, mapeamento_id: int):
        mapeamento = self.__repository.get_by_id(mapeamento_id)
        if not mapeamento:
            return None
        return self.__repository.delete(mapeamento)
