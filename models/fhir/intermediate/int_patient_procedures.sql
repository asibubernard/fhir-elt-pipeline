with procedures as (
    select * from {{ ref('stg_fhir_procedures') }}
),

patients as (
    select * from {{ ref('stg_fhir_patients') }}
),

encounters as (
    select * from {{ ref('stg_fhir_encounters') }}
)

select 
    pr.procedure_id,
    pr.patient_id,
    p.first_name,
    p.last_name,
    pr.encounter_id,
    e.encounter_class,
    pr.procedure_code,
    pr.procedure_description,
    pr.procedure_status,
    pr.procedure_start_time,
    pr.procedure_end_time

from procedures pr
left join patients p
    on pr.patient_id = p.patient_id
left join encounters e
    on pr.encounter_id = e.encounter_id
