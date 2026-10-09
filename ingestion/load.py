from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from . import config
from . import schemas


def ensure_table(bq_client, table_ref, table_name):
    try:
        bq_client.get_table(table_ref)
    except NotFound:
        table = bigquery.Table(table_ref, schema=schemas.TABLE_SCHEMAS[table_name])
        bq_client.create_table(table)
        print(f"✅ Created table {table_name} with schema.")


def ensure_dataset(bq_client):
    dataset_ref = bq_client.dataset(config.DATASET_ID)
    try:
        bq_client.get_dataset(dataset_ref)
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        bq_client.create_dataset(dataset)
        print(f"✅ Created dataset {config.DATASET_ID}")


def merge_load(bq_client, table_name, records):
    """Load records into a temporary staging table, then MERGE into the
    real table on its business key so re-running the script (or re-ingesting
    overlapping files) never creates duplicate rows."""
    target_ref = f"{config.GCP_PROJECT_ID}.{config.DATASET_ID}.{table_name}"
    staging_table = f"{table_name}__staging"
    staging_ref = f"{config.GCP_PROJECT_ID}.{config.DATASET_ID}.{staging_table}"
    key_col = config.TABLE_KEYS[table_name]

    ensure_table(bq_client, target_ref, table_name)

    # (Re)create the staging table fresh for this run
    bq_client.delete_table(staging_ref, not_found_ok=True)
    staging_table_obj = bigquery.Table(staging_ref, schema=schemas.TABLE_SCHEMAS[table_name])
    bq_client.create_table(staging_table_obj)

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=False,
        schema=schemas.TABLE_SCHEMAS[table_name],
    )
    print(f"📦 Staging {len(records)} records for {table_name}...")
    load_job = bq_client.load_table_from_json(records, staging_ref, job_config=job_config)
    load_job.result()

    # Build MERGE: update existing rows by key, insert new ones
    all_cols = [f.name for f in schemas.TABLE_SCHEMAS[table_name]]
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
    bq_client.query(merge_sql).result()
    bq_client.delete_table(staging_ref, not_found_ok=True)