-- ============================================================
-- Script de criação do banco de dados do sistema de Telemetria Veicular.
-- Executado automaticamente pelo container do PostgreSQL
-- (montado em /docker-entrypoint-initdb.d/init.sql).
--
-- Modelo com 3 tabelas:
--   rota 1 ── N leitura 1 ── N evento_risco
-- ============================================================

CREATE TABLE IF NOT EXISTS rota (
    id_rota          SERIAL PRIMARY KEY,
    nome             VARCHAR(100) NOT NULL,
    arquivo_origem   VARCHAR(200),
    data_importacao  TIMESTAMP NOT NULL DEFAULT NOW(),
    -- Marca o instante da última análise (eventos de risco). NULL = ainda não
    -- analisada. Permite pular a reanálise e detectar leituras novas/editadas.
    data_analise     TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leitura (
    id_leitura         SERIAL PRIMARY KEY,
    rota_id            INTEGER NOT NULL REFERENCES rota(id_rota) ON DELETE CASCADE,
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
    leitura_id     INTEGER NOT NULL REFERENCES leitura(id_leitura) ON DELETE CASCADE,
    rota_id        INTEGER NOT NULL REFERENCES rota(id_rota) ON DELETE CASCADE,
    canal          VARCHAR(30) NOT NULL DEFAULT 'geral',
    valor          DOUBLE PRECISION,
    forca_g        DOUBLE PRECISION,
    instabilidade  DOUBLE PRECISION,
    classificacao  VARCHAR(40) NOT NULL DEFAULT 'Comportamento atípico',
    metodo         VARCHAR(30) NOT NULL,
    data_hora      TIMESTAMP NOT NULL,
    descricao      VARCHAR(255),
    CONSTRAINT uq_evento_leitura_metodo_clas_canal
        UNIQUE (leitura_id, metodo, classificacao, canal)
);

-- A constraint UNIQUE (rota_id, data_hora) já cria o índice usado para
-- buscar as leituras de uma rota em ordem cronológica.
CREATE INDEX IF NOT EXISTS idx_evento_risco_rota ON evento_risco (rota_id);
