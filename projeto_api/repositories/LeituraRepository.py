from entities.Leitura import Leitura
from entities.Base import db


# Camada de persistência da entidade Leitura (frame de telemetria).
class LeituraRepository:

    def get_all(self):
        return db.session.query(Leitura).all()

    def get_by_id(self, leitura_id):
        return db.session.get(Leitura, leitura_id)

    def get_by_rota(self, rota_id):
        """Leituras de uma rota, ordenadas pelo instante de coleta."""
        return (
            db.session.query(Leitura)
            .filter(Leitura.rota_id == rota_id)
            .order_by(Leitura.data_hora)
            .all()
        )

    def find_duplicada(self, rota_id, data_hora):
        return (
            db.session.query(Leitura)
            .filter(Leitura.rota_id == rota_id, Leitura.data_hora == data_hora)
            .first()
        )

    def add(self, leitura: Leitura) -> Leitura:
        db.session.add(leitura)
        db.session.commit()
        return leitura

    def update(self, leitura: Leitura) -> Leitura:
        db.session.commit()
        return leitura

    def delete(self, leitura: Leitura) -> Leitura:
        db.session.delete(leitura)
        db.session.commit()
        return leitura
