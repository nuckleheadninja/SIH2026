"""
Hybrid Retriever combining Dense Vector Search, BM25 Keyword Search,
Compliance Intent Query Expansion, Exact Legal Provision Match, and RRF Fusion.
Tracks retrieval provenance for debugging.
"""

import os
import json
from typing import List, Dict, Any, Optional, Union
from legal_metrology_rag.rag_core.database.vector_store import VectorStore
from legal_metrology_rag.rag_core.retrieval.vector_retriever import VectorRetriever
from legal_metrology_rag.rag_core.retrieval.keyword_retriever import KeywordRetriever
from legal_metrology_rag.rag_core.query.legal_query_parser import LegalQueryParser
from legal_metrology_rag.rag_core.query.compliance_intent_normalizer import ComplianceIntentNormalizer


class HybridRetriever:
    def __init__(self, vector_store=None, rrf_k: int = 60, alpha: float = 0.5):
        if vector_store is None:
            self.vector_store = VectorStore(collection_name="legal_metrology")
            chunks_path = r"d:\SIH2026\legal_metrology_rag\outputs\validated_legal_chunks.json"
            if os.path.exists(chunks_path):
                with open(chunks_path, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
                self.vector_store.add_documents(chunks)
        else:
            self.vector_store = vector_store

        self.vector_retriever = VectorRetriever(vector_store=self.vector_store)
        self.keyword_retriever = KeywordRetriever(vector_store=self.vector_store)
        self.intent_normalizer = ComplianceIntentNormalizer()
        self.rrf_k = rrf_k
        self.alpha = alpha

    def retrieve(
        self,
        query: Union[str, List[str]] = "",
        query_terms: Optional[List[str]] = None,
        raw_query_string: str = "",
        top_k: int = 20,
        status_filter: Optional[str] = "current"
    ) -> List[Dict[str, Any]]:
        """
        Performs multi-representation hybrid retrieval:
        1. Parse explicit legal references (Rules, Sections, Schedules).
        2. Normalize query to compliance intent and canonical expansion.
        3. Retrieve candidates via Original Vector, Intent Vector, BM25, and Exact Provision streams.
        4. Track retrieval provenance in candidate metadata.
        5. Perform RRF fusion across candidate streams.
        """
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

        if not query_str:
            return []

        # 1. Legal Query Parsing & Intent Normalization
        parsed_meta = LegalQueryParser.parse(query_str)
        normalized_intent = self.intent_normalizer.normalize(query_str)

        # 2. Original Vector Search (top 20)
        vector_results = self.vector_retriever.retrieve(
            query=query_str, top_k=top_k, status_filter=status_filter
        )

        # 3. Intent Expansion Vector Search (top 20)
        intent_results = []
        if normalized_intent.get("confidence", 0.0) >= 0.35 and normalized_intent.get("canonical_expansion"):
            intent_results = self.vector_retriever.retrieve(
                query=normalized_intent["canonical_expansion"], top_k=top_k, status_filter=status_filter
            )

        # 4. BM25 Keyword Search (top 20)
        bm25_results = self.keyword_retriever.retrieve(
            query=query_str, top_k=top_k, status_filter=status_filter
        )

        # 5. Exact Provision & Schedule Search
        exact_results = self._search_exact_provisions(parsed_meta, status_filter=status_filter)

        # Provenance and Reciprocal Rank Fusion tracking
        doc_map: Dict[str, Dict[str, Any]] = {}
        provenance_map: Dict[str, List[str]] = {}
        rrf_scores: Dict[str, float] = {}
        vector_scores: Dict[str, float] = {}
        bm25_scores: Dict[str, float] = {}
        vector_ranks: Dict[str, int] = {}
        bm25_ranks: Dict[str, int] = {}
        intent_ranks: Dict[str, int] = {}
        exact_ranks: Dict[str, int] = {}

        def add_provenance(cid: str, source: str):
            if cid not in provenance_map:
                provenance_map[cid] = []
            if source not in provenance_map[cid]:
                provenance_map[cid].append(source)

        # Stream A: Original Vector
        for rank, doc in enumerate(vector_results, start=1):
            cid = doc["chunk_id"]
            doc_map[cid] = doc
            vector_scores[cid] = float(doc.get("vector_score", doc.get("score", 0.0)))
            vector_ranks[cid] = rank
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))
            add_provenance(cid, "original_vector")

        # Stream B: Intent Vector Expansion
        for rank, doc in enumerate(intent_results, start=1):
            cid = doc["chunk_id"]
            if cid not in doc_map:
                doc_map[cid] = doc
            intent_ranks[cid] = rank
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))
            add_provenance(cid, "intent_vector")

        # Stream C: BM25
        for rank, doc in enumerate(bm25_results, start=1):
            cid = doc["chunk_id"]
            if cid not in doc_map:
                doc_map[cid] = doc
            bm25_scores[cid] = float(doc.get("bm25_score", doc.get("score", 0.0)))
            bm25_ranks[cid] = rank
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))
            add_provenance(cid, "bm25")

        # Stream D: Exact Provision Match (Priority boost)
        for rank, doc in enumerate(exact_results, start=1):
            cid = doc["chunk_id"]
            if cid not in doc_map:
                doc_map[cid] = doc
            exact_ranks[cid] = rank
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (2.0 / (self.rrf_k + rank))
            add_provenance(cid, "exact_provision")

        merged = []
        for cid, rrf_val in rrf_scores.items():
            doc_copy = dict(doc_map[cid])
            doc_copy["vector_score"] = float(vector_scores.get(cid, 0.0))
            doc_copy["bm25_score"] = float(bm25_scores.get(cid, 0.0))
            doc_copy["vector_rank"] = vector_ranks.get(cid)
            doc_copy["bm25_rank"] = bm25_ranks.get(cid)
            doc_copy["intent_rank"] = intent_ranks.get(cid)
            doc_copy["exact_rank"] = exact_ranks.get(cid)
            doc_copy["retrieval_sources"] = provenance_map.get(cid, [])
            doc_copy["rrf_score"] = float(rrf_val)
            doc_copy["hybrid_score"] = float(rrf_val)
            doc_copy["score"] = float(rrf_val)
            doc_copy["parsed_query_meta"] = parsed_meta
            doc_copy["normalized_intent"] = normalized_intent
            merged.append(doc_copy)

        merged.sort(key=lambda x: x["rrf_score"], reverse=True)
        return merged

    def _search_exact_provisions(self, parsed_meta: Dict[str, Any], status_filter: Optional[str] = "current") -> List[Dict[str, Any]]:
        """Searches index for exact metadata matches based on parsed query legal references."""
        if not parsed_meta or not parsed_meta.get("explicit_provision"):
            return []

        q_rule = parsed_meta.get("rule")
        q_sub = parsed_meta.get("sub_rule")
        q_clause = parsed_meta.get("clause")
        q_sec = parsed_meta.get("section")
        q_sched = parsed_meta.get("schedule")

        matches = []
        for doc in self.vector_store.documents.values():
            if status_filter and doc.get("status") and doc.get("status") != status_filter:
                continue

            doc_rule = str(doc.get("rule", "")) if doc.get("rule") else None
            doc_sub = str(doc.get("sub_rule", "")) if doc.get("sub_rule") else None
            doc_clause = str(doc.get("clause", "")) if doc.get("clause") else None
            doc_sec = str(doc.get("section", "")) if doc.get("section") else None
            doc_sched = str(doc.get("schedule", "")) if doc.get("schedule") else None

            # Priority 1: Clause Match
            if q_clause and doc_clause and q_clause.lower() == doc_clause.lower():
                matches.append((1, doc))
                continue

            # Priority 2: Sub-rule Match
            if q_sub and doc_sub and q_sub.lower() == doc_sub.lower():
                matches.append((2, doc))
                continue

            # Priority 3: Schedule Match
            if q_sched and doc_sched and q_sched.lower() == doc_sched.lower():
                matches.append((3, doc))
                continue

            # Priority 4: Section Match
            if q_sec and doc_sec and q_sec.lower() == doc_sec.lower():
                matches.append((4, doc))
                continue

            # Priority 5: Rule Match
            if q_rule and doc_rule and q_rule.lower() == doc_rule.lower():
                matches.append((5, doc))
                continue

        matches.sort(key=lambda x: x[0])
        return [item[1] for item in matches]
