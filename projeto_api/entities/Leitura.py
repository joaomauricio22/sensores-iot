from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from entities.Base import db


# Classe que mapeia a tabela "leitura".
# Representa uma medição coletada por um sensor em um determinado instante.
#
# A restrição UNIQUE (sensor_id, valor, data_hora) implementa a regra de negócio
# de não considerar como nova leitura duas medições iguais do mesmo sensor
# com o mesmo valor e o mesmo instante de coleta.
class Leitura(db.Model):
    __tablename__ = "leitura"
    __table_args__ = (
        UniqueConstraint("sensor_id", "valor", "data_hora", name="uq_leitura_sensor_valor_data"),
    )

    id = Column("id_leitura", Integer, primary_key=True)
    sensor_id = Column("sensor_id", Integer, ForeignKey("sensor.id_sensor"), nullable=False)
    valor = Column("valor", Float, nullable=False)
    data_hora = Column("data_hora", DateTime, nullable=False)
    # Classificação atribuída pelo modelo de Machine Learning: "NORMAL" ou "ANOMALO".
    classificacao = Column("classificacao", String(20))

    # Relacionamento N:1 -> uma leitura pertence a um único sensor.
    sensor = relationship("Sensor", backref="leituras")

    def __repr__(self):
        return f"<Leitura id={self.id} sensor={self.sensor_id} valor={self.valor}>"
