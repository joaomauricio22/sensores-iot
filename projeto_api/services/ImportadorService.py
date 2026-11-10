import csv
import io
from datetime import datetime, timedelta

from marshmallow import ValidationError

from entities.Base import db
from entities.Leitura import Leitura
from entities.Rota import Rota
from services.limpeza import limpar_leituras


# Padronização dos parâmetros (back-end): traduz os nomes brutos das colunas
# dos arquivos para os atributos canônicos da entidade Leitura.
# Colunas não mapeadas são ignoradas na importação.
MAPEAMENTO_PADRAO = {
    "Velocidade do veículo (km/h)": "velocidade",
    "Vehicle speed (km/h)": "velocidade",
    "RPM do motor (RPM)": "rpm",
    "Engine RPM (RPM)": "rpm",
    "Aceleração X (m/s²)": "accel_x",
    "Accel X (m/s²)": "accel_x",
    "Aceleração Y (m/s²)": "accel_y",
    "Accel Y (m/s²)": "accel_y",
    "Aceleração Z (m/s²)": "accel_z",
    "Accel Z (m/s²)": "accel_z",
    "Posição absoluta do acelerador (%)": "posicao_acelerador",
    "Absolute throttle position (%)": "posicao_acelerador",
    "Latitude (deg)": "latitude",
    "Longitude (deg)": "longitude",
}


# Camada de serviço responsável pela importação de um CSV de telemetria,
# criando a Rota e as Leituras correspondentes, com padronização dos parâmetros.
class ImportadorService:

    def importar_csv(self, nome: str, arquivo_origem: str, conteudo_csv: str) -> dict:
        """Importa um CSV (texto), criando a Rota e as Leituras.

        O CSV é lido e validado antes de a rota ser criada. Se algo falhar,
        nada é persistido (transação única).
        """
        if not nome or not str(nome).strip():
            raise ValidationError("O nome da rota é obrigatório.")
        nome = str(nome).strip()
        if len(nome) > 100:
            raise ValidationError("O nome da rota deve ter no máximo 100 caracteres.")
        if arquivo_origem is not None and len(arquivo_origem) > 200:
            raise ValidationError("O arquivo de origem deve ter no máximo 200 caracteres.")

        registros = self.__parse(conteudo_csv)
        if not registros:
            raise ValidationError("O arquivo não possui leituras válidas.")

        registros, relatorio = limpar_leituras(registros)
        if not registros:
            raise ValidationError(
                "Todas as leituras foram descartadas pela limpeza dos dados."
            )

        rota = Rota(nome=str(nome).strip(), arquivo_origem=arquivo_origem)
        try:
            db.session.add(rota)
            db.session.flush()  # garante o id da rota antes das leituras

            leituras = [
                Leitura(rota_id=rota.id, **registro)
                for registro in registros
            ]
            db.session.add_all(leituras)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return {
            "rota_id": rota.id,
            "total_leituras": len(leituras),
            "limpeza": relatorio,
        }

    def __parse(self, conteudo_csv: str) -> list:
        reader = csv.reader(io.StringIO(conteudo_csv))
        start_time = None
        colunas = []

        for row in reader:
            if not row:
                continue
            primeiro = row[0].strip()
            if primeiro.startswith("# StartTime"):
                try:
                    start_time = self.__parse_start_time(row[0])
                except (ValueError, IndexError):
                    raise ValidationError(
                        "O cabeçalho '# StartTime' está em formato inválido. "
                        "Use '# StartTime = MM/DD/AAAA HH:MM:SS.mmm AM' (ou PM)."
                    )
            elif primeiro.lower().startswith("time"):
                colunas = [c.strip() for c in row]
                break

        if start_time is None:
            raise ValidationError("StartTime não encontrado no arquivo CSV.")

        indice_time = next(
            (i for i, c in enumerate(colunas) if c.lower().startswith("time")), None
        )
        if indice_time is None:
            raise ValidationError("Coluna de tempo não encontrada no arquivo CSV.")

        indice_atributo = {}
        for i, nome in enumerate(colunas):
            if nome in MAPEAMENTO_PADRAO:
                indice_atributo[i] = MAPEAMENTO_PADRAO[nome]

        if not indice_atributo:
            raise ValidationError(
                "Nenhuma coluna de telemetria reconhecida no arquivo CSV."
            )

        existentes = set()
        registros = []
        for row in reader:
            if not row:
                continue
            try:
                offset = float(row[indice_time])
            except (ValueError, IndexError, TypeError):
                continue
            data_hora = start_time + timedelta(seconds=offset)

            if data_hora in existentes:
                continue
            existentes.add(data_hora)

            dados = {"data_hora": data_hora}
            for i, atributo in indice_atributo.items():
                if i < len(row) and row[i].strip() != "":
                    try:
                        dados[atributo] = float(row[i])
                    except ValueError:
                        pass

            # Regra 2: uma leitura sem nenhum valor medido não é registrada.
            if len(dados) <= 1:
                continue
            registros.append(dados)

        return registros

    @staticmethod
    def __parse_start_time(linha: str) -> datetime:
        # Formato do cabeçalho: "# StartTime = 01/21/2026 08:41:21.0884 AM"
        s = linha.split("=", 1)[1].strip()
        return datetime.strptime(s, "%m/%d/%Y %I:%M:%S.%f %p")
