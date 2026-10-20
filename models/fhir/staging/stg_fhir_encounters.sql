with source_encounters as (
    select * from {{ source('raw_fhir_data', 'fhir_encounters') }}
),

renamed as (
    select
        encounter_id,
        patient_id,
        status as encounter_status,
        class as encounter_class,
        type_code as encounter_type_code,
        type_display as encounter_type_description,
        cast(start_time as DATE) as start_date,
        cast(end_time as DATE) as end_date,
        _ingested_at as ingested_at

    from source_encounters
)

select * from renamed
