select
    condition_id,
    patient_id,
    encounter_id,
    condition_code,
    condition_description,
    condition_category,
    clinical_status,
    recorded_date

from {{ ref('int_patient_conditions') }}
where recorded_date is not null
