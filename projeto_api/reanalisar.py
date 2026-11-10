"""Reanálise das rotas com os limiares atuais de `config/limiares.json`.

Útil depois de alterar o JSON: apaga os eventos gerados pelos detectores e
executa novamente os três métodos (limite, estatístico e ML) sobre as leituras
já armazenadas. Eventos cadastrados manualmente (método MANUAL) são
preservados. Não altera rotas nem leituras.

Uso:
    python reanalisar.py            # reanalisa todas as rotas
    python reanalisar.py 1 3        # reanalisa apenas as rotas indicadas
"""
import sys

from app import app
from services.AnaliseService import AnaliseService


def main(rota_ids):
    with app.app_context():
        servico = AnaliseService()
        if not rota_ids:
            total = servico.reanalisar_todas()
            print(f"Rotas reanalisadas: {total}.")
            return

        for rota_id in rota_ids:
            eventos = servico.reanalisar_rota(rota_id)
            if eventos is None:
                print(f"Rota {rota_id}: não encontrada.")
            else:
                print(f"Rota {rota_id}: {len(eventos)} eventos de risco.")


if __name__ == "__main__":
    ids = []
    for argumento in sys.argv[1:]:
        try:
            ids.append(int(argumento))
        except ValueError:
            print(f"Id inválido: {argumento}")
            sys.exit(1)
    main(ids)
