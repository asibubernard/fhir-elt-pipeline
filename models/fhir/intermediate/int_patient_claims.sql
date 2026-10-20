with claims as (
    -- Staged FHIR claims data (one row per insurance claim)
    select * from {{ ref('stg_fhir_claims') }}
)

select
    c.claim_id,
    c.encounter_id,
    c.patient_id,
    c.total_cost,
    c.item_count,
    c.claim_created_date,
    c.service_start_date,
    c.service_end_date

from claims as c
