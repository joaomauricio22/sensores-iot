from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from entities.Base import db


# Classe que mapeia a tabela "rota".
# Representa uma viagem monitorada, importada a partir de um arquivo CSV.
class Rota(db.Model):
    __tablename__ = "rota"

    id = Column("id_rota", Integer, primary_key=True)
    usuario_id = Column("usuario_id", Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    nome = Column("nome", String(100), nullable=False)
    arquivo_origem = Column("arquivo_origem", String(200))
    data_importacao = Column("data_importacao", DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<Rota id={self.id} nome={self.nome}>"
