with source_patients as (
    select * from {{ source('raw_fhir_data', 'fhir_patients') }}
),

renamed as (
    select 
        patient_id,
        gender,
        cast(birth_date as DATE) as birth_date,
        {{ mask_phi('first_name') }} as first_name,
        {{ mask_phi('last_name') }} as last_name,
        city,
        _ingested_at as ingested_at
 
    from source_patients
)

select * from renamed
