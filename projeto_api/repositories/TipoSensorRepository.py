from entities.TipoSensor import TipoSensor
from entities.Base import db


# Camada de persistência da entidade TipoSensor.
# Concentra as operações no banco (SELECT, INSERT, UPDATE, DELETE).
class TipoSensorRepository:

    def get_all(self):
        """SELECT * FROM tipo_sensor"""
        return db.session.query(TipoSensor).all()

    def get_by_id(self, tipo_sensor_id):
        """SELECT * FROM tipo_sensor WHERE id_tipo_sensor = :id"""
        return db.session.get(TipoSensor, tipo_sensor_id)

    def get_by_nome(self, nome):
        """Busca um tipo de sensor pelo nome (usado para validar unicidade)."""
        return db.session.query(TipoSensor).filter(TipoSensor.nome == nome).first()

    def add(self, tipo_sensor: TipoSensor) -> TipoSensor:
        """INSERT INTO tipo_sensor"""
        db.session.add(tipo_sensor)
        db.session.commit()
        return tipo_sensor

    def update(self, tipo_sensor: TipoSensor) -> TipoSensor:
        """Confirma as alterações de um registro já carregado."""
        db.session.commit()
        return tipo_sensor

    def delete(self, tipo_sensor: TipoSensor) -> TipoSensor:
        """DELETE FROM tipo_sensor WHERE id_tipo_sensor = :id"""
        db.session.delete(tipo_sensor)
        db.session.commit()
        return tipo_sensor
