# FHIR ELT Pipeline

A modern healthcare ELT pipeline that ingests FHIR (Fast Healthcare Interoperability Resources) data into Google BigQuery, transforms it with dbt, orchestrates workflows with Prefect, and produces analytics-ready healthcare datasets.

This project demonstrates Analytics Engineering skills using Python, BigQuery, dbt, Prefect, SQL, and healthcare data modeling.

---

## Project Overview

This project follows a modern ELT (Extract, Load, Transform) architecture used by data teams.

The pipeline:

1. Extracts FHIR healthcare resources using Python.
2. Loads raw data into Google BigQuery.
3. Transforms raw data with dbt.
4. Validates data quality using dbt tests.
5. Orchestrates the workflow with Prefect.
6. Produces analytics-ready datasets for reporting.

---

## Architecture

```text
FHIR Source
     │
     ▼
Python (fhir_ingestion.py)
     │
     ▼
Google BigQuery (raw_fhir_data)
     │
     ▼
dbt Staging Models
     │
     ▼
dbt Intermediate Models
     │
     ▼
dbt Mart Models
     │
     ▼
Prefect Flow
     │
     ▼
Looker Studio Dashboard
```

> Prefect orchestrates the end-to-end workflow by running the ingestion script and dbt commands as a single automated pipeline.

---

## Technology Stack

| Tool | Purpose |
|------|---------|
| Python | FHIR data ingestion |
| Google BigQuery | Cloud data warehouse |
| dbt | Data transformation and testing |
| Prefect | Pipeline orchestration |
| SQL | Analytics modeling |
| Git & GitHub | Version control |
| Looker Studio | Business intelligence dashboard |

---

## Project Structure

```text
fhir_elt_pipeline/
├── ingestion/
│   └── fhir_ingestion.py
├── flows/
│   └── healthcare_pipeline.py
├── models/
│   ├── staging/
│   ├── intermediate/
│   └── marts/
├── tests/
├── macros/
├── dbt_project.yml
├── packages.yml
└── README.md
```

---

## FHIR Resources

The pipeline currently ingests five core FHIR resources.

| Resource | Purpose |
|----------|---------|
| Patient | Patient demographics |
| Encounter | Healthcare visits |
| Condition | Diagnoses |
| Procedure | Clinical procedures |
| Claim | Healthcare claims |

These resources provide enough data to build meaningful healthcare analytics while keeping the project focused.

---

## BigQuery Source Configuration

Raw FHIR resources are stored in:

- **Project:** `health-dbt-portfolio`
- **Dataset:** `raw_fhir_data`

Example dbt source configuration:

```yaml
sources:
  - name: raw_fhir_data
    database: health-dbt-portfolio
    schema: raw_fhir_data
```

---

## Running the Project

### 1. Create a virtual environment

```bash
python -m venv dbt-env
```

Activate it on Windows:

```bash
dbt-env\Scripts\activate
```

### 2. Install dependencies

```bash
pip install dbt-bigquery prefect pandas google-cloud-bigquery
```

### 3. Configure dbt

Create `profiles.yml` in:

```text
C:\Users\<username>\.dbt\
```

Example:

```yaml
fhir_elt_pipeline:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth
      project: health-dbt-portfolio
      dataset: dbt_asibu
      location: US
      threads: 4
```

### 4. Verify the connection

```bash
dbt debug
```

Expected output:

```text
All checks passed!
```

### 5. Run the complete pipeline

Execute the Prefect flow:

```bash
python flows/healthcare_pipeline.py
```

The flow will:

1. Run `fhir_ingestion.py`
2. Load raw FHIR data into BigQuery
3. Execute `dbt run`
4. Execute `dbt test`

You can also run individual steps manually.

Run ingestion:

```bash
python ingestion/fhir_ingestion.py
```

Run dbt:

```bash
dbt run
dbt test
```

Generate documentation:

```bash
dbt docs generate
dbt docs serve
```

---

## Data Modeling

The dbt project follows a layered modeling approach.

### Staging Layer

- `stg_patients`
- `stg_encounters`
- `stg_conditions`
- `stg_procedures`
- `stg_claims`

### Intermediate Layer

Business logic combines related healthcare resources, including:

- Patient encounters
- Patient conditions
- Patient procedures

### Mart Layer

Analytics-ready models support dashboards and reporting, including:

- Patient Summary
- Encounter Summary
- Claims Analytics

---

## Data Quality

dbt tests help ensure reliable healthcare data.

Examples include:

- Primary keys are unique.
- Required fields are not null.
- Relationships between FHIR resources are valid.

---

## Skills Demonstrated

- Python data ingestion
- Google BigQuery
- dbt transformations
- SQL analytics engineering
- Prefect orchestration
- Healthcare FHIR data modeling
- Data quality testing
- ELT pipeline design
- Modern data engineering workflows

---

## Next Improvements

- Add additional FHIR resources such as `Observation` and `MedicationRequest`.
- Implement incremental dbt models.
- Add CI/CD with GitHub Actions.
- Expand Looker Studio dashboards.
- Add pipeline monitoring and notifications in Prefect.

---

## Author

Built as an Analytics Engineering portfolio project demonstrating an end-to-end healthcare data pipeline using Python, BigQuery, dbt, Prefect, and Looker Studio.