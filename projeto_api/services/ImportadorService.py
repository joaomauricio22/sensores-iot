import csv
from datetime import datetime, timedelta

from entities.Base import db
from entities.Leitura import Leitura
from entities.Veiculo import Veiculo
from repositories.LeituraRepository import LeituraRepository
from repositories.MapeamentoParametroRepository import MapeamentoParametroRepository
from repositories.VeiculoRepository import VeiculoRepository


# Camada de serviço responsável pela importação e padronização dos dados.
#
# Arquivos de telemetria de fontes diferentes usam nomes de colunas diferentes
# para a mesma grandeza (ex.: "Vehicle speed (km/h)" e "Velocidade do veículo
# (km/h)"). O importador usa a tabela MapeamentoParametro para traduzir cada
# nome bruto para um parâmetro canônico, ignorando colunas não mapeadas.
class ImportadorService:

    def __init__(self):
        self.__veiculo_repository = VeiculoRepository()
        self.__mapeamento_repository = MapeamentoParametroRepository()
        self.__leitura_repository = LeituraRepository()

    def importar_csv(self, caminho: str, identificador_veiculo: str, modelo: str = None) -> dict:
        """Importa um CSV, padronizando os parâmetros para o veículo informado."""
        veiculo = self.__veiculo_repository.get_by_identificador(identificador_veiculo)
        if not veiculo:
            veiculo = self.__veiculo_repository.add(
                Veiculo(identificador=identificador_veiculo, modelo=modelo)
            )

        # Mapa de padronização: nome bruto -> parâmetro canônico.
        mapeamentos = {m.nome_bruto: m.parametro for m in self.__mapeamento_repository.get_all()}

        with open(caminho, encoding="utf-8-sig", errors="replace", newline="") as fh:
            reader = csv.reader(fh)
            start_time = None
            colunas = []

            # Varre as linhas até encontrar o cabeçalho (a que começa com "Time").
            for row in reader:
                if not row:
                    continue
                primeiro = row[0].strip()
                if primeiro.startswith("# StartTime"):
                    start_time = self.__parse_start_time(row[0])
                elif primeiro.lower().startswith("time"):
                    colunas = [c.strip() for c in row]
                    break

            if start_time is None:
                raise ValueError(f"StartTime não encontrado no arquivo {caminho}.")

            indice_time = next(
                (i for i, c in enumerate(colunas) if c.lower().startswith("time")), None
            )
            indice_parametro = {}
            for i, nome in enumerate(colunas):
                if nome in mapeamentos:
                    indice_parametro[i] = mapeamentos[nome]

            # Instantes já existentes (para evitar duplicatas em memória).
            existentes = {l.data_hora for l in self.__leitura_repository.get_by_veiculo(veiculo.id)}

            leituras_novas = []
            for row in reader:
                if not row:
                    continue
                try:
                    offset = float(row[indice_time]) if indice_time is not None else 0.0
                except (ValueError, IndexError, TypeError):
                    continue
                data_hora = start_time + timedelta(seconds=offset)

                if data_hora in existentes:
                    continue
                existentes.add(data_hora)

                dados = {}
                for i, parametro in indice_parametro.items():
                    if i < len(row) and row[i].strip() != "":
                        try:
                            dados[parametro.nome] = float(row[i])
                        except ValueError:
                            pass

                leituras_novas.append(Leitura(veiculo_id=veiculo.id, data_hora=data_hora, **dados))

            # Commit em lote (uma única transação).
            db.session.add_all(leituras_novas)
            db.session.commit()

        return {"veiculo_id": veiculo.id, "total_importadas": len(leituras_novas)}

    @staticmethod
    def __parse_start_time(linha: str) -> datetime:
        # Formato do cabeçalho: "# StartTime = 01/21/2026 08:41:21.0884 AM"
        s = linha.split("=", 1)[1].strip()
        return datetime.strptime(s, "%m/%d/%Y %I:%M:%S.%f %p")
