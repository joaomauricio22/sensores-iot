from services.detectors.DetectorAnomalia import DetectorAnomalia
from services.features import forca_g, instabilidade_janela


# Método 1 - Limite físico:
# considera evento de risco uma leitura cuja Força G resultante ultrapassa
# um limiar de referência (manobras agressivas: frenagem/aceleração/curva bruscas).
class LimiteDetector(DetectorAnomalia):

    LIMIAR_FORCA_G = 0.5  # em g

    def detectar(self, leituras, veiculo):
        eventos = []
        for i, leitura in enumerate(leituras):
            fg = forca_g(leitura)
            if fg is None:
                continue
            if fg > self.LIMIAR_FORCA_G:
                eventos.append({
                    "leitura": leitura,
                    "forca_g": fg,
                    "instabilidade": instabilidade_janela(leituras, i),
                    "descricao": f"Força G de {fg:.2f}g acima do limiar de {self.LIMIAR_FORCA_G}g.",
                })
        return eventos

    def get_metodo(self):
        return "LIMITE"
