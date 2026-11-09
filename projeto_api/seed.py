"""Seed opcional do sistema de telemetria veicular.

Importa os arquivos CSV da pasta `dados/` como rotas. O programa NÃO executa
este script automaticamente: o banco começa vazio e a primeira rota cadastrada
recebe o id 1.

Uso:
    python seed.py            # importa apenas se o banco estiver vazio
    python seed.py --reset    # apaga todas as rotas/leituras/eventos e reimporta

Os CSVs não fazem parte do repositório (pasta `dados/` é ignorada pelo Git).
"""
import os
import sys

from sqlalchemy import text

from app import app
from entities.Base import db
from entities.Rota import Rota
from services.ImportadorService import ImportadorService

DADOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")

# Arquivos CSV -> nome amigável da rota.
ARQUIVOS = [
    ("CSVLog_20260121_084120.csv", "Rota 1"),
    ("CSVLog_20260121_085814.csv", "Rota 2"),
    ("CSVLog_20260121_152135.csv", "Rota 3"),
    ("OBDLink.csv", "Rota 4"),
]


def seed(reset: bool = False):
    with app.app_context():
        if reset:
            db.session.execute(text(
                "TRUNCATE TABLE evento_risco, leitura, rota RESTART IDENTITY CASCADE"
            ))
            db.session.commit()
            print("Banco limpo (sequências reiniciadas em 1).")

        if db.session.query(Rota).first() is not None:
            print("O banco já possui rotas. Use 'python seed.py --reset' para reimportar.")
            return

        importador = ImportadorService()
        for arquivo, nome in ARQUIVOS:
            caminho = os.path.join(DADOS_DIR, arquivo)
            if not os.path.exists(caminho):
                print(f"Arquivo não encontrado: {caminho}")
                continue
            with open(caminho, encoding="utf-8-sig", errors="replace") as fh:
                conteudo = fh.read()
            resultado = importador.importar_csv(
                nome, os.path.basename(caminho), conteudo
            )
            print(
                f"{nome} ({arquivo}): {resultado['total_leituras']} leituras "
                f"(id {resultado['rota_id']})."
            )


if __name__ == "__main__":
    seed(reset="--reset" in sys.argv)
