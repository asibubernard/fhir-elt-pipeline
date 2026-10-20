with source_conditions as (
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
        _ingested_at as ingested_at,
        safe_cast(onset_date as timestamp) as recorded_date

    from source_conditions
)

select * from renamed
