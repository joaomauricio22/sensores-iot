from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from entities.Base import db


# Classe que mapeia a tabela "evento_risco".
# Registra um evento de risco detectado na análise, com a magnitude da Força G,
# a instabilidade, a classificação (ex.: frenagem brusca, excesso de velocidade),
# o método de detecção e o instante.
class EventoRisco(db.Model):
    __tablename__ = "evento_risco"
    __table_args__ = (
        UniqueConstraint("leitura_id", "metodo", "classificacao", name="uq_evento_leitura_metodo_clas"),
    )

    id = Column("id_evento", Integer, primary_key=True)
    leitura_id = Column("leitura_id", Integer, ForeignKey("leitura.id_leitura"), nullable=False)
    rota_id = Column("rota_id", Integer, ForeignKey("rota.id_rota"), nullable=False)
    forca_g = Column("forca_g", Float)
    instabilidade = Column("instabilidade", Float)
    classificacao = Column("classificacao", String(30), nullable=False, default="Comportamento atípico")
    metodo = Column("metodo", String(30), nullable=False)
    data_hora = Column("data_hora", DateTime, nullable=False)
    descricao = Column("descricao", String(255))

    leitura = relationship("Leitura", backref="eventos_risco")
    rota = relationship("Rota", backref="eventos_risco")

    def __repr__(self):
        return f"<EventoRisco id={self.id} metodo={self.metodo} classificacao={self.classificacao}>"
