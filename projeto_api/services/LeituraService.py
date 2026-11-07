import math

from marshmallow import ValidationError

from entities.Leitura import Leitura
from repositories.LeituraRepository import LeituraRepository
from repositories.RotaRepository import RotaRepository


# Camada de serviço: regras de negócio da Leitura (frame de telemetria).
class LeituraService:

    def __init__(self):
        self.__repository = LeituraRepository()
        self.__rota_repository = RotaRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, leitura_id):
        return self.__repository.get_by_id(leitura_id)

    def add(self, rota_id: int, data_hora, velocidade=None, rpm=None,
            accel_x=None, accel_y=None, accel_z=None, posicao_acelerador=None,
            latitude=None, longitude=None) -> Leitura:
        # Regra 2: dados obrigatórios.
        if rota_id is None:
            raise ValidationError("A rota é obrigatória.")
        if data_hora is None:
            raise ValidationError("A data/hora da coleta é obrigatória.")

        # Regra 3: rota cadastrada.
        if self.__rota_repository.get_by_id(rota_id) is None:
            raise ValidationError("Não é possível registrar leitura para uma rota não cadastrada.")

        # Regra 4: valores numéricos e finitos.
        valores = {
            "velocidade": self.__validar_numero(velocidade, "velocidade"),
            "rpm": self.__validar_numero(rpm, "rpm"),
            "accel_x": self.__validar_numero(accel_x, "accel_x"),
            "accel_y": self.__validar_numero(accel_y, "accel_y"),
            "accel_z": self.__validar_numero(accel_z, "accel_z"),
            "posicao_acelerador": self.__validar_numero(posicao_acelerador, "posição do acelerador"),
            "latitude": self.__validar_numero(latitude, "latitude"),
            "longitude": self.__validar_numero(longitude, "longitude"),
        }

        # Regra 5: sem frames duplicados.
        if self.__repository.find_duplicada(rota_id, data_hora):
            raise ValidationError("Já existe uma leitura para esta rota nesse instante.")

        leitura = Leitura(rota_id=rota_id, data_hora=data_hora, **valores)
        return self.__repository.add(leitura)

    def update(self, leitura_id: int, rota_id: int, data_hora, velocidade=None,
               rpm=None, accel_x=None, accel_y=None, accel_z=None,
               posicao_acelerador=None, latitude=None, longitude=None):
        leitura = self.__repository.get_by_id(leitura_id)
        if not leitura:
            return None
        if self.__rota_repository.get_by_id(rota_id) is None:
            raise ValidationError("Não é possível registrar leitura para uma rota não cadastrada.")
        valores = {
            "velocidade": self.__validar_numero(velocidade, "velocidade"),
            "rpm": self.__validar_numero(rpm, "rpm"),
            "accel_x": self.__validar_numero(accel_x, "accel_x"),
            "accel_y": self.__validar_numero(accel_y, "accel_y"),
            "accel_z": self.__validar_numero(accel_z, "accel_z"),
            "posicao_acelerador": self.__validar_numero(posicao_acelerador, "posição do acelerador"),
            "latitude": self.__validar_numero(latitude, "latitude"),
            "longitude": self.__validar_numero(longitude, "longitude"),
        }
        leitura.rota_id = rota_id
        leitura.data_hora = data_hora
        for campo, valor in valores.items():
            setattr(leitura, campo, valor)
        return self.__repository.update(leitura)

    def delete(self, leitura_id: int):
        leitura = self.__repository.get_by_id(leitura_id)
        if not leitura:
            return None
        return self.__repository.delete(leitura)

    def __validar_numero(self, valor, nome) -> float:
        if valor is None:
            return None
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            raise ValidationError(f"O valor de {nome} deve ser numérico.")
        if not math.isfinite(valor):
            raise ValidationError(f"O valor de {nome} deve ser um número finito.")
        return valor
