"""Geração de CSVs sintéticos de telemetria (dados de demonstração).

Módulo puro (sem Tkinter/Matplotlib) para poder ser usado tanto pela captura de
telas quanto por um script de linha de comando que grava os arquivos em disco.

Formato do CSV gerado (mesmo layout produzido pelo app OBD de aquisição):

    # StartTime = 01/21/2026 08:00:00.0000 AM
    Time (sec), Vehicle speed (km/h), Engine RPM (RPM), Accel X (m/s²),
    Accel Y (m/s²), Accel Z (m/s²), Absolute throttle position (%),
    Latitude (deg), Longitude (deg)

Os eventos são "janelas" curtas e isoladas (frenagem/aceleração brusca, curva,
excesso de velocidade, RPM excessivo e acelerador brusco); o restante da rota é
um cruzeiro suave. A geração é determinística (seed fixa), então a mesma rota é
sempre reproduzida.
"""
import math
import random

# --------------------------------------------------------------------------- #
# Perfis de condução (nome do arquivo -> (seed, velocidade base, janelas)).
# --------------------------------------------------------------------------- #
JANELAS_AGRESSIVO = [
    ("fren", 60, 1),
    ("acel", 90, 1),
    ("curva", 140, 2),
    ("fren", 200, 1),
    ("acel", 230, 1),
    ("acelerador", 270, 1),
    ("curva", 320, 2),
    ("fren", 380, 1),
    ("acel", 410, 1),
    ("curva", 460, 2),
    ("excesso", 520, 11),
    ("rpm", 560, 1),
    ("acelerador", 590, 1),
    ("fren", 640, 1),
    ("acel", 670, 1),
]

JANELAS_DEFENSIVO = [
    ("curva", 400, 2),
    ("excesso", 510, 11),
    ("rpm", 560, 1),
]

PERFIS = {
    "Conducao_Agressiva": (1, 70.0, JANELAS_AGRESSIVO),
    "Conducao_Defensiva": (2, 70.0, JANELAS_DEFENSIVO),
}


def gerar_csv(seed, base_vel, janelas, n=720, dt=0.5):
    """Gera o texto de um CSV sintético de telemetria com anomalias isoladas.

    ``janelas`` é uma lista de tuplas ``(tipo, início, duração)`` que descreve
    cada evento. Os tipos suportados são: ``fren`` (frenagem brusca), ``acel``
    (aceleração brusca), ``curva`` (curva em alta velocidade), ``excesso``
    (excesso de velocidade), ``rpm`` (RPM excessivo) e ``acelerador``
    (acelerador brusco).
    """
    rng = random.Random(seed)
    linhas = [
        "# StartTime = 01/21/2026 08:00:00.0000 AM",
        "Time (sec), Vehicle speed (km/h), Engine RPM (RPM), Accel X (m/s²), "
        "Accel Y (m/s²), Accel Z (m/s²), Absolute throttle position (%), "
        "Latitude (deg), Longitude (deg)",
    ]
    lat0, lon0 = -22.588833, -43.284300
    lat, lon = lat0, lon0
    rumo = math.radians(40.0)  # direção fixa (nordeste) da rota sintética
    speed = base_vel
    rpm = 850.0 + base_vel * 30.0
    throttle = 10.0 + base_vel * 0.35

    ativo = {}
    for tipo, inicio, duracao in janelas:
        for j in range(duracao):
            ativo[inicio + j] = tipo

    for i in range(n):
        t = i * dt
        k = ativo.get(i)
        prev = speed

        if k == "fren":
            speed = max(15.0, speed - 13.0)
        elif k == "acel":
            speed = min(115.0, speed + 11.0)
        elif k == "curva":
            speed = base_vel + 5.0
        elif k == "excesso":
            # Sobe gradualmente até ultrapassar o limite (aceleração ~0,23 g,
            # abaixo do limiar de "aceleração brusca", para não gerar cascata).
            speed = min(108.0, speed + 4.0)
        elif k == "rpm":
            speed = base_vel + 4.0
        elif k == "acelerador":
            speed = base_vel - 8.0
        else:
            # Cruzeiro quase constante, com deriva bem suave.
            alvo = base_vel + 2.0 * math.sin(i / 60.0)
            speed += (alvo - speed) * 0.08
            speed = max(0.0, min(115.0, speed))
        speed = round(speed, 1)

        if k in ("fren", "acel"):
            ax = (speed - prev) / 3.6 / dt
        else:
            ax = rng.gauss(0.0, 0.04)

        if k == "curva":
            ay = 4.0 * (1 if i % 2 == 0 else -1)
        else:
            ay = rng.gauss(0.0, 0.05)

        az = rng.gauss(0.1, 0.03)

        if k == "rpm":
            rpm = 6100.0
        else:
            rpm = 850.0 + speed * 30.0 + rng.gauss(0, 40)
        rpm = round(rpm, 0)

        if k == "acelerador":
            throttle = 75.0
        else:
            throttle = 10.0 + speed * 0.35 + rng.gauss(0, 0.5)
        throttle = round(max(0.0, min(100.0, throttle)), 1)

        # GPS integrado a partir da velocidade (coerente com o painel):
        # desloca-se na direção fixa pela distância percorrida no passo.
        vm = (prev + speed) / 2.0  # km/h médio do passo
        passo_km = vm / 3.6 * dt / 1000.0
        lat += passo_km * math.cos(rumo) / 111.32
        lon += passo_km * math.sin(rumo) / (111.32 * math.cos(math.radians(lat)))
        linhas.append(
            f"{t:.1f}, {speed:.1f}, {rpm:.0f}, {ax:.2f}, {ay:.2f}, "
            f"{az:.2f}, {throttle:.1f}, {lat:.6f}, {lon:.6f}"
        )
    return "\n".join(linhas)
