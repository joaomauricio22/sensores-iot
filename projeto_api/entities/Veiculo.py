from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from entities.Base import db


# Classe que mapeia a tabela "veiculo".
# Representa o veículo monitorado pela telemetria OBD-II.
class Veiculo(db.Model):
    __tablename__ = "veiculo"

    id = Column("id_veiculo", Integer, primary_key=True)
    identificador = Column("identificador", String(50), nullable=False, unique=True)
    modelo = Column("modelo", String(100))
    data_cadastro = Column("data_cadastro", DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<Veiculo id={self.id} identificador={self.identificador}>"
