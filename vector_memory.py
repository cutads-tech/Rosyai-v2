import os
import time

# ── ChromaDB ─────────────────────────────────
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_OK = True
except ImportError:
    CHROMA_OK = False
    print("[vector_memory] chromadb not installed. Falling back to in-memory dict.")

# ── Sentence Transformers ─────────────────────
try:
    from sentence_transformers import SentenceTransformer
    _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    EMBED_OK = True
except ImportError:
    EMBED_OK = False
    print("[vector_memory] sentence-transformers not installed.")

PERSIST_DIR = os.path.join(os.path.dirname(__file__), "memory", "chroma_store")

# ── Setup client ─────────────────────────────
_client = None
_collection = None
_fallback_store: list = []   # in-memory fallback


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection
    if not CHROMA_OK:
        return None
    try:
        os.makedirs(PERSIST_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=PERSIST_DIR)
        _collection = _client.get_or_create_collection(
            name="rosy_memory",
            metadata={"hnsw:space": "cosine"}
        )
        return _collection
    except Exception as e:
        print(f"[vector_memory] ChromaDB init error: {e}")
        return None


def _embed(text: str) -> list:
    if EMBED_OK:
        return _embed_model.encode(text).tolist()
    # fallback: simple hash-based fake embedding (not semantic but won't crash)
    h = hash(text) % (2**31)
    return [float((h >> i) & 1) for i in range(384)]


# ═══════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════
def remember(text: str, metadata: dict = None) -> str:
    """Store a text memory. metadata can include tags, source, etc."""
    emb = _embed(text)
    doc_id = str(abs(hash(text + str(time.time()))))
    meta = {"ts": time.time(), **(metadata or {})}

    col = _get_collection()
    if col:
        try:
            col.add(embeddings=[emb], documents=[text], ids=[doc_id], metadatas=[meta])
            return f"Memory stored: '{text[:60]}'"
        except Exception as e:
            print(f"[vector_memory] remember error: {e}")

    # Fallback
    _fallback_store.append({"id": doc_id, "text": text, "ts": time.time()})
    return f"Memory stored (local): '{text[:60]}'"


def recall(query: str, n: int = 3) -> list:
    """Return top-n semantically similar memories for a query."""
    emb = _embed(query)
    col = _get_collection()

    if col:
        try:
            results = col.query(query_embeddings=[emb], n_results=min(n, col.count() or 1))
            docs = results.get("documents", [[]])[0]
            return docs if docs else ["No relevant memories found."]
        except Exception as e:
            print(f"[vector_memory] recall error: {e}")

    # Fallback: return last n entries
    recent = [entry["text"] for entry in _fallback_store[-n:]]
    return recent if recent else ["No memories yet."]


def forget_all():
    """Clear all vector memories."""
    global _collection, _fallback_store
    _fallback_store = []
    col = _get_collection()
    if col:
        try:
            ids = col.get()["ids"]
            if ids:
                col.delete(ids=ids)
            return "All vector memories cleared."
        except Exception as e:
            return f"Clear error: {e}"
    return "Cleared local memory."


def memory_count() -> int:
    col = _get_collection()
    if col:
        try:
            return col.count()
        except Exception:
            pass
    return len(_fallback_store)
