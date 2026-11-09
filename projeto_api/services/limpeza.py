"""Limpeza dos dados brutos de telemetria durante a importação.

As regras evitam que ruído de sensor vire evento falso:

  - aceleração de cada eixo limitada a ±5 m/s² (spikes fisicamente improváveis);
  - leituras com velocidade acima de 200 km/h são descartadas;
  - no máximo 3 leituras consecutivas com o veículo parado (< 1 km/h).

A limpeza não divide a rota em sub-rotas por gaps de tempo: a rota continua
sendo a viagem inteira, como definido no modelo de dados.
"""
LIMITE_ACELERACAO = 5.0      # m/s²
VELOCIDADE_MAXIMA = 200.0    # km/h
VELOCIDADE_PARADO = 1.0      # km/h
MAX_PARADOS_CONSECUTIVOS = 3


def limpar_leituras(registros: list) -> tuple:
    """Aplica a limpeza a uma lista de dicts de leitura.

    Cada dict deve conter `data_hora` e os campos de telemetria. Retorna
    `(registros_limpos, relatorio)`.
    """
    limpos = []
    acelerometro_ajustado = 0
    velocidade_removida = 0
    paradas_removidas = 0
    parados_consecutivos = 0

    for registro in registros:
        dados = dict(registro)

        # 1) Clip dos spikes do acelerômetro.
        for canal in ("accel_x", "accel_y", "accel_z"):
            valor = dados.get(canal)
            if valor is not None and abs(valor) > LIMITE_ACELERACAO:
                dados[canal] = max(-LIMITE_ACELERACAO, min(LIMITE_ACELERACAO, valor))
                acelerometro_ajustado += 1

        # 2) Velocidade implausível: descarta a leitura.
        velocidade = dados.get("velocidade")
        if velocidade is not None and velocidade > VELOCIDADE_MAXIMA:
            velocidade_removida += 1
            continue

        # 3) Excesso de leituras paradas consecutivas.
        if velocidade is not None and velocidade < VELOCIDADE_PARADO:
            parados_consecutivos += 1
            if parados_consecutivos > MAX_PARADOS_CONSECUTIVOS:
                paradas_removidas += 1
                continue
        else:
            parados_consecutivos = 0

        limpos.append(dados)

    relatorio = {
        "acelerometro_ajustado": acelerometro_ajustado,
        "velocidade_removida": velocidade_removida,
        "paradas_removidas": paradas_removidas,
        "total_removido": velocidade_removida + paradas_removidas,
    }
    return limpos, relatorio
