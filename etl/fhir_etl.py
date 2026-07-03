# MatBank FHIR ETL Pipeline
# Parses HL7/FHIR R4 JSON bundles and loads into MatBank PostgreSQL schema
# Mativa Diagnostics | Version 1.0

import json
import os
import psycopg2
from datetime import datetime

# Database connection
def get_connection():
    return psycopg2.connect(
        dbname="matbank",
        user="ananyarangaraju",
        host="localhost",
        port="5432"
    )

# Parse and insert Patient resource
def insert_patient(cursor, resource):
    patient_ref = resource.get("id", "")
    dob = resource.get("birthDate", None)
    
    cursor.execute("""
        INSERT INTO patients (date_of_birth, enrollment_date, gestational_age_at_enrollment, risk_flag)
        VALUES (%s, %s, %s, %s)
        RETURNING patient_id
    """, (dob, datetime.today().date(), 0, False))
    
    patient_id = cursor.fetchone()[0]
    print(f"Inserted patient: {patient_id} (FHIR ref: {patient_ref})")
    return patient_ref, patient_id

# Parse and insert Observation resource
def insert_observation(cursor, resource, patient_map):
    subject_ref = resource.get("subject", {}).get("reference", "").replace("Patient/", "")
    patient_id = patient_map.get(subject_ref)
    
    if not patient_id:
        print(f"Skipping observation - no matching patient for ref: {subject_ref}")
        return

    obs_type = resource.get("code", {}).get("text", None)
    value_quantity = resource.get("valueQuantity")
    
    if value_quantity is None:
        print(f"Skipping observation {resource.get('id')} - null valueQuantity")
        return
    
    value = value_quantity.get("value", None)
    unit = value_quantity.get("unit", None)
    obs_date = resource.get("effectiveDateTime", None)
    
    gestational_week = None
    for ext in resource.get("extension", []):
        if ext.get("url") == "gestational_week":
            gestational_week = ext.get("valueInteger")
    
    source = None
    performers = resource.get("performer", [])
    if performers:
        source = performers[0].get("display", None)

    cursor.execute("""
        INSERT INTO observations 
        (patient_id, observation_date, observation_type, value_numeric, value_unit, gestational_week, source_system)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (patient_id, obs_date, obs_type, value, unit, gestational_week, source))
    
    print(f"Inserted observation: {obs_type} = {value} {unit} at week {gestational_week}")

# Parse and insert Condition resource
def insert_condition(cursor, resource, patient_map):
    subject_ref = resource.get("subject", {}).get("reference", "").replace("Patient/", "")
    patient_id = patient_map.get(subject_ref)
    
    if not patient_id:
        print(f"Skipping condition - no matching patient for ref: {subject_ref}")
        return

    coding = resource.get("code", {}).get("coding", [{}])[0]
    condition_code = coding.get("code", None)
    condition_name = coding.get("display", None)
    onset_date = resource.get("onsetDateTime", None)
    status = resource.get("clinicalStatus", {}).get("text", None)

    cursor.execute("""
        INSERT INTO conditions 
        (patient_id, condition_code, condition_name, onset_date, status)
        VALUES (%s, %s, %s, %s, %s)
    """, (patient_id, condition_code, condition_name, onset_date, status))
    
    print(f"Inserted condition: {condition_name} ({condition_code}) - {status}")

# Main ETL function
def process_fhir_bundle(filepath):
    print(f"\nProcessing: {filepath}")
    
    with open(filepath, "r") as f:
        bundle = json.load(f)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    patient_map = {}
    
    try:
        # First pass - insert patients and build reference map
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                fhir_ref, patient_id = insert_patient(cursor, resource)
                patient_map[fhir_ref] = patient_id
        
        # Second pass - insert observations and conditions
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")
            
            if resource_type == "Observation":
                insert_observation(cursor, resource, patient_map)
            elif resource_type == "Condition":
                insert_condition(cursor, resource, patient_map)
        
        conn.commit()
        print(f"Successfully committed all records from {filepath}")
    
    except Exception as e:
        conn.rollback()
        print(f"Error processing {filepath}: {e}")
    
    finally:
        cursor.close()
        conn.close()

# Run ETL on all files in data folder
if __name__ == "__main__":
    data_folder = "../data"
    
    for filename in sorted(os.listdir(data_folder)):
        if filename.endswith(".json"):
            filepath = os.path.join(data_folder, filename)
            process_fhir_bundle(filepath)
    
    print("\nETL pipeline complete.")