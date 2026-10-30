"""Script de carga de dados de exemplo.

Popula o banco com tipos de sensor, sensores e leituras (normais e anômalas)
para facilitar os testes e a demonstração da detecção de anomalias.

Executar (com a API e o banco configurados):  python seed.py
"""
from datetime import datetime, timedelta

from sqlalchemy import text

from app import app
from entities.Base import db
from entities.Leitura import Leitura
from entities.Sensor import Sensor
from entities.TipoSensor import TipoSensor


def limpar():
    """Remove os dados existentes e reinicia as sequências (IDs voltam a 1)."""
    db.session.execute(
        text("TRUNCATE TABLE anomalia, leitura, sensor, tipo_sensor RESTART IDENTITY CASCADE")
    )
    db.session.commit()


def seed():
    with app.app_context():
        limpar()

        # ---- Tipos de sensor ----
        t_temp = TipoSensor(nome="Temperatura", unidade="°C", descricao="Temperatura ambiente")
        t_umid = TipoSensor(nome="Umidade", unidade="%", descricao="Umidade relativa do ar")
        db.session.add_all([t_temp, t_umid])
        db.session.commit()

        # ---- Sensores ----
        s_temp = Sensor(
            identificador="SENSOR-001", nome="Sensor Temperatura - Sala A",
            tipo_sensor_id=t_temp.id, limite_min=10.0, limite_max=40.0,
        )
        s_umid = Sensor(
            identificador="SENSOR-002", nome="Sensor Umidade - Sala A",
            tipo_sensor_id=t_umid.id, limite_min=20.0, limite_max=80.0,
        )
        db.session.add_all([s_temp, s_umid])
        db.session.commit()

        agora = datetime.now()

        # ---- Leituras normais (temperatura ~ 25°C) ----
        for i in range(30):
            valor = 25.0 + ((i % 7) - 3) * 0.6  # variação suave em torno de 25
            db.session.add(Leitura(
                sensor_id=s_temp.id, valor=round(valor, 2),
                data_hora=agora - timedelta(minutes=(30 - i) * 10),
            ))

        # ---- Leituras normais (umidade ~ 55%) ----
        for i in range(20):
            valor = 55.0 + ((i % 5) - 2) * 1.5
            db.session.add(Leitura(
                sensor_id=s_umid.id, valor=round(valor, 2),
                data_hora=agora - timedelta(minutes=(20 - i) * 10),
            ))

        # ---- Leituras anômalas (para demonstrar a detecção) ----
        db.session.add(Leitura(
            sensor_id=s_temp.id, valor=75.0,  # muito acima do limite máximo (40)
            data_hora=agora + timedelta(minutes=5),
        ))
        db.session.add(Leitura(
            sensor_id=s_temp.id, valor=-5.0,  # abaixo do limite mínimo (10)
            data_hora=agora + timedelta(minutes=6),
        ))
        db.session.add(Leitura(
            sensor_id=s_umid.id, valor=99.0,  # acima do limite máximo (80)
            data_hora=agora + timedelta(minutes=5),
        ))

        db.session.commit()

        total_leituras = db.session.query(Leitura).count()
        total_sensores = db.session.query(Sensor).count()
        print(f"Seed concluído: {total_sensores} sensores, {total_leituras} leituras.")


if __name__ == "__main__":
    seed()
