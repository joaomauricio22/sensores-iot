import os


# Configuração central da aplicação.
# A conexão com o banco pode ser sobrescrita pela variável de ambiente DATABASE_URI.
class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URI",
        "postgresql://postgres:admin@localhost:5432/iot_sensores",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
