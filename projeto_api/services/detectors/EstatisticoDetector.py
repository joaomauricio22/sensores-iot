import statistics

from services.detectors.DetectorAnomalia import DetectorAnomalia
from services.features import forca_g, instabilidade_janela


# Método 2 - Análise estatística (padrão histórico):
# calcula a média e o desvio padrão da Força G do histórico do veículo e usa o
# z-score. Leituras com |z-score| acima do limiar são consideradas significativamente
# diferentes do padrão de condução (comportamento de risco).
class EstatisticoDetector(DetectorAnomalia):

    LIMIAR_ZSCORE = 3.0

    def detectar(self, leituras, veiculo):
        forcas = [forca_g(l) for l in leituras if forca_g(l) is not None]
        if len(forcas) < 2:
            return []

        media = statistics.mean(forcas)
        desvio = statistics.stdev(forcas)
        if desvio == 0:
            return []

        eventos = []
        for i, leitura in enumerate(leituras):
            fg = forca_g(leitura)
            if fg is None:
                continue
            zscore = abs(fg - media) / desvio
            if zscore > self.LIMIAR_ZSCORE:
                eventos.append({
                    "leitura": leitura,
                    "forca_g": fg,
                    "instabilidade": instabilidade_janela(leituras, i),
                    "descricao": f"Força G de {fg:.2f}g com z-score {zscore:.1f} (acima de {self.LIMIAR_ZSCORE}).",
                })
        return eventos

    def get_metodo(self):
        return "ESTATISTICO"
