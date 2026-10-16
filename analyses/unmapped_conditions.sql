select
    c.condition_code,
    c.condition_description,
    count(*) as records
from {{ ref('stg_fhir_conditions') }} c
left join {{ ref('condition_category_map') }} m
    on c.condition_code = m.condition_code
where m.condition_code is null
group by 1, 2
order by records desc