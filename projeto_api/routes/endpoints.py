from controllers.ConfiguracaoController import (
    ConfiguracaoItem,
    ConfiguracaoLimiares,
    ConfiguracaoList,
)
from controllers.EventoRiscoController import EventoRiscoItem, EventoRiscoList
from controllers.LeituraController import LeituraItem, LeituraList
from controllers.RotaController import (
    RotaAnalisar,
    RotaComparar,
    RotaGrafico,
    RotaImportar,
    RotaItem,
    RotaList,
    RotaResumo,
)
from controllers.UsuarioController import UsuarioItem, UsuarioList, UsuarioLogin


# Registra as rotas (URLs) que a API sabe responder.
def initialize_endpoints(api):
    api.add_resource(UsuarioList, "/usuarios")
    api.add_resource(UsuarioLogin, "/usuarios/login")
    api.add_resource(UsuarioItem, "/usuarios/<int:usuario_id>")

    api.add_resource(RotaList, "/rotas")
    api.add_resource(RotaImportar, "/rotas/importar")
    api.add_resource(RotaComparar, "/rotas/comparar")
    api.add_resource(RotaItem, "/rotas/<int:rota_id>")
    api.add_resource(RotaAnalisar, "/rotas/<int:rota_id>/analisar")
    api.add_resource(RotaGrafico, "/rotas/<int:rota_id>/grafico")
    api.add_resource(RotaResumo, "/rotas/<int:rota_id>/resumo")

    api.add_resource(LeituraList, "/leituras")
    api.add_resource(LeituraItem, "/leituras/<int:leitura_id>")

    api.add_resource(EventoRiscoList, "/eventos-risco")
    api.add_resource(EventoRiscoItem, "/eventos-risco/<int:evento_id>")

    api.add_resource(ConfiguracaoList, "/configuracoes")
    api.add_resource(ConfiguracaoLimiares, "/configuracoes/limiares")
    api.add_resource(ConfiguracaoItem, "/configuracoes/<int:config_id>")
