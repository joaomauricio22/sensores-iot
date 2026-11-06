from marshmallow import ValidationError

from entities.Parametro import Parametro
from repositories.ParametroRepository import ParametroRepository


# Camada de serviço: regras de negócio do Parametro (catálogo canônico).
class ParametroService:

    def __init__(self):
        self.__repository = ParametroRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, parametro_id):
        return self.__repository.get_by_id(parametro_id)

    def add(self, nome: str, unidade: str, limite_min: float, limite_max: float) -> Parametro:
        if not nome or not str(nome).strip():
            raise ValidationError("O nome do parâmetro é obrigatório.")
        if not unidade or not str(unidade).strip():
            raise ValidationError("A unidade é obrigatória.")
        if self.__repository.get_by_nome(nome):
            raise ValidationError("Já existe um parâmetro com esse nome.")
        # Regra 6: limites coerentes.
        if limite_min > limite_max:
            raise ValidationError("O limite mínimo não pode ser maior que o máximo.")
        parametro = Parametro(nome=nome, unidade=unidade, limite_min=limite_min, limite_max=limite_max)
        return self.__repository.add(parametro)

    def update(self, parametro_id: int, nome: str, unidade: str, limite_min: float, limite_max: float):
        parametro = self.__repository.get_by_id(parametro_id)
        if not parametro:
            return None
        if not nome or not str(nome).strip():
            raise ValidationError("O nome do parâmetro é obrigatório.")
        existente = self.__repository.get_by_nome(nome)
        if existente and existente.id != parametro.id:
            raise ValidationError("Já existe um parâmetro com esse nome.")
        if limite_min > limite_max:
            raise ValidationError("O limite mínimo não pode ser maior que o máximo.")
        parametro.nome = nome
        parametro.unidade = unidade
        parametro.limite_min = limite_min
        parametro.limite_max = limite_max
        return self.__repository.update(parametro)

    def delete(self, parametro_id: int):
        parametro = self.__repository.get_by_id(parametro_id)
        if not parametro:
            return None
        return self.__repository.delete(parametro)
