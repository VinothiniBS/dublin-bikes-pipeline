CREATE TABLE IF NOT EXISTS `dublin-bikes-pipeline.dublin_bikes.raw_station_status` (
  pulled_at              TIMESTAMP,
  number                 INT64,
  name                   STRING,
  address                STRING,
  latitude               FLOAT64,
  longitude              FLOAT64,
  banking                BOOL,
  bonus                  BOOL,
  status                 STRING,
  bike_stands            INT64,
  available_bikes        INT64,
  available_bike_stands  INT64,
  last_update            INT64
)
PARTITION BY DATE(pulled_at);