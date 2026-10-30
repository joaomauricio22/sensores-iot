import numpy as np
from sklearn.ensemble import IsolationForest

from services.detectors.DetectorAnomalia import DetectorAnomalia


# Método 3 - Modelo de Machine Learning:
# treina um IsolationForest (detecção de anomalias não supervisionada) com o
# histórico do sensor e classifica a nova leitura como normal ou anômala.
class ModeloMLDetector(DetectorAnomalia):

    MIN_AMOSTRAS = 10

    def detectar(self, valor, sensor, historico):
        # O modelo precisa de uma quantidade mínima de dados para ser treinado.
        if len(historico) < self.MIN_AMOSTRAS:
            return False

        X = np.array(historico, dtype=float).reshape(-1, 1)
        modelo = IsolationForest(contamination=0.1, random_state=42)
        modelo.fit(X)

        # O modelo retorna -1 (anomalia) ou 1 (normal).
        predicao = modelo.predict([[float(valor)]])[0]
        return predicao == -1

    def get_metodo(self):
        return "MODELO_ML"
