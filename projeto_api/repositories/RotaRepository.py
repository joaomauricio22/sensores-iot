from entities.Rota import Rota
from entities.Base import db


# Camada de persistência da entidade Rota.
class RotaRepository:

    def get_all(self):
        return db.session.query(Rota).order_by(Rota.data_importacao).all()

    def get_by_id(self, rota_id):
        return db.session.get(Rota, rota_id)

    def add(self, rota: Rota) -> Rota:
        db.session.add(rota)
        db.session.commit()
        return rota

    def update(self, rota: Rota) -> Rota:
        db.session.commit()
        return rota

    def delete(self, rota: Rota) -> Rota:
        db.session.delete(rota)
        db.session.commit()
        return rota
