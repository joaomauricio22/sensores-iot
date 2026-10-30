import os

from flask import Flask
from flask_restful import Api

from config import Config
from entities import Anomalia, Leitura, Sensor, TipoSensor  # noqa: F401  (registra os modelos)
from entities.Base import db
from routes.endpoints import initialize_endpoints


# Função que cria e configura a API (design pattern "Application Factory").
def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Prefixo "/iot" agrupa todos os endpoints desta API.
    api = Api(app, prefix="/iot")
    initialize_endpoints(api)

    return app


app = create_app()

if __name__ == "__main__":
    # Executar: python app.py  (sobe a API na porta 8080)
    # O debug fica ativo apenas quando FLASK_DEBUG=1 (não ativo no Docker).
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=8080, debug=debug)
