from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from entities.Base import db


# Classe que mapeia a tabela "rota".
# Representa uma viagem monitorada, importada a partir de um arquivo CSV.
#
# As relações usam "passive_deletes=True" para que a exclusão em cascata seja
# executada pelo PostgreSQL (ON DELETE CASCADE), sem o ORM tentar anular as
# chaves estrangeiras das leituras e dos eventos.
class Rota(db.Model):
    __tablename__ = "rota"

    id = Column("id_rota", Integer, primary_key=True)
    nome = Column("nome", String(100), nullable=False)
    arquivo_origem = Column("arquivo_origem", String(200))
    data_importacao = Column("data_importacao", DateTime, nullable=False, default=datetime.now)
    # Instante da última análise de risco. None = rota ainda não analisada
    # (ou invalidada após edição/criação/exclusão de leituras).
    data_analise = Column("data_analise", DateTime)

    leituras = relationship(
        "Leitura",
        back_populates="rota",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    eventos_risco = relationship(
        "EventoRisco",
        back_populates="rota",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<Rota id={self.id} nome={self.nome}>"
