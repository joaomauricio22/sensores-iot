import statistics

from entities.Anomalia import Anomalia
from repositories.AnomaliaRepository import AnomaliaRepository
from repositories.LeituraRepository import LeituraRepository
from repositories.SensorRepository import SensorRepository
from services.detectors.LimiteDetector import LimiteDetector
from services.detectors.EstatisticoDetector import EstatisticoDetector
from services.detectors.ModeloMLDetector import ModeloMLDetector


# Camada de serviço responsável pela ANÁLISE dos dados.
#   - Executa os detectores de anomalia (limites, estatístico e ML);
#   - Registra as anomalias identificadas;
#   - Classifica leituras com o modelo de Machine Learning;
#   - Calcula padrões estatísticos do histórico (regra 10).
class AnaliseService:

    def __init__(self):
        self.__leitura_repository = LeituraRepository()
        self.__sensor_repository = SensorRepository()
        self.__anomalia_repository = AnomaliaRepository()
        # Lista de detectores (polimorfismo: todos obedecem ao mesmo contrato).
        self.__detectores = [LimiteDetector(), EstatisticoDetector(), ModeloMLDetector()]

    def __historico(self, sensor_id: int, excluir_leitura_id: int = None) -> list:
        """Valores históricos do sensor, opcionalmente excluindo a leitura avaliada."""
        leituras = self.__leitura_repository.get_by_sensor(sensor_id)
        return [l.valor for l in leituras if l.id != excluir_leitura_id]

    def analisar_leitura(self, leitura_id: int):
        """Executa os detectores sobre uma leitura e registra as anomalias."""
        leitura = self.__leitura_repository.get_by_id(leitura_id)
        if not leitura:
            return None

        sensor = self.__sensor_repository.get_by_id(leitura.sensor_id)
        historico = self.__historico(leitura.sensor_id, excluir_leitura_id=leitura.id)

        anomalias = []
        for detector in self.__detectores:
            if detector.detectar(leitura.valor, sensor, historico):
                # Evita registrar duas vezes a mesma anomalia para o mesmo método.
                if self.__anomalia_repository.get_by_leitura_metodo(
                    leitura.id, detector.get_metodo()
                ):
                    continue
                anomalia = Anomalia(
                    leitura_id=leitura.id,
                    sensor_id=leitura.sensor_id,
                    valor=leitura.valor,
                    data_hora=leitura.data_hora,
                    metodo=detector.get_metodo(),
                    descricao=f"Anomalia detectada pelo método {detector.get_metodo()}.",
                )
                self.__anomalia_repository.add(anomalia)
                anomalias.append(anomalia)

        return anomalias

    def classificar_ml(self, leitura_id: int):
        """Aplica o modelo de ML e grava a classificação na leitura (regra 8)."""
        leitura = self.__leitura_repository.get_by_id(leitura_id)
        if not leitura:
            return None

        sensor = self.__sensor_repository.get_by_id(leitura.sensor_id)
        historico = self.__historico(leitura.sensor_id, excluir_leitura_id=leitura.id)

        detector = ModeloMLDetector()
        if len(historico) < detector.MIN_AMOSTRAS:
            leitura.classificacao = "INDETERMINADO"
        else:
            leitura.classificacao = "ANOMALO" if detector.detectar(
                leitura.valor, sensor, historico
            ) else "NORMAL"

            # Se o ML sinalizar anomalia, registra com o método MODELO_ML.
            if leitura.classificacao == "ANOMALO" and not self.__anomalia_repository.get_by_leitura_metodo(
                leitura.id, "MODELO_ML"
            ):
                anomalia = Anomalia(
                    leitura_id=leitura.id,
                    sensor_id=leitura.sensor_id,
                    valor=leitura.valor,
                    data_hora=leitura.data_hora,
                    metodo="MODELO_ML",
                    descricao="Anomalia detectada pelo modelo de Machine Learning.",
                )
                self.__anomalia_repository.add(anomalia)

        return self.__leitura_repository.update(leitura)

    def estatisticas_sensor(self, sensor_id: int):
        """Calcula padrões estatísticos do histórico de um sensor (regra 10)."""
        sensor = self.__sensor_repository.get_by_id(sensor_id)
        if not sensor:
            return None

        leituras = self.__leitura_repository.get_by_sensor(sensor_id)
        valores = [l.valor for l in leituras]
        total = len(valores)

        anomalias = self.__anomalia_repository.get_by_sensor(sensor_id)

        estatisticas = {
            "sensor_id": sensor_id,
            "identificador": sensor.identificador,
            "total_leituras": total,
            "limite_min": sensor.limite_min,
            "limite_max": sensor.limite_max,
            "total_anomalias": len(anomalias),
        }

        if total > 0:
            estatisticas["minimo"] = min(valores)
            estatisticas["maximo"] = max(valores)
            estatisticas["media"] = statistics.mean(valores)
            estatisticas["desvio_padrao"] = statistics.stdev(valores) if total >= 2 else 0.0

        return estatisticas
