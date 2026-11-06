from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from entities.Base import db


# Classe que mapeia a tabela "mapeamento_parametro".
# Padroniza os nomes brutos das colunas dos arquivos (que variam entre fontes)
# para um parâmetro canônico. Ex.: "Vehicle speed (km/h)" e "Velocidade do
# veículo (km/h)" apontam ambos para o parâmetro "velocidade".
class MapeamentoParametro(db.Model):
    __tablename__ = "mapeamento_parametro"

    id = Column("id_mapeamento", Integer, primary_key=True)
    nome_bruto = Column("nome_bruto", String(200), nullable=False, unique=True)
    parametro_id = Column(
        "parametro_id", Integer, ForeignKey("parametro.id_parametro"), nullable=False
    )

    parametro = relationship("Parametro", backref="mapeamentos")

    def __repr__(self):
        return f"<Mapeamento id={self.id} {self.nome_bruto} -> {self.parametro_id}>"
