# Dublin Bikes Data Pipeline

An end-to-end data pipeline that ingests live Dublin Bikes station data, transforms it into analysis-ready tables, and surfaces availability and station-health insights through an interactive dashboard.

**Live dashboard:** [Dublin Bikes - Availability & Station Health](https://datastudio.google.com/s/jqqFSljMhps)

---

## What it does

Every 15 minutes, the pipeline pulls a live snapshot of all ~114 Dublin Bikes stations from the JCDecaux API, lands it in BigQuery, and rebuilds a set of clean, tested analytical tables with dbt. A Data Studio dashboard reads those tables to show how bike availability moves through the day and which stations most often run empty or full.

---

## Architecture

```
JCDecaux API
     │   Python fetch (requests)
     ▼
BigQuery - raw_station_status        (raw layer: one row per station per snapshot, partitioned by date)
     │   dbt transformations (SQL)
     ▼
BigQuery - stg_station_status        (staging: deduplicated, typed, epoch → timestamp, occupancy derived)
     │
     ▼
BigQuery - fct_station_hourly        (mart: average availability by hour of day)
BigQuery - fct_station_summary       (mart: per-station availability + % time empty / full)
     │   BigQuery connector
     ▼
Data Studio dashboard                (hourly trend, station map, most-empty stations)
```

Orchestration is handled by **Apache Airflow** (run locally via the Astro CLI in **Docker**), which schedules the ingestion, retries on failure, and provides run-level visibility.

---

## Tech stack

| Layer | Tool | Why |
|-------|------|-----|
| Source | JCDecaux API | Official live Dublin Bikes data |
| Ingestion | Python (`requests`, `google-cloud-bigquery`) | Fetch, flatten, load |
| Orchestration | Apache Airflow (Astro CLI) | Reliable 15-minute scheduling with retries |
| Environment | Docker | Reproducible, portable runtime for Airflow |
| Warehouse | Google BigQuery | Serverless storage and SQL compute |
| Transformation | dbt (dbt-bigquery) | Tested, documented, version-controlled SQL models |
| Visualisation | Data Studio (Looker Studio) | Free, native BigQuery dashboards |

---

## Data quality

Transformation is validated, not assumed. The dbt project runs **14 tests** across the models, including:

- `not_null` on all key fields (station id, snapshot timestamp, availability)
- `unique_combination_of_columns` on station + snapshot (proves deduplication works)
- `accepted_values` on station status (`OPEN` / `CLOSED`)
- `accepted_range` on occupancy ratio (0–1) and hour of day (0–23)
- source **freshness** checks that flag if ingestion stalls

---

## Sample insight

Across the collected snapshots, a cluster of north-inner-city stations (Hardwicke Place, Eccles Street) sat **completely empty around 70% of the time** - a rebalancing signal a bike-share operator would act on.

---

## Project structure

```
dublin-bikes-pipeline/
├── dags/
│   └── dublin_bikes_ingestion.py     # Airflow DAG (every 15 min)
├── include/
│   ├── fetch_stations.py             # API → BigQuery load
│   ├── create_raw_table.sql          # raw table DDL
│   └── validate_raw_load.sql         # ingestion health check
├── dbt_dublin_bikes/
│   └── models/
│       ├── staging/                  # stg_station_status + tests
│       └── marts/                    # fct_station_hourly, fct_station_summary + tests
├── Dockerfile                        # Astro/Airflow runtime
├── requirements.txt
└── .env.example                      # required environment variables (no secrets)
```

---

## Running it locally

1. Clone the repo and add your credentials to a `.env` file (see `.env.example`) and a BigQuery service-account key at `include/gcp_keyfile.json`.
2. Start Airflow: `astro dev start` - the ingestion DAG runs every 15 minutes.
3. Build the models: `cd dbt_dublin_bikes && dbt deps && dbt run && dbt test`.

---

## Design notes

This project uses a deliberately production-shaped stack - Airflow for scheduled ingestion, Docker for a reproducible runtime, and dbt for tested transformations, because the value of the dashboard depends entirely on data being collected reliably and transformed correctly, not just visualised.

One deliberate scoping choice: Airflow runs locally via the Astro CLI, so collection depends on the host machine being available. A fully production deployment would move ingestion to an always-on serverless scheduler - a natural extension rather than a redesign, since the pipeline logic stays identical.
