from services.detectors.DetectorAnomalia import DetectorAnomalia


# Método 1 - Limites de operação:
# considera anômalo um valor fora dos limites mínimo/máximo de referência do sensor.
class LimiteDetector(DetectorAnomalia):

    def detectar(self, valor, sensor, historico):
        return valor < sensor.limite_min or valor > sensor.limite_max

    def get_metodo(self):
        return "LIMITE"
