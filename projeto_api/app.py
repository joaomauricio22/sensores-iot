import os

from flask import Flask, jsonify
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

    # Respostas de erro sempre em JSON — a interface (extract_error) espera
    # um corpo {"message": ...}. Sem estes handlers, alguns erros (ex.: payload
    # inválido do flask-apispec/webargs) voltam como HTML e quebram a exibição.
    @app.errorhandler(422)
    def tratar_422(erro):
        dados = getattr(erro, "data", None) or {}
        mensagens = dados.get("messages") if isinstance(dados, dict) else dados
        return jsonify({
            "message": "Dados inválidos na requisição.",
            "errors": mensagens,
        }), 422

    @app.errorhandler(404)
    def tratar_404(erro):
        dados = getattr(erro, "data", None)
        mensagem = dados.get("message") if isinstance(dados, dict) else None
        return jsonify({
            "message": mensagem or "Recurso não encontrado.",
        }), 404

    api = Api(app, prefix="/telemetria")
    initialize_endpoints(api)

    return app


app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=8080, debug=debug)
