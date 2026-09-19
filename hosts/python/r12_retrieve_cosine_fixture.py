"""P8 realization B: dict-backed cosine-similarity `retrieve/4` fixture.

Scope authority: issue #945 (implementation), design
`docs/design/p8-alternate-provider-substitution-proof-design.md` section 2.3.

This module is a Python-host-only fixture, never reachable from Genia
source and never registered in the global environment (`genia.builtins`).
It adds **no new public Genia builtin, no new factory, and no change to**
`src/genia/retrieval.py`. It supplies exactly one handler pair -- an index
handler and a paired `retrieve/4` handler -- installed through the
existing, unmodified `create_fixture_index_provider` and
`create_fixture_retrieve_provider` factories.

This is realization B of the P8 alternate-provider substitution proof: a
genuinely distinct implementation path from realization A's fixed-order/
fixed-score list-backed fixture (see
`hosts/python/exec_r12_grounded_fixture.py` and
`tests/unit/test_r12_retrieval_fixture.py`'s `_env` helper). Realization B:

- stores the indexed corpus as a `dict` keyed by a synthetic integer id
  (`backend_ref`'s shape here is private to this handler pair -- it is
  never observed by `GeniaRetriever`, by Genia source, or by realization
  A's handler), not realization A's plain ordered `list`;
- computes a real, deterministic cosine similarity between the query
  vector and every stored vector using plain Python arithmetic;
- sorts descending by that computed similarity with a deterministic
  tie-break (original corpus insertion index, ascending) so equal scores
  never produce nondeterministic order;
- returns `score` as the computed cosine similarity itself (a genuine
  finite `float`), not a constant.

It does not call realization A, does not copy realization A's output, and
does not relabel a field -- it is an independently written algorithm over
an independently shaped backend, satisfying the same `retrieve/4`
interface contract realization A satisfies.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from genia.retrieval import create_fixture_index_result, create_fixture_retrieve_result
from genia.values import GeniaMap, GeniaOptionSome


def build_cosine_index_handler() -> Callable[[GeniaMap, list[Any], str], Any]:
    """Return an index handler storing the corpus as an id-keyed dict.

    The dict shape (`{int_id: {"chunk": ..., "vector": ...}}`) is private
    to this handler pair and is not structurally interchangeable with
    realization A's plain list backend.
    """

    def handler(_config: GeniaMap, corpus: list[Any], _credential: str) -> Any:
        backend = {
            position: {
                "chunk": embedded.get("chunk"),
                "vector": embedded.get("embedding").get("vector"),
            }
            for position, embedded in enumerate(corpus)
        }
        return GeniaOptionSome(create_fixture_index_result(backend))

    return handler


def _cosine_similarity(query_vector: list[Any], stored_vector: list[Any]) -> float:
    """Real, deterministic cosine similarity over plain Python arithmetic."""

    dot_product = sum(float(q) * float(s) for q, s in zip(query_vector, stored_vector))
    query_magnitude = math.sqrt(sum(float(q) * float(q) for q in query_vector))
    stored_magnitude = math.sqrt(sum(float(s) * float(s) for s in stored_vector))
    if query_magnitude == 0.0 or stored_magnitude == 0.0:
        return 0.0
    return dot_product / (query_magnitude * stored_magnitude)


def build_cosine_retrieve_handler() -> Callable[[GeniaMap, Any, GeniaMap, int, str], Any]:
    """Return a retrieve handler ranking by real computed cosine similarity.

    Ties are broken by ascending original corpus insertion index, so the
    output order is fully deterministic for identical input, per R12's
    "Deterministic test obligations".
    """

    def handler(
        _config: GeniaMap, backend_ref: Any, query: GeniaMap, k: int, _credential: str
    ) -> Any:
        query_vector = query.get("embedding").get("vector")
        scored = [
            (position, entry["chunk"], _cosine_similarity(query_vector, entry["vector"]))
            for position, entry in backend_ref.items()
        ]
        scored.sort(key=lambda item: (-item[2], item[0]))
        top = scored[:k]
        results = [
            GeniaMap().put("chunk", chunk).put("score", score) for _position, chunk, score in top
        ]
        return GeniaOptionSome(create_fixture_retrieve_result(results))

    return handler
