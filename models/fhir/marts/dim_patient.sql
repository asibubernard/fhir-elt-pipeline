select

    patient_id,
    first_name,
    last_name,
    gender,
    birth_date, 
    city

from {{ ref('int_patient_profiles') }}
