from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from entities.Base import db


# Classe que mapeia a tabela "anomalia".
# Toda anomalia identificada mantém: sensor, valor, data/hora e o método
# utilizado para sua identificação ("LIMITE", "ESTATISTICO" ou "MODELO_ML").
#
# A mesma leitura pode ser sinalizada por mais de um método, por isso a
# restrição UNIQUE é (leitura_id, metodo): evita registrar duas vezes a mesma
# anomalia para o mesmo método.
class Anomalia(db.Model):
    __tablename__ = "anomalia"
    __table_args__ = (
        UniqueConstraint("leitura_id", "metodo", name="uq_anomalia_leitura_metodo"),
    )

    id = Column("id_anomalia", Integer, primary_key=True)
    leitura_id = Column("leitura_id", Integer, ForeignKey("leitura.id_leitura"), nullable=False)
    sensor_id = Column("sensor_id", Integer, ForeignKey("sensor.id_sensor"), nullable=False)
    valor = Column("valor", Float, nullable=False)
    data_hora = Column("data_hora", DateTime, nullable=False)
    metodo = Column("metodo", String(30), nullable=False)
    descricao = Column("descricao", String(255))

    # Relacionamento N:1 -> uma anomalia está ligada a uma única leitura.
    leitura = relationship("Leitura", backref="anomalias")
    # Relacionamento N:1 -> uma anomalia pertence a um único sensor.
    sensor = relationship("Sensor", backref="anomalias")

    def __repr__(self):
        return f"<Anomalia id={self.id} metodo={self.metodo} valor={self.valor}>"
