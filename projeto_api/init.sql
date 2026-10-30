-- ============================================================
-- Script de criação do banco de dados do sistema de Sensores IoT.
-- Executado automaticamente pelo container do PostgreSQL
-- (montado em /docker-entrypoint-initdb.d/init.sql).
-- ============================================================

CREATE TABLE IF NOT EXISTS tipo_sensor (
    id_tipo_sensor SERIAL PRIMARY KEY,
    nome           VARCHAR(100) NOT NULL UNIQUE,
    unidade        VARCHAR(20)  NOT NULL,
    descricao      VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS sensor (
    id_sensor      SERIAL PRIMARY KEY,
    identificador  VARCHAR(100) NOT NULL UNIQUE,
    nome           VARCHAR(200),
    tipo_sensor_id INTEGER      NOT NULL REFERENCES tipo_sensor(id_tipo_sensor),
    limite_min     DOUBLE PRECISION NOT NULL,
    limite_max     DOUBLE PRECISION NOT NULL,
    data_cadastro  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS leitura (
    id_leitura    SERIAL PRIMARY KEY,
    sensor_id     INTEGER NOT NULL REFERENCES sensor(id_sensor),
    valor         DOUBLE PRECISION NOT NULL,
    data_hora     TIMESTAMP NOT NULL,
    classificacao VARCHAR(20),
    CONSTRAINT uq_leitura_sensor_valor_data UNIQUE (sensor_id, valor, data_hora)
);

CREATE TABLE IF NOT EXISTS anomalia (
    id_anomalia SERIAL PRIMARY KEY,
    leitura_id  INTEGER NOT NULL REFERENCES leitura(id_leitura),
    sensor_id   INTEGER NOT NULL REFERENCES sensor(id_sensor),
    valor       DOUBLE PRECISION NOT NULL,
    data_hora   TIMESTAMP NOT NULL,
    metodo      VARCHAR(30) NOT NULL,
    descricao   VARCHAR(255),
    CONSTRAINT uq_anomalia_leitura_metodo UNIQUE (leitura_id, metodo)
);
