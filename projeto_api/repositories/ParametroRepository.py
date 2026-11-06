from entities.Parametro import Parametro
from entities.Base import db


# Camada de persistência da entidade Parametro.
class ParametroRepository:

    def get_all(self):
        return db.session.query(Parametro).all()

    def get_by_id(self, parametro_id):
        return db.session.get(Parametro, parametro_id)

    def get_by_nome(self, nome):
        return db.session.query(Parametro).filter(Parametro.nome == nome).first()

    def add(self, parametro: Parametro) -> Parametro:
        db.session.add(parametro)
        db.session.commit()
        return parametro

    def update(self, parametro: Parametro) -> Parametro:
        db.session.commit()
        return parametro

    def delete(self, parametro: Parametro) -> Parametro:
        db.session.delete(parametro)
        db.session.commit()
        return parametro
