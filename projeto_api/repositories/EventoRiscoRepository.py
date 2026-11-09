from entities.EventoRisco import EventoRisco
from entities.Base import db


# Camada de persistência da entidade EventoRisco.
class EventoRiscoRepository:

    def get_all(self, tipo=None):
        query = db.session.query(EventoRisco)
        if tipo:
            query = query.filter(EventoRisco.classificacao == tipo)
        return query.all()

    def get_by_id(self, evento_id):
        return db.session.get(EventoRisco, evento_id)

    def get_by_rota(self, rota_id, tipo=None):
        query = db.session.query(EventoRisco).filter(EventoRisco.rota_id == rota_id)
        if tipo:
            query = query.filter(EventoRisco.classificacao == tipo)
        return query.all()

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
