"""
Hybrid Retriever Smoke Test Script with Cross-Encoder Neural Reranking.
Combines Vector Search (top 20) + BM25 Search (top 20) via RRF and CrossEncoder Reranker (top 5).
Runs 4 original queries + 2 new queries, reporting vector_score, bm25_score, rrf_score, cross_encoder_score, and final rank.
"""

import json
from pathlib import Path
from legal_metrology_rag.rag_core.embeddings.embedder import LegalEmbedder
from legal_metrology_rag.rag_core.database.vector_store import VectorStore
from legal_metrology_rag.rag_core.retrieval.hybrid_retriever import HybridRetriever
from legal_metrology_rag.rag_core.retrieval.reranker import LegalReranker


def main():
    chunks_file = Path(r"d:\SIH2026\legal_metrology_rag\outputs\validated_legal_chunks.json")
    if not chunks_file.exists():
        raise FileNotFoundError(f"Validated legal chunks file not found at {chunks_file}")

    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} validated legal chunks from {chunks_file.name}")

    print("\n[1/3] Initializing LegalEmbedder & VectorStore ('legal_metrology')...")
    embedder = LegalEmbedder(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = VectorStore(collection_name="legal_metrology", embedder=embedder)
    vector_store.add_documents(chunks)
    print(f"Indexed {len(vector_store.documents)} chunks into VectorStore.")

    print("\n[2/3] Initializing HybridRetriever (RRF) & Cross-Encoder LegalReranker...")
    hybrid_retriever = HybridRetriever(vector_store=vector_store, rrf_k=60)
    reranker = LegalReranker(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2", target_top_k=5)

    test_queries = [
        # 4 Original Queries
        "MRP declaration",
        "net quantity",
        "consumer care details",
        "height of numerals Schedule II",
        # 2 New Queries
        "Schedule II standard package sizes",
        "importer name address imported package"
    ]

    print("\n[3/3] Running Hybrid Retrieval & Neural Cross-Encoder Reranking Smoke Test...")
    print("=" * 100)

    for q_idx, q in enumerate(test_queries, 1):
        print(f"\nQUERY #{q_idx}: \"{q}\"")
        print("-" * 100)

        # 1. Retrieve top 20 merged hybrid candidates using RRF & status_filter="current"
        hybrid_candidates = hybrid_retriever.retrieve(query=q, top_k=20, status_filter="current")

        # 2. Cross-encoder neural rerank to top 5 final results
        final_top5 = reranker.rerank(query=q, candidate_chunks=hybrid_candidates, top_k=5)

        for res in final_top5:
            rank = res.get("final_rank")
            cid = res.get("chunk_id")
            status = res.get("status")
            rule = res.get("rule")
            sub_rule = res.get("sub_rule")
            clause = res.get("clause")
            vec_score = res.get("vector_score", 0.0)
            bm25_score = res.get("bm25_score", 0.0)
            rrf_score = res.get("rrf_score", 0.0)
            ce_score = res.get("cross_encoder_score", res.get("final_score", 0.0))
            text = res.get("text", "")
            snippet = text[:120] + "..." if len(text) > 120 else text

            print(f"  Rank #{rank}:")
            print(f"    - Chunk ID            : {cid}")
            print(f"    - Status              : {status}")
            print(f"    - Provision           : Rule {rule} (Sub: {sub_rule}, Clause: {clause})")
            print(f"    - Vector Score        : {vec_score:.4f} (Cosine Similarity)")
            print(f"    - BM25 Score          : {bm25_score:.4f} (Raw BM25)")
            print(f"    - RRF Score           : {rrf_score:.4f}")
            print(f"    - Cross-Encoder Score : {ce_score:.4f} (Neural Pair Logit)")
            print(f"    - Text Snippet        : {snippet}")

    print("\n" + "=" * 100)
    print("Hybrid Retrieval Neural Reranking Smoke Test completed successfully!")


if __name__ == "__main__":
    main()
