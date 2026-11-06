from entities.MapeamentoParametro import MapeamentoParametro
from entities.Base import db


# Camada de persistência da entidade MapeamentoParametro.
class MapeamentoParametroRepository:

    def get_all(self):
        return db.session.query(MapeamentoParametro).all()

    def get_by_id(self, mapeamento_id):
        return db.session.get(MapeamentoParametro, mapeamento_id)

    def get_by_nome_bruto(self, nome_bruto):
        return (
            db.session.query(MapeamentoParametro)
            .filter(MapeamentoParametro.nome_bruto == nome_bruto)
            .first()
        )

    def add(self, mapeamento: MapeamentoParametro) -> MapeamentoParametro:
        db.session.add(mapeamento)
        db.session.commit()
        return mapeamento

    def update(self, mapeamento: MapeamentoParametro) -> MapeamentoParametro:
        db.session.commit()
        return mapeamento

    def delete(self, mapeamento: MapeamentoParametro) -> MapeamentoParametro:
        db.session.delete(mapeamento)
        db.session.commit()
        return mapeamento
