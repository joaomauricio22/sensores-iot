from services.detectors.DetectorAnomalia import DetectorAnomalia
from services.features import (
    forca_g_resultante,
    instabilidade_janela,
    lista_aceleracoes_longitudinais,
    variacao_acelerador,
)


# Método 1 - Limites físicos (Código de Trânsito Brasileiro - CTB) e
# limites operacionais do veículo. Classifica o evento em um dos tipos:
#   - Frenagem brusca           (desaceleração abaixo do limite negativo)
#   - Aceleração brusca         (aceleração acima do limite positivo)
#   - Curva em alta velocidade  (aceleração lateral alta com velocidade)
#   - Excesso de velocidade     (velocidade acima do máximo)
#   - RPM excessivo             (rotação do motor acima do máximo)
#   - Acelerador brusco         (variação rápida da posição do acelerador)
#
# Cada evento aponta o canal (sensor) responsável e o valor observado nele,
# permitindo rastrear qual parâmetro disparou o alerta.
class LimiteDetector(DetectorAnomalia):

    def detectar(self, leituras, rota, limiares, historico=None):
        acels = lista_aceleracoes_longitudinais(leituras)
        eventos = []

        for i, leitura in enumerate(leituras):
            acel = acels[i]
            fg = forca_g_resultante(leitura)
            inst = instabilidade_janela(acels, i)
            var_acelerador = variacao_acelerador(leituras, i)

            # Frenagem brusca: desaceleração mais intensa que o limite.
            if acel < limiares["frenagem_max"]:
                eventos.append(self._evento(
                    leitura, "accel_x", acel, fg, inst, "Frenagem brusca",
                    f"Desaceleração de {acel:.2f} m/s² "
                    f"(limite: {limiares['frenagem_max']:.1f} m/s²).",
                ))

            # Aceleração brusca: aceleração mais intensa que o limite.
            if acel > limiares["aceleracao_max"]:
                eventos.append(self._evento(
                    leitura, "accel_x", acel, fg, inst, "Aceleração brusca",
                    f"Aceleração de {acel:.2f} m/s² "
                    f"(limite: {limiares['aceleracao_max']:.1f} m/s²).",
                ))

            # Curva em alta velocidade: aceleração lateral forte com velocidade alta.
            if (
                leitura.accel_y is not None
                and abs(leitura.accel_y) > limiares["lateral_max"]
                and leitura.velocidade is not None
                and leitura.velocidade > limiares["curva_velocidade_min"]
            ):
                eventos.append(self._evento(
                    leitura, "accel_y", leitura.accel_y, fg, inst,
                    "Curva em alta velocidade",
                    f"Aceleração lateral de {leitura.accel_y:.2f} m/s² a "
                    f"{leitura.velocidade:.0f} km/h.",
                ))

            # Excesso de velocidade.
            if leitura.velocidade is not None and leitura.velocidade > limiares["velocidade_max"]:
                eventos.append(self._evento(
                    leitura, "velocidade", leitura.velocidade, fg, inst,
                    "Excesso de velocidade",
                    f"Velocidade de {leitura.velocidade:.0f} km/h "
                    f"(limite: {limiares['velocidade_max']:.0f} km/h).",
                ))

            # RPM excessivo: motor forçado.
            if leitura.rpm is not None and leitura.rpm > limiares["rpm_max"]:
                eventos.append(self._evento(
                    leitura, "rpm", leitura.rpm, fg, inst,
                    "RPM excessivo",
                    f"Rotação de {leitura.rpm:.0f} RPM "
                    f"(limite: {limiares['rpm_max']:.0f} RPM).",
                ))

            # Acelerador brusco: pisada rápida no acelerador.
            if var_acelerador > limiares["acelerador_delta_max"]:
                eventos.append(self._evento(
                    leitura, "posicao_acelerador", leitura.posicao_acelerador,
                    fg, inst, "Acelerador brusco",
                    f"Variação de {var_acelerador:.1f} %/s na posição do acelerador.",
                ))

        return eventos

    def _evento(self, leitura, canal, valor, forca_g, instabilidade,
                classificacao, descricao):
        return {
            "leitura": leitura,
            "canal": canal,
            "valor": valor,
            "forca_g": forca_g,
            "instabilidade": instabilidade,
            "classificacao": classificacao,
            "descricao": descricao,
        }

    def get_metodo(self):
        return "LIMITE"
