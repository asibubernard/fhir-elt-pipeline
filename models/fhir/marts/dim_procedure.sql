select distinct
    procedure_code,
    procedure_description

from {{ ref('int_patient_procedures') }}