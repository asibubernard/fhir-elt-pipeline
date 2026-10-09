from datetime import datetime, timezone

# ==========================================
# Helper functions
# ==========================================

def safe_scalar(value):
    """Ensure a value going into a STRING column is never a list.
    FHIR sometimes sends 'family' or 'display' style fields as a
    single-item array instead of a plain string. Grab the first
    element if so, otherwise pass the value through unchanged."""
    if isinstance(value, list):
        return value[0] if value else None
    return value

def safe_extract_code(codeable_concept):
    """Helper to extract the first coding code and display from a FHIR CodeableConcept."""
    if not codeable_concept:
        return None, None
    coding = codeable_concept.get("coding", [])
    if coding:
        return safe_scalar(coding[0].get("code")), safe_scalar(coding[0].get("display"))
    return None, safe_scalar(codeable_concept.get("text"))

def clean_reference(ref):
    """Strip a FHIR reference down to a plain ID.
    References can come as 'urn:uuid:<id>' (local Synthea bundles) or
    'ResourceType/<id>' (typical REST API style) - this normalizes both
    to just the bare ID so ids match across tables."""
    if not ref:
        return None
    return ref.replace("urn:uuid:", "").split("/")[-1]

# ==========================================
# Flattening functions
# ==========================================

def flatten_patient(resource):
    names = resource.get("name", [])
    first_name = safe_scalar(names[0].get("given", [""])[0]) if names else None
    last_name = safe_scalar(names[0].get("family")) if names else None
    addresses = resource.get("address", [])
    city = safe_scalar(addresses[0].get("city")) if addresses else None
    return {
        "patient_id": resource.get("id"),
        "gender": safe_scalar(resource.get("gender")),
        "birth_date": safe_scalar(resource.get("birthDate")),
        "first_name": first_name,
        "last_name": last_name,
        "city": city,
        "_ingested_at": datetime.now(timezone.utc).isoformat()
    }

def flatten_encounter(resource):
    patient_ref = resource.get("subject", {}).get("reference", "")
    patient_id = clean_reference(patient_ref)
    encounter_type = resource.get("type", [{}])[0]
    code, display = safe_extract_code(encounter_type)
    period = resource.get("period", {})
    class_field = resource.get("class")
    class_value = class_field.get("code") if isinstance(class_field, dict) else class_field
    return {
        "encounter_id": resource.get("id"),
        "patient_id": patient_id,
        "status": safe_scalar(resource.get("status")),
        "class": safe_scalar(class_value),
        "type_code": code,
        "type_display": display,
        "start_time": period.get("start"),
        "end_time": period.get("end"),
        "_ingested_at": datetime.now(timezone.utc).isoformat()
    }

def flatten_condition(resource):
    patient_ref = resource.get("subject", {}).get("reference", "")
    patient_id = clean_reference(patient_ref)
    encounter_ref = resource.get("encounter", {}).get("reference", "")
    encounter_id = clean_reference(encounter_ref)
    code, display = safe_extract_code(resource.get("code"))
    status_obj = resource.get("clinicalStatus")
    status = status_obj.get("coding", [{}])[0].get("code") if isinstance(status_obj, dict) else status_obj
    return {
        "condition_id": resource.get("id"),
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "code": code,
        "display": display,
        "clinical_status": safe_scalar(status),
        "onset_date": safe_scalar(resource.get("onsetDateTime")),
        "_ingested_at": datetime.now(timezone.utc).isoformat()
    }

def flatten_procedure(resource):
    patient_ref = resource.get("subject", {}).get("reference", "")
    patient_id = clean_reference(patient_ref)
    encounter_ref = resource.get("encounter", {}).get("reference", "")
    encounter_id = clean_reference(encounter_ref)
    status = resource.get("status")
    code, display = safe_extract_code(resource.get("code"))
    period = resource.get("performedPeriod", {})
    return {
        "procedure_id": resource.get("id"),
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "code": code,
        "display": display,
        "status": safe_scalar(status),
        "start_time": period.get("start"),
        "end_time": period.get("end"),
        "_ingested_at": datetime.now(timezone.utc).isoformat()
    }

def flatten_claim(resource):
    patient_ref = resource.get("patient", {}).get("reference", "")
    patient_id = clean_reference(patient_ref)
    items = resource.get("item", [])

    # New: Find the encounter this claim belongs to 
    encounter_id = None
    for item in items:
        encounter_refs = item.get("encounter", [])
        if encounter_refs:
            encounter_id = clean_reference(encounter_refs[0].get("reference"))
            break

    total_cost = 0.0
    for item in items:
        money = item.get("net") or item.get("unitPrice") or {}
        total_cost += money.get("value") or 0 

    if total_cost == 0 and "total" in resource:
        total_cost = resource.get("total", {}).get("value") or 0

    billable_period = resource.get("billablePeriod", {})
    return {
        "claim_id": resource.get("id"),
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "total_cost": total_cost,
        "item_count": len(items),
        "created_date": resource.get("created"),
        "billable_period_start": billable_period.get("start"),
        "billable_period_end": billable_period.get("end"),
        "_ingested_at": datetime.now(timezone.utc).isoformat()
    }

# ==========================================
# Resource type -> flattener function
# ==========================================
FLATTENERS = {
    "Patient": flatten_patient,
    "Encounter": flatten_encounter,
    "Condition": flatten_condition,
    "Procedure": flatten_procedure,
    "Claim": flatten_claim
}