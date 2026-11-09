from abc import ABC, abstractmethod


# Classe abstrata que define o contrato de um detector de eventos de risco.
# Demonstra HERANÇA (as classes concretas herdam dela) e POLIMORFISMO
# (cada subclasse implementa "detectar" de uma forma diferente).
class DetectorAnomalia(ABC):

    @abstractmethod
    def detectar(self, leituras: list, rota, limiares: dict, historico: list = None) -> list:
        """Retorna a lista de eventos de risco detectados.

        Cada evento é um dict com as chaves:
          leitura       -> objeto Leitura sinalizado
          canal         -> sensor (canal) que disparou o evento; usa um nome do
                           catálogo em limiares["sensores"] ou um canal especial
                           ("geral", "forca_g", "multivariado")
          valor         -> valor medido no canal no instante do evento
          forca_g       -> Força G resultante calculada (float ou None)
          instabilidade -> instabilidade da janela (float)
          classificacao -> tipo do evento de risco (str)
          descricao     -> texto explicativo

        :param leituras: leituras da rota, em ordem cronológica.
        :param rota: rota de origem.
        :param limiares: dicionário com os limiares de detecção (configuráveis)
                         e o catálogo de sensores em limiares["sensores"].
        :param historico: leituras de outras rotas, usadas pelo modelo de ML
                          para aprender o padrão histórico (pode ser None).
        """
        raise NotImplementedError

    @abstractmethod
    def get_metodo(self) -> str:
        """Nome do método de detecção (usado no registro do evento)."""
        raise NotImplementedError
