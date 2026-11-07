from services.detectors.DetectorAnomalia import DetectorAnomalia
from services.features import (
    aceleracao_longitudinal,
    forca_g_resultante,
    instabilidade_janela,
    lista_aceleracoes_longitudinais,
)


# Método 1 - Limites físicos (Código de Trânsito Brasileiro - CTB):
# considera evento de risco uma leitura cuja aceleração longitudinal
# ultrapassa +2,5 m/s² (aceleração brusca) ou fica abaixo de -3,0 m/s² (frenagem brusca).
class LimiteDetector(DetectorAnomalia):

    LIMITE_ACELERACAO = 2.5   # m/s²
    LIMITE_FRENAGEM = -3.0    # m/s²

    def detectar(self, leituras, rota):
        acels = lista_aceleracoes_longitudinais(leituras)
        eventos = []
        for i, leitura in enumerate(leituras):
            acel = acels[i]
            if acel > self.LIMITE_ACELERACAO or acel < self.LIMITE_FRENAGEM:
                eventos.append({
                    "leitura": leitura,
                    "forca_g": forca_g_resultante(leitura),
                    "instabilidade": instabilidade_janela(acels, i),
                    "descricao": (
                        f"Aceleração longitudinal de {acel:.2f} m/s² "
                        f"(limite CTB: {self.LIMITE_FRENAGEM} a {self.LIMITE_ACELERACAO} m/s²)."
                    ),
                })
        return eventos

    def get_metodo(self):
        return "LIMITE"
