from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from entities.Base import db


# Classe que mapeia a tabela "leitura".
# Representa um "frame" de telemetria OBD-II: todos os parâmetros coletados
# em um mesmo instante, já padronizados para os nomes canônicos.
#
# A restrição UNIQUE (veiculo_id, data_hora) implementa a regra de negócio
# de não registrar duas vezes o mesmo instante de um veículo.
class Leitura(db.Model):
    __tablename__ = "leitura"
    __table_args__ = (
        UniqueConstraint("veiculo_id", "data_hora", name="uq_leitura_veiculo_data"),
    )

    id = Column("id_leitura", Integer, primary_key=True)
    veiculo_id = Column("veiculo_id", Integer, ForeignKey("veiculo.id_veiculo"), nullable=False)
    data_hora = Column("data_hora", DateTime, nullable=False)

    velocidade = Column("velocidade", Float)
    rpm = Column("rpm", Float)
    accel_x = Column("accel_x", Float)
    accel_y = Column("accel_y", Float)
    accel_z = Column("accel_z", Float)
    posicao_acelerador = Column("posicao_acelerador", Float)
    latitude = Column("latitude", Float)
    longitude = Column("longitude", Float)

    veiculo = relationship("Veiculo", backref="leituras")

    def __repr__(self):
        return f"<Leitura id={self.id} veiculo={self.veiculo_id} data_hora={self.data_hora}>"
