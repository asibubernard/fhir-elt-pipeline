with source_claims as (
    select * from {{ source('raw_fhir_data', 'fhir_claims') }}
),

renamed as (
    select
        claim_id,
        encounter_id,
        patient_id,
        round(total_cost, 2) as total_cost,
        item_count,
        created_date as claim_created_date,
        billable_period_start as service_start_date,
        billable_period_end as service_end_date,
        _ingested_at as ingested_at

    from source_claims
)

select * from renamed   
