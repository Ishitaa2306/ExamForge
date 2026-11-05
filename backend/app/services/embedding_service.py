"""
Embedding service — chunk documents and store vectors in ChromaDB.
"""
import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

# Approximate token budget per chunk
CHUNK_TOKEN_LIMIT = 512
CHUNK_OVERLAP_TOKENS = 64


def _split_text(text: str, max_tokens: int = CHUNK_TOKEN_LIMIT) -> list[str]:
    """Naïve whitespace-based chunker by word count (proxy for tokens)."""
    words = text.split()
    chunks: list[str] = []
    start = 0
    overlap = CHUNK_OVERLAP_TOKENS
    while start < len(words):
        end = min(start + max_tokens, len(words))
        chunks.append(" ".join(words[start:end]))
        start = end - overlap if end < len(words) else end
    return [c for c in chunks if c.strip()]


class EmbeddingService:
    _collection = None

    @classmethod
    def _get_collection(cls, chroma_dir: str):
        """Lazy-init ChromaDB persistent client + collection."""
        if cls._collection is None:
            try:
                import chromadb

                client = chromadb.PersistentClient(path=chroma_dir)
                cls._collection = client.get_or_create_collection(
                    name="document_chunks",
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("ChromaDB init failed: %s", exc)
                raise
        return cls._collection

    @classmethod
    def embed_document(
        cls,
        db,  # SQLAlchemy Session
        document,  # Document ORM instance
        text_pages: list[str],
    ) -> None:
        """Chunk pages, embed them, and persist to ChromaDB + PostgreSQL."""
        from app.core.config import settings
        from app.database.models import DocumentChunk

        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as exc:  # noqa: BLE001
            logger.warning("sentence-transformers unavailable, skipping embeddings: %s", exc)
            return

        collection = cls._get_collection(settings.CHROMA_DIR)

        chunk_index = 0
        for page_number, page_text in enumerate(text_pages, start=1):
            for chunk_text in _split_text(page_text):
                chroma_id = str(uuid.uuid4())
                try:
                    embedding = model.encode(chunk_text).tolist()
                    collection.add(
                        ids=[chroma_id],
                        embeddings=[embedding],
                        documents=[chunk_text],
                        metadatas=[{
                            "document_id": document.id,
                            "page_number": page_number,
                            "chunk_index": chunk_index,
                        }],
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Chroma add failed for chunk %d: %s", chunk_index, exc)

                db_chunk = DocumentChunk(
                    document_id=document.id,
                    content=chunk_text,
                    chunk_index=chunk_index,
                    page_number=page_number,
                    token_count=len(chunk_text.split()),
                    chroma_id=chroma_id,
                )
                db.add(db_chunk)
                chunk_index += 1

        db.commit()
        logger.info("Embedded %d chunks for document %d", chunk_index, document.id)

    @classmethod
    def similarity_search(
        cls,
        query: str,
        document_id: int,
        n_results: int = 5,
    ) -> list[str]:
        """Return the top-n most similar chunks for a query string."""
        from app.core.config import settings

        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("all-MiniLM-L6-v2")
            collection = cls._get_collection(settings.CHROMA_DIR)
            embedding = model.encode(query).tolist()
            results = collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                where={"document_id": document_id},
            )
            return results.get("documents", [[]])[0]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Similarity search failed: %s", exc)
            return []
