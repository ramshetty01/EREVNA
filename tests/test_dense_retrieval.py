import numpy as np
import pytest

from research.models import Document
from research.retrieval import chunk_documents, retrieve


class Encoder:
    def encode(self, texts, normalize_embeddings=True):
        # Fixed embeddings isolate ranking/fusion behavior from model downloads.
        return np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]])


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
