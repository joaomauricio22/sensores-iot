import statistics

from entities.Base import db
from entities.EventoRisco import EventoRisco
from repositories.EventoRiscoRepository import EventoRiscoRepository
from repositories.LeituraRepository import LeituraRepository
from repositories.VeiculoRepository import VeiculoRepository
from services.detectors.LimiteDetector import LimiteDetector
from services.detectors.EstatisticoDetector import EstatisticoDetector
from services.detectors.ModeloMLDetector import ModeloMLDetector
from services.features import forcas_g


# Camada de serviço responsável pela ANÁLISE da telemetria.
#   - Executa os detectores de risco (limite, estatístico e ML);
#   - Registra os eventos de risco identificados;
#   - Calcula indicadores do histórico de condução (regra 10).
class AnaliseService:

    def __init__(self):
        self.__leitura_repository = LeituraRepository()
        self.__veiculo_repository = VeiculoRepository()
        self.__evento_repository = EventoRiscoRepository()
        # Lista de detectores (polimorfismo: todos obedecem ao mesmo contrato).
        self.__detectores = [LimiteDetector(), EstatisticoDetector(), ModeloMLDetector()]

    def analisar_veiculo(self, veiculo_id: int):
        """Executa os detectores sobre o histórico de um veículo e registra os eventos."""
        veiculo = self.__veiculo_repository.get_by_id(veiculo_id)
        if not veiculo:
            return None

        leituras = self.__leitura_repository.get_by_veiculo(veiculo_id)

        # 1. Executa todos os detectores (sem commitar, para não expirar os objetos).
        detectados = []
        for detector in self.__detectores:
            for evento in detector.detectar(leituras, veiculo):
                detectados.append((detector.get_metodo(), evento))

        # 2. Conjunto de eventos já existentes para evitar duplicatas.
        existentes = {(e.leitura_id, e.metodo) for e in self.__evento_repository.get_by_veiculo(veiculo_id)}

        # 3. Monta os novos eventos de risco.
        novos = []
        for metodo, evento in detectados:
            leitura = evento["leitura"]
            if (leitura.id, metodo) in existentes:
                continue
            existentes.add((leitura.id, metodo))
            novos.append(EventoRisco(
                leitura_id=leitura.id,
                veiculo_id=veiculo_id,
                data_hora=leitura.data_hora,
                metodo=metodo,
                forca_g=evento.get("forca_g"),
                instabilidade=evento.get("instabilidade"),
                classificacao="RISCO",
                descricao=evento.get("descricao"),
            ))

        # 4. Persiste em lote (uma única transação).
        db.session.add_all(novos)
        db.session.commit()

        return novos

    def estatisticas_veiculo(self, veiculo_id: int):
        """Calcula indicadores do histórico de condução de um veículo (regra 10)."""
        veiculo = self.__veiculo_repository.get_by_id(veiculo_id)
        if not veiculo:
            return None

        leituras = self.__leitura_repository.get_by_veiculo(veiculo_id)
        forcas = forcas_g(leituras)
        eventos = self.__evento_repository.get_by_veiculo(veiculo_id)

        estatisticas = {
            "veiculo_id": veiculo_id,
            "identificador": veiculo.identificador,
            "total_leituras": len(leituras),
            "total_eventos": len(eventos),
        }
        if forcas:
            estatisticas["forca_g_media"] = statistics.mean(forcas)
            estatisticas["forca_g_maxima"] = max(forcas)
            estatisticas["forca_g_desvio"] = statistics.stdev(forcas) if len(forcas) >= 2 else 0.0

        return estatisticas
