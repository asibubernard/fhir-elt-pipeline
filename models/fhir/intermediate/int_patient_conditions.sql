with conditions as (
    select * from {{ ref('stg_fhir_conditions') }}
),

patients as (
    select * from {{ ref('stg_fhir_patients') }}
)

select 

    c.condition_id,
    c.patient_id,
    p.first_name,
    p.last_name,
    c.condition_code,
    c.condition_description,
    c.clinical_status,
    c.onset_date

from conditions c

left join patients p
    on c.patient_id = p.patient_id