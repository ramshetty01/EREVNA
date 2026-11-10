import numpy as np
import pytest

from research.models import Document
from research.retrieval import chunk_documents, retrieve


class Encoder:
    def encode(self, texts, normalize_embeddings=True):
        # Fixed embeddings isolate ranking/fusion behavior from model downloads.
        return np.array([[0.0, 1.0] if "Cooking" in text else [1.0, 0.0] for text in texts])


@pytest.mark.parametrize("method", ["dense", "hybrid"])
def test_vector_and_hybrid_ranking_contract(method):
    passages = chunk_documents(
        [
            Document(
                title="Cooking",
                url="https://example.org/cooking",
                text="Cooking recipes and ovens.",
            ),
            Document(
                title="Transport",
                url="https://example.org/transport",
                text="Vehicles carry people between cities.",
            ),
        ]
    )
    result = retrieve("automobile", passages, method=method, encoder=Encoder(), k=1)
    assert result[0].source_id == "S2"


def test_invalid_retrieval_method_is_not_silently_ignored():
    with pytest.raises(ValueError):
        retrieve("test", [], method="typo")


def test_index_encodes_corpus_once_and_does_not_mutate_sources():
    from research.retrieval import RetrievalIndex

    class RecordingEncoder(Encoder):
        def __init__(self):
            self.batches = []

        def encode(self, texts, normalize_embeddings=True):
            self.batches.append(list(texts))
            return super().encode(texts, normalize_embeddings)

    passages = chunk_documents(
        [
            Document(
                title="Transport",
                url="https://example.org/transport",
                text="Vehicles carry people.",
            ),
            Document(title="Cooking", url="https://example.org/cooking", text="Cooking recipes."),
        ]
    )
    encoder = RecordingEncoder()
    index = RetrievalIndex(passages, method="hybrid", encoder=encoder)
    first = index.search("automobile", k=1)
    passages[0].text = "Changed after indexing"
    first[0].text = "Changed result"
    second = index.search("automobile", k=1)
    assert second[0].text == "Vehicles carry people."
    assert [len(batch) for batch in encoder.batches] == [2, 1, 1]
    assert passages[0].score == 0


@pytest.mark.parametrize(
    "vectors", [np.array([[float("nan"), 0]]), np.array([1.0, 0]), np.zeros((2, 2))]
)
def test_invalid_embeddings_are_rejected(vectors):
    from research.retrieval import RetrievalIndex

    class Invalid:
        def encode(self, *args, **kwargs):
            return vectors

    passages = chunk_documents(
        [Document(title="Doc", url="https://example.org", text="Some document text.")]
    )
    with pytest.raises(ValueError, match="Embedding model"):
        RetrievalIndex(passages, method="dense", encoder=Invalid())


def test_lexical_and_empty_indexes_never_load_optional_model(monkeypatch):
    from research.retrieval import RetrievalIndex

    def forbidden():
        pytest.fail("Optional model must not load")

    monkeypatch.setattr("research.retrieval.get_dense_encoder", forbidden)
    for method in ("bm25", "dense", "hybrid"):
        assert RetrievalIndex([], method=method).search("query") == []
    passages = chunk_documents(
        [Document(title="Doc", url="https://example.org", text="Some document text.")]
    )
    assert RetrievalIndex(passages).search("document")
    assert retrieve("query", passages, method="dense", k=0) == []


def test_hybrid_ties_use_stable_passage_ids():
    from research.models import Passage
    from research.retrieval import RetrievalIndex

    passages = [
        Passage(
            id=i,
            source_id=i,
            title="Doc",
            url="https://example.org/" + i,
            text="Vehicles carry people.",
        )
        for i in ("S2", "S1")
    ]
    for order in (passages, list(reversed(passages))):
        result = RetrievalIndex(order, method="hybrid", encoder=Encoder()).search("vehicles")
        assert [p.id for p in result] == ["S1", "S2"]


def test_concurrent_first_requests_load_pinned_encoder_once(monkeypatch):
    import sys
    from concurrent.futures import ThreadPoolExecutor
    from types import SimpleNamespace

    from research.retrieval import MODEL_ID, MODEL_REVISION, _load_encoder, get_dense_encoder

    calls = []
    instance = object()

    def load(model_id, **kwargs):
        calls.append((model_id, kwargs))
        return instance

    monkeypatch.setitem(
        sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=load)
    )
    _load_encoder.cache_clear()
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: get_dense_encoder(), range(4)))
        assert all(result is instance for result in results)
        assert calls == [
            (
                MODEL_ID,
                {
                    "revision": MODEL_REVISION,
                    "device": "cpu",
                    "trust_remote_code": False,
                    "model_kwargs": {"use_safetensors": True},
                },
            )
        ]
    finally:
        _load_encoder.cache_clear()
