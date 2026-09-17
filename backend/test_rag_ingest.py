from sqlalchemy import text

from database import SessionLocal
from embedding_service import generate_embeddings
from models import Document, DocumentChunk
from rag_ingest import SOURCES, process_document


TEST_SOURCE = SOURCES[0]


def main():
    print("=" * 70)
    print("CONTROLLED RAG INGESTION TEST")
    print("=" * 70)

    # 1. Reuse the existing PDF extraction + chunking pipeline.
    result = process_document(TEST_SOURCE)

    chunks = result["chunks"][:3]

    if len(chunks) != 3:
        raise RuntimeError(
            f"Expected at least 3 chunks, got {len(chunks)}"
        )

    print(f"\nSelected chunks: {len(chunks)}")

    # 2. Generate one embedding per chunk.
    texts = [chunk["chunk_text"] for chunk in chunks]

    embeddings = generate_embeddings(texts)

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            f"Embedding mismatch: "
            f"{len(chunks)} chunks, "
            f"{len(embeddings)} embeddings"
        )

    for i, embedding in enumerate(embeddings, start=1):
        if len(embedding) != 768:
            raise RuntimeError(
                f"Embedding {i} has dimension {len(embedding)}, "
                f"expected 768"
            )

    print("Embedding mapping verified: 3 chunks -> 3 embeddings")
    print("Embedding dimension verified: 768")

    # 3. Write the controlled test data to PostgreSQL.
    db = SessionLocal()

    try:
        # Remove a previous test document if this script was already run.
        existing = (
            db.query(Document)
            .filter(
                Document.document_id == TEST_SOURCE["document_id"]
            )
            .first()
        )

        if existing:
            db.delete(existing)
            db.commit()
            print("Removed previous test document.")

        document = Document(
            document_id=TEST_SOURCE["document_id"],
            source=TEST_SOURCE["source"],
            title=TEST_SOURCE["title"],
            topic=TEST_SOURCE["topic"],
            source_url=TEST_SOURCE["source_url"],
        )

        db.add(document)
        db.flush()

        for chunk, embedding in zip(chunks, embeddings):
            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_number=chunk["chunk_number"],
                page=chunk["page_start"],
                chunk_text=chunk["chunk_text"],
                embedding=embedding,
                meta_data={
                    "page_start": chunk["page_start"],
                    "page_end": chunk["page_end"],
                    "source": TEST_SOURCE["source"],
                    "title": TEST_SOURCE["title"],
                    "topic": TEST_SOURCE["topic"],
                    "source_url": TEST_SOURCE["source_url"],
                },
            )

            db.add(db_chunk)

        db.commit()

        print("\nDatabase write successful.")

        # 4. Verify what PostgreSQL actually stored.
        document_count = (
            db.query(Document)
            .filter(
                Document.document_id == TEST_SOURCE["document_id"]
            )
            .count()
        )

        chunk_count = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == document.id
            )
            .count()
        )

        print(f"Documents stored: {document_count}")
        print(f"Chunks stored: {chunk_count}")

        # 5. Verify vector dimensions inside PostgreSQL.
        vector_dimensions = db.execute(
            text(
                """
                SELECT vector_dims(embedding)
                FROM document_chunks
                WHERE document_id = :document_id
                ORDER BY chunk_number
                """
            ),
            {"document_id": document.id},
        ).scalars().all()

        print(f"Stored vector dimensions: {vector_dimensions}")

        if document_count != 1:
            raise RuntimeError("Document count verification failed.")

        if chunk_count != 3:
            raise RuntimeError("Chunk count verification failed.")

        if vector_dimensions != [768, 768, 768]:
            raise RuntimeError(
                f"Vector dimension verification failed: "
                f"{vector_dimensions}"
            )

        print("\n" + "=" * 70)
        print("CONTROLLED RAG INGESTION TEST PASSED")
        print("=" * 70)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()