from pathlib import Path
from google.cloud import bigquery


# Source selection
SOURCE_TYPE = "LOCAL" # Options: "LOCAL" or "API"

# GCP / BigQuery settings
GCP_PROJECT_ID = "health-dbt-portfolio"
DATASET_ID = "raw_fhir_data"

# Local file settings
LOCAL_FOLDER = Path(r"C:/Users/Asibu/Desktop/projects/dbt-projects/data/raw_fhir_data")

# API settings
FHIR_API_URL = "https://hapi.fhir.org/baseR4"
 
# Dead-letter (quarantine) settings
DEAD_LETTER_DIR = Path("./dead_letter")

# Resource type -> BigQuery table name
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