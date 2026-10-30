from entities.Leitura import Leitura
from entities.Base import db


# Camada de persistência da entidade Leitura.
class LeituraRepository:

    def get_all(self):
        return db.session.query(Leitura).all()

    def get_by_id(self, leitura_id):
        return db.session.get(Leitura, leitura_id)

    def get_by_sensor(self, sensor_id):
        """Lista as leituras de um sensor, ordenadas pela data/hora de coleta."""
        return (
            db.session.query(Leitura)
            .filter(Leitura.sensor_id == sensor_id)
            .order_by(Leitura.data_hora)
            .all()
        )

    def find_duplicada(self, sensor_id, valor, data_hora):
        """Verifica se já existe leitura com o mesmo sensor, valor e instante."""
        return (
            db.session.query(Leitura)
            .filter(
                Leitura.sensor_id == sensor_id,
                Leitura.valor == valor,
                Leitura.data_hora == data_hora,
            )
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
