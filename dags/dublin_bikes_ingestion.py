"""Ingest Dublin Bikes station snapshots from the JCDecaux API into BigQuery.

Runs every 15 minutes and appends one snapshot (~114 station records) per run
to the partitioned raw table.
"""

from __future__ import annotations

import pendulum
from airflow.decorators import dag, task

from include.fetch_stations import run as fetch_and_load_stations


@dag(
    dag_id="dublin_bikes_ingestion",
    description="Fetch live Dublin Bikes station status and append to the BigQuery raw layer",
    start_date=pendulum.datetime(2026, 7, 23, tz="Europe/Dublin"),
    schedule="*/15 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": pendulum.duration(minutes=2),
    },
    tags=["dublin-bikes", "ingestion", "bigquery"],
)
def dublin_bikes_ingestion():
    """One task: call the API, flatten the payload, append to BigQuery."""

    @task
    def fetch_and_load() -> int:
        """Return the number of station records loaded, for run visibility in the UI."""
        return fetch_and_load_stations()

    fetch_and_load()


dublin_bikes_ingestion()
