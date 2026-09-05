"""
Smoke test script for Legal Metrology RAG VectorStore & Dense Embeddings.
Embeds all 35 validated legal chunks and runs raw similarity searches.
"""

import json
from pathlib import Path
from legal_metrology_rag.rag_core.embeddings.embedder import LegalEmbedder
from legal_metrology_rag.rag_core.database.vector_store import VectorStore


def main():
    chunks_file = Path(r"d:\SIH2026\legal_metrology_rag\outputs\validated_legal_chunks.json")
    if not chunks_file.exists():
        raise FileNotFoundError(f"Validated legal chunks file not found at {chunks_file}")

    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} validated legal chunks from {chunks_file.name}")

    # 1. Initialize embedder and vector store
    print("\n[1/3] Initializing LegalEmbedder with 'sentence-transformers/all-MiniLM-L6-v2'...")
    embedder = LegalEmbedder(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    print("[2/3] Initializing VectorStore collection 'legal_metrology' and adding documents...")
    vector_store = VectorStore(collection_name="legal_metrology", embedder=embedder)
    vector_store.add_documents(chunks)
    print(f"Indexed {len(vector_store.documents)} vectors into collection 'legal_metrology'.")

    # 2. Define smoke test queries
    query_terms = [
        "MRP declaration",
        "net quantity",
        "consumer care details",
        "height of numerals Schedule II"
    ]

    print("\n[3/3] Running Smoke Test for known query terms...")
    print("=" * 80)

    for q in query_terms:
        print(f"\nQUERY: \"{q}\"")
        print("-" * 80)

        # Raw similarity search (returns top 3 results including superseded/current chunks)
        results = vector_store.search(q, top_k=3)
        for idx, res in enumerate(results, 1):
            chunk_id = res.get("chunk_id")
            status = res.get("status")
            rule = res.get("rule")
            sub_rule = res.get("sub_rule")
            clause = res.get("clause")
            eff_from = res.get("effective_from")
            eff_to = res.get("effective_to")
            score = res.get("score")
            text = res.get("text", "")
            snippet = text[:120] + "..." if len(text) > 120 else text

            print(f"  Result {idx}:")
            print(f"    - Chunk ID       : {chunk_id}")
            print(f"    - Status         : {status}")
            print(f"    - Provision      : Rule {rule} (Sub-rule: {sub_rule}, Clause: {clause})")
            print(f"    - Effective dates: {eff_from} to {eff_to}")
            print(f"    - Score          : {score:.4f}")
            print(f"    - Text snippet   : {snippet}")

        # Also test with status_filter="current" to verify metadata filtering
        current_results = vector_store.search(q, top_k=3, status_filter="current")
        print(f"  [Filter status='current'] Top result: {current_results[0]['chunk_id']} (Status: {current_results[0]['status']}, Score: {current_results[0]['score']:.4f})")

    print("\n" + "=" * 80)
    print("Smoke test completed successfully!")


if __name__ == "__main__":
    main()
