from marshmallow import ValidationError

from entities.Sensor import Sensor
from repositories.SensorRepository import SensorRepository
from repositories.TipoSensorRepository import TipoSensorRepository


# Camada de serviço: implementa as regras de negócio do Sensor.
class SensorService:

    def __init__(self):
        self.__repository = SensorRepository()
        self.__tipo_repository = TipoSensorRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, sensor_id):
        return self.__repository.get_by_id(sensor_id)

    def add(self, identificador: str, nome: str = None, tipo_sensor_id: int = None,
            limite_min: float = None, limite_max: float = None) -> Sensor:
        # Regra 1: identificador obrigatório e único.
        if not identificador or not str(identificador).strip():
            raise ValidationError("O identificador do sensor é obrigatório.")
        if self.__repository.get_by_identificador(identificador):
            raise ValidationError("Já existe um sensor com esse identificador.")

        # O tipo de sensor deve estar cadastrado.
        if self.__tipo_repository.get_by_id(tipo_sensor_id) is None:
            raise ValidationError("O tipo de sensor informado não está cadastrado.")

        # Regra 6: limites coerentes (mínimo não pode superar o máximo).
        if limite_min > limite_max:
            raise ValidationError("O limite mínimo não pode ser maior que o limite máximo.")

        sensor = Sensor(
            identificador=identificador,
            nome=nome,
            tipo_sensor_id=tipo_sensor_id,
            limite_min=limite_min,
            limite_max=limite_max,
        )
        return self.__repository.add(sensor)

    def update(self, sensor_id: int, identificador: str = None, nome: str = None,
               tipo_sensor_id: int = None, limite_min: float = None, limite_max: float = None):
        sensor = self.__repository.get_by_id(sensor_id)
        if not sensor:
            return None

        if not identificador or not str(identificador).strip():
            raise ValidationError("O identificador do sensor é obrigatório.")

        existente = self.__repository.get_by_identificador(identificador)
        if existente and existente.id != sensor.id:
            raise ValidationError("Já existe um sensor com esse identificador.")

        if self.__tipo_repository.get_by_id(tipo_sensor_id) is None:
            raise ValidationError("O tipo de sensor informado não está cadastrado.")

        if limite_min > limite_max:
            raise ValidationError("O limite mínimo não pode ser maior que o limite máximo.")

        sensor.identificador = identificador
        sensor.nome = nome
        sensor.tipo_sensor_id = tipo_sensor_id
        sensor.limite_min = limite_min
        sensor.limite_max = limite_max
        return self.__repository.update(sensor)

    def delete(self, sensor_id: int):
        sensor = self.__repository.get_by_id(sensor_id)
        if not sensor:
            return None
        return self.__repository.delete(sensor)
