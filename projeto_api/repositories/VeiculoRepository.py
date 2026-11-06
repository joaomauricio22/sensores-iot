from entities.Veiculo import Veiculo
from entities.Base import db


# Camada de persistência da entidade Veiculo.
class VeiculoRepository:

    def get_all(self):
        return db.session.query(Veiculo).all()

    def get_by_id(self, veiculo_id):
        return db.session.get(Veiculo, veiculo_id)

    def get_by_identificador(self, identificador):
        return db.session.query(Veiculo).filter(Veiculo.identificador == identificador).first()

    def add(self, veiculo: Veiculo) -> Veiculo:
        db.session.add(veiculo)
        db.session.commit()
        return veiculo

    def update(self, veiculo: Veiculo) -> Veiculo:
        db.session.commit()
        return veiculo

    def delete(self, veiculo: Veiculo) -> Veiculo:
        db.session.delete(veiculo)
        db.session.commit()
        return veiculo
