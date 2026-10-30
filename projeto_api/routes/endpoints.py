from controllers.AnomaliaController import AnomaliaItem, AnomaliaList
from controllers.LeituraController import (
    LeituraAnalise,
    LeituraClassificacao,
    LeituraItem,
    LeituraList,
)
from controllers.SensorController import SensorEstatisticas, SensorItem, SensorList
from controllers.TipoSensorController import TipoSensorItem, TipoSensorList


# Registra as rotas (URLs) que a API sabe responder.
# Cada rota está ligada a um Controller (Resource) responsável.
def initialize_endpoints(api):
    api.add_resource(TipoSensorList, "/tipos-sensor")
    api.add_resource(TipoSensorItem, "/tipos-sensor/<int:tipo_sensor_id>")

    api.add_resource(SensorList, "/sensores")
    api.add_resource(SensorItem, "/sensores/<int:sensor_id>")
    api.add_resource(SensorEstatisticas, "/sensores/<int:sensor_id>/estatisticas")

    api.add_resource(LeituraList, "/leituras")
    api.add_resource(LeituraItem, "/leituras/<int:leitura_id>")
    api.add_resource(LeituraAnalise, "/leituras/<int:leitura_id>/analisar")
    api.add_resource(LeituraClassificacao, "/leituras/<int:leitura_id>/classificar")

    api.add_resource(AnomaliaList, "/anomalias")
    api.add_resource(AnomaliaItem, "/anomalias/<int:anomalia_id>")
