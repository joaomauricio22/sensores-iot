"""Avaliação do detector de Machine Learning em relação às regras de limite.

Para cada rota, compara as leituras sinalizadas pelo MODELO_ML com as leituras
sinalizadas pelo detector de LIMITE (usado como referência) e calcula:
  - precisão, recall e F1-score;
  - silhouette score do agrupamento DBSCAN (qualidade da separação).

O modelo é treinado com o histórico das OUTRAS rotas; se não houver histórico
suficiente, usa a própria rota como fallback (mesma lógica do detector).

Uso:
    python avaliar_ml.py
"""
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import f1_score, precision_score, recall_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from app import app
from repositories.LeituraRepository import LeituraRepository
from repositories.RotaRepository import RotaRepository
from services.LimiaresService import LimiaresService
from services.detectors.LimiteDetector import LimiteDetector
from services.detectors.ModeloMLDetector import ModeloMLDetector
from services.features import (
    forca_g_resultante,
    instabilidade_janela,
    lista_aceleracoes_longitudinais,
    media_janela,
)


def extrair_matriz(leituras):
    acels = lista_aceleracoes_longitudinais(leituras)
    matriz = []
    validas = []
    for i, leitura in enumerate(leituras):
        fg = forca_g_resultante(leitura)
        if fg is None:
            continue
        matriz.append([
            media_janela(acels, i),
            instabilidade_janela(acels, i),
            leitura.accel_y if leitura.accel_y is not None else 0.0,
            fg,
        ])
        validas.append(leitura)
    return matriz, validas


def silhouette(leituras, historico):
    matriz, _ = extrair_matriz(historico if len(historico) >= 30 else leituras)
    if len(matriz) < 30:
        return None
    X = StandardScaler().fit_transform(np.array(matriz))
    labels = DBSCAN(eps=1.0, min_samples=15).fit(X).labels_
    if len(set(labels.tolist())) < 2 or len(set(labels.tolist())) >= len(labels):
        return None
    return silhouette_score(X, labels)


def avaliar_rota(rota, leitura_repo, limiares, historico):
    leituras = leitura_repo.get_by_rota(rota.id)
    if len(leituras) < 30:
        return None

    regras = LimiteDetector().detectar(leituras, rota, limiares, historico=historico)
    ml = ModeloMLDetector().detectar(leituras, rota, limiares, historico=historico)

    ids_regras = {evento["leitura"].id for evento in regras}
    ids_ml = {evento["leitura"].id for evento in ml}
    y_true = [1 if leitura.id in ids_regras else 0 for leitura in leituras]
    y_pred = [1 if leitura.id in ids_ml else 0 for leitura in leituras]

    return {
        "rota_id": rota.id,
        "nome": rota.nome,
        "leituras": len(leituras),
        "eventos_regras": len(ids_regras),
        "eventos_ml": len(ids_ml),
        "precisao": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "silhouette": silhouette(leituras, historico),
    }


def main():
    with app.app_context():
        rota_repo = RotaRepository()
        leitura_repo = LeituraRepository()
        limiares_service = LimiaresService()
        limiares = limiares_service.get_limiares()
        limiares["sensores"] = limiares_service.get_sensores()

        rotas = rota_repo.get_all()
        if not rotas:
            print("Nenhuma rota cadastrada. Importe um CSV antes de avaliar.")
            return

        resultados = []
        for rota in rotas:
            historico = leitura_repo.get_historico(rota.id)
            resultado = avaliar_rota(rota, leitura_repo, limiares, historico)
            if resultado is None:
                print(f"Rota {rota.id} ({rota.nome}): ignorada (menos de 30 leituras).")
                continue
            resultados.append(resultado)

        if not resultados:
            print("Nenhuma rota com leituras suficientes para avaliar o modelo.")
            return

        print(
            f"{'Rota':<6}{'Leituras':>10}{'Regras':>9}{'ML':>6}"
            f"{'Precisão':>11}{'Recall':>9}{'F1':>8}{'Silhouette':>12}"
        )
        for r in resultados:
            sil = f"{r['silhouette']:.3f}" if r["silhouette"] is not None else "n/d"
            print(
                f"{r['rota_id']:<6}{r['leituras']:>10}{r['eventos_regras']:>9}"
                f"{r['eventos_ml']:>6}{r['precisao']:>11.3f}{r['recall']:>9.3f}"
                f"{r['f1']:>8.3f}{sil:>12}"
            )

        print(
            f"\nMédia: precisão={np.mean([r['precisao'] for r in resultados]):.3f} "
            f"recall={np.mean([r['recall'] for r in resultados]):.3f} "
            f"F1={np.mean([r['f1'] for r in resultados]):.3f}"
        )


if __name__ == "__main__":
    main()
