-- Mart: per-station summary across all snapshots collected.
-- One row per station, showing its typical availability and how often it runs
-- empty or full. Feeds the "busiest / emptiest stations" view on the dashboard.

with staged as (

    select * from {{ ref('stg_station_status') }}

),

station_rollup as (

    select
        station_id,
        station_name,
        latitude,
        longitude,
        max(total_stands)                        as total_stands,

        count(*)                                 as readings,

        -- typical availability
        round(avg(available_bikes), 1)           as avg_bikes_available,
        round(avg(occupancy_ratio), 3)           as avg_occupancy_ratio,

        -- stress signals: how often the station is unusable
        countif(available_bikes = 0)             as times_empty,
        countif(available_bike_stands = 0)       as times_full,

        round(100 * countif(available_bikes = 0) / count(*), 1)        as pct_time_empty,
        round(100 * countif(available_bike_stands = 0) / count(*), 1)  as pct_time_full

    from staged
    group by station_id, station_name, latitude, longitude

)

select * from station_rollup
order by avg_occupancy_ratio desc
