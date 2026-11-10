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
#
# O treinamento usa as leituras das OUTRAS rotas (histórico). Quando ainda não
# há histórico suficiente, usa a própria rota como fallback (regra 10).
class ModeloMLDetector(DetectorAnomalia):

    MIN_AMOSTRAS = 30

    def detectar(self, leituras, rota, limiares, historico=None):
        matriz_alvo, validas = self.__extrair_matriz(leituras)
        if len(matriz_alvo) == 0:
            return []

        matriz_treino, _ = self.__extrair_matriz(historico or [])
        if len(matriz_treino) < self.MIN_AMOSTRAS:
            # Fallback: aprende o padrão da própria rota.
            matriz_treino = matriz_alvo

        if len(matriz_treino) < self.MIN_AMOSTRAS:
            return []

        normalizador = StandardScaler().fit(np.array(matriz_treino))
        X_treino = normalizador.transform(np.array(matriz_treino))
        X_alvo = normalizador.transform(np.array(matriz_alvo))

        # DBSCAN: pseudo-rotulagem (cluster denso = normal, -1 = risco/ruído).
        labels = DBSCAN(eps=1.0, min_samples=15).fit(X_treino).labels_
        y = np.where(labels == -1, 1, 0)  # 1 = risco, 0 = normal

        # Sem as duas classes, não há como treinar o classificador.
        if len(set(y.tolist())) < 2:
            return []

        modelo = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo.fit(X_treino, y)
        pred = modelo.predict(X_alvo)

        eventos = []
        for i, leitura in enumerate(validas):
            if pred[i] == 1:
                eventos.append({
                    "leitura": leitura,
                    "canal": "multivariado",
                    "valor": matriz_alvo[i][3],
                    "forca_g": matriz_alvo[i][3],
                    "instabilidade": matriz_alvo[i][1],
                    "classificacao": "Comportamento atípico",
                    "descricao": (
                        "Anomalia multivariada detectada pelo modelo de ML "
                        "(DBSCAN + RandomForest) a partir da combinação de "
                        "aceleração, instabilidade e Força G."
                    ),
                })
        return eventos

    def __extrair_matriz(self, leituras):
        """Extrai os atributos por leitura e devolve (matriz, leituras válidas)."""
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
        return matriz, validas

    def get_metodo(self):
        return "MODELO_ML"
