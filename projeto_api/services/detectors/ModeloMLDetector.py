import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from services.detectors.DetectorAnomalia import DetectorAnomalia
from services.features import (
    forca_g_resultante,
    instabilidade_janela,
    lista_aceleracoes_longitudinais,
    media_janela,
)


# Método 3 - Modelo de Machine Learning (DBSCAN + RandomForest):
# combina aprendizado não supervisionado e supervisionado:
#   1. extrai atributos por leitura (aceleração média, instabilidade, aceleração lateral, Força G);
#   2. normaliza com StandardScaler;
#   3. DBSCAN separa condução normal (cluster denso) de eventos de risco (-1) — pseudo-rótulos;
#   4. RandomForest aprende a classificar e sinaliza os eventos de risco.
class ModeloMLDetector(DetectorAnomalia):

    MIN_AMOSTRAS = 30

    def detectar(self, leituras, rota):
        if len(leituras) < self.MIN_AMOSTRAS:
            return []

        acels = lista_aceleracoes_longitudinais(leituras)

        matriz = []
        validas = []
        for i, leitura in enumerate(leituras):
            fg = forca_g_resultante(leitura)
            if fg is None:
                continue
            acel_y = leitura.accel_y if leitura.accel_y is not None else 0.0
            matriz.append([
                media_janela(acels, i),          # aceleração média (3s)
                instabilidade_janela(acels, i),  # instabilidade (3s)
                acel_y,                          # aceleração lateral
                fg,                              # Força G resultante
            ])
            validas.append(leitura)

        if len(matriz) < self.MIN_AMOSTRAS:
            return []

        X = StandardScaler().fit_transform(np.array(matriz))

        # DBSCAN: pseudo-rotulagem (cluster denso = normal, -1 = risco/ruído).
        labels = DBSCAN(eps=1.0, min_samples=15).fit(X).labels_
        y = np.where(labels == -1, 1, 0)  # 1 = risco, 0 = normal

        # Sem as duas classes, não há como treinar o classificador.
        if len(set(y.tolist())) < 2:
            return []

        modelo = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo.fit(X, y)
        pred = modelo.predict(X)

        eventos = []
        for i, leitura in enumerate(validas):
            if pred[i] == 1:
                eventos.append({
                    "leitura": leitura,
                    "forca_g": matriz[i][3],
                    "instabilidade": matriz[i][1],
                    "descricao": "Evento de risco classificado pelo modelo DBSCAN + RandomForest.",
                })
        return eventos

    def get_metodo(self):
        return "MODELO_ML"
