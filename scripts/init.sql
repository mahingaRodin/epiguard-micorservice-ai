-- EpiGuard PostgreSQL schema
-- Full schema lives in the main epiguard repo scripts/init.sql
-- This file is used for the epiguard-ai standalone dev environment

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE gender_type    AS ENUM ('MALE', 'FEMALE', 'OTHER');
CREATE TYPE priority_level AS ENUM ('LOW', 'MEDIUM', 'HIGH');

CREATE TABLE IF NOT EXISTS patients (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    age          INT          NOT NULL,
    gender       gender_type  NOT NULL,
    district     VARCHAR(50)  NOT NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS symptoms (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id   UUID         NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    symptom_type VARCHAR(50)  NOT NULL,
    severity     INT          NOT NULL CHECK (severity >= 1 AND severity <= 5),
    recorded_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS triage_results (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id       UUID           NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    risk_score       DECIMAL(5,4)   NOT NULL,
    priority_level   priority_level NOT NULL,
    predicted_disease VARCHAR(100),
    created_at       TIMESTAMP      NOT NULL DEFAULT NOW()
);
