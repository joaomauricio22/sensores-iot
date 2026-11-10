from marshmallow import ValidationError

from entities.EventoRisco import EventoRisco
from repositories.EventoRiscoRepository import EventoRiscoRepository
from repositories.LeituraRepository import LeituraRepository
from services.LimiaresService import LimiaresService

METODOS_VALIDOS = {"MANUAL", "LIMITE", "ESTATISTICO", "MODELO_ML"}
CANAIS_ESPECIAIS = {"geral", "forca_g", "multivariado"}


# Camada de serviço: regras de negócio e CRUD da entidade EventoRisco.
class EventoRiscoService:

    def __init__(self):
        self.__repository = EventoRiscoRepository()
        self.__leitura_repository = LeituraRepository()
        self.__limiares_service = LimiaresService()

    def get_all(self, tipo=None):
        return self.__repository.get_all(tipo)

    def get_by_id(self, evento_id):
        return self.__repository.get_by_id(evento_id)

    def get_by_rota(self, rota_id, tipo=None):
        return self.__repository.get_by_rota(rota_id, tipo)

    def add(self, leitura_id: int, metodo: str, rota_id: int = None,
            data_hora=None, canal: str = None, valor=None, forca_g=None,
            instabilidade=None, classificacao=None, descricao=None) -> EventoRisco:
        leitura = self.__validar_leitura(leitura_id, rota_id, data_hora)
        metodo = self.__validar_metodo(metodo)
        canal = self.__validar_canal(canal)
        classificacao = self.__validar_classificacao(classificacao)
        descricao = self.__validar_descricao(descricao)

        evento = EventoRisco(
            leitura_id=leitura.id,
            rota_id=leitura.rota_id,
            data_hora=leitura.data_hora,
            metodo=metodo,
            canal=canal,
            valor=valor,
            forca_g=forca_g,
            instabilidade=instabilidade,
            classificacao=classificacao,
            descricao=descricao,
        )
        return self.__repository.add(evento)

    def update(self, evento_id: int, leitura_id: int, metodo: str,
               rota_id: int = None, data_hora=None, canal: str = None,
               valor=None, forca_g=None, instabilidade=None,
               classificacao=None, descricao=None):
        evento = self.__repository.get_by_id(evento_id)
        if not evento:
            return None

        leitura = self.__validar_leitura(leitura_id, rota_id, data_hora)
        metodo = self.__validar_metodo(metodo)
        canal = self.__validar_canal(canal)
        classificacao = self.__validar_classificacao(classificacao)
        descricao = self.__validar_descricao(descricao)

        evento.leitura_id = leitura.id
        evento.rota_id = leitura.rota_id
        evento.data_hora = leitura.data_hora
        evento.metodo = metodo
        evento.canal = canal
        evento.valor = valor
        evento.forca_g = forca_g
        evento.instabilidade = instabilidade
        evento.classificacao = classificacao
        evento.descricao = descricao
        return self.__repository.update(evento)

    def delete(self, evento_id: int):
        evento = self.__repository.get_by_id(evento_id)
        if not evento:
            return None
        return self.__repository.delete(evento)

    # ------------------------------------------------------------------ #
    # Validações
    # ------------------------------------------------------------------ #
    def __validar_leitura(self, leitura_id, rota_id, data_hora):
        if leitura_id is None:
            raise ValidationError("A leitura é obrigatória.")
        leitura = self.__leitura_repository.get_by_id(leitura_id)
        if leitura is None:
            raise ValidationError("A leitura informada não está cadastrada.")
        if rota_id is not None and rota_id != leitura.rota_id:
            raise ValidationError("A rota informada não corresponde à rota da leitura.")
        if data_hora is not None and data_hora != leitura.data_hora:
            raise ValidationError("A data/hora informada não corresponde à data/hora da leitura.")
        return leitura

    def __validar_metodo(self, metodo):
        if not metodo or not str(metodo).strip():
            raise ValidationError("O método de identificação é obrigatório.")
        metodo = str(metodo).strip()
        if metodo not in METODOS_VALIDOS:
            raise ValidationError(
                "Método inválido. Use um destes: MANUAL, LIMITE, ESTATISTICO ou MODELO_ML."
            )
        return metodo

    def __validar_canal(self, canal):
        canal = str(canal).strip() if canal and str(canal).strip() else "geral"
        if canal in CANAIS_ESPECIAIS:
            return canal
        if canal not in self.__limiares_service.get_sensores():
            raise ValidationError(
                f"Canal '{canal}' não cadastrado. Use um sensor do catálogo "
                "ou um dos canais especiais: geral, forca_g, multivariado."
            )
        return canal

    def __validar_classificacao(self, classificacao):
        classificacao = str(classificacao).strip() if classificacao else ""
        if not classificacao:
            return "Comportamento atípico"
        if len(classificacao) > 40:
            raise ValidationError("A classificação deve ter no máximo 40 caracteres.")
        return classificacao

    def __validar_descricao(self, descricao):
        if descricao is None:
            return None
        descricao = str(descricao).strip()
        if len(descricao) > 255:
            raise ValidationError("A descrição deve ter no máximo 255 caracteres.")
        return descricao
