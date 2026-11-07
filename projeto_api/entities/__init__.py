# Importa todas as entidades para que o SQLAlchemy registre
# os modelos no metadata (necessário para refletir/criar as tabelas).
from entities.Usuario import Usuario
from entities.Rota import Rota
from entities.Leitura import Leitura
from entities.EventoRisco import EventoRisco
from entities.Configuracao import Configuracao

__all__ = ["Usuario", "Rota", "Leitura", "EventoRisco", "Configuracao"]
