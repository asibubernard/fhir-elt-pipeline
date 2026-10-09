from google.cloud import bigquery

# ==========================================
# Explicit BigQuery table schemas
# ==========================================
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
        bigquery.SchemaField("status", "STRING", mode="NULLABLE"),
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
        bigquery.SchemaField("encounter_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("patient_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("total_cost", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("item_count", "INT64", mode="NULLABLE"),
        bigquery.SchemaField("created_date", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("billable_period_start", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("billable_period_end", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED")
    ]
}