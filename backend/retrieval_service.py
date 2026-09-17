import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from embedding_service import generate_query_embedding


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")


engine = create_engine(DATABASE_URL)


def retrieve_chunks(
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Retrieve the most semantically relevant knowledge chunks
    using Cohere query embeddings and PostgreSQL pgvector.
    """

    if not query.strip():
        return []

    if top_k < 1:
        top_k = 1

    if top_k > 20:
        top_k = 20

    query_embedding = generate_query_embedding(query)

    embedding_string = "[" + ",".join(
        str(value) for value in query_embedding
    ) + "]"

    sql = text(
        """
        SELECT
            id,
            document_id,
            chunk_text,
            1 - (
                embedding <=> CAST(:embedding AS vector)
            ) AS similarity
        FROM document_chunks
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {
                "embedding": embedding_string,
                "top_k": top_k,
            },
        ).fetchall()

    return [
        {
            "id": row.id,
            "document_id": row.document_id,
            "text": row.chunk_text,
            "similarity": float(row.similarity),
        }
        for row in rows
    ]