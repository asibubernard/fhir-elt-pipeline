with source_patients as (
    select * from {{ source('raw_fhir_data', 'fhir_patients') }}
),

dated as (
    select
        *,
        date_diff(current_date(), cast(birth_date as DATE), year) as age_years
    from source_patients
),

renamed as (
    select
        patient_id,
        gender,
        -- Safe Harbor: Year only, and no year for ages over 89
        case
            when age_years > 89 then null
            else extract(year from cast(birth_date as DATE))
        end as birth_year,
        coalesce(age_years >= 90, false) as is_age_90_plus,
        state,
        _ingested_at as ingested_at

    from dated
)

select * from renamed
