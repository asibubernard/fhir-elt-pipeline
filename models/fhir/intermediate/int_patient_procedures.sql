with procedures as (
    -- Staged FHIR procedure data (one row per procedure)
    select * from {{ ref('stg_fhir_procedures') }}
),

encounters as (
    -- Staged FHIR encounter data (one row per visit)
    select * from {{ ref('stg_fhir_encounters') }}
)

select
    pr.procedure_id,
    pr.patient_id,
    pr.encounter_id,
    e.encounter_class,
    pr.procedure_code,
    pr.procedure_description,
    pr.procedure_status,
    pr.procedure_start_time,
    pr.procedure_end_time

from procedures as pr
left join encounters as e
    on pr.encounter_id = e.encounter_id
