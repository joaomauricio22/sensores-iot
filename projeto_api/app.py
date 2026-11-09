import os

from flask import Flask
from flask_restful import Api

from settings import Config
from entities import EventoRisco, Leitura, Rota  # noqa: F401
from entities.Base import db
from routes.endpoints import initialize_endpoints


# Função que cria e configura a API (design pattern "Application Factory").
def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    api = Api(app, prefix="/telemetria")
    initialize_endpoints(api)

    return app


app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=8080, debug=debug)
