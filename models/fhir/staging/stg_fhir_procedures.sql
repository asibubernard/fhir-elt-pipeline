with source_procedures as (
    select * from {{ source('raw_fhir_data', 'fhir_procedures') }}
),

renamed as (
    select
        procedure_id,
        patient_id,
        encounter_id,
        code as procedure_code,
        display as procedure_description,
        status as procedure_status,
        _ingested_at as ingested_at,
        safe_cast(start_time as timestamp) as procedure_start_time,
        safe_cast(end_time as timestamp) as procedure_end_time

    from source_procedures
)

select * from renamed
