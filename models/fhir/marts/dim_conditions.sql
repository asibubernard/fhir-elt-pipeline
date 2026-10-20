-- Condition dimension: one row per distinct condition code
select distinct
    condition_code,
    condition_description,
    condition_category

from {{ ref('int_patient_conditions') }}
