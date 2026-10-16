-- Calendar dimension: comprehensive date table for reporting
with dates as (
    -- Generate date range from 1900-01-01 to 2030-12-31
    select date_day
    from unnest(generate_date_array('1900-01-01', '2030-12-31')) as date_day
)

select
    date_day as date_key,
    extract(year from date_day) as year,
    extract(month from date_day) as month_number,
    format_date('%B', date_day) as month_name,
    extract(day from date_day) as day_of_month,
    format_date('%A', date_day) as day_name,
    extract(quarter from date_day) as quarter,
    extract(isoweek from date_day) as week_number,
    extract(dayofweek from date_day) in (1, 7) as is_weekend

from dates