from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from entities.Base import db


# Classe que mapeia a tabela "sensor".
# Cada sensor possui um identificador único, está associado a um TipoSensor
# e guarda os limites mínimo/máximo de referência para suas medições.
class Sensor(db.Model):
    __tablename__ = "sensor"

    id = Column("id_sensor", Integer, primary_key=True)
    identificador = Column("identificador", String(100), nullable=False, unique=True)
    nome = Column("nome", String(200))
    tipo_sensor_id = Column(
        "tipo_sensor_id", Integer, ForeignKey("tipo_sensor.id_tipo_sensor"), nullable=False
    )
    limite_min = Column("limite_min", Float, nullable=False)
    limite_max = Column("limite_max", Float, nullable=False)
    data_cadastro = Column("data_cadastro", DateTime, nullable=False, default=datetime.now)

    # Relacionamento N:1 -> um sensor pertence a um único tipo.
    tipo_sensor = relationship("TipoSensor", backref="sensores")

    def __repr__(self):
        return f"<Sensor id={self.id} identificador={self.identificador}>"
