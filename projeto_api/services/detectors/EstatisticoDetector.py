import statistics

from services.detectors.DetectorAnomalia import DetectorAnomalia
from services.features import (
    forca_g_resultante,
    instabilidade_janela,
    lista_aceleracoes_longitudinais,
)


# Método 2 - Análise estatística (padrão histórico):
# calcula a média e o desvio padrão da Força G resultante do histórico da rota
# e usa o z-score. Leituras com |z-score| acima do limiar são consideradas
# significativamente diferentes do padrão de condução.
class EstatisticoDetector(DetectorAnomalia):

    LIMIAR_ZSCORE_PADRAO = 3.0

    def detectar(self, leituras, rota, limiares, historico=None):
        forcas = [forca_g_resultante(l) for l in leituras if forca_g_resultante(l) is not None]
        if len(forcas) < 2:
            return []

        limiar = float(limiares.get("zscore_max", self.LIMIAR_ZSCORE_PADRAO))

        media = statistics.mean(forcas)
        desvio = statistics.stdev(forcas)
        if desvio == 0:
            return []

        acels = lista_aceleracoes_longitudinais(leituras)
        eventos = []
        for i, leitura in enumerate(leituras):
            fg = forca_g_resultante(leitura)
            if fg is None:
                continue
            zscore = abs(fg - media) / desvio
            if zscore > limiar:
                eventos.append({
                    "leitura": leitura,
                    "canal": "forca_g",
                    "valor": fg,
                    "forca_g": fg,
                    "instabilidade": instabilidade_janela(acels, i),
                    "classificacao": "Comportamento atípico",
                    "descricao": (
                        f"Anomalia estatística da Força G: {fg:.2f} m/s² "
                        f"(z-score {zscore:.1f}, acima do limiar {limiar:.1f}) — "
                        f"desvio do padrão histórico de condução da rota."
                    ),
                })
        return eventos

    def get_metodo(self):
        return "ESTATISTICO"
