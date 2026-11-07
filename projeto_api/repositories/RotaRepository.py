from entities.Rota import Rota
from entities.Base import db


# Camada de persistência da entidade Rota.
class RotaRepository:

    def get_all(self):
        return db.session.query(Rota).all()

    def get_by_id(self, rota_id):
        return db.session.get(Rota, rota_id)

    def get_by_usuario(self, usuario_id):
        """Rotas de um usuário, ordenadas pela data de importação."""
        return (
            db.session.query(Rota)
            .filter(Rota.usuario_id == usuario_id)
            .order_by(Rota.data_importacao)
            .all()
        )

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
