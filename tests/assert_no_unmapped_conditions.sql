{{ config(severity='warn') }}

select
    condition_code,
    condition_description,
    count(*) as records
from {{ ref('int_patient_conditions') }}
where condition_category = 'Unmapped'
group by 1, 2 