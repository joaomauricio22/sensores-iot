from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from entities.Base import db


# Classe que mapeia a tabela "leitura".
# Representa um "frame" de telemetria OBD-II: os valores dos sensores do veículo
# em um mesmo instante, já padronizados.
#
# A restrição UNIQUE (rota_id, data_hora) implementa a regra de negócio
# de não registrar duas vezes o mesmo instante de uma rota.
class Leitura(db.Model):
    __tablename__ = "leitura"
    __table_args__ = (
        UniqueConstraint("rota_id", "data_hora", name="uq_leitura_rota_data"),
    )

    id = Column("id_leitura", Integer, primary_key=True)
    rota_id = Column(
        "rota_id", Integer,
        ForeignKey("rota.id_rota", ondelete="CASCADE"),
        nullable=False,
    )
    data_hora = Column("data_hora", DateTime, nullable=False)

    velocidade = Column("velocidade", Float)
    rpm = Column("rpm", Float)
    accel_x = Column("accel_x", Float)
    accel_y = Column("accel_y", Float)
    accel_z = Column("accel_z", Float)
    posicao_acelerador = Column("posicao_acelerador", Float)
    latitude = Column("latitude", Float)
    longitude = Column("longitude", Float)

    rota = relationship("Rota", back_populates="leituras")
    eventos_risco = relationship(
        "EventoRisco",
        back_populates="leitura",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<Leitura id={self.id} rota={self.rota_id} data_hora={self.data_hora}>"
