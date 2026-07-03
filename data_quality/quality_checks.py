# MatBank Data Quality and Validation Layer
# Automatically flags outliers, missing values, and corrupted records
# before downstream model ingestion
# Mativa Diagnostics | Version 1.0

import pandas as pd
import psycopg2
from datetime import datetime
import os

# Database connection
def get_connection():
    return psycopg2.connect(
        dbname="matbank",
        user="ananyarangaraju",
        host="localhost",
        port="5432"
    )

# Load observations from MatBank into a DataFrame
def load_observations():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT 
            o.observation_id,
            o.patient_id,
            o.observation_type,
            o.value_numeric,
            o.value_unit,
            o.gestational_week,
            o.observation_date,
            o.source_system
        FROM observations o
    """, conn)
    conn.close()
    return df

# Load patients from MatBank into a DataFrame
def load_patients():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT 
            patient_id,
            date_of_birth,
            gestational_age_at_enrollment,
            enrollment_date,
            risk_flag
        FROM patients
    """, conn)
    conn.close()
    return df

# 12 Clinical Validation Rules
def run_quality_checks(obs_df, patients_df):
    
    quarantine_log = []

    def flag(row, rule_id, reason):
        quarantine_log.append({
            "rule_id": rule_id,
            "observation_id": str(row.get("observation_id", "N/A")),
            "patient_id": str(row.get("patient_id", "N/A")),
            "observation_type": row.get("observation_type", "N/A"),
            "value_numeric": row.get("value_numeric", "N/A"),
            "gestational_week": row.get("gestational_week", "N/A"),
            "reason": reason,
            "flagged_at": datetime.now().isoformat()
        })

    print("\nRunning 12 clinical validation rules...\n")

    # Rule 1: Systolic blood pressure above 180 mmHg
    rule1 = obs_df[
        (obs_df["observation_type"] == "systolic_blood_pressure") &
        (obs_df["value_numeric"] > 180)
    ]
    for _, row in rule1.iterrows():
        flag(row, "RULE_01", f"Systolic BP {row['value_numeric']} mmHg exceeds clinical threshold of 180")
    print(f"Rule 01 - Systolic BP > 180: {len(rule1)} record(s) flagged")

    # Rule 2: Diastolic blood pressure above 120 mmHg
    rule2 = obs_df[
        (obs_df["observation_type"] == "diastolic_blood_pressure") &
        (obs_df["value_numeric"] > 120)
    ]
    for _, row in rule2.iterrows():
        flag(row, "RULE_02", f"Diastolic BP {row['value_numeric']} mmHg exceeds clinical threshold of 120")
    print(f"Rule 02 - Diastolic BP > 120: {len(rule2)} record(s) flagged")

    # Rule 3: Systolic blood pressure below 60 mmHg
    rule3 = obs_df[
        (obs_df["observation_type"] == "systolic_blood_pressure") &
        (obs_df["value_numeric"] < 60)
    ]
    for _, row in rule3.iterrows():
        flag(row, "RULE_03", f"Systolic BP {row['value_numeric']} mmHg below minimum threshold of 60")
    print(f"Rule 03 - Systolic BP < 60: {len(rule3)} record(s) flagged")

    # Rule 4: Blood glucose above 200 mg/dL
    rule4 = obs_df[
        (obs_df["observation_type"] == "blood_glucose") &
        (obs_df["value_numeric"] > 200)
    ]
    for _, row in rule4.iterrows():
        flag(row, "RULE_04", f"Blood glucose {row['value_numeric']} mg/dL exceeds threshold of 200")
    print(f"Rule 04 - Blood glucose > 200: {len(rule4)} record(s) flagged")

    # Rule 5: Urine protein above 0.3 g/dL - key preeclampsia indicator
    rule5 = obs_df[
        (obs_df["observation_type"] == "urine_protein") &
        (obs_df["value_numeric"] > 0.3)
    ]
    for _, row in rule5.iterrows():
        flag(row, "RULE_05", f"Urine protein {row['value_numeric']} g/dL exceeds preeclampsia threshold of 0.3")
    print(f"Rule 05 - Urine protein > 0.3 g/dL: {len(rule5)} record(s) flagged")

    # Rule 6: Missing gestational week
    rule6 = obs_df[obs_df["gestational_week"].isnull()]
    for _, row in rule6.iterrows():
        flag(row, "RULE_06", "Missing gestational week - cannot place observation on pregnancy timeline")
    print(f"Rule 06 - Missing gestational week: {len(rule6)} record(s) flagged")

    # Rule 7: Missing value_numeric
    rule7 = obs_df[obs_df["value_numeric"].isnull()]
    for _, row in rule7.iterrows():
        flag(row, "RULE_07", "Missing numeric value - observation cannot be used for analysis")
    print(f"Rule 07 - Missing value_numeric: {len(rule7)} record(s) flagged")

    # Rule 8: Gestational week out of valid range (1 to 42)
    rule8 = obs_df[
        (obs_df["gestational_week"] < 1) |
        (obs_df["gestational_week"] > 42)
    ]
    for _, row in rule8.iterrows():
        flag(row, "RULE_08", f"Gestational week {row['gestational_week']} outside valid range of 1 to 42")
    print(f"Rule 08 - Gestational week out of range: {len(rule8)} record(s) flagged")

    # Rule 9: Weight below 30 kg or above 200 kg
    rule9 = obs_df[
        (obs_df["observation_type"] == "weight") &
        ((obs_df["value_numeric"] < 30) | (obs_df["value_numeric"] > 200))
    ]
    for _, row in rule9.iterrows():
        flag(row, "RULE_09", f"Weight {row['value_numeric']} kg outside valid range of 30 to 200 kg")
    print(f"Rule 09 - Weight out of range: {len(rule9)} record(s) flagged")

    # Rule 10: Missing observation date
    rule10 = obs_df[obs_df["observation_date"].isnull()]
    for _, row in rule10.iterrows():
        flag(row, "RULE_10", "Missing observation date - cannot place on timeline")
    print(f"Rule 10 - Missing observation date: {len(rule10)} record(s) flagged")

    # Rule 11: Missing source system
    rule11 = obs_df[obs_df["source_system"].isnull()]
    for _, row in rule11.iterrows():
        flag(row, "RULE_11", "Missing source system - data provenance unknown")
    print(f"Rule 11 - Missing source system: {len(rule11)} record(s) flagged")

    # Rule 12: Duplicate observation - same patient, type, date, and gestational week
    rule12 = obs_df[
        obs_df.duplicated(
            subset=["patient_id", "observation_type", "observation_date", "gestational_week"],
            keep=False
        )
    ]
    for _, row in rule12.iterrows():
        flag(row, "RULE_12", "Duplicate observation detected - same patient, type, date, and gestational week")
    print(f"Rule 12 - Duplicate observations: {len(rule12)} record(s) flagged")

    return quarantine_log

# Save quarantine log to CSV
def save_quarantine_log(quarantine_log):
    if not quarantine_log:
        print("\nNo records flagged. Data quality is clean.")
        return
    
    df = pd.DataFrame(quarantine_log)
    output_path = "../data_quality/quarantine_log.csv"
    df.to_csv(output_path, index=False)
    print(f"\n{len(quarantine_log)} record(s) flagged and saved to quarantine_log.csv")
    print("\nQuarantine log summary:")
    print(df[["rule_id", "observation_type", "value_numeric", "reason"]].to_string(index=False))

# Main
if __name__ == "__main__":
    print("MatBank Data Quality Layer")
    print("=" * 50)
    
    obs_df = load_observations()
    patients_df = load_patients()
    
    print(f"Loaded {len(obs_df)} observations and {len(patients_df)} patients from MatBank")
    
    quarantine_log = run_quality_checks(obs_df, patients_df)
    save_quarantine_log(quarantine_log)
    
    total = len(obs_df)
    flagged = len(quarantine_log)
    clean = total - flagged
    failure_rate = (flagged / total * 100) if total > 0 else 0
    
    print(f"\nData Quality Summary")
    print(f"=" * 50)
    print(f"Total observations: {total}")
    print(f"Clean records: {clean}")
    print(f"Flagged records: {flagged}")
    print(f"Failure rate: {failure_rate:.1f}%")