from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from entities.Base import db


# Classe que mapeia a tabela "usuario".
# Usuário com acesso ao sistema (login por nome + senha).
class Usuario(db.Model):
    __tablename__ = "usuario"

    id = Column("id_usuario", Integer, primary_key=True)
    nome = Column("nome", String(100), nullable=False, unique=True)
    senha = Column("senha", String(200), nullable=False)  # armazenada como hash
    data_cadastro = Column("data_cadastro", DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<Usuario id={self.id} nome={self.nome}>"
