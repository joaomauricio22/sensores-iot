import math

from marshmallow import ValidationError

from entities.Leitura import Leitura
from repositories.LeituraRepository import LeituraRepository
from repositories.SensorRepository import SensorRepository


# Camada de serviço: implementa as regras de negócio da Leitura.
class LeituraService:

    def __init__(self):
        self.__repository = LeituraRepository()
        self.__sensor_repository = SensorRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, leitura_id):
        return self.__repository.get_by_id(leitura_id)

    def add(self, sensor_id: int, valor, data_hora) -> Leitura:
        valor = self.__validar(sensor_id, valor, data_hora)

        # Regra 5: não aceitar leitura duplicada (mesmo sensor, valor e instante).
        if self.__repository.find_duplicada(sensor_id, valor, data_hora):
            raise ValidationError(
                "Já existe uma leitura idêntica para este sensor (mesmo valor e instante)."
            )

        leitura = Leitura(sensor_id=sensor_id, valor=valor, data_hora=data_hora)
        return self.__repository.add(leitura)

    def update(self, leitura_id: int, sensor_id: int, valor, data_hora):
        leitura = self.__repository.get_by_id(leitura_id)
        if not leitura:
            return None

        valor = self.__validar(sensor_id, valor, data_hora)

        duplicada = self.__repository.find_duplicada(sensor_id, valor, data_hora)
        if duplicada and duplicada.id != leitura.id:
            raise ValidationError(
                "Já existe uma leitura idêntica para este sensor (mesmo valor e instante)."
            )

        leitura.sensor_id = sensor_id
        leitura.valor = valor
        leitura.data_hora = data_hora
        return self.__repository.update(leitura)

    def delete(self, leitura_id: int):
        leitura = self.__repository.get_by_id(leitura_id)
        if not leitura:
            return None
        return self.__repository.delete(leitura)

    # Validações comuns a cadastro e edição.
    def __validar(self, sensor_id: int, valor, data_hora) -> float:
        # Regra 2: dados obrigatórios.
        if sensor_id is None:
            raise ValidationError("O sensor é obrigatório.")
        if valor is None:
            raise ValidationError("O valor medido é obrigatório.")
        if data_hora is None:
            raise ValidationError("A data/hora da coleta é obrigatória.")

        # Regra 4: o valor deve ser numérico e finito.
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            raise ValidationError("O valor medido deve ser numérico.")
        if not math.isfinite(valor):
            raise ValidationError("O valor medido deve ser um número finito.")

        # Regra 3: o sensor deve estar cadastrado.
        if self.__sensor_repository.get_by_id(sensor_id) is None:
            raise ValidationError(
                "Não é possível registrar leitura para um sensor não cadastrado."
            )

        return valor
