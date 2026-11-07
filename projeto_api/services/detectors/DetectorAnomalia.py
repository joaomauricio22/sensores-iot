from abc import ABC, abstractmethod


# Classe abstrata que define o contrato de um detector de eventos de risco.
# Demonstra HERANÇA (as classes concretas herdam dela) e POLIMORFISMO
# (cada subclasse implementa "detectar" de uma forma diferente).
class DetectorAnomalia(ABC):

    @abstractmethod
    def detectar(self, leituras: list, rota) -> list:
        """Retorna a lista de eventos de risco detectados.

        Cada evento é um dict com as chaves:
          leitura       -> objeto Leitura sinalizado
          forca_g       -> Força G resultante calculada (float ou None)
          instabilidade -> instabilidade da janela (float)
          descricao     -> texto explicativo

        :param leituras: leituras da rota, em ordem cronológica.
        :param rota: rota de origem.
        """
        raise NotImplementedError

    @abstractmethod
    def get_metodo(self) -> str:
        """Nome do método de detecção (usado no registro do evento)."""
        raise NotImplementedError
