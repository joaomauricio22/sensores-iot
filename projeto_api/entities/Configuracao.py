from sqlalchemy import Column, Integer, String

from entities.Base import db


# Classe que mapeia a tabela "configuracao" (parâmetros ajustáveis do sistema).
# Armazena pares chave/valor, usados para os limiares de detecção de risco.
class Configuracao(db.Model):
    __tablename__ = "configuracao"

    id = Column("id_configuracao", Integer, primary_key=True)
    chave = Column("chave", String(100), nullable=False, unique=True)
    valor = Column("valor", String(200), nullable=False)

    def __repr__(self):
        return f"<Configuracao chave={self.chave} valor={self.valor}>"
