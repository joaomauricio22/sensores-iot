import math

from marshmallow import ValidationError

from entities.Leitura import Leitura
from repositories.LeituraRepository import LeituraRepository
from repositories.RotaRepository import RotaRepository

CAMPOS_VALOR = (
    "velocidade",
    "rpm",
    "accel_x",
    "accel_y",
    "accel_z",
    "posicao_acelerador",
    "latitude",
    "longitude",
)


# Camada de serviço: regras de negócio da Leitura (frame de telemetria).
class LeituraService:

    def __init__(self):
        self.__repository = LeituraRepository()
        self.__rota_repository = RotaRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, leitura_id):
        return self.__repository.get_by_id(leitura_id)

    def get_by_rota(self, rota_id):
        return self.__repository.get_by_rota(rota_id)

    def add(self, rota_id: int, data_hora, velocidade=None, rpm=None,
            accel_x=None, accel_y=None, accel_z=None, posicao_acelerador=None,
            latitude=None, longitude=None) -> Leitura:
        # Regra 2: dados obrigatórios (rota, data/hora e ao menos um valor medido).
        if rota_id is None:
            raise ValidationError("A rota é obrigatória.")
        if data_hora is None:
            raise ValidationError("A data/hora da coleta é obrigatória.")

        # Regra 3: a rota precisa estar cadastrada.
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

        self.__exigir_algum_valor(valores)

        # Regra 5: sem frames duplicados.
        if self.__repository.find_duplicada(rota_id, data_hora):
            raise ValidationError("Já existe uma leitura para esta rota nesse instante.")

        leitura = Leitura(rota_id=rota_id, data_hora=data_hora, **valores)
        resultado = self.__repository.add(leitura)
        self.__invalidar_analise(rota_id)
        return resultado

    def update(self, leitura_id: int, rota_id: int, data_hora, velocidade=None,
               rpm=None, accel_x=None, accel_y=None, accel_z=None,
               posicao_acelerador=None, latitude=None, longitude=None):
        leitura = self.__repository.get_by_id(leitura_id)
        if not leitura:
            return None
        rota_anterior = leitura.rota_id
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

        self.__exigir_algum_valor(valores)

        if self.__repository.find_duplicada(rota_id, data_hora, excluir_id=leitura_id):
            raise ValidationError("Já existe uma leitura para esta rota nesse instante.")

        leitura.rota_id = rota_id
        leitura.data_hora = data_hora
        for campo, valor in valores.items():
            setattr(leitura, campo, valor)
        resultado = self.__repository.update(leitura)
        self.__invalidar_analise(rota_id)
        if rota_anterior != rota_id:
            self.__invalidar_analise(rota_anterior)
        return resultado

    def delete(self, leitura_id: int):
        leitura = self.__repository.get_by_id(leitura_id)
        if not leitura:
            return None
        rota_id = leitura.rota_id
        resultado = self.__repository.delete(leitura)
        self.__invalidar_analise(rota_id)
        return resultado

    def __exigir_algum_valor(self, valores):
        if not any(valores[campo] is not None for campo in CAMPOS_VALOR):
            raise ValidationError(
                "A leitura deve possuir ao menos um valor medido por um sensor."
            )

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

    def __invalidar_analise(self, rota_id):
        """Marca a rota como não analisada após mudança nas leituras.

        Assim, a próxima consulta a resumo/gráfico reexecuta a análise e
        incorpora a leitura nova/editada/excluída.
        """
        rota = self.__rota_repository.get_by_id(rota_id)
        if rota is not None:
            rota.data_analise = None
            self.__rota_repository.update(rota)
