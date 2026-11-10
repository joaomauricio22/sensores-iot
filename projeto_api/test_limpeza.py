"""Testes unitários da limpeza aplicada na importação de telemetria.

Executar:  python test_limpeza.py
"""
import unittest

from services.limpeza import (
    LIMITE_ACELERACAO,
    MAX_PARADOS_CONSECUTIVOS,
    VELOCIDADE_MAXIMA,
    limpar_leituras,
)


def registro(i, velocidade=50.0, accel_x=0.0):
    return {
        "data_hora": i,
        "velocidade": velocidade,
        "accel_x": accel_x,
        "accel_y": 0.0,
        "accel_z": 0.0,
    }


class TestLimpeza(unittest.TestCase):

    def test_clip_do_acelerometro(self):
        limpos, relatorio = limpar_leituras([
            registro(0, accel_x=9.0),
            registro(1, accel_x=-8.0),
        ])
        self.assertEqual(len(limpos), 2)
        self.assertEqual(limpos[0]["accel_x"], LIMITE_ACELERACAO)
        self.assertEqual(limpos[1]["accel_x"], -LIMITE_ACELERACAO)
        self.assertEqual(relatorio["acelerometro_ajustado"], 2)

    def test_descarta_velocidade_implausivel(self):
        limpos, relatorio = limpar_leituras([
            registro(0, velocidade=VELOCIDADE_MAXIMA + 1),
            registro(1, velocidade=80.0),
        ])
        self.assertEqual(len(limpos), 1)
        self.assertEqual(relatorio["velocidade_removida"], 1)

    def test_limita_paradas_consecutivas(self):
        registros = [registro(i, velocidade=0.0) for i in range(6)]
        limpos, relatorio = limpar_leituras(registros)
        self.assertEqual(len(limpos), MAX_PARADOS_CONSECUTIVOS)
        self.assertEqual(relatorio["paradas_removidas"], 3)

    def test_movimento_reinicia_contagem_de_paradas(self):
        registros = [
            registro(0, velocidade=0.0),
            registro(1, velocidade=0.0),
            registro(2, velocidade=0.0),
            registro(3, velocidade=50.0),
            registro(4, velocidade=0.0),
        ]
        limpos, _ = limpar_leituras(registros)
        self.assertEqual(len(limpos), 5)

    def test_nao_altera_os_registros_originais(self):
        original = registro(0, accel_x=9.0)
        limpar_leituras([original])
        self.assertEqual(original["accel_x"], 9.0)

    def test_descarta_valores_nao_finitos(self):
        limpos, relatorio = limpar_leituras([
            registro(0, velocidade=float("nan")),
            registro(1, velocidade=50.0, accel_x=float("inf")),
            registro(2, velocidade=60.0),
        ])
        self.assertEqual(len(limpos), 1)
        self.assertEqual(limpos[0]["velocidade"], 60.0)
        self.assertEqual(relatorio["valores_invalidos"], 2)
        self.assertEqual(relatorio["total_removido"], 2)


if __name__ == "__main__":
    unittest.main()
