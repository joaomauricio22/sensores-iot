import statistics

from services.detectors.DetectorAnomalia import DetectorAnomalia


# Método 2 - Análise estatística (padrão histórico):
# calcula a média e o desvio padrão do histórico do sensor e usa o z-score.
# Um valor com |z-score| maior que o limiar é considerado significativamente
# diferente do padrão histórico (comportamento anômalo).
class EstatisticoDetector(DetectorAnomalia):

    LIMIAR_ZSCORE = 3.0

    def detectar(self, valor, sensor, historico):
        # Precisa de ao menos 2 leituras históricas para calcular o desvio padrão.
        if len(historico) < 2:
            return False

        media = statistics.mean(historico)
        desvio = statistics.stdev(historico)

        # Se não há variação no histórico, não há como avaliar desvio.
        if desvio == 0:
            return False

        zscore = abs(valor - media) / desvio
        return zscore > self.LIMIAR_ZSCORE

    def get_metodo(self):
        return "ESTATISTICO"
