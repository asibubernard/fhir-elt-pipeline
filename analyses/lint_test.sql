SELECT   claim_id,patient_id from {{ ref('fact_claims') }}
