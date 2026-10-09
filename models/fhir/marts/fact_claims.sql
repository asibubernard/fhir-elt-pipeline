select 
    c.claim_id,
    c.encounter_id,
    c.patient_id,
    c.total_cost,
    c.item_count,
    
    e.encounter_class,

    -- info about when the claim was filed
    d_created.date_key as created_date,
    d_created.year as created_year,
    d_created.month_name as created_month,
    d_created.month_number as created_month_number,
    d_created.day_name as created_day,

    -- info about when the service started
    d_service.date_key as service_date,
    d_service.year as service_year,
    d_service.month_name as service_month,
    d_service.is_weekend as service_was_weekend


from {{ ref('int_patient_claims') }} as c
left join {{ ref('int_patient_encounters') }} as e 
    on c.encounter_id = e.encounter_id
left join {{ ref('dim_date') }} as d_created
    on date(timestamp(c.claim_created_date)) = d_created.date_key
left join {{ ref('dim_date') }} as d_service
    on date(timestamp(c.service_start_date)) = d_service.date_key
