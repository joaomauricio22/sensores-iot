# Schemas (DTOs) da API.
from marshmallow import Schema, fields


# --------------------------------------------------------------------------- #
# Rota
# --------------------------------------------------------------------------- #
class RotaResponseSchema(Schema):
    id = fields.Int()
    nome = fields.Str()
    arquivo_origem = fields.Str(allow_none=True)
    data_importacao = fields.DateTime()


class RotaRequestSchema(Schema):
    nome = fields.Str(required=True)
    arquivo_origem = fields.Str(allow_none=True)


class ImportarRequestSchema(Schema):
    nome = fields.Str(required=True)
    arquivo_origem = fields.Str(allow_none=True)
    conteudo_csv = fields.Str(required=True)


# --------------------------------------------------------------------------- #
# Leitura
# --------------------------------------------------------------------------- #
class LeituraResponseSchema(Schema):
    id = fields.Int()
    rota_id = fields.Int()
    data_hora = fields.DateTime()
    velocidade = fields.Float(allow_none=True)
    rpm = fields.Float(allow_none=True)
    accel_x = fields.Float(allow_none=True)
    accel_y = fields.Float(allow_none=True)
    accel_z = fields.Float(allow_none=True)
    posicao_acelerador = fields.Float(allow_none=True)
    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)


class LeituraRequestSchema(Schema):
    rota_id = fields.Int(required=True)
    data_hora = fields.DateTime(required=True)
    velocidade = fields.Float(allow_none=True)
    rpm = fields.Float(allow_none=True)
    accel_x = fields.Float(allow_none=True)
    accel_y = fields.Float(allow_none=True)
    accel_z = fields.Float(allow_none=True)
    posicao_acelerador = fields.Float(allow_none=True)
    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)


# --------------------------------------------------------------------------- #
# Evento de risco
# --------------------------------------------------------------------------- #
class EventoRiscoResponseSchema(Schema):
    id = fields.Int()
    leitura_id = fields.Int()
    rota_id = fields.Int()
    canal = fields.Str()
    valor = fields.Float(allow_none=True)
    forca_g = fields.Float(allow_none=True)
    instabilidade = fields.Float(allow_none=True)
    classificacao = fields.Str(allow_none=True)
    metodo = fields.Str()
    data_hora = fields.DateTime()
    descricao = fields.Str(allow_none=True)


class EventoRiscoRequestSchema(Schema):
    leitura_id = fields.Int(required=True)
    metodo = fields.Str(required=True)
    rota_id = fields.Int(allow_none=True)
    data_hora = fields.DateTime(allow_none=True)
    canal = fields.Str(allow_none=True)
    valor = fields.Float(allow_none=True)
    forca_g = fields.Float(allow_none=True)
    instabilidade = fields.Float(allow_none=True)
    classificacao = fields.Str(allow_none=True)
    descricao = fields.Str(allow_none=True)
