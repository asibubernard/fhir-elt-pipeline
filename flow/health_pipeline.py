"""Prefect flow: load FHIR data into BigQuery, then run dbt build.

Save as flow/health_pipeline.py inside the fhir_elt_pipeline folder.
Not run yet: test with  python flow/health_pipeline.py
"""

import os
import subprocess
import sys
import apprise
from pathlib import Path

from dbt.cli.main import dbtRunner
from prefect import flow, get_run_logger, task


# Project root = the folder that holds dbt_project.yml and ingestion/
# (this file lives in <root>/flows/, so go up one level)
ROOT = Path(__file__).resolve().parents[1]

# Time limits in seconds. A step that hangs is stopped and marked failed.
INGESTION_TIMEOUT = 30 * 60
DBT_TIMEOUT = 30 * 60
FLOW_TIMEOUT = 75 * 60


def _status(run_result) -> str:
    """Return a dbt node status as plain lowercase text, e.g. 'pass', 'warn', 'fail'."""
    status = run_result.status
    return str(getattr(status, "value", status)).lower()


@task(retries=2, retry_delay_seconds=30, timeout_seconds=INGESTION_TIMEOUT)
def run_ingestion():
    """Load FHIR data into BigQuery."""
    logger = get_run_logger()
    result = subprocess.run(
        [sys.executable, "-m", "ingestion"],
        check=False,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=INGESTION_TIMEOUT,
        # Script prints emoji. When the output is captured on Windows,
        # Python may fail on them unless it is told to use UTF-8.
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    if result.stdout:
        logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr[-4000:])  # last part of the error
        raise RuntimeError(f"Ingestion failed (exit code {result.returncode})")


@task(timeout_seconds=DBT_TIMEOUT)  # no retries: a failed dbt test is a data problem
def run_dbt_build(target: str) -> dict:
    """Run dbt build (seeds, models and tests) and report what happened."""
    logger = get_run_logger()
    res = dbtRunner().invoke(["build", "--project-dir", str(ROOT), "--target", target])
    result_obj = res.result
    if isinstance(result_obj, (list, tuple)):
        nodes = list(result_obj)
    else:
        # dbt's result object is not always directly iterable; the node results are
        # usually attached to `.results` for build/test runs.
        nodes = list(getattr(result_obj, "results", []) or [])
    failed = [
        getattr(getattr(r, "node", None), "name", str(r))
        for r in nodes
        if _status(r) in ("fail", "error")
    ]
    warned = [
        getattr(getattr(r, "node", None), "name", str(r))
        for r in nodes
        if _status(r) == "warn"
    ]

    if warned:
        # Example: the test that warns about unmapped condition codes
        logger.warning(f"dbt finished with {len(warned)} warning(s): {warned}")
    if not res.success:
        raise RuntimeError(
            f"dbt build failed. Failed: {failed or 'see logs'}. Error: {res.exception}"
        )
    return {"nodes": len(nodes), "warnings": len(warned)}


@task
def send_notification(summary: dict):
    """Log a success message. Replace with Slack or email later."""
    get_run_logger().info(
        f"Pipeline finished: {summary['nodes']} dbt nodes ran, "
        f"{summary['warnings']} warning(s)."
    )


def alert_on_failure(flow, flow_run, state):
    """Runs when the flow fails. Replace the print with Slack or email later."""
    print(f"Pipeline FAILED: {state.message}")


@flow(
    name="Health Analytics Pipeline",
    timeout_seconds=FLOW_TIMEOUT,
    on_failure=[alert_on_failure],
    log_prints=True,
)
def health_pipeline(dbt_target: str = "dev"):
    run_ingestion()
    summary = run_dbt_build(dbt_target)
    send_notification(summary)


if __name__ == "__main__":
    health_pipeline()
