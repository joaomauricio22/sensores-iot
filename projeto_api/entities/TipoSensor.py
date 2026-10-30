from sqlalchemy import Column, Integer, String

from entities.Base import db


# Classe que mapeia a tabela "tipo_sensor".
# Representa o tipo de dado produzido por um sensor (ex.: Temperatura, Umidade),
# incluindo a unidade de medida utilizada (ex.: °C, %).
class TipoSensor(db.Model):
    __tablename__ = "tipo_sensor"

    id = Column("id_tipo_sensor", Integer, primary_key=True)
    nome = Column("nome", String(100), nullable=False, unique=True)
    unidade = Column("unidade", String(20), nullable=False)
    descricao = Column("descricao", String(255))

    def __repr__(self):
        return f"<TipoSensor id={self.id} nome={self.nome} unidade={self.unidade}>"
