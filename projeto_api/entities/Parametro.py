from sqlalchemy import Column, Integer, String, Float

from entities.Base import db


# Classe que mapeia a tabela "parametro".
# Catálogo de parâmetros canônicos (padronizados) monitorados na telemetria.
# Cada parâmetro possui unidade e limites de referência (regra de negócio 6).
# Registramos aqui apenas os parâmetros que agregam valor à análise.
class Parametro(db.Model):
    __tablename__ = "parametro"

    id = Column("id_parametro", Integer, primary_key=True)
    nome = Column("nome", String(100), nullable=False, unique=True)
    unidade = Column("unidade", String(20), nullable=False)
    limite_min = Column("limite_min", Float, nullable=False)
    limite_max = Column("limite_max", Float, nullable=False)

    def __repr__(self):
        return f"<Parametro id={self.id} nome={self.nome} unidade={self.unidade}>"
