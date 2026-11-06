from marshmallow import ValidationError

from entities.EventoRisco import EventoRisco
from repositories.EventoRiscoRepository import EventoRiscoRepository

# Métodos de detecção aceitos pelo sistema.
METODOS_VALIDOS = {"LIMITE", "ESTATISTICO", "MODELO_ML"}


# Camada de serviço: regras de negócio e CRUD da entidade EventoRisco.
# Em uso normal os eventos são gerados automaticamente pela análise,
# mas a entidade também expõe as operações de CRUD (exigência do trabalho).
class EventoRiscoService:

    def __init__(self):
        self.__repository = EventoRiscoRepository()

    def get_all(self):
        return self.__repository.get_all()

    def get_by_id(self, evento_id):
        return self.__repository.get_by_id(evento_id)

    def add(self, leitura_id: int, veiculo_id: int, data_hora, metodo: str,
            forca_g=None, instabilidade=None, classificacao=None, descricao=None) -> EventoRisco:
        if leitura_id is None or veiculo_id is None:
            raise ValidationError("A leitura e o veículo são obrigatórios.")
        if data_hora is None:
            raise ValidationError("A data/hora é obrigatória.")
        if not metodo or not str(metodo).strip():
            raise ValidationError("O método de identificação é obrigatório.")
        if metodo not in METODOS_VALIDOS:
            raise ValidationError("Método inválido. Use um destes: LIMITE, ESTATISTICO ou MODELO_ML.")

        evento = EventoRisco(
            leitura_id=leitura_id,
            veiculo_id=veiculo_id,
            data_hora=data_hora,
            metodo=metodo,
            forca_g=forca_g,
            instabilidade=instabilidade,
            classificacao=classificacao,
            descricao=descricao,
        )
        return self.__repository.add(evento)

    def update(self, evento_id: int, leitura_id: int, veiculo_id: int, data_hora,
               metodo: str, forca_g=None, instabilidade=None, classificacao=None, descricao=None):
        evento = self.__repository.get_by_id(evento_id)
        if not evento:
            return None
        if metodo not in METODOS_VALIDOS:
            raise ValidationError("Método inválido. Use um destes: LIMITE, ESTATISTICO ou MODELO_ML.")
        evento.leitura_id = leitura_id
        evento.veiculo_id = veiculo_id
        evento.data_hora = data_hora
        evento.metodo = metodo
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
