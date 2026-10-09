with claims as (
    select * from {{ ref('stg_fhir_claims') }}
),

patients as (
    select * from {{ ref('stg_fhir_patients') }}
)

select
    c.claim_id,
    c.encounter_id,
    c.patient_id,
    p.first_name,
    p.last_name,
    c.total_cost,
    c.item_count,
    c.claim_created_date,
    c.service_start_date,
    c.service_end_date

from claims c
left join patients p
    on c.patient_id = p.patient_id
