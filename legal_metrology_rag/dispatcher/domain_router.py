"""Domain Router dispatcher for dynamically selecting domain RAG modules based on commodity_type."""

from typing import List, Dict, Any
from legal_metrology_rag.domains.legal_metrology.rag import LegalMetrologyRAG
from legal_metrology_rag.domains.fssai.rag import FSSAIRAG
from shared.constants import CommodityType


class DomainRouter:
    def __init__(self):
        self.legal_metrology_rag = LegalMetrologyRAG()
        self.fssai_rag = FSSAIRAG()

    def select_domains(self, commodity_type: str) -> List[Any]:
        """Selects active domain RAG instances depending on commodity_type.
        
        Rules:
        - Always include LegalMetrologyRAG.
        - Include FSSAIRAG if commodity_type == 'food'.
        """
        active_domains = [self.legal_metrology_rag]

        if commodity_type == CommodityType.FOOD.value or commodity_type == "food":
            active_domains.append(self.fssai_rag)

        return active_domains

    def dispatch_and_query(self, check_queries: List[Dict[str, Any]], commodity_type: str) -> List[Dict[str, Any]]:
        """Dispatches check queries across selected domain RAG modules and collects evidence."""
        domains = self.select_domains(commodity_type)
        all_evidences = []

        for q in check_queries:
            for domain_rag in domains:
                evidence = domain_rag.query_compliance(q)
                all_evidences.append(evidence)

        return all_evidences
