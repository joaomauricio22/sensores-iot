from marshmallow import ValidationError

from entities.TipoSensor import TipoSensor
from repositories.TipoSensorRepository import TipoSensorRepository


# Camada de serviço: implementa as regras de negócio do TipoSensor.
class TipoSensorService:

    def __init__(self):
        self.__repository = TipoSensorRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, tipo_sensor_id):
        return self.__repository.get_by_id(tipo_sensor_id)

    def add(self, nome: str, unidade: str, descricao: str = None) -> TipoSensor:
        if not nome or not str(nome).strip():
            raise ValidationError("O nome do tipo de sensor é obrigatório.")
        if not unidade or not str(unidade).strip():
            raise ValidationError("A unidade é obrigatória.")
        if self.__repository.get_by_nome(nome):
            raise ValidationError("Já existe um tipo de sensor com esse nome.")

        tipo_sensor = TipoSensor(nome=nome, unidade=unidade, descricao=descricao)
        return self.__repository.add(tipo_sensor)

    def update(self, tipo_sensor_id: int, nome: str, unidade: str, descricao: str = None):
        tipo_sensor = self.__repository.get_by_id(tipo_sensor_id)
        if not tipo_sensor:
            return None

        if not nome or not str(nome).strip():
            raise ValidationError("O nome do tipo de sensor é obrigatório.")
        if not unidade or not str(unidade).strip():
            raise ValidationError("A unidade é obrigatória.")

        existente = self.__repository.get_by_nome(nome)
        if existente and existente.id != tipo_sensor.id:
            raise ValidationError("Já existe um tipo de sensor com esse nome.")

        tipo_sensor.nome = nome
        tipo_sensor.unidade = unidade
        tipo_sensor.descricao = descricao
        return self.__repository.update(tipo_sensor)

    def delete(self, tipo_sensor_id: int):
        tipo_sensor = self.__repository.get_by_id(tipo_sensor_id)
        if not tipo_sensor:
            return None
        return self.__repository.delete(tipo_sensor)
