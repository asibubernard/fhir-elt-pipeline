with patients as (
    select * from {{ ref('stg_fhir_patients') }}
)

select 
    patient_id,
    first_name,
    last_name,    
    gender,
    birth_date,
    city

from patients
