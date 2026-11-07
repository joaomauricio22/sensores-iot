from marshmallow import ValidationError

from entities.Configuracao import Configuracao
from repositories.ConfiguracaoRepository import ConfiguracaoRepository


# Limiares padrão de detecção de risco (sobrescrevíveis pela tabela configuracao).
LIMIARES_PADRAO = {
    "velocidade_max": 100.0,       # km/h
    "rpm_max": 5000.0,             # RPM
    "aceleracao_max": 2.5,         # m/s²
    "frenagem_max": -3.0,          # m/s²
    "lateral_max": 3.0,            # m/s²
    "curva_velocidade_min": 30.0,  # km/h
    "acelerador_delta_max": 15.0,  # % por segundo
}


# Camada de serviço: gerencia as configurações (limiares) do sistema.
class ConfiguracaoService:

    def __init__(self):
        self.__repository = ConfiguracaoRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, config_id):
        return self.__repository.get_by_id(config_id)

    def add(self, chave: str, valor) -> Configuracao:
        if not chave or not str(chave).strip():
            raise ValidationError("A chave da configuração é obrigatória.")
        if self.__repository.get_by_chave(chave):
            raise ValidationError("Já existe uma configuração com essa chave.")
        return self.__repository.add(Configuracao(chave=chave, valor=str(valor)))

    def update(self, config_id: int, chave: str = None, valor=None) -> Configuracao:
        config = self.__repository.get_by_id(config_id)
        if not config:
            return None
        if chave and str(chave).strip():
            config.chave = chave
        if valor is not None:
            config.valor = str(valor)
        return self.__repository.update(config)

    def delete(self, config_id: int):
        config = self.__repository.get_by_id(config_id)
        if not config:
            return None
        return self.__repository.delete(config)

    def get_limiares(self) -> dict:
        """Retorna os limiares atuais (padrão + sobreposições da tabela)."""
        limiares = dict(LIMIARES_PADRAO)
        for c in self.__repository.get_all():
            if c.chave in limiares:
                try:
                    limiares[c.chave] = float(c.valor)
                except ValueError:
                    pass
        return limiares

    def set_limiares(self, limiares: dict) -> dict:
        """Atualiza vários limiares de uma vez (apenas os reconhecidos)."""
        atualizados = {}
        for chave, valor in limiares.items():
            if chave not in LIMIARES_PADRAO:
                continue
            try:
                valor_float = float(valor)
            except (TypeError, ValueError):
                raise ValidationError(f"Valor inválido para '{chave}': {valor}.")
            config = self.__repository.get_by_chave(chave)
            if config:
                config.valor = str(valor_float)
                self.__repository.update(config)
            else:
                self.__repository.add(Configuracao(chave=chave, valor=str(valor_float)))
            atualizados[chave] = valor_float
        return atualizados
