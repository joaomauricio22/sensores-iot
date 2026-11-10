"""Funções de extração de atributos (feature engineering) da telemetria.

Alinhado à metodologia de análise:
  - aceleração longitudinal (derivada da velocidade, em m/s²);
  - Força G resultante (magnitude horizontal da aceleração: √(ax² + ay²), em m/s²);
  - variação da posição do acelerador (indicador de condução agressiva);
  - janela deslizante de 3 leituras (média e desvio padrão = instabilidade).
"""
import math
import statistics

# Janela temporal mínima para estimar derivadas (aceleração e variação do
# acelerador). Quando a amostragem é muito densa (ex.: OBD-II a ~333 Hz), a
# diferença entre amostras quase simultâneas amplifica o ruído de quantização
# (velocidade em 1 km/h, acelerador em 1 %) e produz valores fisicamente
# impossíveis (centenas de m/s²). Derivar sobre uma janela mínima de 0,5 s
# suaviza esse ruído sem alterar o resultado em coletas com dt >= 0,5 s.
MIN_DT = 0.5  # segundos


def _anterior_na_janela(leituras, indice, campo):
    """Última leitura anterior (com ``campo`` não nulo) a pelo menos ``MIN_DT``
    segundos da leitura ``indice``. Retorna ``None`` se não houver."""
    atual = leituras[indice]
    for j in range(indice - 1, -1, -1):
        candidato = leituras[j]
        if getattr(candidato, campo) is None:
            continue
        if (atual.data_hora - candidato.data_hora).total_seconds() >= MIN_DT:
            return candidato
    return None


def distancia_haversine(lat1, lon1, lat2, lon2) -> float:
    """Distância (em km) entre duas coordenadas, pela fórmula de Haversine."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    raio_terra = 6371.0  # km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    # Protege o domínio do asin contra erros de arredondamento (a pode ficar
    # ligeiramente acima de 1 para pontos antípodas, causando ValueError).
    a = min(1.0, max(0.0, a))
    return 2 * raio_terra * math.asin(math.sqrt(a))


def forca_g_resultante(leitura) -> float:
    """Magnitude horizontal da aceleração: √(ax² + ay²), em m/s²."""
    if leitura.accel_x is None or leitura.accel_y is None:
        return None
    return math.sqrt(leitura.accel_x ** 2 + leitura.accel_y ** 2)


def aceleracao_longitudinal(leituras, indice) -> float:
    """Aceleração longitudinal derivada da velocidade (Δv/Δt), em m/s².

    Usa uma janela mínima de ``MIN_DT`` segundos (ver ``_anterior_na_janela``)
    para não amplificar o ruído de quantização em amostragens muito densas.
    """
    if indice == 0:
        return 0.0
    atual = leituras[indice]
    if atual.velocidade is None:
        return 0.0
    anterior = _anterior_na_janela(leituras, indice, "velocidade")
    if anterior is None:
        return 0.0
    dt = (atual.data_hora - anterior.data_hora).total_seconds()
    if dt <= 0:
        return 0.0
    dv = atual.velocidade - anterior.velocidade  # km/h
    return (dv / 3.6) / dt  # conversão para m/s²


def variacao_acelerador(leituras, indice) -> float:
    """Variação da posição do acelerador (Δ% / Δt), indicador de condução agressiva.

    Usa uma janela mínima de ``MIN_DT`` segundos (ver ``_anterior_na_janela``).
    """
    if indice == 0:
        return 0.0
    atual = leituras[indice]
    if atual.posicao_acelerador is None:
        return 0.0
    anterior = _anterior_na_janela(leituras, indice, "posicao_acelerador")
    if anterior is None:
        return 0.0
    dt = (atual.data_hora - anterior.data_hora).total_seconds()
    if dt <= 0:
        return 0.0
    return (atual.posicao_acelerador - anterior.posicao_acelerador) / dt  # % por segundo


def lista_aceleracoes_longitudinais(leituras) -> list:
    return [aceleracao_longitudinal(leituras, i) for i in range(len(leituras))]


def _janela_trailing(valores, indice, tamanho=3):
    inicio = max(0, indice - tamanho + 1)
    return valores[inicio:indice + 1]


def media_janela(valores, indice, tamanho=3) -> float:
    janela = _janela_trailing(valores, indice, tamanho)
    return statistics.mean(janela) if janela else 0.0


def instabilidade_janela(valores, indice, tamanho=3) -> float:
    janela = _janela_trailing(valores, indice, tamanho)
    if len(janela) < 2:
        return 0.0
    return statistics.stdev(janela)
