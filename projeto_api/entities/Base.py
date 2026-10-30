# Instância única do SQLAlchemy, compartilhada por toda a aplicação.
# Ela é responsável por:
#   - Gerenciar a sessão com o banco (db.session);
#   - Registrar as classes de modelo (db.Model) e seus mapeamentos (ORM).
#
# ORM (Object-Relational Mapping): técnica que liga as tabelas do banco
# às classes Python, permitindo manipular registros como objetos.
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
