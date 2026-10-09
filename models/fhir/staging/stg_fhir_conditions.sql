with source_condtions as (
    select * from {{ source('raw_fhir_data', 'fhir_conditions') }}
),

renamed as (
    select 
        condition_id,
        patient_id,
        encounter_id,
        code as condition_code,
        clinical_status,
        display as condition_description,
        safe_cast(onset_date as timestamp) as onset_date,
        _ingested_at as ingested_at,

    from source_condtions
)

select * from renamed