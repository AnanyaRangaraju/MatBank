-- MatBank Clinical Data Schema
-- FHIR R4 Aligned | PostgreSQL
-- Mativa Diagnostics | Version 1.0

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. PATIENTS TABLE
-- Modeled after FHIR R4 Patient resource
CREATE TABLE patients (
    patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date_of_birth DATE,
    gestational_age_at_enrollment INTEGER,
    enrollment_date DATE,
    risk_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. OBSERVATIONS TABLE
-- Modeled after FHIR R4 Observation resource
-- Stores longitudinal clinical measurements per visit
CREATE TABLE observations (
    observation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(patient_id),
    observation_date DATE,
    observation_type VARCHAR(100),
    value_numeric DECIMAL,
    value_unit VARCHAR(50),
    gestational_week INTEGER,
    source_system VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. CONDITIONS TABLE
-- Modeled after FHIR R4 Condition resource
-- Stores formal clinical diagnoses per patient
CREATE TABLE conditions (
    condition_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(patient_id),
    condition_code VARCHAR(50),
    condition_name VARCHAR(200),
    onset_date DATE,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. BIOMARKERS TABLE
-- Placeholder for genomic and transcriptomic metadata
-- Intentionally flexible to accommodate future data formats
CREATE TABLE biomarkers (
    biomarker_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),