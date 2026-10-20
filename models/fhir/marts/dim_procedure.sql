-- Procedure dimension: one row per distinct procedure code
select distinct
    procedure_code,
    procedure_description

from {{ ref('int_patient_procedures') }}
