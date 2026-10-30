from abc import ABC, abstractmethod


# Classe abstrata que define o contrato de um detector de anomalias.
# Demonstra os conceitos de HERANÇA (as classes concretas herdam dela) e
# POLIMORFISMO (cada subclasse implementa "detectar" de uma forma diferente).
class DetectorAnomalia(ABC):

    @abstractmethod
    def detectar(self, valor: float, sensor, historico: list) -> bool:
        """Retorna True se o valor for considerado potencialmente anômalo.

        :param valor: valor medido que será avaliado.
        :param sensor: sensor de origem da leitura (para acessar limites e tipo).
        :param historico: lista de valores históricos do sensor (sem a leitura atual).
        """
        raise NotImplementedError

    @abstractmethod
    def get_metodo(self) -> str:
        """Nome do método de detecção (usado no registro da anomalia)."""
        raise NotImplementedError
