from datetime import datetime

from entities.Base import db
from entities.EventoRisco import EventoRisco
from entities.Rota import Rota
from repositories.EventoRiscoRepository import EventoRiscoRepository
from repositories.LeituraRepository import LeituraRepository
from repositories.RotaRepository import RotaRepository
from services.LimiaresService import LimiaresService
from services.detectors.LimiteDetector import LimiteDetector
from services.detectors.EstatisticoDetector import EstatisticoDetector
from services.detectors.ModeloMLDetector import ModeloMLDetector
from services.features import (
    distancia_haversine,
    forca_g_resultante,
    lista_aceleracoes_longitudinais,
)

# Pesos de cada tipo de evento no cálculo do "score de segurança" (0-100).
PESOS_SCORE = {
    "Frenagem brusca": 6,
    "Curva em alta velocidade": 5,
    "Aceleração brusca": 4,
    "Excesso de velocidade": 3,
    "RPM excessivo": 2,
    "Acelerador brusco": 2,
    "Comportamento atípico": 1,
}


# Camada de serviço responsável pela ANÁLISE da telemetria.
#   - Executa os detectores de risco (limite, estatístico e ML);
#   - Classifica o tipo de cada evento (frenagem, aceleração, curva, etc.);
#   - Fornece o resumo (dashboard + score) e os dados do gráfico/análise por sensor.
class AnaliseService:

    def __init__(self):
        self.__leitura_repository = LeituraRepository()
        self.__rota_repository = RotaRepository()
        self.__evento_repository = EventoRiscoRepository()
        self.__limiares_service = LimiaresService()
        self.__detectores = [LimiteDetector(), EstatisticoDetector(), ModeloMLDetector()]

    def analisar_rota(self, rota_id: int, forcar: bool = False):
        """Executa os detectores e classifica os eventos de risco (idempotente).

        - ``forcar=False`` (análise automática): se a rota já foi analisada e as
          leituras não mudaram, não refaz. Se a análise está pendente (rota nova
          ou invalidada após edição de leituras), executa os detectores e
          **acrescenta** os eventos novos, preservando os já existentes (evita
          apagar eventos cadastrados manualmente via CRUD). Usado por
          ``resumo_rota``/``grafico_rota``.
        - ``forcar=True``: apaga os eventos gerados pelos detectores e reexecuta
          a análise do zero, **preservando os eventos manuais** (método
          ``MANUAL``). Usado pelo endpoint ``POST /rotas/<id>/analisar``, pelo
          botão "Reanalisar" e pelo ``reanalisar.py``.
        """
        # Caminho rápido: rota já analisada e leituras inalteradas não têm
        # trabalho (evita abrir transação em toda consulta de resumo/gráfico).
        rota = self.__rota_repository.get_by_id(rota_id)
        if not rota:
            return None
        if not forcar and rota.data_analise is not None:
            return []

        # Serializa análises concorrentes da MESMA rota: trava a linha da rota
        # (SELECT ... FOR UPDATE) e relê o estado após adquirir o lock. Sem isso,
        # requisições simultâneas a /resumo e /grafico tentam inserir os mesmos
        # eventos ao mesmo tempo, causando erro de chave única (unique constraint).
        try:
            rota = (
                db.session.query(Rota)
                .filter(Rota.id == rota_id)
                .with_for_update()
                .populate_existing()
                .one_or_none()
            )
            if not rota:
                db.session.rollback()
                return None

            # Outra requisição pode ter analisado a rota enquanto esta esperava
            # pelo lock. Nesse caso, apenas libera e retorna sem reprocessar.
            if not forcar and rota.data_analise is not None:
                db.session.rollback()
                return []

            # Reanálise forçada: remove apenas os eventos dos detectores,
            # preservando os cadastrados manualmente (método MANUAL). Na análise
            # automática (forcar=False) nada é apagado: apenas acrescenta.
            if forcar:
                db.session.query(EventoRisco).filter(
                    EventoRisco.rota_id == rota_id,
                    EventoRisco.metodo != "MANUAL",
                ).delete(synchronize_session=False)

            leituras = self.__leitura_repository.get_by_rota(rota_id)
            historico = self.__leitura_repository.get_historico(rota_id)
            limiares = self.__limiares_service.get_limiares()
            limiares["sensores"] = self.__limiares_service.get_sensores()

            detectados = []
            for detector in self.__detectores:
                for evento in detector.detectar(leituras, rota, limiares, historico=historico):
                    detectados.append((detector.get_metodo(), evento))

            # Eventos já persistidos (para não duplicar na análise automática).
            existentes = {
                (e.leitura_id, e.metodo, e.classificacao, e.canal)
                for e in self.__evento_repository.get_by_rota(rota_id)
            }
            vistos = set()
            novos = []
            for metodo, evento in detectados:
                leitura = evento["leitura"]
                classificacao = evento.get("classificacao") or "Comportamento atípico"
                canal = evento.get("canal") or "geral"
                chave = (leitura.id, metodo, classificacao, canal)
                if chave in existentes or chave in vistos:
                    continue
                vistos.add(chave)
                novos.append(EventoRisco(
                    leitura_id=leitura.id,
                    rota_id=rota_id,
                    data_hora=leitura.data_hora,
                    metodo=metodo,
                    canal=canal,
                    valor=evento.get("valor"),
                    forca_g=evento.get("forca_g"),
                    instabilidade=evento.get("instabilidade"),
                    classificacao=classificacao,
                    descricao=evento.get("descricao"),
                ))

            db.session.add_all(novos)
            rota.data_analise = datetime.now()
            db.session.commit()
            return novos
        except Exception:
            # Nunca deixa a sessão "suja" após um erro no meio da análise.
            db.session.rollback()
            raise

    def grafico_rota(self, rota_id: int):
        """Retorna os dados do gráfico (velocidade, Força G, RPM) e de GPS."""
        rota = self.__rota_repository.get_by_id(rota_id)
        if not rota:
            return None

        # Garante que a análise foi executada (idempotente).
        self.analisar_rota(rota_id)

        leituras = self.__leitura_repository.get_by_rota(rota_id)
        eventos = self.__evento_repository.get_by_rota(rota_id)
        tipo_por_leitura = {}
        for e in eventos:
            tipo_por_leitura.setdefault(e.leitura_id, []).append(e.classificacao)

        if not leituras:
            return {"rota_id": rota_id, "nome": rota.nome, "pontos": []}

        t0 = leituras[0].data_hora
        acels = lista_aceleracoes_longitudinais(leituras)

        pontos = []
        for i, leitura in enumerate(leituras):
            classificacoes = tipo_por_leitura.get(leitura.id, [])
            pontos.append({
                "tempo": (leitura.data_hora - t0).total_seconds(),
                "velocidade": leitura.velocidade,
                "rpm": leitura.rpm,
                "forca_g": forca_g_resultante(leitura),
                "acel_longitudinal": acels[i],
                "latitude": leitura.latitude,
                "longitude": leitura.longitude,
                "risco": bool(classificacoes),
                "classificacoes": classificacoes,
            })

        return {"rota_id": rota_id, "nome": rota.nome, "pontos": pontos}

    def resumo_rota(self, rota_id: int):
        """Calcula o resumo (dashboard) e o score de segurança da rota."""
        rota = self.__rota_repository.get_by_id(rota_id)
        if not rota:
            return None

        # Garante que a análise foi executada (idempotente).
        self.analisar_rota(rota_id)

        leituras = self.__leitura_repository.get_by_rota(rota_id)
        eventos = self.__evento_repository.get_by_rota(rota_id)

        velocidades = [l.velocidade for l in leituras if l.velocidade is not None]
        rpms = [l.rpm for l in leituras if l.rpm is not None]

        duracao = 0.0
        if len(leituras) >= 2:
            duracao = (leituras[-1].data_hora - leituras[0].data_hora).total_seconds()

        distancia = self.__calcular_distancia(leituras)

        eventos_por_tipo = {}
        for e in eventos:
            tipo = e.classificacao or "Comportamento atípico"
            eventos_por_tipo[tipo] = eventos_por_tipo.get(tipo, 0) + 1

        return {
            "rota_id": rota_id,
            "nome": rota.nome,
            "duracao_segundos": round(duracao, 1),
            "distancia_km": round(distancia, 3),
            "velocidade_media": round(self.__velocidade_media(leituras), 1),
            "velocidade_maxima": round(max(velocidades), 1) if velocidades else 0.0,
            "rpm_maximo": round(max(rpms), 1) if rpms else 0.0,
            "total_eventos": len(eventos),
            "eventos_por_tipo": eventos_por_tipo,
            "score": self.__calcular_score(eventos_por_tipo),
        }

    def comparar_rotas(self, rota_ids: list):
        """Retorna o resumo de duas ou mais rotas para comparação."""
        resumos = []
        for rota_id in rota_ids:
            resumo = self.resumo_rota(rota_id)
            if resumo:
                resumos.append(resumo)
        return resumos

    def reanalisar_rota(self, rota_id: int):
        """Remove os eventos existentes e reexecuta a análise (novos limiares)."""
        return self.analisar_rota(rota_id, forcar=True)

    def reanalisar_todas(self) -> int:
        """Reanalisa todas as rotas; retorna a quantidade de rotas reprocessadas."""
        rotas = self.__rota_repository.get_all()
        for rota in rotas:
            self.reanalisar_rota(rota.id)
        return len(rotas)

    def __calcular_distancia(self, leituras) -> float:
        """Soma a distância percorrida entre leituras consecutivas (km)."""
        total = 0.0
        for i in range(1, len(leituras)):
            d = distancia_haversine(
                leituras[i - 1].latitude, leituras[i - 1].longitude,
                leituras[i].latitude, leituras[i].longitude,
            )
            if d is not None:
                total += d
        return total

    def __velocidade_media(self, leituras) -> float:
        """Velocidade média ponderada pelo tempo (km/h).

        A média aritmética simples pesa igualmente amostras coletadas em ritmos
        diferentes. Quando o veículo para (ou há falhas de coleta), as amostras
        em movimento ficam super-representadas e a média aritmética superestima
        a velocidade real. Pondera cada leitura pelo intervalo até a próxima.
        """
        total = 0.0
        tempo_total = 0.0
        for i in range(len(leituras) - 1):
            atual = leituras[i]
            if atual.velocidade is None:
                continue
            dt = (leituras[i + 1].data_hora - atual.data_hora).total_seconds()
            if dt <= 0:
                continue
            total += atual.velocidade * dt
            tempo_total += dt
        return total / tempo_total if tempo_total else 0.0

    def __calcular_score(self, eventos_por_tipo: dict) -> int:
        """Score de segurança: começa em 100 e desconta conforme a severidade."""
        penalidade = sum(
            PESOS_SCORE.get(tipo, 1) * qtd
            for tipo, qtd in eventos_por_tipo.items()
        )
        return max(0, 100 - penalidade)
