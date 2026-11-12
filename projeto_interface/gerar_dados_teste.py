"""Gera os CSVs sintéticos de demonstração em ``apresentacao/dados_teste``.

Útil para ter os arquivos prontos antes da apresentação: durante a demo, basta
importá-los pela interface (Dados → Rotas → Nova Rota, selecionando vários de
uma vez). A geração é determinística (seed fixa), então os arquivos são sempre
os mesmos.

Uso:
    python gerar_dados_teste.py                 # gera todos os perfis
    python gerar_dados_teste.py --listar        # só lista os perfis disponíveis
    python gerar_dados_teste.py --perfis Conducao_Agressiva
    python gerar_dados_teste.py --pasta C:/caminho/qualquer
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dados_sinteticos import PERFIS, gerar_csv

PASTA_PADRAO = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "apresentacao", "dados_teste"))


def _lista_arquivos():
    return sorted(PERFIS)


def main():
    parser = argparse.ArgumentParser(description="Gera CSVs sintéticos de demonstração.")
    parser.add_argument("--pasta", "-p", default=PASTA_PADRAO,
                        help=f"Pasta de saída (padrão: {PASTA_PADRAO}).")
    parser.add_argument("--perfis", nargs="+", choices=sorted(PERFIS), default=None,
                        help="Perfis a gerar (padrão: todos).")
    parser.add_argument("--listar", action="store_true",
                        help="Lista os perfis disponíveis e encerra.")
    args = parser.parse_args()

    if args.listar:
        print("Perfis disponíveis:")
        for nome, (seed, base_vel, janelas) in sorted(PERFIS.items()):
            print(f"  {nome:<22} seed={seed}  vel_base={base_vel} km/h  "
                  f"{len(janelas)} janelas de evento")
        return

    perfis = args.perfis or sorted(PERFIS)
    pasta = os.path.normpath(args.pasta)
    os.makedirs(pasta, exist_ok=True)

    print(f"Gerando {len(perfis)} arquivo(s) em: {pasta}")
    for nome in perfis:
        seed, base_vel, janelas = PERFIS[nome]
        conteudo = gerar_csv(seed, base_vel, janelas)
        caminho = os.path.join(pasta, f"{nome}.csv")
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
        linhas = conteudo.count("\n") + 1
        kb = os.path.getsize(caminho) / 1024
        print(f"  {nome}.csv  {linhas} linhas  {kb:.1f} KB")


if __name__ == "__main__":
    main()
