"""Seed do sistema de telemetria veicular.

Cria os parâmetros canônicos, os mapeamentos de padronização e importa
os arquivos CSV reais de telemetria OBD-II.

Executar:  python seed.py
"""
import os

from sqlalchemy import text

from app import app
from entities.Base import db
from entities.MapeamentoParametro import MapeamentoParametro
from entities.Parametro import Parametro
from repositories.MapeamentoParametroRepository import MapeamentoParametroRepository
from repositories.ParametroRepository import ParametroRepository
from services.ImportadorService import ImportadorService

# Parâmetros canônicos (apenas os que agregam valor à análise de risco).
PARAMETROS = [
    ("velocidade", "km/h", 0.0, 220.0),
    ("rpm", "RPM", 0.0, 8000.0),
    ("accel_x", "m/s²", -30.0, 30.0),
    ("accel_y", "m/s²", -30.0, 30.0),
    ("accel_z", "m/s²", -30.0, 30.0),
    ("posicao_acelerador", "%", 0.0, 100.0),
    ("latitude", "deg", -90.0, 90.0),
    ("longitude", "deg", -180.0, 180.0),
]

# Padronização: nome bruto (do arquivo) -> parâmetro canônico.
MAPEAMENTOS = [
    ("Velocidade do veículo (km/h)", "velocidade"),
    ("Vehicle speed (km/h)", "velocidade"),
    ("RPM do motor (RPM)", "rpm"),
    ("Engine RPM (RPM)", "rpm"),
    ("Aceleração X (m/s²)", "accel_x"),
    ("Accel X (m/s²)", "accel_x"),
    ("Acelere Y (m/s²)", "accel_y"),
    ("Accel Y (m/s²)", "accel_y"),
    ("Aceleração Z (m/s²)", "accel_z"),
    ("Accel Z (m/s²)", "accel_z"),
    ("Posição absoluta do acelerador (%)", "posicao_acelerador"),
    ("Absolute throttle position (%)", "posicao_acelerador"),
    ("Latitude (deg)", "latitude"),
    ("Longitude (deg)", "longitude"),
]

# Arquivos CSV -> (identificador do veículo, modelo).
DADOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")
ARQUIVOS = [
    (os.path.join(DADOS_DIR, "CSVLog_20260121_084120.csv"), "VEICULO-001", "CSVLog"),
    (os.path.join(DADOS_DIR, "CSVLog_20260121_085814.csv"), "VEICULO-002", "CSVLog"),
    (os.path.join(DADOS_DIR, "CSVLog_20260121_152135.csv"), "VEICULO-003", "CSVLog"),
    (os.path.join(DADOS_DIR, "OBDLink.csv"), "VEICULO-004", "OBDLink"),
]


def seed():
    with app.app_context():
        # Limpa tudo (respeitando a ordem das FKs) e reinicia as sequências.
        db.session.execute(text(
            "TRUNCATE TABLE evento_risco, leitura, mapeamento_parametro, parametro, veiculo "
            "RESTART IDENTITY CASCADE"
        ))
        db.session.commit()

        param_repo = ParametroRepository()
        ids = {}
        for nome, unidade, lmin, lmax in PARAMETROS:
            p = param_repo.add(Parametro(nome=nome, unidade=unidade, limite_min=lmin, limite_max=lmax))
            ids[nome] = p.id

        map_repo = MapeamentoParametroRepository()
        for nome_bruto, parametro in MAPEAMENTOS:
            map_repo.add(MapeamentoParametro(nome_bruto=nome_bruto, parametro_id=ids[parametro]))

        importador = ImportadorService()
        for caminho, identificador, modelo in ARQUIVOS:
            resultado = importador.importar_csv(caminho, identificador, modelo)
            print(f"{identificador}: {resultado['total_importadas']} leituras importadas.")

        from entities.Leitura import Leitura
        from entities.Veiculo import Veiculo
        print(f"Total: {db.session.query(Veiculo).count()} veículos, "
              f"{db.session.query(Leitura).count()} leituras.")


if __name__ == "__main__":
    seed()
