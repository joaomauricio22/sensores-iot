from entities.Sensor import Sensor
from entities.Base import db


# Camada de persistência da entidade Sensor.
class SensorRepository:

    def get_all(self):
        return db.session.query(Sensor).all()

    def get_by_id(self, sensor_id):
        return db.session.get(Sensor, sensor_id)

    def get_by_identificador(self, identificador):
        """Busca um sensor pelo identificador (usado para validar unicidade)."""
        return db.session.query(Sensor).filter(Sensor.identificador == identificador).first()

    def add(self, sensor: Sensor) -> Sensor:
        db.session.add(sensor)
        db.session.commit()
        return sensor

    def update(self, sensor: Sensor) -> Sensor:
        db.session.commit()
        return sensor

    def delete(self, sensor: Sensor) -> Sensor:
        db.session.delete(sensor)
        db.session.commit()
        return sensor
