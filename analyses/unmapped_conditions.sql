select
    c.condition_code,
    c.condition_description,
    count(*) as records
from {{ ref('stg_fhir_conditions') }} as c
left join {{ ref('condition_category_map') }} as m
    on c.condition_code = m.condition_code
where m.condition_code is null
group by c.condition_code, c.condition_description
order by records desc
