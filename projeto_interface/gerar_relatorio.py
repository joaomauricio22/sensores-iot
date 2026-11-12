"""Gera o relatório visual (HTML) de uma rota via linha de comando.

Útil para preparar o relatório antes da apresentação, sem abrir a interface.
O arquivo é gravado, por padrão, em ``apresentacao/relatorios``.

Uso (com a API no ar):
    python gerar_relatorio.py 104
    python gerar_relatorio.py 104 --titulo "Relatório Rota 104"
    python gerar_relatorio.py 104 --saida C:\\caminho\\meu_relatorio.html
"""
import argparse
import os
import sys

from api_client import ApiClient
from relatorio import PASTA_RELATORIOS, gerar_relatorio, nome_arquivo


def main():
    parser = argparse.ArgumentParser(description="Relatório visual (HTML) de uma rota.")
    parser.add_argument("rota_id", type=int, help="Identificador da rota.")
    parser.add_argument("--titulo", "-t", default=None,
                        help="Nome do relatório (padrão: nome da rota).")
    parser.add_argument("--saida", "-o", default=None,
                        help="Arquivo de saída (padrão: apresentacao/relatorios/<rota>.html).")
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

    titulo = args.titulo or f"Relatório {resumo.get('nome') or f'Rota {args.rota_id}'}"
    if args.saida:
        saida = os.path.abspath(args.saida)
    else:
        saida = os.path.join(PASTA_RELATORIOS, f"{nome_arquivo(titulo)}.html")

    gerar_relatorio(resumo, eventos, grafico, saida, titulo=titulo)
    print(f"Relatório gerado: {saida}")


if __name__ == "__main__":
    main()
