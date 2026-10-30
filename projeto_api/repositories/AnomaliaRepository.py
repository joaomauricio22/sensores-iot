from entities.Anomalia import Anomalia
from entities.Base import db


# Camada de persistência da entidade Anomalia.
class AnomaliaRepository:

    def get_all(self):
        return db.session.query(Anomalia).all()

    def get_by_id(self, anomalia_id):
        return db.session.get(Anomalia, anomalia_id)

    def get_by_sensor(self, sensor_id):
        return db.session.query(Anomalia).filter(Anomalia.sensor_id == sensor_id).all()

    def get_by_leitura(self, leitura_id):
        """Lista as anomalias registradas para uma leitura (uma por método)."""
        return db.session.query(Anomalia).filter(Anomalia.leitura_id == leitura_id).all()

    def get_by_leitura_metodo(self, leitura_id, metodo):
        """Verifica se já existe anomalia para uma leitura e um método específico."""
        return (
            db.session.query(Anomalia)
            .filter(Anomalia.leitura_id == leitura_id, Anomalia.metodo == metodo)
            .first()
        )

    def add(self, anomalia: Anomalia) -> Anomalia:
        db.session.add(anomalia)
        db.session.commit()
        return anomalia

    def update(self, anomalia: Anomalia) -> Anomalia:
        db.session.commit()
        return anomalia

    def delete(self, anomalia: Anomalia) -> Anomalia:
        db.session.delete(anomalia)
        db.session.commit()
        return anomalia
