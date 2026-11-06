-- ============================================================
-- Script de criação do banco de dados do sistema de Telemetria Veicular (OBD-II).
-- Executado automaticamente pelo container do PostgreSQL
-- (montado em /docker-entrypoint-initdb.d/init.sql).
-- ============================================================

CREATE TABLE IF NOT EXISTS parametro (
    id_parametro SERIAL PRIMARY KEY,
    nome         VARCHAR(100) NOT NULL UNIQUE,
    unidade      VARCHAR(20)  NOT NULL,
    limite_min   DOUBLE PRECISION NOT NULL,
    limite_max   DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS veiculo (
    id_veiculo    SERIAL PRIMARY KEY,
    identificador VARCHAR(50)  NOT NULL UNIQUE,
    modelo        VARCHAR(100),
    data_cadastro TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mapeamento_parametro (
    id_mapeamento SERIAL PRIMARY KEY,
    nome_bruto    VARCHAR(200) NOT NULL UNIQUE,
    parametro_id  INTEGER NOT NULL REFERENCES parametro(id_parametro)
);

CREATE TABLE IF NOT EXISTS leitura (
    id_leitura         SERIAL PRIMARY KEY,
    veiculo_id         INTEGER NOT NULL REFERENCES veiculo(id_veiculo),
    data_hora          TIMESTAMP NOT NULL,
    velocidade         DOUBLE PRECISION,
    rpm                DOUBLE PRECISION,
    accel_x            DOUBLE PRECISION,
    accel_y            DOUBLE PRECISION,
    accel_z            DOUBLE PRECISION,
    posicao_acelerador DOUBLE PRECISION,
    latitude           DOUBLE PRECISION,
    longitude          DOUBLE PRECISION,
    CONSTRAINT uq_leitura_veiculo_data UNIQUE (veiculo_id, data_hora)
);

CREATE TABLE IF NOT EXISTS evento_risco (
    id_evento      SERIAL PRIMARY KEY,
    leitura_id     INTEGER NOT NULL REFERENCES leitura(id_leitura),
    veiculo_id     INTEGER NOT NULL REFERENCES veiculo(id_veiculo),
    forca_g        DOUBLE PRECISION,
    instabilidade  DOUBLE PRECISION,
    classificacao  VARCHAR(30),
    metodo         VARCHAR(30) NOT NULL,
    data_hora      TIMESTAMP NOT NULL,
    descricao      VARCHAR(255),
    CONSTRAINT uq_evento_leitura_metodo UNIQUE (leitura_id, metodo)
);
