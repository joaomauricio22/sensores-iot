"""Seed do sistema de telemetria veicular.

Importa os arquivos CSV de telemetria como "rotas" para o primeiro usuário
cadastrado (que deve ser criado pela interface, na tela de cadastro).

Executar:  python seed.py
"""
import os

from sqlalchemy import text

from app import app
from entities.Base import db
from entities.Usuario import Usuario
from services.ImportadorService import ImportadorService

DADOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")

# Arquivos CSV -> nome amigável da rota.
ARQUIVOS = [
    (os.path.join(DADOS_DIR, "CSVLog_20260121_084120.csv"), "Rota 1"),
    (os.path.join(DADOS_DIR, "CSVLog_20260121_085814.csv"), "Rota 2"),
    (os.path.join(DADOS_DIR, "CSVLog_20260121_152135.csv"), "Rota 3"),
    (os.path.join(DADOS_DIR, "OBDLink.csv"), "Rota 4"),
]


def seed():
    with app.app_context():
        db.session.execute(text(
            "TRUNCATE TABLE evento_risco, leitura, rota RESTART IDENTITY CASCADE"
        ))
        db.session.commit()

        usuario = db.session.query(Usuario).order_by(Usuario.id).first()
        if not usuario:
            print("Nenhum usuário cadastrado. Cadastre um usuário pela interface antes de importar.")
            return

        importador = ImportadorService()
        for caminho, nome in ARQUIVOS:
            if not os.path.exists(caminho):
                print(f"Arquivo não encontrado: {caminho}")
                continue
            with open(caminho, encoding="utf-8-sig", errors="replace") as fh:
                conteudo = fh.read()
            resultado = importador.importar_csv(usuario.id, nome, os.path.basename(caminho), conteudo)
            print(f"{nome} ({os.path.basename(caminho)}): {resultado['total_leituras']} leituras.")


if __name__ == "__main__":
    seed()
