select distinct
    condition_code,
    condition_description

from {{ ref('int_patient_conditions')}}
