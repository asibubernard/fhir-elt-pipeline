from datetime import UTC, datetime

from google.cloud.bigquery import Client

from . import config, dead_letter, extract, load
from .flatteners import FLATTENERS


def process_and_load(source_generator):
    bq_client = Client(project=config.GCP_PROJECT_ID)

    load.ensure_dataset(bq_client)

    collected_data = {table: [] for table in config.RESOURCE_TABLE_MAP.values()}
    dead_letters = []

    for bundle in source_generator:
        entries = bundle.get("entry", [])
        for entry in entries:
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")

            if resource_type not in FLATTENERS:
                continue

            table_name = config.RESOURCE_TABLE_MAP[resource_type]
            key_col = config.TABLE_KEYS[table_name]

            try:
                flat_record = FLATTENERS[resource_type](resource)

                # Reject records missing their own primary key up front —
                # a record with no ID can't be de-duplicated or merged safely.
                if not flat_record.get(key_col):
                    raise ValueError(f"Missing required key '{key_col}'")

                collected_data[table_name].append(flat_record)

            except Exception as e: # noqa: BLE001 - one bad record goes to dead letters
                dead_letters.append(
                    {
                        "resource_type": resource_type,
                        "error": str(e),
                        "raw_resource": resource,
                        "quarantined_at": datetime.now(UTC).isoformat(),
                    }
                )
                print(f"⚠️  Quarantined a {resource_type} record: {e}")

    dead_letter.write_dead_letters(dead_letters)

    print("🚀 Loading data into BigQuery...")
    for table_name, records in collected_data.items():
        if not records:
            print(f"⚠️ No records found for {table_name}, skipping load.")
            continue
        load.merge_load(bq_client, table_name, records)

    if dead_letters:
        print(
            f"\n⚠️  Run finished with {len(dead_letters)} quarantined record(s). "
            f"Review the file(s) in {config.DEAD_LETTER_DIR}/ before assuming the load is complete."
        )


if __name__ == "__main__":
    if config.SOURCE_TYPE == "LOCAL":
        print("📂 Ingesting from Local Folder...")
        process_and_load(extract.get_local_files())
    elif config.SOURCE_TYPE == "API":
        print("🌐 Ingesting from API...")
        process_and_load(extract.get_api_data())
    else:
        print("❌ Invalid Source Type")
