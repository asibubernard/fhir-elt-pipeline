![CI](https://github.com/asibubernard/fhir-elt-pipeline/actions/workflows/ci.yml/badge.svg)

# FHIR ELT Pipeline

An end-to-end ELT pipeline for healthcare data. It loads FHIR resources into BigQuery, transforms them with dbt into a star-schema reporting layer, orchestrates the run with Prefect, and feeds a Looker Studio dashboard.

**The data is synthetic** (generated with [Synthea](https://synthetichealth.github.io/synthea/)). No real patient data is used. The project is still built with privacy in mind: see [Privacy and de-identification](#privacy-and-de-identification).

> **Status:** portfolio project. It is tested in CI and runs reliably, but it is not a production system. See [Limitations](#limitations).

---

## What it does

| Stage | Tool | What happens |
|-------|------|--------------|
| Extract | Python | Reads FHIR Bundles from local files or a FHIR API |
| Load | Python + BigQuery | Flattens five resource types and MERGEs them into `raw_fhir_data` by business key, so re-runs do not create duplicates |
| Transform | dbt | Staging, intermediate and mart layers, with tests |
| Orchestrate | Prefect | Runs ingestion then `dbt build`, with retries, timeouts and Slack alerts |
| Serve | Looker Studio | Dashboard on the mart tables |
| Verify | GitHub Actions | Lint, then a full `dbt build` against a separate CI dataset on every push and pull request |

## Architecture

```text
FHIR Bundles (local files or API)
        │
        ▼
Python ingestion ── bad records ──▶ dead-letter JSONL (quarantine)
        │ MERGE by business key
        ▼
BigQuery  raw_fhir_data
        │
        ▼
dbt staging       stg_fhir_*       rename, cast, de-identify
        │
        ▼
dbt intermediate  int_patient_*    joins and business logic
        │
        ▼
dbt marts         dim_* / fact_*   star schema for BI
        │
        ▼
Looker Studio dashboard

Prefect flow:  ingestion ─▶ dbt build ─▶ Slack notification (success or failure)
GitHub Actions: ruff ─▶ SQLFluff ─▶ dbt build on a separate dataset (dbt_ci)
```

## Design decisions

**Idempotent loading.** Each table loads into a temporary staging table, then a `MERGE` updates or inserts by business key. Running the pipeline twice gives the same result.

**Dead-letter quarantine.** A record that fails to flatten is written to a JSONL file with the reason, instead of failing the whole run or being dropped silently.

**Reference table instead of keyword rules.** Conditions are grouped into categories using a reviewed seed, `seeds/condition_category_map.csv`, keyed on the SNOMED CT code. An earlier keyword macro was only a draft, and I replaced it because matching on description text is fragile. Codes missing from the seed show as `Unmapped` and trigger a warning test (`assert_no_unmapped_conditions`), so new codes cannot slip through unnoticed.

**De-identify early.** Names and exact birth dates are removed in the staging layer, so no downstream model can use them. Age bands are built later, in `dim_patient`.

**Tests do the gatekeeping.** The build fails on broken keys, nulls, bad relationships and out-of-range values. Warnings are used only where a failure would be a data-quality signal, not a code bug.

**Separate CI dataset.** CI builds into `dbt_ci`, never into the development dataset. The CI service account has write access to that dataset only and read-only access to the raw data.

## Privacy and de-identification

The staging layer follows the spirit of the HIPAA Safe Harbor method:

- Patient names are not carried into any model.
- Only the **birth year** is kept, not the full date of birth.
- For patients aged **90 or over**, the birth year is withheld and an `is_age_90_plus` flag is used instead.
- Location is limited to **state**. City and ZIP are not used.

Dates elsewhere (encounters, claims) are kept because the data is synthetic. With real data, those would also need review, because Safe Harbor covers dates more broadly.

## Data model

**Staging** (`models/fhir/staging`): `stg_fhir_patients`, `stg_fhir_encounters`, `stg_fhir_conditions`, `stg_fhir_procedures`, `stg_fhir_claims`.

**Intermediate** (`models/fhir/intermediate`): `int_patient_profiles`, `int_patient_encounters`, `int_patient_conditions`, `int_patient_procedures`, `int_patient_claims`.

**Marts** (`models/fhir/marts`):

| Model | Type | Purpose |
|-------|------|---------|
| `dim_patient` | Dimension | Gender, state, birth year, age group |
| `dim_conditions` | Dimension | Condition code, description, category |
| `dim_procedure` | Dimension | Procedures |
| `dim_date` | Dimension | Calendar |
| `fact_encounters` | Fact | Visits |
| `fact_conditions` | Fact | Diagnoses |
| `fact_claims` | Fact | Claims and costs |

The dashboard is declared as a dbt exposure (`models/fhir/exposures.yml`), so the models it depends on are visible in the lineage graph.

## Testing and CI

The workflow in `.github/workflows/ci.yml` runs on every push and pull request to `main`:

1. `ruff check .` for Python lint and import order
2. `dbt deps`
3. `sqlfluff lint` for SQL style
4. `dbt build` against the `dbt_ci` dataset: 17 models, 1 seed and 88 tests

Locally, `dbt build --profiles-dir ci` runs the same build, so you can rehearse CI before pushing.

Other settings: concurrency control so superseded runs cancel, a job timeout, pinned dependencies, and `main` protected by a ruleset that requires the CI check to pass before merging.

Pipeline failures and successes post to a Slack channel via a webhook that is read from the `SLACK_WEBHOOK_URL` environment variable. It is never stored in the repository.

## Running it locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt
dbt deps
```

Create `~/.dbt/profiles.yml`:

```yaml
health_dbt:
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

Then:

```bash
dbt debug                       # check the connection
python -m ingestion             # load raw data
dbt seed && dbt build           # transform and test
python flow/health_pipeline.py  # or run everything through Prefect
dbt docs generate && dbt docs serve
```

## Project structure

```text
.github/workflows/ci.yml   CI pipeline
ci/profiles.yml            dbt profile for CI (values come from environment variables)
ingestion/                 extract, flatten, MERGE load, dead-letter handling
flow/                      Prefect flow and deployment
models/fhir/               staging, intermediate, marts, exposure
seeds/                     condition_category_map (SNOMED code to category)
tests/                     custom data tests
analyses/                  ad hoc queries (unmapped conditions)
```

## Limitations

Stated plainly, so nobody has to guess:

- **Synthetic data only.** The privacy steps are good practice, not a compliance claim.
- **SNOMED CT licensing is unconfirmed.** The category map uses SNOMED codes but not the licensed release files. If this is reused outside a portfolio setting, the licensing terms should be checked.
- **Category mapping is a judgment call.** It was reviewed by hand and is not a clinical standard.
- **Marts are views.** That is fine at this size. At larger volumes they would become tables or incremental models.
- **Local-first ingestion.** The default source is a local folder; the API path is lightly used.
- **Single environment.** There is a dev dataset and a CI dataset, but no production deployment.

## Roadmap

- Use Workload Identity Federation in CI instead of a service account key
- Run slim CI (`state:modified+`) to speed up pull requests
- Add source freshness checks and a test asserting that no identifiers reach the marts
- Materialize large marts as tables or incremental models
- Add `Observation` and `MedicationRequest` resources
- Move ingestion settings out of `config.py` into environment variables

## Author

Bernard Asibu, analytics engineer. [LinkedIn](https://www.linkedin.com/in/asibubernard)
