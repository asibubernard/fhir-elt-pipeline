import os
import json
import requests
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from pathlib import Path
from datetime import datetime, timezone

# ==========================================
# 1. Configuration
# ==========================================
SOURCE_TYPE = "LOCAL"  # Change this to "API" or "LOCAL"

GCP_PROJECT_ID = "health-dbt-portfolio"
DATASET_ID = "raw_fhir_data"

# Local Settings
LOCAL_FOLDER = r"C:\Users\Asibu\Desktop\projects\dbt-projects\data\raw_fhir_data"

# API Settings
FHIR_API_URL = "https://hapi.fhir.org/baseR4"

# Where quarantined (dead-letter) records get written locally
DEAD_LETTER_DIR = Path("./dead_letter")

# Map FHIR Resource Types to BigQuery Table Names
RESOURCE_TABLE_MAP = {
    "Patient": "fhir_patients",
    "Encounter": "fhir_encounters",
    "Condition": "fhir_conditions",
    "Procedure": "fhir_procedures",
    "Claim": "fhir_claims"
}

# The natural/business key used to de-duplicate each table on MERGE
TABLE_KEYS = {
    "fhir_patients": "patient_id",
    "fhir_encounters": "encounter_id",
    "fhir_conditions": "condition_id",
    "fhir_procedures": "procedure_id",
    "fhir_claims": "claim_id",
}

# Define explicit schemas for BigQuery tables
TABLE_SCHEMAS = {
    "fhir_patients": [
        bigquery.SchemaField("patient_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("gender", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("birth_date", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("first_name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("last_name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("city", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED")
    ],
    "fhir_conditions": [
        bigquery.SchemaField("condition_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("patient_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("encounter_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("code", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("display", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("clinical_status", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("onset_date", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED")
    ],
    "fhir_procedures": [
        bigquery.SchemaField("procedure_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("patient_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("encounter_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("code", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("display", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("start_time", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("end_time", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED")
    ],
    "fhir_encounters": [
        bigquery.SchemaField("encounter_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("patient_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("status", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("class", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("type_code", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("type_display", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("start_time", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("end_time", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED")
    ],
    "fhir_claims": [
        bigquery.SchemaField("claim_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("patient_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("total_cost", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("item_count", "INT64", mode="NULLABLE"),
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED")
    ]
}

# ==========================================
# 2. FLATTENING FUNCTIONS
# ==========================================

def safe_scalar(value):
    """Ensure a value going into a STRING column is never a list.
    FHIR sometimes sends 'family' or 'display' style fields as a
    single-item array instead of a plain string. Grab the first
    element if so, otherwise pass the value through unchanged."""
    if isinstance(value, list):
        return value[0] if value else None
    return value

def safe_extract_code(codeable_concept):
    """Helper to extract the first coding code and display from a FHIR CodeableConcept."""
    if not codeable_concept:
        return None, None
    coding = codeable_concept.get("coding", [])
    if coding:
        return safe_scalar(coding[0].get("code")), safe_scalar(coding[0].get("display"))
    return None, safe_scalar(codeable_concept.get("text"))

def flatten_patient(resource):
    names = resource.get("name", [])
    first_name = safe_scalar(names[0].get("given", [""])[0]) if names else None
    last_name = safe_scalar(names[0].get("family")) if names else None
    addresses = resource.get("address", [])
    city = safe_scalar(addresses[0].get("city")) if addresses else None
    return {
        "patient_id": resource.get("id"),
        "gender": safe_scalar(resource.get("gender")),
        "birth_date": safe_scalar(resource.get("birthDate")),
        "first_name": first_name,
        "last_name": last_name,
        "city": city,
        "_ingested_at": datetime.now(timezone.utc).isoformat()
    }

def flatten_encounter(resource):
    patient_ref = resource.get("patient", {}).get("reference", "")
    patient_id = patient_ref.replace("urn:uuid:", "").split("/")[-1] if patient_ref else None
    encounter_type = resource.get("type", [{}])[0]
    code, display = safe_extract_code(encounter_type)
    period = resource.get("period", {})
    class_field = resource.get("class")
    class_value = class_field.get("code") if isinstance(class_field, dict) else class_field
    return {
        "encounter_id": resource.get("id"),
        "patient_id": patient_id,
        "status": safe_scalar(resource.get("status")),
        "class": safe_scalar(class_value),
        "type_code": code,
        "type_display": display,
        "start_time": period.get("start"),
        "end_time": period.get("end"),
        "_ingested_at": datetime.now(timezone.utc).isoformat()
    }

def flatten_condition(resource):
    patient_ref = resource.get("patient", {}).get("reference", "")
    patient_id = patient_ref.replace("urn:uuid:", "").split("/")[-1] if patient_ref else None
    encounter_ref = resource.get("encounter", {}).get("reference", "")
    encounter_id = encounter_ref.replace("urn:uuid:", "").split("/")[-1] if encounter_ref else None
    code, display = safe_extract_code(resource.get("code"))
    status_obj = resource.get("clinicalStatus")
    status = status_obj.get("coding", [{}])[0].get("code") if isinstance(status_obj, dict) else status_obj
    return {
        "condition_id": resource.get("id"),
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "code": code,
        "display": display,
        "clinical_status": safe_scalar(status),
        "onset_date": safe_scalar(resource.get("onsetDateTime")),
        "_ingested_at": datetime.now(timezone.utc).isoformat()
    }

def flatten_procedure(resource):
    subject_ref = resource.get("subject", {}).get("reference", "")
    patient_id = subject_ref.replace("urn:uuid:", "").split("/")[-1] if subject_ref else None
    encounter_ref = resource.get("encounter", {}).get("reference", "")
    encounter_id = encounter_ref.replace("urn:uuid:", "").split("/")[-1] if encounter_ref else None
    code, display = safe_extract_code(resource.get("code"))
    period = resource.get("performedPeriod", {})
    return {
        "procedure_id": resource.get("id"),
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "code": code,
        "display": display,
        "start_time": period.get("start"),
        "end_time": period.get("end"),
        "_ingested_at": datetime.now(timezone.utc).isoformat()
    }

def flatten_claim(resource):
    patient_ref = resource.get("patient", {}).get("reference", "")
    patient_id = patient_ref.replace("urn:uuid:", "").split("/")[-1] if patient_ref else None
    items = resource.get("item", [])

    total_cost = 0.0
    for item in items:
        money = item.get("net") or item.get("unitPrice") or {}
        total_cost += money.get("value") or 0

    if total_cost == 0 and "total" in resource:
        total_cost = resource.get("total", {}).get("value") or 0
    
    # total_cost = sum(item.get("net", {}).get("value") or 0 for item in items)
    return {
        "claim_id": resource.get("id"),
        "patient_id": patient_id,
        "total_cost": total_cost,
        "item_count": len(items),
        "_ingested_at": datetime.now(timezone.utc).isoformat()
    }

FLATTENERS = {
    "Patient": flatten_patient,
    "Encounter": flatten_encounter,
    "Condition": flatten_condition,
    "Procedure": flatten_procedure,
    "Claim": flatten_claim
}

# ==========================================
# 3. DATA RETRIEVAL FUNCTIONS
# ==========================================

def get_local_files():
    folder = Path(LOCAL_FOLDER)
    if not folder.exists():
        print(f"❌ Local folder {LOCAL_FOLDER} does not exist.")
        return
    for file_path in folder.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                yield json.load(f)
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")

def get_api_data():
    for resource_type in RESOURCE_TABLE_MAP.keys():
        url = f"{FHIR_API_URL}/{resource_type}"
        params = {"_count": "50"}
        pages_fetched = 0
        max_pages = 3

        while url and pages_fetched < max_pages:
            try:
                if pages_fetched == 0:
                    response = requests.get(url, params=params)
                else:
                    response = requests.get(url)

                if response.status_code == 200:
                    data = response.json()
                    yield data
                    links = data.get("link", [])
                    next_link = next((link['url'] for link in links if link.get('relation') == 'next'), None)
                    url = next_link
                    pages_fetched += 1
                else:
                    print(f"❌ API Error fetching {resource_type}: {response.status_code} - {response.text}")
                    break
            except Exception as e:
                print(f"❌ Request failed for {resource_type}: {e}")
                break

# ==========================================
# 4. DEAD-LETTER HANDLING
# ==========================================

def write_dead_letters(dead_letters):
    """Append quarantined records to a local JSONL file, one run-batch per file.
    Each line has the raw resource, the resource type, and why it failed,
    so nothing is silently lost and you can inspect/reprocess later."""
    if not dead_letters:
        return
    DEAD_LETTER_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = DEAD_LETTER_DIR / f"dead_letters_{ts}.jsonl"
    with open(out_path, "w") as f:
        for entry in dead_letters:
            f.write(json.dumps(entry) + "\n")
    print(f"⚠️  {len(dead_letters)} record(s) quarantined -> {out_path}")

# ==========================================
# 5. PROCESS AND LOAD (with MERGE-based dedup)
# ==========================================

def ensure_table(bg_client, table_ref, table_name):
    try:
        bg_client.get_table(table_ref)
    except NotFound:
        table = bigquery.Table(table_ref, schema=TABLE_SCHEMAS[table_name])
        bg_client.create_table(table)
        print(f"✅ Created table {table_name} with schema.")

def merge_load(bg_client, table_name, records):
    """Load records into a temporary staging table, then MERGE into the
    real table on its business key so re-running the script (or re-ingesting
    overlapping files) never creates duplicate rows."""
    target_ref = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    staging_table = f"{table_name}__staging"
    staging_ref = f"{GCP_PROJECT_ID}.{DATASET_ID}.{staging_table}"
    key_col = TABLE_KEYS[table_name]

    ensure_table(bg_client, target_ref, table_name)

    # (Re)create the staging table fresh for this run
    bg_client.delete_table(staging_ref, not_found_ok=True)
    staging_table_obj = bigquery.Table(staging_ref, schema=TABLE_SCHEMAS[table_name])
    bg_client.create_table(staging_table_obj)

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=False,
        schema=TABLE_SCHEMAS[table_name],
    )
    print(f"📦 Staging {len(records)} records for {table_name}...")
    load_job = bg_client.load_table_from_json(records, staging_ref, job_config=job_config)
    load_job.result()

    # Build MERGE: update existing rows by key, insert new ones
    all_cols = [f.name for f in TABLE_SCHEMAS[table_name]]
    update_cols = [c for c in all_cols if c != key_col]
    update_clause = ", ".join(f"T.{c} = S.{c}" for c in update_cols)
    insert_cols = ", ".join(all_cols)
    insert_vals = ", ".join(f"S.{c}" for c in all_cols)

    merge_sql = f"""
    MERGE `{target_ref}` T
    USING `{staging_ref}` S
    ON T.{key_col} = S.{key_col}
    WHEN MATCHED THEN
      UPDATE SET {update_clause}
    WHEN NOT MATCHED THEN
      INSERT ({insert_cols}) VALUES ({insert_vals})
    """
    print(f"🔀 Merging into {table_name} on {key_col}...")
    bg_client.query(merge_sql).result()
    bg_client.delete_table(staging_ref, not_found_ok=True)

def process_and_load(source_generator):
    bg_client = bigquery.Client(project=GCP_PROJECT_ID)

    dataset_ref = bg_client.dataset(DATASET_ID)
    try:
        bg_client.get_dataset(dataset_ref)
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        bg_client.create_dataset(dataset)
        print(f"✅ Created dataset {DATASET_ID}")

    collected_data = {table: [] for table in RESOURCE_TABLE_MAP.values()}
    dead_letters = []

    for bundle in source_generator:
        entries = bundle.get("entry", [])
        for entry in entries:
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")

            if resource_type not in FLATTENERS:
                continue

            table_name = RESOURCE_TABLE_MAP[resource_type]
            key_col = TABLE_KEYS[table_name]

            try:
                flat_record = FLATTENERS[resource_type](resource)

                # Reject records missing their own primary key up front —
                # a record with no ID can't be de-duplicated or merged safely.
                if not flat_record.get(key_col):
                    raise ValueError(f"Missing required key '{key_col}'")

                collected_data[table_name].append(flat_record)

            except Exception as e:
                dead_letters.append({
                    "resource_type": resource_type,
                    "error": str(e),
                    "raw_resource": resource,
                    "quarantined_at": datetime.now(timezone.utc).isoformat()
                })
                print(f"⚠️  Quarantined a {resource_type} record: {e}")

    write_dead_letters(dead_letters)

    print("🚀 Loading data into BigQuery...")
    for table_name, records in collected_data.items():
        if not records:
            print(f"⚠️ No records found for {table_name}, skipping load.")
            continue
        merge_load(bg_client, table_name, records)

    if dead_letters:
        print(f"\n⚠️  Run finished with {len(dead_letters)} quarantined record(s). "
              f"Review the file(s) in {DEAD_LETTER_DIR}/ before assuming the load is complete.")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    if SOURCE_TYPE == "LOCAL":
        print("📂 Ingesting from Local Folder...")
        process_and_load(get_local_files())
    elif SOURCE_TYPE == "API":
        print("🌐 Ingesting from API...")
        process_and_load(get_api_data())
    else:
        print("❌ Invalid Source Type")