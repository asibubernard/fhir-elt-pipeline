with encounters as (
    select * from {{ ref('stg_fhir_encounters') }}
),

patients as (
    select * from {{ ref('stg_fhir_patients') }}
)

select
    e.encounter_id,
    e.patient_id,
    p.first_name,
    p.last_name,
    p.gender,
    e.encounter_class,
    e.encounter_status,
    e.start_date,
    e.end_date

from encounters e
left join patients p
    on e.patient_id = p.patient_id
    