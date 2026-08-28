with sources_claims as (
    select *
    from {{ source('raw_fhir_data', 'fhir_claims') }}
),

renamed as (
    select
        id as claim_id,
        status as claim_status,
        type as claim_type,
        use as claim_use,
        patient_id as patient_id,
        created_at as claim_created_at,
        updated_at as claim_updated_at
    from sources_claims
)
select * from renamed   
