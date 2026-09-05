"""BaseComplianceRAG abstract base class implemented by specialized domain RAG modules."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseComplianceRAG(ABC):
    def __init__(self, domain_name: str, config_path: str = None):
        self.domain_name = domain_name
        self.config_path = config_path

    @abstractmethod
    def query_compliance(self, check_query: Dict[str, Any]) -> Dict[str, Any]:
        """Queries compliance rule evidence for a given structured compliance check query."""
        pass

    @abstractmethod
    def load_documents(self, raw_dir: str):
        """Loads and indexes legal documents into domain vector store."""
        pass
