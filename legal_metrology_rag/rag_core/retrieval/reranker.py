"""
LegalReranker: Combines Cross-Encoder neural pair scoring, Requirement-Level Compliance Intent & Facet Matching,
Context Disambiguation, and Legal Hierarchy Boosting to rank hybrid candidate chunks.
"""

import os
from typing import List, Dict, Any, Optional, Union
from legal_metrology_rag.rag_core.query.legal_query_parser import LegalQueryParser
from legal_metrology_rag.rag_core.query.compliance_intent_normalizer import ComplianceIntentNormalizer

try:
    from sentence_transformers import CrossEncoder
    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False


class LegalReranker:
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        target_top_k: int = 5
    ):
        self.target_top_k = target_top_k
        self.model_name = model_name
        self.model = None
        self.intent_normalizer = ComplianceIntentNormalizer()

        if HAS_CROSS_ENCODER:
            try:
                self.model = CrossEncoder(self.model_name)
            except Exception as e:
                print(f"Warning: Failed to load CrossEncoder '{model_name}': {e}. Falling back to RRF + Hierarchy ranking.")
                self.model = None

    def rerank(
        self,
        query: Union[str, List[str]] = "",
        candidate_chunks: Optional[List[Dict[str, Any]]] = None,
        query_terms: Optional[List[str]] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs Requirement-Level Intent, Facet, Context, and Legal Hierarchy Reranking.
        """
        cands = candidate_chunks or []
        if not cands:
            return []

        limit = top_k or self.target_top_k
        if isinstance(query, str) and query:
            query_str = query
        elif query_terms:
            query_str = " ".join(query_terms)
        elif isinstance(query, list):
            query_str = " ".join(query)
        else:
            query_str = ""

        query_str = query_str.strip()

        # Parse query for explicit reference and requirement intent
        parsed_meta = LegalQueryParser.parse(query_str)
        normalized_intent = self.intent_normalizer.normalize(query_str)

        # Extract normalized features
        q_object = normalized_intent.get("detected_object")
        q_facets = normalized_intent.get("detected_facets", [])
        q_context = normalized_intent.get("detected_context", "PACKAGE_LABEL")
        detected_intent_rule = normalized_intent.get("matched_rule")
        intent_confidence = normalized_intent.get("confidence", 0.0)

        # Prepare Cross-Encoder neural context pairs
        if self.model is not None and query_str:
            pairs = []
            for cand in cands:
                text = cand.get("text", "")
                rule = cand.get("rule", "")
                sub_rule = cand.get("sub_rule", "")
                clause = cand.get("clause", "")
                sched = cand.get("schedule", "")
                req_name = normalized_intent.get("requirement_name", "") or "Legal Metrology Provision"

                context_str = (
                    f"QUERY: {query_str}\n"
                    f"INTENT: {normalized_intent.get('intent_id', 'general_query')}\n"
                    f"FACETS: {', '.join(q_facets)}\n"
                    f"CONTEXT: {q_context}\n"
                    f"REQUIREMENT: {req_name}\n"
                    f"PROVISION: Rule {rule} (Sub {sub_rule}, Clause {clause}, Schedule {sched})\n"
                    f"DOCUMENT: Legal Metrology (Packaged Commodities) Rules, 2011\n"
                    f"TEXT: {text}"
                )
                pairs.append([query_str, context_str])

            ce_scores = self.model.predict(pairs)
        else:
            ce_scores = [0.0] * len(cands)

        q_clause = parsed_meta.get("clause")
        q_sub = parsed_meta.get("sub_rule")
        q_rule = parsed_meta.get("rule")
        q_sec = parsed_meta.get("section")
        q_sched = parsed_meta.get("schedule")
        explicit = parsed_meta.get("explicit_provision", False)

        reranked = []
        for idx, cand in enumerate(cands):
            item = dict(cand)
            ce_score = float(ce_scores[idx]) if self.model is not None else 0.0
            rrf_score = float(cand.get("rrf_score", 0.0))
            vec_score = float(cand.get("vector_score", 0.0))
            bm25_score = float(cand.get("bm25_score", 0.0))

            doc_clause = str(cand.get("clause", "")) if cand.get("clause") else None
            doc_sub = str(cand.get("sub_rule", "")) if cand.get("sub_rule") else None
            doc_rule = str(cand.get("rule", "")) if cand.get("rule") else None
            doc_sec = str(cand.get("section", "")) if cand.get("section") else None
            doc_sched = str(cand.get("schedule", "")) if cand.get("schedule") else None
            doc_text = cand.get("text", "").lower()
            doc_chapter = cand.get("chapter", "").lower()

            hierarchy_boost = 0.0
            intent_boost = 0.0
            facet_boost = 0.0
            context_boost = 0.0
            contradiction_penalty = 0.0
            meta_match_type = "NO_MATCH"

            # 1. Legal Hierarchy Boosts for Explicit Legal References
            if explicit:
                if q_clause:
                    if doc_clause and q_clause.lower() == doc_clause.lower():
                        hierarchy_boost += 15.0
                        meta_match_type = "EXACT_CLAUSE"
                    elif (doc_sub and q_sub and q_sub.lower() == doc_sub.lower()) or (doc_rule and q_rule and q_rule.lower() == doc_rule.lower()):
                        hierarchy_boost += 5.0
                        meta_match_type = "PARENT_RULE"
                elif q_sub:
                    if doc_sub and q_sub.lower() == doc_sub.lower():
                        hierarchy_boost += 15.0
                        meta_match_type = "EXACT_SUBRULE"
                    elif doc_rule and q_rule and q_rule.lower() == doc_rule.lower():
                        hierarchy_boost += 5.0
                        meta_match_type = "PARENT_RULE"
                elif q_sec:
                    if doc_sec and q_sec.lower() == doc_sec.lower():
                        hierarchy_boost += 15.0
                        meta_match_type = "EXACT_SECTION"
                elif q_rule:
                    if doc_rule and q_rule.lower() == doc_rule.lower():
                        hierarchy_boost += 15.0
                        meta_match_type = "EXACT_RULE"

                # Level 3: Exact Schedule Match
                if q_sched and doc_sched and q_sched.lower() == doc_sched.lower():
                    hierarchy_boost += 15.0
                    meta_match_type = "EXACT_SCHEDULE"
                elif q_sched and (not doc_sched or doc_sched.lower() != q_sched.lower()):
                    # Level 4: Explicit Schedule Mismatch Penalty
                    hierarchy_boost -= 20.0
                    meta_match_type = "SCHEDULE_MISMATCH"

            # 2. Compliance Intent Boost for Natural-Language Queries
            if detected_intent_rule and intent_confidence >= 0.35:
                prov_str = format_prov_string(doc_rule, doc_sub, doc_clause, doc_sched)
                if detected_intent_rule.lower() in prov_str.lower():
                    intent_boost += 5.0 * intent_confidence
                    if meta_match_type == "NO_MATCH":
                        meta_match_type = "INTENT_MATCH"

            # 3. Requirement Facet Matching & Context Disambiguation
            # A. Context Matching & Contradiction Penalties
            if q_context == "WHOLESALE_PACKAGE":
                if doc_rule == "24" or "wholesale" in doc_chapter:
                    context_boost += 3.0
                elif doc_rule == "13" and doc_sub == "13(6)":
                    # Retail multi-pack penalized when query specifies wholesale context
                    contradiction_penalty -= 15.0
            elif q_context == "ADVERTISEMENT":
                if doc_rule == "31":
                    context_boost += 3.0
            elif q_context == "PACKAGE_LABEL":
                # Package label context: penalize advertisement rule (Rule 31) if advertisement wasn't asked
                if doc_rule == "31":
                    contradiction_penalty -= 15.0

            # B. Facet Matching
            if "spacing" in q_facets or "placement" in q_facets:
                if doc_rule == "8" and doc_sub == "8(1)":
                    facet_boost += 5.0
                elif doc_rule == "6" and doc_clause == "6(1)(c)":
                    # Net quantity declaration without clear space facet gets small penalty
                    contradiction_penalty -= 3.0

            if "font_size" in q_facets:
                if q_context == "PACKAGE_LABEL" and doc_rule == "7" and doc_sub == "7(2)":
                    facet_boost += 5.0
                elif q_context == "ADVERTISEMENT" and doc_rule == "31" and doc_sub == "31(2)":
                    facet_boost += 5.0

            if "wrapper_visibility" in q_facets:
                if doc_rule == "9" and doc_sub == "9(2)":
                    facet_boost += 5.0

            if "multipack" in q_facets:
                if doc_rule == "13" and doc_sub == "13(6)":
                    facet_boost += 5.0
                elif doc_rule == "11" and doc_sub == "11(1)":
                    contradiction_penalty -= 5.0

            if "wrapper_exclusion" in q_facets:
                if doc_rule == "11" and doc_sub == "11(1)":
                    facet_boost += 5.0

            # Final composite ranking score
            final_score = (
                ce_score +
                hierarchy_boost +
                intent_boost +
                facet_boost +
                context_boost +
                contradiction_penalty +
                (rrf_score * 10.0) +
                (vec_score * 2.0)
            )

            score_components = {
                "vector": float(vec_score),
                "bm25": float(bm25_score),
                "rrf": float(rrf_score),
                "cross_encoder": float(ce_score),
                "intent_match": float(intent_boost),
                "facet_match": float(facet_boost),
                "context_match": float(context_boost),
                "contradiction_penalty": float(contradiction_penalty),
                "hierarchy": float(hierarchy_boost),
                "final": float(final_score)
            }

            item["cross_encoder_score"] = ce_score
            item["hierarchy_boost"] = hierarchy_boost
            item["intent_boost"] = intent_boost
            item["facet_boost"] = facet_boost
            item["context_boost"] = context_boost
            item["contradiction_penalty"] = contradiction_penalty
            item["meta_match_type"] = meta_match_type
            item["score_components"] = score_components
            item["final_score"] = float(final_score)
            item["retrieval_score"] = float(final_score)
            reranked.append(item)

        reranked.sort(key=lambda x: x["final_score"], reverse=True)

        for final_rank, item in enumerate(reranked[:limit], start=1):
            item["final_rank"] = final_rank

        return reranked[:limit]


def format_prov_string(rule, sub_rule, clause, schedule) -> str:
    if clause:
        return f"Rule {clause}"
    elif sub_rule:
        return f"Rule {sub_rule}"
    elif rule:
        return f"Rule {rule}"
    elif schedule:
        return f"Schedule {schedule}"
    return ""
