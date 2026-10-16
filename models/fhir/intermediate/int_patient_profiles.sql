with patients as (
    -- Staged FHIR patient demographics (one row per patient)
    select * from {{ ref('stg_fhir_patients') }}
)

select
    patient_id,
    gender,
    birth_year,
    is_age_90_plus,
    state

from patients
