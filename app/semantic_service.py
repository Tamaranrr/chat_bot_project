from typing import Optional, Tuple
from app.retrieval import SemanticRetriever, QA
from app.knowledge_base import build_semantic_corpus

_retriever: Optional[SemanticRetriever] = None

def get_retriever() -> SemanticRetriever:
    global _retriever
    if _retriever is None:
        corpus = build_semantic_corpus()
        _retriever = SemanticRetriever(corpus)
    return _retriever

def semantic_answer(query: str, threshold: float = 0.35) -> Optional[Tuple[QA, float]]:
    r = get_retriever()
    return r.best(query, threshold=threshold)
