SELECT
  COUNT(*)                              AS row_count,
  COUNT(DISTINCT number)                AS distinct_stations,
  COUNT(DISTINCT pulled_at)             AS snapshot_count,
  MIN(pulled_at)                        AS first_snapshot,
  MAX(pulled_at)                        AS latest_snapshot,
  SUM(available_bikes)                  AS bikes_available_now
FROM `dublin-bikes-pipeline.dublin_bikes.raw_station_status`;