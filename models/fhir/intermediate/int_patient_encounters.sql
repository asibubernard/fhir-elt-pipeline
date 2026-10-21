with encounters as (
    -- Staged FHIR encounter data (one row per visit/encounter)
    select * from {{ ref('stg_fhir_encounters') }}
),

patients as (
    -- Staged FHIR patient demographics (one row per patient)
    select * from {{ ref('stg_fhir_patients') }}
)

select
    e.encounter_id,
    e.patient_id,
    p.gender,
    e.encounter_class,
    e.encounter_status,
    e.start_date,
    e.end_date,
    e.ingested_at

from encounters as e
left join patients as p
    on e.patient_id = p.patient_id
