from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from entities.Base import db


# Classe que mapeia a tabela "evento_risco".
# Registra um evento de risco detectado na análise, com o canal (sensor) e o
# valor que dispararam a anomalia, a magnitude da Força G, a instabilidade,
# a classificação, o método de detecção e o instante.
class EventoRisco(db.Model):
    __tablename__ = "evento_risco"
    __table_args__ = (
        UniqueConstraint(
            "leitura_id", "metodo", "classificacao", "canal",
            name="uq_evento_leitura_metodo_clas_canal",
        ),
    )

    id = Column("id_evento", Integer, primary_key=True)
    leitura_id = Column(
        "leitura_id", Integer,
        ForeignKey("leitura.id_leitura", ondelete="CASCADE"),
        nullable=False,
    )
    rota_id = Column(
        "rota_id", Integer,
        ForeignKey("rota.id_rota", ondelete="CASCADE"),
        nullable=False,
    )
    canal = Column("canal", String(30), nullable=False, default="geral")
    valor = Column("valor", Float)
    forca_g = Column("forca_g", Float)
    instabilidade = Column("instabilidade", Float)
    classificacao = Column("classificacao", String(40), nullable=False, default="Comportamento atípico")
    metodo = Column("metodo", String(30), nullable=False)
    data_hora = Column("data_hora", DateTime, nullable=False)
    descricao = Column("descricao", String(255))

    leitura = relationship("Leitura", back_populates="eventos_risco")
    rota = relationship("Rota", back_populates="eventos_risco")

    def __repr__(self):
        return (
            f"<EventoRisco id={self.id} metodo={self.metodo} "
            f"classificacao={self.classificacao} canal={self.canal}>"
        )
