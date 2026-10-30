# Schemas (DTOs) da API.
# Cada entidade possui um RequestSchema (valida/parseia a entrada)
# e um ResponseSchema (serializa a saída para JSON).
from marshmallow import Schema, fields


class TipoSensorResponseSchema(Schema):
    id = fields.Int()
    nome = fields.Str()
    unidade = fields.Str()
    descricao = fields.Str()


class TipoSensorRequestSchema(Schema):
    nome = fields.Str(required=True)
    unidade = fields.Str(required=True)
    descricao = fields.Str(allow_none=True)


class SensorResponseSchema(Schema):
    id = fields.Int()
    identificador = fields.Str()
    nome = fields.Str()
    tipo_sensor_id = fields.Int()
    limite_min = fields.Float()
    limite_max = fields.Float()
    data_cadastro = fields.DateTime()


class SensorRequestSchema(Schema):
    identificador = fields.Str(required=True)
    nome = fields.Str(allow_none=True)
    tipo_sensor_id = fields.Int(required=True)
    limite_min = fields.Float(required=True)
    limite_max = fields.Float(required=True)


class LeituraResponseSchema(Schema):
    id = fields.Int()
    sensor_id = fields.Int()
    valor = fields.Float()
    data_hora = fields.DateTime()
    classificacao = fields.Str(allow_none=True)


class LeituraRequestSchema(Schema):
    sensor_id = fields.Int(required=True)
    valor = fields.Float(required=True)
    data_hora = fields.DateTime(required=True)


class AnomaliaResponseSchema(Schema):
    id = fields.Int()
    leitura_id = fields.Int()
    sensor_id = fields.Int()
    valor = fields.Float()
    data_hora = fields.DateTime()
    metodo = fields.Str()
    descricao = fields.Str(allow_none=True)


class AnomaliaRequestSchema(Schema):
    leitura_id = fields.Int(required=True)
    sensor_id = fields.Int(required=True)
    valor = fields.Float(required=True)
    data_hora = fields.DateTime(required=True)
    metodo = fields.Str(required=True)
    descricao = fields.Str(allow_none=True)
