import os
import re

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from embedding_service import generate_query_embedding


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")


engine = create_engine(DATABASE_URL)


# Retrieve more candidates than we finally return.
#
# Why:
# A semantically similar chunk can be a bibliography/reference list.
# We want pgvector to give us a wider candidate pool so we can filter
# unusable chunks without ending up with too little evidence.
RETRIEVAL_CANDIDATE_MULTIPLIER = 4


def _is_reference_chunk(chunk_text: str) -> bool:
    """
    Detect chunks that are primarily bibliographic/reference material
    rather than scientific evidence.

    The filter uses multiple signals because reference chunks do not
    always contain DOI URLs.
    """

    text_value = " ".join(chunk_text.split())

    if not text_value:
        return True

    lower_text = text_value.lower()

    # ---------------------------------------------------------
    # 1. Explicit reference-section headings
    # ---------------------------------------------------------

    reference_headings = (
        "references",
        "reference list",
        "bibliography",
        "literature cited",
        "references cited",
    )

    # Only treat these as a strong signal when they occur near
    # the beginning of the chunk.
    beginning = lower_text[:250]

    if any(
        heading in beginning
        for heading in reference_headings
    ):
        return True

    # ---------------------------------------------------------
    # 2. Bibliographic citation density
    # ---------------------------------------------------------

    year_count = len(
        re.findall(
            r"\b(?:19|20)\d{2}\b",
            text_value,
        )
    )

    doi_count = len(
        re.findall(
            r"(?:https?://)?doi\.org/10\.\d{4,9}/",
            lower_text,
        )
    )

    url_count = len(
        re.findall(
            r"https?://",
            lower_text,
        )
    )

    # Common reference formatting:
    #
    # Author, A. B. 2020. Title...
    # Author, A.B., Author, C.D. (2021)...
    author_year_count = len(
        re.findall(
            r"""
            \b
            [A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’-]{2,}
            (?:[-'][A-Za-zÀ-ÖØ-öø-ÿ]+)?
            (?:,\s*[A-Z]\.?)?
            (?:\s+et\ al\.)?
            [,\s]*
            (?:\(|\s)?
            (?:19|20)\d{2}
            (?:\))?
            """,
            text_value,
            flags=re.VERBOSE,
        )
    )

    # ---------------------------------------------------------
    # 3. Reference-list punctuation / structure
    # ---------------------------------------------------------

    citation_markers = len(
        re.findall(
            r"""
            \b
            (?:et\ al\.|eds?\.|vol\.|no\.|pp?\.|doi|isbn)
            \b
            """,
            lower_text,
            flags=re.VERBOSE,
        )
    )

    # ---------------------------------------------------------
    # 4. Strong bibliography decisions
    # ---------------------------------------------------------

    # Multiple DOI links are almost certainly bibliography.
    if doi_count >= 2:
        return True

    # Many URLs + many publication years strongly indicate
    # a reference list.
    if url_count >= 3 and year_count >= 4:
        return True

    # Dense author/year citation structure is characteristic
    # of bibliography chunks.
    if (
        author_year_count >= 5
        and year_count >= 5
        and citation_markers >= 2
    ):
        return True

    # Very high year density is another strong signal.
    #
    # Example:
    # 10+ publication years in a relatively short chunk.
    if (
        year_count >= 8
        and year_count / max(len(text_value), 1) > 0.006
    ):
        return True

    return False


def retrieve_chunks(
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Retrieve the most semantically relevant usable scientific
    knowledge chunks using Cohere query embeddings and PostgreSQL
    pgvector.

    Retrieval pipeline:

        query
          ↓
        Cohere query embedding
          ↓
        pgvector candidate retrieval
          ↓
        reference/bibliography filtering
          ↓
        top-k scientific evidence
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

    # Retrieve a larger candidate pool so reference chunks can be
    # removed without reducing the final number of useful results.
    candidate_limit = min(
        top_k * RETRIEVAL_CANDIDATE_MULTIPLIER,
        100,
    )

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
        LIMIT :candidate_limit
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {
                "embedding": embedding_string,
                "candidate_limit": candidate_limit,
            },
        ).fetchall()

    results = []

    for row in rows:
        chunk_text = row.chunk_text or ""

        # Never expose bibliography/reference-list chunks as
        # scientific evidence.
        if _is_reference_chunk(chunk_text):
            continue

        results.append(
            {
                "id": row.id,
                "document_id": row.document_id,
                "text": chunk_text,
                "similarity": float(row.similarity),
            }
        )

        if len(results) >= top_k:
            break

    return results