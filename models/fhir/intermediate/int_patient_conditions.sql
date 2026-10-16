with conditions as (
    -- Staged FHIR condition data (one row per condition)
    select * from {{ ref('stg_fhir_conditions') }}
),

category_map as (
    -- Map of condition codes to categories (from a seed file)
    select
        condition_code,
        category
    from {{ ref('condition_category_map') }}
)

select
    c.condition_id,
    c.patient_id,
    c.encounter_id,
    c.condition_code,
    c.condition_description,
    -- New: category from the hand-checked list
    coalesce(m.category, 'Unmapped') as condition_category,
    c.clinical_status,
    c.recorded_date

from conditions c
left join category_map m
    on c.condition_code = m.condition_code