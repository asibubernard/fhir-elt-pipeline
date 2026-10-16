-- Patient dimension: one row per patient with demographics
select
    patient_id,
    gender,
    state,
    birth_year,
    case 
        when is_age_90_plus then '90+'
        when birth_year is null then 'Unknown'
        when extract(year from current_date()) - birth_year < 10 then '0-9'
        when extract(year from current_date()) - birth_year < 20 then '10-19'
        when extract(year from current_date()) - birth_year < 30 then '20-29'
        when extract(year from current_date()) - birth_year < 40 then '30-39'
        when extract(year from current_date()) - birth_year < 50 then '40-49'
        when extract(year from current_date()) - birth_year < 60 then '50-59'
        when extract(year from current_date()) - birth_year < 70 then '60-69'
        when extract(year from current_date()) - birth_year < 80 then '70-79'
        else '80-89'
    end as age_group
    
from {{ ref('int_patient_profiles') }}
