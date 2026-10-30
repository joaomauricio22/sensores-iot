"""Prepara os dados para demonstração / captura de telas.

Analisa as leituras anômalas e classifica as leituras com o modelo de ML,
para que as telas de Leituras e Anomalias fiquem preenchidas de forma realista.

Executar (com a API no ar):  python preparar_demo.py
"""
import requests

BASE = "http://localhost:8080/iot"


def main():
    leituras = requests.get(f"{BASE}/leituras").json()

    anomalas = [l for l in leituras if l["valor"] in (75.0, -5.0, 99.0)]

    # Analisa as leituras anômalas (gera registros em 'anomalia')
    for l in anomalas:
        requests.post(f"{BASE}/leituras/{l['id']}/analisar")

    # Classifica todas as leituras com o modelo de ML
    for l in leituras:
        requests.post(f"{BASE}/leituras/{l['id']}/classificar")

    anomalias = requests.get(f"{BASE}/anomalias").json()
    print(f"Leituras classificadas: {len(leituras)}")
    print(f"Anomalias registradas: {len(anomalias)}")


if __name__ == "__main__":
    main()
