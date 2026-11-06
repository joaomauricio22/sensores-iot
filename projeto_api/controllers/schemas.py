# Schemas (DTOs) da API.
# Cada entidade possui um RequestSchema (valida/parseia a entrada)
# e um ResponseSchema (serializa a saída para JSON).
from marshmallow import Schema, fields


class VeiculoResponseSchema(Schema):
    id = fields.Int()
    identificador = fields.Str()
    modelo = fields.Str(allow_none=True)
    data_cadastro = fields.DateTime()


class VeiculoRequestSchema(Schema):
    identificador = fields.Str(required=True)
    modelo = fields.Str(allow_none=True)


class ParametroResponseSchema(Schema):
    id = fields.Int()
    nome = fields.Str()
    unidade = fields.Str()
    limite_min = fields.Float()
    limite_max = fields.Float()


class ParametroRequestSchema(Schema):
    nome = fields.Str(required=True)
    unidade = fields.Str(required=True)
    limite_min = fields.Float(required=True)
    limite_max = fields.Float(required=True)


class MapeamentoResponseSchema(Schema):
    id = fields.Int()
    nome_bruto = fields.Str()
    parametro_id = fields.Int()


class MapeamentoRequestSchema(Schema):
    nome_bruto = fields.Str(required=True)
    parametro_id = fields.Int(required=True)


class LeituraResponseSchema(Schema):
    id = fields.Int()
    veiculo_id = fields.Int()
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
    veiculo_id = fields.Int(required=True)
    data_hora = fields.DateTime(required=True)
    velocidade = fields.Float(allow_none=True)
    rpm = fields.Float(allow_none=True)
    accel_x = fields.Float(allow_none=True)
    accel_y = fields.Float(allow_none=True)
    accel_z = fields.Float(allow_none=True)
    posicao_acelerador = fields.Float(allow_none=True)
    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)


class EventoRiscoResponseSchema(Schema):
    id = fields.Int()
    leitura_id = fields.Int()
    veiculo_id = fields.Int()
    forca_g = fields.Float(allow_none=True)
    instabilidade = fields.Float(allow_none=True)
    classificacao = fields.Str(allow_none=True)
    metodo = fields.Str()
    data_hora = fields.DateTime()
    descricao = fields.Str(allow_none=True)


class EventoRiscoRequestSchema(Schema):
    leitura_id = fields.Int(required=True)
    veiculo_id = fields.Int(required=True)
    data_hora = fields.DateTime(required=True)
    metodo = fields.Str(required=True)
    forca_g = fields.Float(allow_none=True)
    instabilidade = fields.Float(allow_none=True)
    classificacao = fields.Str(allow_none=True)
    descricao = fields.Str(allow_none=True)
