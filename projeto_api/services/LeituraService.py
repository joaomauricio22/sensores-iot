import math

from marshmallow import ValidationError

from entities.Leitura import Leitura
from repositories.LeituraRepository import LeituraRepository
from repositories.VeiculoRepository import VeiculoRepository


# Camada de serviço: regras de negócio da Leitura (frame de telemetria).
class LeituraService:

    def __init__(self):
        self.__repository = LeituraRepository()
        self.__veiculo_repository = VeiculoRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, leitura_id):
        return self.__repository.get_by_id(leitura_id)

    def add(self, veiculo_id: int, data_hora, velocidade=None, rpm=None,
            accel_x=None, accel_y=None, accel_z=None, posicao_acelerador=None,
            latitude=None, longitude=None) -> Leitura:
        # Regra 2: dados obrigatórios (veículo e data/hora).
        if veiculo_id is None:
            raise ValidationError("O veículo é obrigatório.")
        if data_hora is None:
            raise ValidationError("A data/hora da coleta é obrigatória.")

        # Regra 3: veículo cadastrado.
        if self.__veiculo_repository.get_by_id(veiculo_id) is None:
            raise ValidationError("Não é possível registrar leitura para um veículo não cadastrado.")

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

        # Regra 5: sem frames duplicados (mesmo veículo + instante).
        if self.__repository.find_duplicada(veiculo_id, data_hora):
            raise ValidationError("Já existe uma leitura para este veículo nesse instante.")

        leitura = Leitura(veiculo_id=veiculo_id, data_hora=data_hora, **valores)
        return self.__repository.add(leitura)

    def update(self, leitura_id: int, veiculo_id: int, data_hora, velocidade=None,
               rpm=None, accel_x=None, accel_y=None, accel_z=None,
               posicao_acelerador=None, latitude=None, longitude=None):
        leitura = self.__repository.get_by_id(leitura_id)
        if not leitura:
            return None

        if self.__veiculo_repository.get_by_id(veiculo_id) is None:
            raise ValidationError("Não é possível registrar leitura para um veículo não cadastrado.")

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

        duplicada = self.__repository.find_duplicada(veiculo_id, data_hora)
        if duplicada and duplicada.id != leitura.id:
            raise ValidationError("Já existe uma leitura para este veículo nesse instante.")

        leitura.veiculo_id = veiculo_id
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
