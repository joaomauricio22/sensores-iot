-- ============================================================
-- Script de criação do banco de dados do sistema de Telemetria Veicular.
-- Executado automaticamente pelo container do PostgreSQL
-- (montado em /docker-entrypoint-initdb.d/init.sql).
-- ============================================================

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario    SERIAL PRIMARY KEY,
    nome          VARCHAR(100) NOT NULL UNIQUE,
    senha         VARCHAR(200) NOT NULL,
    data_cadastro TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rota (
    id_rota        SERIAL PRIMARY KEY,
    usuario_id     INTEGER NOT NULL REFERENCES usuario(id_usuario),
    nome           VARCHAR(100) NOT NULL,
    arquivo_origem VARCHAR(200),
    data_importacao TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS leitura (
    id_leitura         SERIAL PRIMARY KEY,
    rota_id            INTEGER NOT NULL REFERENCES rota(id_rota),
    data_hora          TIMESTAMP NOT NULL,
    velocidade         DOUBLE PRECISION,
    rpm                DOUBLE PRECISION,
    accel_x            DOUBLE PRECISION,
    accel_y            DOUBLE PRECISION,
    accel_z            DOUBLE PRECISION,
    posicao_acelerador DOUBLE PRECISION,
    latitude           DOUBLE PRECISION,
    longitude          DOUBLE PRECISION,
    CONSTRAINT uq_leitura_rota_data UNIQUE (rota_id, data_hora)
);

CREATE TABLE IF NOT EXISTS evento_risco (
    id_evento      SERIAL PRIMARY KEY,
    leitura_id     INTEGER NOT NULL REFERENCES leitura(id_leitura),
    rota_id        INTEGER NOT NULL REFERENCES rota(id_rota),
    forca_g        DOUBLE PRECISION,
    instabilidade  DOUBLE PRECISION,
    classificacao  VARCHAR(30),
    metodo         VARCHAR(30) NOT NULL,
    data_hora      TIMESTAMP NOT NULL,
    descricao      VARCHAR(255),
    CONSTRAINT uq_evento_leitura_metodo UNIQUE (leitura_id, metodo)
);
