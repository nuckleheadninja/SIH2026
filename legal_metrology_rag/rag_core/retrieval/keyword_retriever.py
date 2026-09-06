"""BM25 Keyword Retriever for exact legal clause and term matching using rank_bm25."""

import re
from typing import List, Dict, Any, Optional, Union
from rank_bm25 import BM25Okapi


def simple_tokenize(text: str) -> List[str]:
    """Basic lowercasing and alphanumeric tokenization."""
    return re.findall(r"\w+", text.lower())


class KeywordRetriever:
    def __init__(self, vector_store=None):
        self.vector_store = vector_store
        self.bm25 = None
        self.doc_ids = []
        self._build_index()

    def _build_index(self):
        if not self.vector_store or not self.vector_store.documents:
            self.bm25 = None
            self.doc_ids = []
            return

        corpus_tokens = []
        self.doc_ids = list(self.vector_store.documents.keys())

        for doc_id in self.doc_ids:
            doc = self.vector_store.documents[doc_id]
            combined_text = " ".join([
                str(doc.get("text", "")),
                str(doc.get("rule", "")),
                str(doc.get("sub_rule", "")),
                str(doc.get("clause", "")),
                str(doc.get("chapter", "")),
                str(doc.get("schedule", ""))
            ])
            corpus_tokens.append(simple_tokenize(combined_text))

        if corpus_tokens:
            self.bm25 = BM25Okapi(corpus_tokens)

    def retrieve(
        self,
        query: Union[str, List[str]] = "",
        query_terms: Optional[List[str]] = None,
        raw_query_string: str = "",
        top_k: int = 20,
        status_filter: Optional[str] = "current"
    ) -> List[Dict[str, Any]]:
        """Retrieves top_k document chunks matching BM25 keyword search."""
        if not self.vector_store or not self.vector_store.documents:
            return []

        if self.bm25 is None or len(self.doc_ids) != len(self.vector_store.documents):
            self._build_index()

        if self.bm25 is None:
            return []

        if raw_query_string:
            query_str = raw_query_string
        elif isinstance(query, str) and query:
            query_str = query
        elif query_terms:
            query_str = " ".join(query_terms)
        elif isinstance(query, list):
            query_str = " ".join(query)
        else:
            query_str = ""

        query_tokens = simple_tokenize(query_str)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        scored_docs = []
        for doc_id, score in zip(self.doc_ids, scores):
            if score <= 0:
                continue
            doc = self.vector_store.documents[doc_id]
            doc_status = doc.get("status", "current")
            if status_filter is not None and doc_status != status_filter:
                continue

            doc_copy = {k: v for k, v in doc.items() if k != "embedding"}
            doc_copy["bm25_score"] = float(score)
            doc_copy["score"] = float(score)
            scored_docs.append(doc_copy)

        scored_docs.sort(key=lambda x: x["bm25_score"], reverse=True)
        return scored_docs[:top_k]


