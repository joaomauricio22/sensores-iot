from controllers.EventoRiscoController import EventoRiscoItem, EventoRiscoList
from controllers.LeituraController import LeituraItem, LeituraList
from controllers.MapeamentoController import MapeamentoItem, MapeamentoList
from controllers.ParametroController import ParametroItem, ParametroList
from controllers.VeiculoController import (
    VeiculoAnalise,
    VeiculoEstatisticas,
    VeiculoItem,
    VeiculoList,
)


# Registra as rotas (URLs) que a API sabe responder.
def initialize_endpoints(api):
    api.add_resource(ParametroList, "/parametros")
    api.add_resource(ParametroItem, "/parametros/<int:parametro_id>")

    api.add_resource(VeiculoList, "/veiculos")
    api.add_resource(VeiculoItem, "/veiculos/<int:veiculo_id>")
    api.add_resource(VeiculoEstatisticas, "/veiculos/<int:veiculo_id>/estatisticas")
    api.add_resource(VeiculoAnalise, "/veiculos/<int:veiculo_id>/analisar")

    api.add_resource(MapeamentoList, "/mapeamentos")
    api.add_resource(MapeamentoItem, "/mapeamentos/<int:mapeamento_id>")

    api.add_resource(LeituraList, "/leituras")
    api.add_resource(LeituraItem, "/leituras/<int:leitura_id>")

    api.add_resource(EventoRiscoList, "/eventos-risco")
    api.add_resource(EventoRiscoItem, "/eventos-risco/<int:evento_id>")
