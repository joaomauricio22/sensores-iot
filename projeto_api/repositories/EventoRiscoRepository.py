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

    def delete_por_leitura(self, leitura_id, preservar_manual=True) -> int:
        """Remove os eventos de uma leitura (usado ao editar a leitura).

        Por padrão preserva os eventos cadastrados manualmente (``metodo ==
        "MANUAL"``): eles foram inseridos pelo usuário no CRUD e não devem ser
        apagados quando a leitura tem um valor corrigido. Os eventos gerados
        pelos detectores são removidos porque ficam obsoletos.
        """
        query = db.session.query(EventoRisco).filter(EventoRisco.leitura_id == leitura_id)
        if preservar_manual:
            query = query.filter(EventoRisco.metodo != "MANUAL")
        return query.delete(synchronize_session=False)

    def mover_eventos_manuais(self, leitura_id, rota_id, data_hora) -> int:
        """Atualiza rota/data dos eventos manuais quando a leitura muda de rota.

        Um evento manual pertence à leitura; se a leitura for movida para outra
        rota (ou tiver a data/hora alterada), o evento deve acompanhá-la.
        """
        return (
            db.session.query(EventoRisco)
            .filter(
                EventoRisco.leitura_id == leitura_id,
                EventoRisco.metodo == "MANUAL",
            )
            .update(
                {"rota_id": rota_id, "data_hora": data_hora},
                synchronize_session=False,
            )
        )
