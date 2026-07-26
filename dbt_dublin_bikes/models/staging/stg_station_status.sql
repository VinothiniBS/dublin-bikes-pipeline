-- Staging model: one clean, deduplicated row per station per snapshot.
-- Reads the raw ingested data, standardises types, converts the epoch
-- last_update into a real timestamp, and derives an occupancy ratio.

with source as (

    select * from {{ source('raw', 'raw_station_status') }}

),

deduplicated as (

    -- The ingestion appends on a schedule; if a run ever double-fires,
    -- the same (station, snapshot) could appear twice. Keep one row each.
    select
        *,
        row_number() over (
            partition by number, pulled_at
            order by last_update desc
        ) as row_num
    from source

),

cleaned as (

    select
        -- identifiers
        number                                          as station_id,
        name                                            as station_name,
        address,

        -- location
        latitude,
        longitude,

        -- flags
        banking                                         as has_payment_terminal,
        bonus                                           as is_bonus_station,
        status,

        -- capacity and availability
        bike_stands                                     as total_stands,
        available_bikes,
        available_bike_stands,

        -- derived: share of docks currently holding a bike (0-1)
        safe_divide(available_bikes, bike_stands)       as occupancy_ratio,

        -- timestamps
        pulled_at                                       as snapshot_at,

        -- the API gives last_update as epoch milliseconds; convert to a timestamp
        timestamp_millis(last_update)                   as station_last_updated_at

    from deduplicated
    where row_num = 1

)

select * from cleaned
