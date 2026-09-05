"""Shared constants and enums for Package Compliance Checker."""

from enum import Enum


class ComplianceStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class FieldName(str, Enum):
    MRP = "mrp"
    NET_QUANTITY = "net_quantity"
    MANUFACTURER_NAME = "manufacturer_name"
    MANUFACTURER_ADDRESS = "manufacturer_address"
    PACKER_DETAILS = "packer_details"
    IMPORTER_DETAILS = "importer_details"
    COUNTRY_OF_ORIGIN = "country_of_origin"
    DATE_OF_MANUFACTURE = "date_of_manufacture"
    EXPIRY_DATE = "expiry_date"
    CONSUMER_CARE = "consumer_care"
    GENERIC_NAME = "generic_name"
    FSSAI_LICENSE = "fssai_license"
    NUTRITIONAL_INFO = "nutritional_info"
    INGREDIENTS = "ingredients"


class CommodityType(str, Enum):
    FOOD = "food"
    DRUGS_COSMETICS = "drugs_cosmetics"
    GENERAL = "general_commodity"
    PRE_PACKAGED = "pre_packaged_commodity"


class DomainType(str, Enum):
    LEGAL_METROLOGY = "legal_metrology"
    FSSAI = "fssai"
    DRUGS_COSMETICS = "drugs_cosmetics"
