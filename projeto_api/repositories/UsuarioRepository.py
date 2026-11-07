from entities.Usuario import Usuario
from entities.Base import db


# Camada de persistência da entidade Usuario.
class UsuarioRepository:

    def get_all(self):
        return db.session.query(Usuario).all()

    def get_by_id(self, usuario_id):
        return db.session.get(Usuario, usuario_id)

    def get_by_nome(self, nome):
        return db.session.query(Usuario).filter(Usuario.nome == nome).first()

    def add(self, usuario: Usuario) -> Usuario:
        db.session.add(usuario)
        db.session.commit()
        return usuario

    def update(self, usuario: Usuario) -> Usuario:
        db.session.commit()
        return usuario

    def delete(self, usuario: Usuario) -> Usuario:
        db.session.delete(usuario)
        db.session.commit()
        return usuario
