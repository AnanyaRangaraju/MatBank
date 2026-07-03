# MatBank - Maternal Health Clinical Data Pipeline
### Mativa Diagnostics | Built by Ananya Rangaraju | July 2026

A longitudinal clinical and biomarker data pipeline designed to serve as the 
training and inference data layer for future LLM and ML powered preeclampsia 
and maternal risk prediction workflows.


---

## The Problem

Preeclampsia affects 1 in 25 pregnancies in the US and is one of the leading 
causes of maternal mortality. The warning signs are detectable in clinical data 
but current healthcare systems look at each measurement in isolation rather than 
tracking trajectories over time.

A blood pressure reading of 138 mmHg at week 20 looks borderline on its own.
But when you see 118 at week 12, 124 at week 16, and 138 at week 20, that 
upward trend tells a completely different story.

MatBank is the data infrastructure that makes that trajectory visible.

---

## Architecture

```
FHIR R4 JSON Bundles
        |
        v
Python ETL Pipeline (fhir_etl.py)
        |
        v
PostgreSQL MatBank Schema
        |
        v
12-Rule Data Quality Layer (quality_checks.py)
        |
        v
Clean Longitudinal Data - Ready for ML/LLM Inference
```

---

## Project Structure

```
matbank/
├── schema/
│   └── matbank_schema.sql        # FHIR R4 aligned PostgreSQL schema
├── etl/
│   └── fhir_etl.py               # FHIR JSON to PostgreSQL ETL pipeline
├── data_quality/
│   ├── quality_checks.py         # 12-rule automated validation layer
│   └── quarantine_log.csv        # Flagged and quarantined records
├── data/
│   ├── patient_001.json          # Mock FHIR bundle - suspected preeclampsia
│   ├── patient_002.json          # Mock FHIR bundle - gestational diabetes
│   └── patient_003.json          # Mock FHIR bundle - severe preeclampsia
└── docs/
    └── MatBank_Schema_Draft.docx # Full schema design document
```

---

## The Schema

Four FHIR R4 aligned tables in PostgreSQL:

| Table | FHIR Resource | Purpose |
|---|---|---|
| patients | Patient | One row per enrolled patient |
| observations | Observation | Longitudinal clinical measurements per visit |
| conditions | Condition | Formal diagnoses per patient |
| biomarkers | - | Genomic and transcriptomic metadata placeholder |

All tables link back to patients via patient_id.
Every observation is tagged with a gestational_week for trajectory analysis.

---

## Pillar 1 - Schema Design

FHIR R4 aligned relational schema covering 7 core clinical indicators:

- Systolic blood pressure
- Diastolic blood pressure
- Urine protein
- Weight
- Blood glucose
- Fundal height
- Fetal heart rate


---

## Pillar 2 - FHIR ETL Pipeline

Python pipeline that parses HL7/FHIR R4 JSON bundles and loads them 
into MatBank across 3 resource types: Patient, Observation, Condition.

To run:

```bash
cd etl
python3 fhir_etl.py
```

Sample output:

```
Processing: ../data/patient_001.json
Inserted patient: c6e59f30-d620-4e68-b34a-ae2973b86cc5
Inserted observation: systolic_blood_pressure = 118 mmHg at week 12
Inserted observation: systolic_blood_pressure = 124 mmHg at week 16
Inserted observation: systolic_blood_pressure = 138 mmHg at week 20
Inserted condition: Mild preeclampsia (O14.0) - suspected
```

---

## Pillar 3 - Data Quality Layer

12-rule automated validation layer using Python and Pandas.
Flags outliers, missing values, and corrupted records before 
downstream model ingestion.

| Rule | Check |
|---|---|
| RULE_01 | Systolic BP above 180 mmHg |
| RULE_02 | Diastolic BP above 120 mmHg |
| RULE_03 | Systolic BP below 60 mmHg |
| RULE_04 | Blood glucose above 200 mg/dL |
| RULE_05 | Urine protein above 0.3 g/dL |
| RULE_06 | Missing gestational week |
| RULE_07 | Missing numeric value |
| RULE_08 | Gestational week outside 1 to 42 |
| RULE_09 | Weight outside 30 to 200 kg |
| RULE_10 | Missing observation date |
| RULE_11 | Missing source system |
| RULE_12 | Duplicate observation |

To run:

```bash
cd data_quality
python3 quality_checks.py
```

Sample output:

```
Total observations: 20
Clean records: 18
Flagged records: 2
Failure rate: 10.0%

RULE_01 - systolic_blood_pressure - 999.0 mmHg - exceeds threshold of 180
RULE_05 - urine_protein - 0.45 g/dL - exceeds preeclampsia threshold of 0.3
```

---

## AI/ML Readiness

MatBank is designed as the data foundation for future clinical AI workflows:

- Longitudinal schema enables time-series feature engineering for ML models
- FHIR R4 alignment enables direct ingestion from hospital EHR systems
- Clean structured data supports LLM fine-tuning and agent grounding
- Data quality layer ensures trustworthy inputs to AI inference pipelines
- Schema supports RAG-style clinical context retrieval for future AI agents

---

## Tech Stack

- Python 3.12
- PostgreSQL 15
- pandas
- psycopg2
- HL7/FHIR R4

---

## Built For

Mativa Diagnostics - pioneering the next generation of pregnancy care.
Developed in collaboration with University of Pennsylvania Medical Center 
and the Wistar Institute.

---

*This is a working prototype. Schema and pipeline are under active development.*
