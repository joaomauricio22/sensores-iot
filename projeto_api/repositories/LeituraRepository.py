from entities.Leitura import Leitura
from entities.Base import db


# Camada de persistência da entidade Leitura (frame de telemetria).
class LeituraRepository:

    def get_all(self):
        return db.session.query(Leitura).order_by(Leitura.rota_id, Leitura.data_hora).all()

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

    def get_historico(self, rota_id, limite=5000):
        """Leituras de outras rotas (histórico para o modelo de ML)."""
        return (
            db.session.query(Leitura)
            .filter(Leitura.rota_id != rota_id)
            .order_by(Leitura.data_hora.desc())
            .limit(limite)
            .all()
        )

    def find_duplicada(self, rota_id, data_hora, excluir_id=None):
        query = db.session.query(Leitura).filter(
            Leitura.rota_id == rota_id,
            Leitura.data_hora == data_hora,
        )
        if excluir_id is not None:
            query = query.filter(Leitura.id != excluir_id)
        return query.first()

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
