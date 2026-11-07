"""Funções de extração de atributos (feature engineering) da telemetria.

Alinhado à metodologia de análise:
  - aceleração longitudinal (derivada da velocidade, em m/s²);
  - Força G resultante (magnitude horizontal da aceleração: √(ax² + ay²), em m/s²);
  - janela deslizante de 3 leituras (média e desvio padrão = instabilidade).
"""
import math
import statistics


def forca_g_resultante(leitura) -> float:
    """Magnitude horizontal da aceleração: √(ax² + ay²), em m/s²."""
    if leitura.accel_x is None or leitura.accel_y is None:
        return None
    return math.sqrt(leitura.accel_x ** 2 + leitura.accel_y ** 2)


def aceleracao_longitudinal(leituras, indice) -> float:
    """Aceleração longitudinal derivada da velocidade (Δv/Δt), em m/s²."""
    if indice == 0:
        return 0.0
    atual = leituras[indice]
    anterior = leituras[indice - 1]
    if atual.velocidade is None or anterior.velocidade is None:
        return 0.0
    dt = (atual.data_hora - anterior.data_hora).total_seconds()
    if dt <= 0:
        return 0.0
    dv = atual.velocidade - anterior.velocidade  # km/h
    return (dv / 3.6) / dt  # conversão para m/s²


def lista_aceleracoes_longitudinais(leituras) -> list:
    return [aceleracao_longitudinal(leituras, i) for i in range(len(leituras))]


def _janela_trailing(valores, indice, tamanho=3):
    inicio = max(0, indice - tamanho + 1)
    return valores[inicio:indice + 1]


def media_janela(valores, indice, tamanho=3) -> float:
    """Média móvel da janela de 3 leituras (~3 s)."""
    janela = _janela_trailing(valores, indice, tamanho)
    return statistics.mean(janela) if janela else 0.0


def instabilidade_janela(valores, indice, tamanho=3) -> float:
    """Desvio padrão da janela de 3 leituras (~3 s) — mede a instabilidade."""
    janela = _janela_trailing(valores, indice, tamanho)
    if len(janela) < 2:
        return 0.0
    return statistics.stdev(janela)
