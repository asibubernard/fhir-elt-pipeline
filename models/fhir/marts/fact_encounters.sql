-- Fact table: one row per patient encounter (visit) with temporal data
select
    e.encounter_id,
    e.patient_id,
    e.encounter_class,

    -- Information about when the encounter started
    d_start.date_key as start_date,
    d_start.year as start_year,
    d_start.month_name as start_month,
    d_start.day_name as start_day,

    -- Information about when the encounter ended
    d_end.date_key as end_date,
    d_end.year as end_year,
    d_end.month_name as end_month,
    d_end.day_name as end_day

from {{ ref('int_patient_encounters') }} as e
left join {{ ref('dim_date') }} as d_start
    on date(timestamp(e.start_date)) = d_start.date_key
left join {{ ref('dim_date') }} as d_end
    on date(timestamp(e.end_date)) = d_end.date_key