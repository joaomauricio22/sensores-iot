"""Funções de extração de atributos (feature engineering) da telemetria.

Extrai indicadores físicos a partir dos dados brutos do OBD-II:
  - Força G resultante (magnitude da aceleração triaxial em unidades de g);
  - Instabilidade temporal (desvio padrão da aceleração numa janela).
"""
import math
import statistics


def forca_g(leitura) -> float:
    """Força G resultante de uma leitura, em g (m/s² dividido por 9,81)."""
    if leitura.accel_x is None or leitura.accel_y is None or leitura.accel_z is None:
        return None
    return math.sqrt(
        leitura.accel_x ** 2 + leitura.accel_y ** 2 + leitura.accel_z ** 2
    ) / 9.81


def magnitude_aceleracao(leitura) -> float:
    """Magnitude da aceleração (m/s²) sem normalizar por g."""
    if leitura.accel_x is None or leitura.accel_y is None or leitura.accel_z is None:
        return None
    return math.sqrt(leitura.accel_x ** 2 + leitura.accel_y ** 2 + leitura.accel_z ** 2)


def instabilidade_janela(leituras, indice, raio=3) -> float:
    """Desvio padrão da magnitude da aceleração numa janela ao redor do índice."""
    inicio = max(0, indice - raio)
    fim = min(len(leituras), indice + raio + 1)
    magnitudes = [m for m in (magnitude_aceleracao(l) for l in leituras[inicio:fim]) if m is not None]
    if len(magnitudes) < 2:
        return 0.0
    return statistics.stdev(magnitudes)


def forcas_g(leituras) -> list:
    """Lista de forças G de um conjunto de leituras (ignora valores ausentes)."""
    return [g for g in (forca_g(l) for l in leituras) if g is not None]
