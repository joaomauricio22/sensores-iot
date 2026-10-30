# Importa todas as entidades para que o SQLAlchemy registre
# os modelos no metadata (necessário para refletir/criar as tabelas).
from entities.TipoSensor import TipoSensor
from entities.Sensor import Sensor
from entities.Leitura import Leitura
from entities.Anomalia import Anomalia

__all__ = ["TipoSensor", "Sensor", "Leitura", "Anomalia"]
