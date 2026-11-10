"""BM25 baseline, optional dense search and reciprocal-rank hybrid retrieval."""

import math
import re
from collections import Counter
from functools import lru_cache
from threading import Lock

import numpy as np

from research.models import Document, Passage

STOP = set(
    "a an the is are was were to of in and or for on with how what when does do can it by as from this that which".split()
)


def tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


def chunk_documents(documents: list[Document], size: int = 160, overlap: int = 35) -> list[Passage]:
    if not 0 <= overlap < size:
        raise ValueError("Chunk overlap must be smaller than size")
    passages = []
    seen_urls: set[str] = set()
    for doc in documents:
        if doc.url in seen_urls:
            continue
        seen_urls.add(doc.url)
        sid = f"S{len(seen_urls)}"
        words = doc.text.split()
        for i, start in enumerate(range(0, len(words), size - overlap), 1):
            passages.append(
                Passage(
                    id=f"{sid}-P{i}",
                    source_id=sid,
                    title=doc.title,
                    url=doc.url,
                    text=" ".join(words[start : start + size]),
                )
            )
            if start + size >= len(words):
                break
    return passages


MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
_MODEL_LOCK = Lock()


@lru_cache(maxsize=1)
def _load_encoder():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ValueError("Install requirements-semantic.txt for dense/hybrid retrieval.") from exc
    return SentenceTransformer(
        MODEL_ID,
        revision=MODEL_REVISION,
        device="cpu",
        trust_remote_code=False,
        model_kwargs={"use_safetensors": True},
    )


def get_dense_encoder():
    # Avoid duplicate model loads when the API receives concurrent first requests.
    with _MODEL_LOCK:
        return _load_encoder()


class RetrievalIndex:
    """Reusable corpus index. Passage text/vectors stay local to this instance."""

    def __init__(self, passages: list[Passage], method: str = "bm25", encoder=None):
        if method not in ("bm25", "dense", "hybrid"):
            raise ValueError("Retrieval must be bm25, dense or hybrid")
        self.passages = [p.model_copy(deep=True) for p in passages]
        self.method = method
        self.counts = [Counter(tokens(p.title + " " + p.text)) for p in self.passages]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.average_length = sum(self.lengths) / len(self.lengths) if self.lengths else 1
        self.average_length = self.average_length or 1
        self.document_frequency = Counter(term for counts in self.counts for term in counts)
        self.encoder = None
        self.vectors = None
        if method != "bm25" and self.passages:
            self.encoder = encoder if encoder is not None else get_dense_encoder()
            self.vectors = self._encode([p.text for p in self.passages])

    def _encode(self, texts: list[str]):
        if self.encoder is None:
            raise ValueError("No embedding model is configured for this index.")
        vectors = np.asarray(self.encoder.encode(texts, normalize_embeddings=True))
        if vectors.ndim != 2 or vectors.shape[0] != len(texts) or vectors.shape[1] == 0:
            raise ValueError("Embedding model returned invalid vector dimensions.")
        if not np.isfinite(vectors).all():
            raise ValueError("Embedding model returned non-finite values.")
        return vectors

    def bm25_scores(self, query: str) -> list[float]:
        scores = [0.0] * len(self.passages)
        for term in set(tokens(query)):
            df = self.document_frequency[term]
            idf = math.log(1 + (len(self.counts) - df + 0.5) / (df + 0.5))
            for i, counts in enumerate(self.counts):
                tf = counts[term]
                scores[i] += (
                    idf
                    * tf
                    * 2.5
                    / (tf + 1.5 * (0.25 + 0.75 * self.lengths[i] / self.average_length))
                )
        return scores

    def search(self, query: str, k: int = 8) -> list[Passage]:
        if not self.passages or k <= 0:
            return []
        scores = self.bm25_scores(query)
        if self.method != "bm25":
            assert self.vectors is not None
            query_vector = self._encode([query])[0]
            if query_vector.shape[0] != self.vectors.shape[1]:
                raise ValueError("Query and corpus embeddings have different dimensions.")
            dense = (self.vectors @ query_vector).tolist()
            if self.method == "dense":
                scores = dense
            else:
                fused = [0.0] * len(self.passages)
                for ranking in (scores, dense):
                    order = sorted(
                        range(len(self.passages)), key=lambda i: (-ranking[i], self.passages[i].id)
                    )
                    for rank, index in enumerate(order, 1):
                        if ranking[index] > 0:
                            fused[index] += 1 / (60 + rank)
                scores = fused
        order = sorted(range(len(self.passages)), key=lambda i: (-scores[i], self.passages[i].id))
        return [
            self.passages[i].model_copy(update={"score": round(scores[i], 6)})
            for i in order
            if scores[i] > 0
        ][:k]


def bm25_scores(query: str, passages: list[Passage]) -> list[float]:
    return RetrievalIndex(passages).bm25_scores(query)


def retrieve(
    query: str, passages: list[Passage], method: str = "bm25", k: int = 8, encoder=None
) -> list[Passage]:
    if method not in ("bm25", "dense", "hybrid"):
        raise ValueError("Retrieval must be bm25, dense or hybrid")
    if not passages or k <= 0:
        return []
    return RetrievalIndex(passages, method=method, encoder=encoder).search(query, k=k)


def evidence_context(passages: list[Passage]) -> str:
    return "\n\n".join(f"[{p.id}] {p.title}\nURL: {p.url}\n{p.text}" for p in passages)
