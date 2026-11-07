import csv
import io
from datetime import datetime, timedelta

from marshmallow import ValidationError

from entities.Base import db
from entities.Leitura import Leitura
from entities.Rota import Rota
from repositories.RotaRepository import RotaRepository
from repositories.UsuarioRepository import UsuarioRepository


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
    "Acelere Y (m/s²)": "accel_y",
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

    def __init__(self):
        self.__rota_repository = RotaRepository()
        self.__usuario_repository = UsuarioRepository()

    def importar_csv(self, usuario_id: int, nome: str, arquivo_origem: str, conteudo_csv: str) -> dict:
        """Importa um CSV (texto) para um usuário, criando a Rota e as Leituras."""
        if self.__usuario_repository.get_by_id(usuario_id) is None:
            raise ValidationError("Usuário não cadastrado.")
        if not nome or not str(nome).strip():
            raise ValidationError("O nome da rota é obrigatório.")

        rota = self.__rota_repository.add(
            Rota(usuario_id=usuario_id, nome=nome, arquivo_origem=arquivo_origem)
        )

        leituras = self.__parse(rota.id, conteudo_csv)
        db.session.add_all(leituras)
        db.session.commit()

        return {"rota_id": rota.id, "total_leituras": len(leituras)}

    def __parse(self, rota_id: int, conteudo_csv: str) -> list:
        reader = csv.reader(io.StringIO(conteudo_csv))
        start_time = None
        colunas = []

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
            raise ValidationError("StartTime não encontrado no arquivo CSV.")

        indice_time = next(
            (i for i, c in enumerate(colunas) if c.lower().startswith("time")), None
        )
        indice_atributo = {}
        for i, nome in enumerate(colunas):
            if nome in MAPEAMENTO_PADRAO:
                indice_atributo[i] = MAPEAMENTO_PADRAO[nome]

        existentes = set()
        leituras = []
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
            for i, atributo in indice_atributo.items():
                if i < len(row) and row[i].strip() != "":
                    try:
                        dados[atributo] = float(row[i])
                    except ValueError:
                        pass

            leituras.append(Leitura(rota_id=rota_id, data_hora=data_hora, **dados))

        return leituras

    @staticmethod
    def __parse_start_time(linha: str) -> datetime:
        # Formato do cabeçalho: "# StartTime = 01/21/2026 08:41:21.0884 AM"
        s = linha.split("=", 1)[1].strip()
        return datetime.strptime(s, "%m/%d/%Y %I:%M:%S.%f %p")
