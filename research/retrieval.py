"""BM25 baseline, optional dense search and reciprocal-rank hybrid retrieval."""

import math
import re
from collections import Counter

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


def bm25_scores(query: str, passages: list[Passage]) -> list[float]:
    if not passages:
        return []
    counts = [Counter(tokens(p.title + " " + p.text)) for p in passages]
    lengths = [sum(c.values()) for c in counts]
    avg = sum(lengths) / len(lengths) or 1
    scores = [0.0] * len(passages)
    for term in set(tokens(query)):
        df = sum(term in c for c in counts)
        idf = math.log(1 + (len(counts) - df + 0.5) / (df + 0.5))
        for i, c in enumerate(counts):
            tf = c[term]
            scores[i] += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * lengths[i] / avg))
    return scores


def retrieve(
    query: str, passages: list[Passage], method: str = "bm25", k: int = 8, encoder=None
) -> list[Passage]:
    if method not in ("bm25", "dense", "hybrid"):
        raise ValueError("Retrieval must be bm25, dense or hybrid")
    if not passages or k <= 0:
        return []
    scores = bm25_scores(query, passages)
    if method != "bm25":
        if encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise ValueError(
                    "Install requirements-semantic.txt for dense/hybrid retrieval."
                ) from exc
            encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        vectors = encoder.encode([query] + [p.text for p in passages], normalize_embeddings=True)
        dense = [float(v @ vectors[0]) for v in vectors[1:]]
        if method == "dense":
            scores = dense
        else:
            fused = [0.0] * len(passages)
            for ranking in (scores, dense):
                for rank, index in enumerate(
                    sorted(range(len(passages)), key=lambda i: ranking[i], reverse=True), 1
                ):
                    if ranking[index] > 0:
                        fused[index] += 1 / (60 + rank)
            scores = fused
    order = sorted(range(len(passages)), key=lambda i: (-scores[i], passages[i].id))
    return [
        passages[i].model_copy(update={"score": round(scores[i], 6)})
        for i in order
        if scores[i] > 0
    ][:k]


def evidence_context(passages: list[Passage]) -> str:
    return "\n\n".join(f"[{p.id}] {p.title}\nURL: {p.url}\n{p.text}" for p in passages)
