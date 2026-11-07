from entities.Configuracao import Configuracao
from entities.Base import db


# Camada de persistência da entidade Configuracao.
class ConfiguracaoRepository:

    def get_all(self):
        return db.session.query(Configuracao).order_by(Configuracao.chave).all()

    def get_by_id(self, config_id):
        return db.session.get(Configuracao, config_id)

    def get_by_chave(self, chave):
        return db.session.query(Configuracao).filter(Configuracao.chave == chave).first()

    def add(self, config: Configuracao) -> Configuracao:
        db.session.add(config)
        db.session.commit()
        return config

    def update(self, config: Configuracao) -> Configuracao:
        db.session.commit()
        return config

    def delete(self, config: Configuracao) -> Configuracao:
        db.session.delete(config)
        db.session.commit()
        return config
