-- Migration: Create predictor app tables
-- This matches Django models from apps/predictor/models.py

-- IHSG Historical Data
CREATE TABLE IF NOT EXISTS predictor_historicaldata (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    close DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_historicaldata_date ON predictor_historicaldata(date DESC);

-- IHSG Prediction Results
CREATE TABLE IF NOT EXISTS predictor_predictionresult (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    yhat DOUBLE PRECISION NOT NULL,
    yhat_lower DOUBLE PRECISION NOT NULL,
    yhat_upper DOUBLE PRECISION NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date, model_version)
);
CREATE INDEX IF NOT EXISTS idx_predictionresult_model ON predictor_predictionresult(model_version);

-- IHSG Model Versions
CREATE TABLE IF NOT EXISTS predictor_modelversion (
    id BIGSERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    trained_at TIMESTAMPTZ NOT NULL,
    data_end_date DATE NOT NULL,
    metrics JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_modelversion_active ON predictor_modelversion(is_active);

-- USD/IDR Historical Data
CREATE TABLE IF NOT EXISTS predictor_usdidrhistoricaldata (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    close DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_usdidrhistoricaldata_date ON predictor_usdidrhistoricaldata(date DESC);

-- USD/IDR Prediction Results
CREATE TABLE IF NOT EXISTS predictor_usdidrpredictionresult (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    yhat DOUBLE PRECISION NOT NULL,
    yhat_lower DOUBLE PRECISION NOT NULL,
    yhat_upper DOUBLE PRECISION NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date, model_version)
);
CREATE INDEX IF NOT EXISTS idx_usdidrpredictionresult_model ON predictor_usdidrpredictionresult(model_version);

-- Django required tables (minimal for migrations tracking)
CREATE TABLE IF NOT EXISTS django_migrations (
    id BIGSERIAL PRIMARY KEY,
    app VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied TIMESTAMPTZ NOT NULL
);

-- Celery Beat schedule tables (minimal)
CREATE TABLE IF NOT EXISTS django_celery_beat_crontabschedule (
    id BIGSERIAL PRIMARY KEY,
    minute VARCHAR(240) NOT NULL DEFAULT '*',
    hour VARCHAR(96) NOT NULL DEFAULT '*',
    day_of_week VARCHAR(64) NOT NULL DEFAULT '*',
    day_of_month VARCHAR(124) NOT NULL DEFAULT '*',
    month_of_year VARCHAR(64) NOT NULL DEFAULT '*',
    timezone VARCHAR(63) NOT NULL DEFAULT 'UTC'
);

CREATE TABLE IF NOT EXISTS django_celery_beat_periodictask (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    task VARCHAR(200) NOT NULL,
    crontab_id BIGINT REFERENCES django_celery_beat_crontabschedule(id),
    args TEXT NOT NULL DEFAULT '[]',
    kwargs TEXT NOT NULL DEFAULT '{}',
    queue VARCHAR(200),
    exchange VARCHAR(200),
    routing_key VARCHAR(200),
    expires TIMESTAMPTZ,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_run_at TIMESTAMPTZ,
    total_run_count INTEGER NOT NULL DEFAULT 0,
    date_changed TIMESTAMPTZ DEFAULT NOW(),
    description TEXT NOT NULL DEFAULT ''
);
