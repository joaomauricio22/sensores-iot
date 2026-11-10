"""Leitura e validação dos limiares e do catálogo de sensores.

Os parâmetros ficam em `config/limiares.json` (fonte única, versionada no
repositório). O arquivo é relido quando muda no disco, então editar o JSON e
chamar a API novamente já reflete o novo valor, sem rebuild.
"""
import copy
import json
import math
import os

from marshmallow import ValidationError

CAMINHO_PADRAO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "limiares.json",
)

LIMIARES_OBRIGATORIOS = {
    "velocidade_max",
    "rpm_max",
    "aceleracao_max",
    "frenagem_max",
    "lateral_max",
    "curva_velocidade_min",
    "acelerador_delta_max",
    "zscore_max",
}

# Limiares opcionais: podem existir no JSON, mas não são obrigatórios. Quando
# ausentes, o código usa um padrão (ex.: ``forca_g_max`` cai em ``lateral_max``).
LIMIARES_OPCIONAIS = {"forca_g_max"}

SENSORES_OBRIGATORIOS = {
    "velocidade",
    "rpm",
    "accel_x",
    "accel_y",
    "accel_z",
    "posicao_acelerador",
    "latitude",
    "longitude",
}

CAMPOS_SENSOR = {"id", "nome", "unidade", "min", "max"}


class LimiaresService:
    """Acessa os limiares de detecção e o catálogo de sensores."""

    def __init__(self, caminho: str = None):
        self.__caminho = caminho or CAMINHO_PADRAO
        self.__cache = None
        self.__mtime = None

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #
    def get_limiares(self) -> dict:
        return copy.deepcopy(self.__carregar()["limiares"])

    def get_sensores(self) -> dict:
        return copy.deepcopy(self.__carregar()["sensores"])

    # ------------------------------------------------------------------ #
    # Carregamento e validação
    # ------------------------------------------------------------------ #
    def __carregar(self) -> dict:
        if not os.path.exists(self.__caminho):
            raise ValidationError(
                f"Arquivo de configuração não encontrado: {self.__caminho}"
            )

        mtime = os.path.getmtime(self.__caminho)
        if self.__cache is not None and mtime == self.__mtime:
            return self.__cache

        try:
            with open(self.__caminho, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except json.JSONDecodeError as erro:
            raise ValidationError(
                f"JSON inválido em {self.__caminho}: linha {erro.lineno}, "
                f"coluna {erro.colno} ({erro.msg})."
            )

        normalizado = self.__validar(dados)
        self.__cache = normalizado
        self.__mtime = mtime
        return normalizado

    def __validar(self, dados) -> dict:
        if not isinstance(dados, dict):
            raise ValidationError("O JSON deve ser um objeto com 'limiares' e 'sensores'.")

        for secao in ("limiares", "sensores"):
            if secao not in dados or not isinstance(dados[secao], dict):
                raise ValidationError(f"A seção '{secao}' é obrigatória e deve ser um objeto.")

        limiares = self.__validar_limiares(dados["limiares"])
        sensores = self.__validar_sensores(dados["sensores"])
        return {"limiares": limiares, "sensores": sensores}

    def __validar_limiares(self, limiares: dict) -> dict:
        faltando = LIMIARES_OBRIGATORIOS - set(limiares)
        if faltando:
            raise ValidationError(
                "Limiares ausentes no JSON: " + ", ".join(sorted(faltando)) + "."
            )
        extras = set(limiares) - LIMIARES_OBRIGATORIOS - LIMIARES_OPCIONAIS
        if extras:
            raise ValidationError(
                "Limiares desconhecidos no JSON: " + ", ".join(sorted(extras)) + "."
            )

        normalizados = {}
        for chave, valor in limiares.items():
            normalizados[chave] = self.__numero(valor, f"limiares.{chave}")

        if normalizados["velocidade_max"] <= 0:
            raise ValidationError("'velocidade_max' deve ser maior que zero.")
        if normalizados["rpm_max"] <= 0:
            raise ValidationError("'rpm_max' deve ser maior que zero.")
        if normalizados["aceleracao_max"] <= 0:
            raise ValidationError("'aceleracao_max' deve ser maior que zero.")
        if normalizados["frenagem_max"] >= 0:
            raise ValidationError("'frenagem_max' deve ser negativo.")
        if normalizados["lateral_max"] <= 0:
            raise ValidationError("'lateral_max' deve ser maior que zero.")
        if normalizados.get("forca_g_max") is not None and normalizados["forca_g_max"] <= 0:
            raise ValidationError("'forca_g_max' deve ser maior que zero.")
        if normalizados["curva_velocidade_min"] < 0:
            raise ValidationError("'curva_velocidade_min' não pode ser negativo.")
        if normalizados["acelerador_delta_max"] <= 0:
            raise ValidationError("'acelerador_delta_max' deve ser maior que zero.")
        if normalizados["zscore_max"] <= 0:
            raise ValidationError("'zscore_max' deve ser maior que zero.")
        if normalizados["curva_velocidade_min"] > normalizados["velocidade_max"]:
            raise ValidationError(
                "'curva_velocidade_min' não pode ser maior que 'velocidade_max'."
            )
        return normalizados

    def __validar_sensores(self, sensores: dict) -> dict:
        faltando = SENSORES_OBRIGATORIOS - set(sensores)
        if faltando:
            raise ValidationError(
                "Sensores ausentes no JSON: " + ", ".join(sorted(faltando)) + "."
            )
        extras = set(sensores) - SENSORES_OBRIGATORIOS
        if extras:
            raise ValidationError(
                "Sensores desconhecidos no JSON: " + ", ".join(sorted(extras)) + "."
            )

        normalizados = {}
        ids = set()
        for canal, dados in sensores.items():
            if not isinstance(dados, dict):
                raise ValidationError(f"O sensor '{canal}' deve ser um objeto.")
            faltando_campos = CAMPOS_SENSOR - set(dados)
            if faltando_campos:
                raise ValidationError(
                    f"O sensor '{canal}' não possui: "
                    + ", ".join(sorted(faltando_campos)) + "."
                )
            for campo in ("id", "nome", "unidade"):
                if not isinstance(dados[campo], str) or not dados[campo].strip():
                    raise ValidationError(
                        f"O campo '{campo}' do sensor '{canal}' deve ser um texto não vazio."
                    )
            if dados["id"] in ids:
                raise ValidationError(f"O identificador '{dados['id']}' está repetido.")
            ids.add(dados["id"])

            minimo = self.__numero(dados["min"], f"sensores.{canal}.min")
            maximo = self.__numero(dados["max"], f"sensores.{canal}.max")
            if minimo >= maximo:
                raise ValidationError(
                    f"Em 'sensores.{canal}', o mínimo deve ser menor que o máximo."
                )

            normalizados[canal] = {
                "id": dados["id"].strip(),
                "nome": dados["nome"].strip(),
                "unidade": dados["unidade"].strip(),
                "min": minimo,
                "max": maximo,
            }

        # Faixas físicas óbvias (evitam configuração absurda).
        self.__exigir_faixa(normalizados, "posicao_acelerador", 0.0, 100.0)
        self.__exigir_faixa(normalizados, "latitude", -90.0, 90.0)
        self.__exigir_faixa(normalizados, "longitude", -180.0, 180.0)
        return normalizados

    def __exigir_faixa(self, sensores, canal, minimo, maximo):
        sensor = sensores[canal]
        if sensor["min"] < minimo or sensor["max"] > maximo:
            raise ValidationError(
                f"O sensor '{canal}' deve estar na faixa [{minimo}, {maximo}]."
            )

    def __numero(self, valor, nome) -> float:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValidationError(f"'{nome}' deve ser numérico.")
        valor = float(valor)
        if not math.isfinite(valor):
            raise ValidationError(f"'{nome}' deve ser um número finito.")
        return valor
