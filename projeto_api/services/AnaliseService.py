from entities.Base import db
from entities.EventoRisco import EventoRisco
from repositories.EventoRiscoRepository import EventoRiscoRepository
from repositories.LeituraRepository import LeituraRepository
from repositories.RotaRepository import RotaRepository
from services.detectors.LimiteDetector import LimiteDetector
from services.detectors.EstatisticoDetector import EstatisticoDetector
from services.detectors.ModeloMLDetector import ModeloMLDetector
from services.features import (
    classificar_risco,
    forca_g_resultante,
    lista_aceleracoes_longitudinais,
)


# Camada de serviço responsável pela ANÁLISE da telemetria.
#   - Executa os detectores de risco (limite CTB, estatístico e ML);
#   - Classifica o tipo de cada evento (frenagem, aceleração, curva);
#   - Fornece os dados para o gráfico de comportamento do condutor.
class AnaliseService:

    def __init__(self):
        self.__leitura_repository = LeituraRepository()
        self.__rota_repository = RotaRepository()
        self.__evento_repository = EventoRiscoRepository()
        self.__detectores = [LimiteDetector(), EstatisticoDetector(), ModeloMLDetector()]

    def analisar_rota(self, rota_id: int):
        """Executa os detectores e classifica os eventos de risco (idempotente)."""
        rota = self.__rota_repository.get_by_id(rota_id)
        if not rota:
            return None

        # Se a rota já foi analisada, não refaz (evita reprocessar o ML).
        if self.__evento_repository.get_by_rota(rota_id):
            return []

        leituras = self.__leitura_repository.get_by_rota(rota_id)
        acels = lista_aceleracoes_longitudinais(leituras)
        acel_por_leitura = {l.id: a for l, a in zip(leituras, acels)}

        detectados = []
        for detector in self.__detectores:
            for evento in detector.detectar(leituras, rota):
                detectados.append((detector.get_metodo(), evento))

        existentes = set()
        novos = []
        for metodo, evento in detectados:
            leitura = evento["leitura"]
            if (leitura.id, metodo) in existentes:
                continue
            existentes.add((leitura.id, metodo))
            acel = acel_por_leitura.get(leitura.id, 0.0)
            novos.append(EventoRisco(
                leitura_id=leitura.id,
                rota_id=rota_id,
                data_hora=leitura.data_hora,
                metodo=metodo,
                forca_g=evento.get("forca_g"),
                instabilidade=evento.get("instabilidade"),
                classificacao=classificar_risco(leitura, acel),
                descricao=evento.get("descricao"),
            ))

        db.session.add_all(novos)
        db.session.commit()
        return novos

    def grafico_rota(self, rota_id: int):
        """Retorna os dados para o gráfico: velocidade e tipo de risco ao longo do tempo."""
        rota = self.__rota_repository.get_by_id(rota_id)
        if not rota:
            return None

        leituras = self.__leitura_repository.get_by_rota(rota_id)
        eventos = self.__evento_repository.get_by_rota(rota_id)
        tipo_por_leitura = {e.leitura_id: e.classificacao for e in eventos}

        if not leituras:
            return {"rota_id": rota_id, "nome": rota.nome, "pontos": []}

        t0 = leituras[0].data_hora
        acels = lista_aceleracoes_longitudinais(leituras)

        pontos = []
        for i, leitura in enumerate(leituras):
            pontos.append({
                "tempo": (leitura.data_hora - t0).total_seconds(),
                "velocidade": leitura.velocidade,
                "forca_g": forca_g_resultante(leitura),
                "acel_longitudinal": acels[i],
                "risco": leitura.id in tipo_por_leitura,
                "classificacao": tipo_por_leitura.get(leitura.id),
            })

        return {"rota_id": rota_id, "nome": rota.nome, "pontos": pontos}
