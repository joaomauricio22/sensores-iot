# Importa todas as entidades para que o SQLAlchemy registre
# os modelos no metadata (necessário para refletir/criar as tabelas).
from entities.Veiculo import Veiculo
from entities.Parametro import Parametro
from entities.MapeamentoParametro import MapeamentoParametro
from entities.Leitura import Leitura
from entities.EventoRisco import EventoRisco

__all__ = ["Veiculo", "Parametro", "MapeamentoParametro", "Leitura", "EventoRisco"]
