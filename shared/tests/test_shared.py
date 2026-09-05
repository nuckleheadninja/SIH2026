import json
from pathlib import Path
from jsonschema import validate
from shared.constants import ComplianceStatus, FieldName, CommodityType, DomainType


def test_shared_constants():
    assert ComplianceStatus.PASS == "PASS"
    assert ComplianceStatus.FAIL == "FAIL"
    assert FieldName.MRP == "mrp"
    assert CommodityType.FOOD == "food"
    assert DomainType.LEGAL_METROLOGY == "legal_metrology"
    assert DomainType.FSSAI == "fssai"


def test_sample_ocr_output_schema():
    schemas_dir = Path(__file__).parent.parent / "schemas"
    sample_dir = Path(__file__).parent.parent / "sample_data"

    with open(schemas_dir / "ocr_output.schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)

    with open(sample_dir / "sample_ocr_output.json", "r", encoding="utf-8") as f:
        sample_data = json.load(f)

    validate(instance=sample_data, schema=schema)


def test_sample_field_extraction_schema():
    schemas_dir = Path(__file__).parent.parent / "schemas"
    sample_dir = Path(__file__).parent.parent / "sample_data"

    with open(schemas_dir / "field_extraction.schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)

    with open(sample_dir / "sample_field_extraction_output.json", "r", encoding="utf-8") as f:
        sample_data = json.load(f)

    validate(instance=sample_data, schema=schema)


def test_sample_compliance_check_schema():
    schemas_dir = Path(__file__).parent.parent / "schemas"
    sample_dir = Path(__file__).parent.parent / "sample_data"

    with open(schemas_dir / "compliance_check.schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)

    with open(sample_dir / "sample_compliance_check.json", "r", encoding="utf-8") as f:
        sample_data = json.load(f)

    validate(instance=sample_data, schema=schema)
