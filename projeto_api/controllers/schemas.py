# Schemas (DTOs) da API.
from marshmallow import Schema, fields


class UsuarioResponseSchema(Schema):
    id = fields.Int()
    nome = fields.Str()
    data_cadastro = fields.DateTime()


class UsuarioRequestSchema(Schema):
    nome = fields.Str(required=True)
    senha = fields.Str(required=True)


class LoginRequestSchema(Schema):
    nome = fields.Str(required=True)
    senha = fields.Str(required=True)


class RotaResponseSchema(Schema):
    id = fields.Int()
    usuario_id = fields.Int()
    nome = fields.Str()
    arquivo_origem = fields.Str(allow_none=True)
    data_importacao = fields.DateTime()


class RotaRequestSchema(Schema):
    usuario_id = fields.Int(required=True)
    nome = fields.Str(required=True)
    arquivo_origem = fields.Str(allow_none=True)


class ImportarRequestSchema(Schema):
    usuario_id = fields.Int(required=True)
    nome = fields.Str(required=True)
    arquivo_origem = fields.Str(allow_none=True)
    conteudo_csv = fields.Str(required=True)


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


class EventoRiscoResponseSchema(Schema):
    id = fields.Int()
    leitura_id = fields.Int()
    rota_id = fields.Int()
    forca_g = fields.Float(allow_none=True)
    instabilidade = fields.Float(allow_none=True)
    classificacao = fields.Str(allow_none=True)
    metodo = fields.Str()
    data_hora = fields.DateTime()
    descricao = fields.Str(allow_none=True)


class EventoRiscoRequestSchema(Schema):
    leitura_id = fields.Int(required=True)
    rota_id = fields.Int(required=True)
    data_hora = fields.DateTime(required=True)
    metodo = fields.Str(required=True)
    forca_g = fields.Float(allow_none=True)
    instabilidade = fields.Float(allow_none=True)
    classificacao = fields.Str(allow_none=True)
    descricao = fields.Str(allow_none=True)


class ConfiguracaoResponseSchema(Schema):
    id = fields.Int()
    chave = fields.Str()
    valor = fields.Str()


class ConfiguracaoRequestSchema(Schema):
    chave = fields.Str(required=True)
    valor = fields.Str(required=True)


class ConfiguracaoUpdateSchema(Schema):
    chave = fields.Str(allow_none=True)
    valor = fields.Str(allow_none=True)


class LimiaresRequestSchema(Schema):
    velocidade_max = fields.Float(allow_none=True)
    rpm_max = fields.Float(allow_none=True)
    aceleracao_max = fields.Float(allow_none=True)
    frenagem_max = fields.Float(allow_none=True)
    lateral_max = fields.Float(allow_none=True)
    curva_velocidade_min = fields.Float(allow_none=True)
    acelerador_delta_max = fields.Float(allow_none=True)
