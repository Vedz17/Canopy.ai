import os

from dotenv import load_dotenv
from cohere import ClientV2
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception


load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
EMBEDDING_MODEL = os.getenv(
    "COHERE_EMBEDDING_MODEL",
    "embed-v4.0",
)
EMBEDDING_DIMENSIONS = int(
    os.getenv("COHERE_EMBEDDING_DIMENSIONS", "1024")
)

if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY is not set")

if EMBEDDING_DIMENSIONS not in (256, 512, 1024, 1536):
    raise ValueError(
        "COHERE_EMBEDDING_DIMENSIONS must be 256, 512, 1024, or 1536"
    )

client = ClientV2(api_key=COHERE_API_KEY)


def is_retryable_error(exception: Exception) -> bool:
    """
    Retry transient API/network failures.
    Do not retry configuration/authentication errors indefinitely.
    """
    status_code = getattr(exception, "status_code", None)
    if status_code is None:
        status_code = getattr(exception, "code", None)

    return status_code in (429, 500, 502, 503, 504)


@retry(
    retry=retry_if_exception(is_retryable_error),
    stop=stop_after_attempt(5),
    wait=wait_exponential(
        multiplier=2,
        min=5,
        max=45,
    ),
    reraise=True,
)
def _embed_batch(
    texts: list[str],
    input_type: str,
) -> list[list[float]]:
    response = client.embed(
        model=EMBEDDING_MODEL,
        texts=texts,
        input_type=input_type,
        output_dimension=EMBEDDING_DIMENSIONS,
        embedding_types=["float"],
    )

    embeddings = response.embeddings.float

    if len(embeddings) != len(texts):
        raise RuntimeError(
            f"Embedding count mismatch: "
            f"{len(texts)} inputs vs {len(embeddings)} embeddings"
        )

    if any(
        len(embedding) != EMBEDDING_DIMENSIONS
        for embedding in embeddings
    ):
        raise RuntimeError(
            "Invalid Cohere embedding dimension returned."
        )

    return embeddings


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate document embeddings for RAG ingestion.
    """
    if not texts:
        return []

    if len(texts) > 96:
        raise ValueError(
            "Cohere allows a maximum of 96 texts per embed request."
        )

    return _embed_batch(texts, "search_document")


def generate_query_embedding(text: str) -> list[float]:
    """
    Generate a query embedding for semantic retrieval.
    """
    return _embed_batch([text], "search_query")[0]


def generate_embedding(text: str) -> list[float]:
    """
    Backward-compatible alias for query embedding.
    """
    return generate_query_embedding(text)
