"""Gera o relatório visual (HTML) de uma rota via linha de comando.

Útil para preparar o relatório antes da apresentação, sem abrir a interface.

Uso (com a API no ar):
    python gerar_relatorio.py 104
    python gerar_relatorio.py 104 --saida relatorio_rota104.html
"""
import argparse
import sys

from api_client import ApiClient
from relatorio import gerar_relatorio


def main():
    parser = argparse.ArgumentParser(description="Relatório visual (HTML) de uma rota.")
    parser.add_argument("rota_id", type=int, help="Identificador da rota.")
    parser.add_argument("--saida", "-o", default=None,
                        help="Arquivo de saída (padrão: relatorio_rota<id>.html).")
    args = parser.parse_args()

    api = ApiClient()
    resp = api.resumo_rota(args.rota_id)
    if resp.status_code != 200:
        print(f"Erro ao obter o resumo da rota {args.rota_id}: {resp.status_code}")
        sys.exit(1)
    resumo = resp.json()

    eventos = api.list_eventos(args.rota_id).json()
    resp_grafico = api.grafico_rota(args.rota_id)
    grafico = resp_grafico.json() if resp_grafico.status_code == 200 else None

    saida = args.saida or f"relatorio_rota{args.rota_id}.html"
    gerar_relatorio(resumo, eventos, grafico, saida)
    print(f"Relatório gerado: {saida}")


if __name__ == "__main__":
    main()
