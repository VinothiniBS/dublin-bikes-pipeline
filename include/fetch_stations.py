"""Fetch live Dublin Bikes station data from the JCDecaux API and append it to BigQuery.

Run locally:
    export JCDECAUX_API_KEY="your_key"
    export GOOGLE_APPLICATION_CREDENTIALS="include/gcp_keyfile.json"
    python include/fetch_stations.py
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import requests
from google.cloud import bigquery

API_URL = "https://api.jcdecaux.com/vls/v1/stations"
CONTRACT = "dublin"
TABLE_ID = "dublin-bikes-pipeline.dublin_bikes.raw_station_status"
REQUEST_TIMEOUT_SECONDS = 30

logger = logging.getLogger(__name__)


def fetch_stations(api_key: str) -> list[dict]:
    """Call the JCDecaux API and return the raw station payload."""
    response = requests.get(
        API_URL,
        params={"contract": CONTRACT, "apiKey": api_key},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    stations = response.json()

    if not isinstance(stations, list) or not stations:
        raise ValueError("JCDecaux API returned no station records")

    return stations


def to_rows(stations: list[dict], pulled_at: datetime) -> list[dict]:
    """Flatten the API payload into rows matching the raw_station_status schema."""
    rows = []
    for station in stations:
        position = station.get("position") or {}
        rows.append(
            {
                "pulled_at": pulled_at.isoformat(),
                "number": station.get("number"),
                "name": station.get("name"),
                "address": station.get("address"),
                "latitude": position.get("lat"),
                "longitude": position.get("lng"),
                "banking": station.get("banking"),
                "bonus": station.get("bonus"),
                "status": station.get("status"),
                "bike_stands": station.get("bike_stands"),
                "available_bikes": station.get("available_bikes"),
                "available_bike_stands": station.get("available_bike_stands"),
                "last_update": station.get("last_update"),
            }
        )
    return rows


def load_to_bigquery(rows: list[dict]) -> int:
    """Append rows to the raw table using a load job (free, unlike streaming inserts)."""
    client = bigquery.Client()
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema=[
            bigquery.SchemaField("pulled_at", "TIMESTAMP"),
            bigquery.SchemaField("number", "INT64"),
            bigquery.SchemaField("name", "STRING"),
            bigquery.SchemaField("address", "STRING"),
            bigquery.SchemaField("latitude", "FLOAT64"),
            bigquery.SchemaField("longitude", "FLOAT64"),
            bigquery.SchemaField("banking", "BOOL"),
            bigquery.SchemaField("bonus", "BOOL"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("bike_stands", "INT64"),
            bigquery.SchemaField("available_bikes", "INT64"),
            bigquery.SchemaField("available_bike_stands", "INT64"),
            bigquery.SchemaField("last_update", "INT64"),
        ],
    )

    job = client.load_table_from_json(rows, TABLE_ID, job_config=job_config)
    job.result()

    if job.errors:
        raise RuntimeError(f"BigQuery load job failed: {job.errors}")

    return len(rows)


def run() -> int:
    """Fetch and load one snapshot. Returns the number of records loaded."""
    api_key = os.environ.get("JCDECAUX_API_KEY")
    if not api_key:
        raise EnvironmentError("JCDECAUX_API_KEY environment variable is not set")

    pulled_at = datetime.now(timezone.utc)
    stations = fetch_stations(api_key)
    rows = to_rows(stations, pulled_at)
    record_count = load_to_bigquery(rows)

    logger.info("Loaded %s station records at %s", record_count, pulled_at.isoformat())
    return record_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    count = run()
    print(f"Loaded {count} station records into {TABLE_ID}")
