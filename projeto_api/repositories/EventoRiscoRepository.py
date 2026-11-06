from entities.EventoRisco import EventoRisco
from entities.Base import db


# Camada de persistência da entidade EventoRisco.
class EventoRiscoRepository:

    def get_all(self):
        return db.session.query(EventoRisco).all()

    def get_by_id(self, evento_id):
        return db.session.get(EventoRisco, evento_id)

    def get_by_veiculo(self, veiculo_id):
        return db.session.query(EventoRisco).filter(EventoRisco.veiculo_id == veiculo_id).all()

    def get_by_leitura_metodo(self, leitura_id, metodo):
        return (
            db.session.query(EventoRisco)
            .filter(EventoRisco.leitura_id == leitura_id, EventoRisco.metodo == metodo)
            .first()
        )

    def add(self, evento: EventoRisco) -> EventoRisco:
        db.session.add(evento)
        db.session.commit()
        return evento

    def update(self, evento: EventoRisco) -> EventoRisco:
        db.session.commit()
        return evento

    def delete(self, evento: EventoRisco) -> EventoRisco:
        db.session.delete(evento)
        db.session.commit()
        return evento
