"""Create a scheduled Prefect deployment (run once, from the project folder).

Save as flows/deploy.py. Not run yet. Replace every YOUR-... value first.

Before this works you need:
  1. A Prefect Cloud account (or your own Prefect server) and `prefect cloud login`
  2. A work pool:  prefect work-pool create YOUR-WORK-POOL --type process
  3. A worker that stays running somewhere that is always on:
       prefect worker start --pool YOUR-WORK-POOL
  4. The repo on GitHub, with dbt and the BigQuery libraries installed on the worker
If your work pool is a Docker pool, add image="..." to .deploy() as well.
"""

from prefect import flow


def main():
    deployment_flow = flow.from_source(
        source="https://github.com/asibubernard/YOUR-REPO.git",
        # Path from the ROOT of the repo to the flow, then :flow_function_name.
        # If your repo root is above fhir_elt_pipeline, keep the folder name.
        entrypoint="fhir_elt_pipeline/flows/health_pipeline.py:health_pipeline",
    )
    deployment_flow.deploy(
        name="health-pipeline-daily",
        work_pool_name="YOUR-WORK-POOL",
        cron="0 6 * * *",  # every day at 06:00 (UTC by default)
        parameters={"dbt_target": "dev"},
    )


if __name__ == "__main__":
    main()
