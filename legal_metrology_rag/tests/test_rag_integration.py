from legal_metrology_rag.dispatcher.domain_router import DomainRouter
from shared.constants import CommodityType


def test_domain_router_food_commodity():
    router = DomainRouter()
    domains = router.select_domains(CommodityType.FOOD.value)
    assert len(domains) == 2


def test_domain_router_general_commodity():
    router = DomainRouter()
    domains = router.select_domains(CommodityType.GENERAL.value)
    assert len(domains) == 1


def test_domain_router_dispatch_and_query():
    router = DomainRouter()
    queries = [{"check_id": "q1", "field": "mrp", "query_terms": ["mrp"]}]
    evidences = router.dispatch_and_query(queries, commodity_type="food")
    assert len(evidences) == 2
    documents = [e.get("document", "") for e in evidences]
    assert any("Legal Metrology" in d for d in documents)
    assert any("FSSAI" in d for d in documents)
