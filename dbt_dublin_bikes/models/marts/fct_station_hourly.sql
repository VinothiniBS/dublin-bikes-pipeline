-- Mart: average station activity by hour of day.
-- Aggregates every snapshot into hour-level averages so we can see how bike
-- availability across Dublin changes through the day. One row per hour (0-23).

with staged as (

    select * from {{ ref('stg_station_status') }}

),

hourly as (

    select
        extract(hour from snapshot_at)          as hour_of_day,
        count(distinct snapshot_at)             as snapshots_in_hour,
        count(distinct station_id)              as stations_reporting,

        -- city-wide availability, averaged across all readings in this hour
        round(avg(available_bikes), 1)          as avg_bikes_available,
        round(avg(available_bike_stands), 1)    as avg_stands_free,
        round(avg(occupancy_ratio), 3)          as avg_occupancy_ratio

    from staged
    group by hour_of_day

)

select * from hourly
order by hour_of_day
