"""
ComplianceIntentNormalizer: Maps natural language user queries to structured compliance intents,
requirement-level facets, execution contexts, and vocabulary expansions derived generically from the compliance rule catalogue.
"""

import os
import json
import re
from typing import Dict, Any, Optional, List


class ComplianceIntentNormalizer:
    """Normalizes natural-language user queries into structured compliance intents, facets, and contexts."""

    def __init__(self, intents_path: Optional[str] = None):
        if intents_path is None:
            intents_path = r"d:\SIH2026\legal_metrology_rag\catalogue\compliance_intents.json"

        self.intents: List[Dict[str, Any]] = []
        if os.path.exists(intents_path):
            with open(intents_path, "r", encoding="utf-8") as f:
                self.intents = json.load(f)

    def normalize(self, query: str) -> Dict[str, Any]:
        """
        Analyzes query string and maps to compliance intent, object, facet, and context.
        Returns structured dictionary containing detected intent, target rule, concepts, facets, context, and expansion.
        """
        if not query or not isinstance(query, str) or not self.intents:
            return self._empty_result()

        q_lower = query.lower().strip()
        q_tokens = set(re.findall(r"\w+", q_lower))

        # Classify query-level Context
        query_context = self._detect_query_context(q_lower, q_tokens)
        query_facets = self._detect_query_facets(q_lower, q_tokens)

        best_intent = None
        max_score = 0.0
        best_concepts = []

        for intent in self.intents:
            intent_id = intent.get("intent_id")
            req_name = intent.get("requirement_name")
            target_rule = intent.get("rule_target")
            entities = set(t.lower() for t in intent.get("entities", []))
            attributes = set(t.lower() for t in intent.get("attributes", []))
            aliases = intent.get("semantic_aliases", [])
            positive_signals = set(t.lower() for t in intent.get("positive_signals", []))
            negative_signals = set(t.lower() for t in intent.get("negative_signals", []))

            # Check for negative signals that penalize intent selection
            has_negative = any(neg in q_lower for neg in negative_signals)
            if has_negative:
                negative_penalty = 0.40
            else:
                negative_penalty = 0.0

            # 1. Alias exact phrase or sub-phrase match
            alias_match_boost = 0.0
            for alias in aliases:
                a_lower = alias.lower()
                if a_lower in q_lower or q_lower in a_lower:
                    alias_match_boost = 0.60
                    break

            # 2. Positive Signal Match
            pos_signal_boost = 0.0
            for sig in positive_signals:
                if sig in q_lower:
                    pos_signal_boost = 0.30
                    break

            # 3. Token overlap score
            matched_entities = [e for e in entities if e in q_tokens or any(e in t for t in q_tokens)]
            matched_attributes = [a for a in attributes if a in q_tokens or any(a in t for t in q_tokens)]

            entity_score = len(matched_entities) / max(len(entities), 1)
            attribute_score = len(matched_attributes) / max(len(attributes), 1)

            # Context compatibility boost
            intent_context = intent.get("context", "PACKAGE_LABEL")
            context_boost = 0.20 if intent_context == query_context else 0.0

            composite_score = (
                (0.40 * entity_score) +
                (0.20 * attribute_score) +
                alias_match_boost +
                pos_signal_boost +
                context_boost -
                negative_penalty
            )

            if composite_score > max_score and composite_score >= 0.25:
                max_score = composite_score
                best_intent = intent
                best_concepts = list(set(matched_entities + matched_attributes))

        if best_intent is not None:
            canonical_expansion = (
                f"{best_intent.get('requirement_name')} "
                f"{' '.join(best_intent.get('attributes', []))} "
                f"{' '.join(best_intent.get('entities', []))}"
            )
            detected_facets = best_intent.get("facets", [])
            # Merge with query-detected facets
            combined_facets = list(set(detected_facets + query_facets))

            return {
                "intent_id": best_intent.get("intent_id"),
                "requirement_name": best_intent.get("requirement_name"),
                "matched_rule": best_intent.get("rule_target"),
                "matched_concepts": best_concepts,
                "detected_object": best_intent.get("object"),
                "detected_facets": combined_facets,
                "detected_context": query_context,
                "canonical_expansion": canonical_expansion,
                "confidence": min(float(max_score), 1.0)
            }

        return self._empty_result(query_context, query_facets)

    @staticmethod
    def _detect_query_context(q_lower: str, q_tokens: set) -> str:
        if any(w in q_lower for w in ["wholesale", "bulk wholesale", "bulk"]):
            return "WHOLESALE_PACKAGE"
        elif any(w in q_lower for w in ["advertisement", "media release", "advertising", "tv ad"]):
            return "ADVERTISEMENT"
        elif any(w in q_lower for w in ["imported", "country of origin", "importer"]):
            return "IMPORT_PACKAGE"
        elif any(w in q_lower for w in ["multi-pack", "multipack", "multiple packages"]):
            return "MULTIPACK"
        return "PACKAGE_LABEL"

    @staticmethod
    def _detect_query_facets(q_lower: str, q_tokens: set) -> List[str]:
        facets = []
        if any(w in q_lower for w in ["font", "height", "numeral", "letter size", "size"]):
            facets.append("font_size")
        if any(w in q_lower for w in ["clear space", "surrounding", "located", "location", "where"]):
            facets.append("spacing")
            facets.append("placement")
        if any(w in q_lower for w in ["transparent", "reading through", "liquid", "visibility"]):
            facets.append("wrapper_visibility")
        if any(w in q_lower for w in ["exclude", "wrapper weight", "packaging material", "tare"]):
            facets.append("wrapper_exclusion")
        if any(w in q_lower for w in ["multi-pack", "multipack", "individual and total"]):
            facets.append("multipack")
        if any(w in q_lower for w in ["unit", "standard unit"]):
            facets.append("unit")
        return facets

    @staticmethod
    def _empty_result(context: str = "PACKAGE_LABEL", facets: Optional[List[str]] = None) -> Dict[str, Any]:
        return {
            "intent_id": None,
            "requirement_name": None,
            "matched_rule": None,
            "matched_concepts": [],
            "detected_object": None,
            "detected_facets": facets or [],
            "detected_context": context,
            "canonical_expansion": "",
            "confidence": 0.0
        }
