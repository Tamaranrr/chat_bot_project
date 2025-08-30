from typing import List, Tuple, Optional
from dataclasses import dataclass
import unicodedata as ud
import regex as re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz

# Normalización simple (quita tildes y baja a minúsculas)
def normalize(text: str) -> str:
    t = text.lower()
    t = ud.normalize("NFKD", t)    
    t = re.sub(r"\p{M}", "", t)    
    t = re.sub(r"\s+", " ", t).strip()
    return t

@dataclass
class QA:
    question: str
    answer: str
    category: str

class SemanticRetriever:
    def __init__(self, qa_list: List[QA]):
        self.qa_list = qa_list
        self.questions = [normalize(q.question) for q in qa_list]
        self.vectorizer = TfidfVectorizer(ngram_range=(1,2), min_df=1)
        self.matrix = self.vectorizer.fit_transform(self.questions)

    def search(self, query: str, top_k: int = 3) -> List[Tuple[QA, float]]:
        qn = normalize(query)
        qvec = self.vectorizer.transform([qn])
        sims = cosine_similarity(qvec, self.matrix).ravel()
        # top-k
        idxs = sims.argsort()[::-1][:top_k]
        results = []
        for i in idxs:
            qa = self.qa_list[i]
            # mezcla coseno + fuzzy (token_set_ratio) para tolerar errores
            fuzzy_score = fuzz.token_set_ratio(qn, self.questions[i]) / 100.0
            score = 0.7 * sims[i] + 0.3 * fuzzy_score
            results.append((qa, float(score)))
        return results

    def best(self, query: str, threshold: float = 0.35) -> Optional[Tuple[QA, float]]:
        candidates = self.search(query, top_k=3)
        if not candidates:
            return None
        qa, score = max(candidates, key=lambda x: x[1])
        return (qa, score) if score >= threshold else None
