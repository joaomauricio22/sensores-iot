import math

from marshmallow import ValidationError

from entities.Anomalia import Anomalia
from repositories.AnomaliaRepository import AnomaliaRepository


# Camada de serviço: regras de negócio e CRUD da entidade Anomalia.
# Em uso normal as anomalias são geradas automaticamente pela análise,
# mas a entidade também expõe as operações de CRUD (exigência do trabalho).
class AnomaliaService:

    def __init__(self):
        self.__repository = AnomaliaRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, anomalia_id):
        return self.__repository.get_by_id(anomalia_id)

    def add(self, leitura_id: int, sensor_id: int, valor, data_hora,
            metodo: str, descricao: str = None) -> Anomalia:
        if leitura_id is None or sensor_id is None:
            raise ValidationError("A leitura e o sensor são obrigatórios.")
        if valor is None:
            raise ValidationError("O valor é obrigatório.")
        if data_hora is None:
            raise ValidationError("A data/hora é obrigatória.")
        if not metodo or not str(metodo).strip():
            raise ValidationError("O método de identificação é obrigatório.")

        try:
            valor = float(valor)
        except (TypeError, ValueError):
            raise ValidationError("O valor deve ser numérico.")
        if not math.isfinite(valor):
            raise ValidationError("O valor deve ser um número finito.")

        anomalia = Anomalia(
            leitura_id=leitura_id,
            sensor_id=sensor_id,
            valor=valor,
            data_hora=data_hora,
            metodo=metodo,
            descricao=descricao,
        )
        return self.__repository.add(anomalia)

    def update(self, anomalia_id: int, leitura_id: int, sensor_id: int, valor,
               data_hora, metodo: str, descricao: str = None):
        anomalia = self.__repository.get_by_id(anomalia_id)
        if not anomalia:
            return None

        anomalia.leitura_id = leitura_id
        anomalia.sensor_id = sensor_id
        anomalia.valor = valor
        anomalia.data_hora = data_hora
        anomalia.metodo = metodo
        anomalia.descricao = descricao
        return self.__repository.update(anomalia)

    def delete(self, anomalia_id: int):
        anomalia = self.__repository.get_by_id(anomalia_id)
        if not anomalia:
            return None
        return self.__repository.delete(anomalia)
