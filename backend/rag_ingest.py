import argparse
import re
from pathlib import Path

from pypdf import PdfReader

from embedding_service import generate_embeddings
from database import SessionLocal
from models import Document, DocumentChunk


BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_DIR = BASE_DIR / "data" / "sources"


SOURCES = [
    {
        "filename": "beillouin_2021.pdf",
        "document_id": "beillouin_2021",
        "source": "Global Change Biology",
        "title": "Positive but variable effects of crop diversification on biodiversity and ecosystem services",
        "topic": "biodiversity",
        "source_url": "https://doi.org/10.1111/gcb.15747",
    },
    {
        "filename": "fao_biodiversity.pdf",
        "document_id": "fao_biodiversity_2019",
        "source": "FAO",
        "title": "The State of the World's Biodiversity for Food and Agriculture",
        "topic": "biodiversity",
        "source_url": "https://www.fao.org/cgrfa/assessment/sow-bfa/en",
    },
    {
        "filename": "gsocseq_technical_report.pdf",
        "document_id": "gsocseq_v1_1",
        "source": "FAO",
        "title": "GSOCseq v1.1",
        "topic": "soil_carbon",
        "source_url": "https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/global-soil-organic-carbon-sequestration-potential-gsocseq-map/en",
    },
    {
        "filename": "ipcc_chapter_5.pdf",
        "document_id": "ipcc_ar6_wgii_chapter_5",
        "source": "IPCC",
        "title": "Food, Fibre and Other Ecosystem Products",
        "topic": "climate_agriculture",
        "source_url": "https://www.ipcc.ch/report/ar6/wg2/",
    },
    {
        "filename": "ipcc_spm.pdf",
        "document_id": "ipcc_ar6_wgii_spm",
        "source": "IPCC",
        "title": "IPCC AR6 WGII Summary for Policymakers",
        "topic": "climate_environment",
        "source_url": "https://www.ipcc.ch/report/ar6/wg2/",
    },
    {
        "filename": "sanchez_2022.pdf",
        "document_id": "sanchez_2022",
        "source": "Agriculture, Ecosystems & Environment",
        "title": "Landscape complexity and functional groups moderate the effect of diversified farming on biodiversity: A global meta-analysis",
        "topic": "biodiversity",
        "source_url": "https://doi.org/10.1016/j.agee.2022.107933",
    },
]


# ---------------------------------------------------------
# TEXT CLEANUP
# ---------------------------------------------------------

def clean_page_text(text: str) -> str:
    if not text:
        return ""

    # PostgreSQL strings cannot contain NUL characters.
    text = text.replace("\x00", "")

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = [line.strip() for line in text.split("\n")]

    cleaned = []
    previous_blank = False

    for line in lines:
        if not line:
            if not previous_blank:
                cleaned.append("")
            previous_blank = True
        else:
            cleaned.append(line)
            previous_blank = False

    text = "\n".join(cleaned)

    # Rejoin words broken across PDF lines.
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    # Turn single line breaks into spaces.
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Normalize spaces.
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def is_blank_page(text: str) -> bool:
    return not text.strip()


def looks_like_references_page(text: str) -> bool:
    normalized = text.strip().lower()

    if not normalized:
        return False

    first_line = normalized.splitlines()[0].strip()

    reference_headings = {
        "references",
        "bibliography",
        "literature cited",
        "references cited",
        "literature references",
    }

    return first_line in reference_headings


# ---------------------------------------------------------
# PDF EXTRACTION
# ---------------------------------------------------------

def extract_pdf_pages(pdf_path: Path):
    reader = PdfReader(str(pdf_path))

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        text = clean_page_text(raw_text)

        if is_blank_page(text):
            continue

        pages.append(
            {
                "page": page_number,
                "text": text,
            }
        )

    return pages


# ---------------------------------------------------------
# CONTINUOUS DOCUMENT + PROVENANCE
# ---------------------------------------------------------

def build_continuous_text(pages):
    """
    Build one continuous document while recording the exact
    character interval belonging to each source page.
    """

    parts = []
    page_ranges = []

    current_position = 0

    for page in pages:
        prefix = "\n\n"

        parts.append(prefix)
        current_position += len(prefix)

        start = current_position

        parts.append(page["text"])
        current_position += len(page["text"])

        end = current_position

        page_ranges.append(
            {
                "page": page["page"],
                "start": start,
                "end": end,
            }
        )

    text = "".join(parts)

    return text, page_ranges


def get_page_range(start: int, end: int, page_ranges):
    """
    Return all source pages touched by a chunk character interval.
    """

    touched_pages = []

    for page in page_ranges:
        if end > page["start"] and start < page["end"]:
            touched_pages.append(page["page"])

    if not touched_pages:
        return None, None

    return min(touched_pages), max(touched_pages)


# ---------------------------------------------------------
# RECURSIVE TEXT SPLITTER
# ---------------------------------------------------------

SEPARATORS = [
    "\n\n",
    "\n",
    ". ",
    "? ",
    "! ",
    "; ",
    ", ",
    " ",
]


def recursive_split(text: str, chunk_size: int = 2000):
    """
    Recursive splitter without LangChain.

    It tries:

        paragraphs
        lines
        sentences
        clauses
        words
        characters
    """

    text = text.strip()

    if len(text) <= chunk_size:
        return [text]

    for separator in SEPARATORS:
        if separator not in text:
            continue

        pieces = text.split(separator)

        chunks = []
        current = ""

        for piece in pieces:
            piece = piece.strip()

            if not piece:
                continue

            candidate = (
                piece
                if not current
                else current + separator + piece
            )

            if len(candidate) <= chunk_size:
                current = candidate

            else:
                if current:
                    chunks.extend(
                        recursive_split(
                            current,
                            chunk_size,
                        )
                    )

                if len(piece) > chunk_size:
                    chunks.extend(
                        recursive_split(
                            piece,
                            chunk_size,
                        )
                    )
                    current = ""
                else:
                    current = piece

        if current:
            chunks.extend(
                recursive_split(
                    current,
                    chunk_size,
                )
            )

        return chunks

    # Final fallback.
    return [
        text[i:i + chunk_size]
        for i in range(0, len(text), chunk_size)
    ]


def recursive_split_with_offsets(
    text: str,
    chunk_size: int = 2000,
    overlap: int = 300,
):
    """
    Split the continuous text while retaining character offsets.

    The overlap is applied to the original continuous text,
    preventing compounded overlap.
    """

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:
        remaining = text[start:]

        if len(remaining) <= chunk_size:
            chunks.append(
                {
                    "text": remaining.strip(),
                    "start": start,
                    "end": text_length,
                }
            )
            break

        window = remaining[:chunk_size]

        # Find the best semantic boundary inside the window.
        boundary = None

        for separator in SEPARATORS:
            position = window.rfind(separator)

            if position >= int(chunk_size * 0.55):
                boundary = position + len(separator)
                break

        if boundary is None:
            boundary = chunk_size

        end = start + boundary

        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append(
                {
                    "text": chunk_text,
                    "start": start,
                    "end": end,
                }
            )

        # Move backward by overlap, but never backwards beyond
        # the current chunk start.
        next_start = max(
            end - overlap,
            start + 1,
        )

        # Prefer beginning at whitespace.
        if next_start < end:
            whitespace = text.find(" ", next_start, min(next_start + 80, end))

            if whitespace != -1:
                next_start = whitespace + 1

        start = next_start

    return chunks


# ---------------------------------------------------------
# DOCUMENT PROCESSING
# ---------------------------------------------------------

def process_document(config):
    pdf_path = SOURCES_DIR / config["filename"]

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Source PDF not found: {pdf_path}"
        )

    print("\n" + "=" * 70)
    print(f"DOCUMENT: {config['filename']}")
    print("=" * 70)

    pages = extract_pdf_pages(pdf_path)

    print(f"Extracted pages: {len(pages)}")

    # Conservative reference filtering.
    filtered_pages = []
    references_started = False

    for page in pages:

        if (
            not references_started
            and looks_like_references_page(page["text"])
        ):
            references_started = True

            print(
                f"Skipping references from page "
                f"{page['page']} onward"
            )

        if not references_started:
            filtered_pages.append(page)

    print(
        f"Pages after cleanup: "
        f"{len(filtered_pages)}"
    )

    continuous_text, page_ranges = build_continuous_text(
        filtered_pages
    )

    print(
        f"Continuous text characters: "
        f"{len(continuous_text):,}"
    )

    chunk_records = recursive_split_with_offsets(
        continuous_text,
        chunk_size=2000,
        overlap=300,
    )

    final_chunks = []

    for chunk_number, record in enumerate(
        chunk_records,
        start=1,
    ):
        page_start, page_end = get_page_range(
            record["start"],
            record["end"],
            page_ranges,
        )

        final_chunks.append(
            {
                "chunk_number": chunk_number,
                "chunk_text": record["text"],
                "page_start": page_start,
                "page_end": page_end,
            }
        )

    print(
        f"Final chunks: "
        f"{len(final_chunks)}"
    )

    if final_chunks:

        lengths = [
            len(chunk["chunk_text"])
            for chunk in final_chunks
        ]

        print(
            f"Chunk length: "
            f"min={min(lengths)}, "
            f"max={max(lengths)}, "
            f"avg={sum(lengths) // len(lengths)}"
        )

        print("\nFirst chunk preview:")
        print("-" * 70)
        print(
            final_chunks[0]["chunk_text"][:700]
        )
        print("-" * 70)

        print(
            "First chunk provenance: "
            f"pages "
            f"{final_chunks[0]['page_start']}"
            f"-"
            f"{final_chunks[0]['page_end']}"
        )

    return {
        "config": config,
        "pages_extracted": len(pages),
        "pages_after_cleanup": len(filtered_pages),
        "chunks": final_chunks,
    }


# ---------------------------------------------------------
# DATABASE INGESTION
# ---------------------------------------------------------

EMBEDDING_BATCH_SIZE = 96


def ingest_document(result):
    config = result["config"]
    chunks = result["chunks"]

    print("\n" + "-" * 70)
    print(f"INGESTING: {config['filename']}")
    print(f"Chunks: {len(chunks)}")
    print(f"Embedding batch size: {EMBEDDING_BATCH_SIZE}")
    print("-" * 70)

    if not chunks:
        print("No chunks to ingest.")
        return 0

    db = SessionLocal()

    try:
        existing = (
            db.query(Document)
            .filter(Document.document_id == config["document_id"])
            .first()
        )

        # If this document is already complete, preserve it and avoid
        # spending Gemini quota on re-embedding it.
        if existing:
            existing_chunk_count = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.document_id == existing.id)
                .count()
            )

            if existing_chunk_count == len(chunks):
                print(
                    f"Already ingested: {config['document_id']} "
                    f"({existing_chunk_count} chunks). Skipping."
                )
                return existing_chunk_count

            print(
                f"Existing incomplete document found: "
                f"{config['document_id']} "
                f"({existing_chunk_count}/{len(chunks)} chunks)."
            )
            print("It will be replaced only after all embeddings succeed.")

        # IMPORTANT:
        # Generate every embedding before changing the database.
        # If Gemini fails, the existing DB document remains untouched.
        all_embeddings = []
        total_chunks = len(chunks)
        total_batches = (
            total_chunks + EMBEDDING_BATCH_SIZE - 1
        ) // EMBEDDING_BATCH_SIZE

        for batch_start in range(0, total_chunks, EMBEDDING_BATCH_SIZE):
            batch_end = min(
                batch_start + EMBEDDING_BATCH_SIZE,
                total_chunks,
            )

            batch_chunks = chunks[batch_start:batch_end]
            batch_number = (
                batch_start // EMBEDDING_BATCH_SIZE
            ) + 1

            print(
                f"Embedding batch {batch_number}/{total_batches}: "
                f"chunks {batch_start + 1}-{batch_end}"
            )

            texts = [
                chunk["chunk_text"]
                for chunk in batch_chunks
            ]

            embeddings = generate_embeddings(texts)

            if len(embeddings) != len(batch_chunks):
                raise RuntimeError(
                    f"Embedding count mismatch for "
                    f"{config['document_id']} batch {batch_number}: "
                    f"{len(batch_chunks)} chunks vs "
                    f"{len(embeddings)} embeddings"
                )

            for index, embedding in enumerate(
                embeddings,
                start=batch_start + 1,
            ):
                if len(embedding) != 1024:
                    raise RuntimeError(
                        f"Invalid embedding dimension at chunk "
                        f"{index}: {len(embedding)}"
                    )

            all_embeddings.extend(embeddings)

        if len(all_embeddings) != total_chunks:
            raise RuntimeError(
                f"Final embedding count mismatch for "
                f"{config['document_id']}: "
                f"expected {total_chunks}, got {len(all_embeddings)}"
            )

        # Only now is it safe to mutate the database.
        if existing:
            db.delete(existing)
            db.flush()

        document = Document(
            document_id=config["document_id"],
            source=config["source"],
            title=config["title"],
            topic=config["topic"],
            source_url=config["source_url"],
        )

        db.add(document)
        db.flush()

        for chunk, embedding in zip(
            chunks,
            all_embeddings,
        ):
            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_number=chunk["chunk_number"],
                page=chunk["page_start"],
                chunk_text=chunk["chunk_text"],
                embedding=embedding,
                meta_data={
                    "page_start": chunk["page_start"],
                    "page_end": chunk["page_end"],
                    "source": config["source"],
                    "title": config["title"],
                    "topic": config["topic"],
                    "source_url": config["source_url"],
                },
            )
            db.add(db_chunk)

        db.flush()

        stored_chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document.id)
            .count()
        )

        if stored_chunks != total_chunks:
            raise RuntimeError(
                f"Stored chunk count mismatch for "
                f"{config['document_id']}: "
                f"expected {total_chunks}, stored {stored_chunks}"
            )

        db.commit()

        print(f"Successfully ingested {stored_chunks} chunks.")
        return stored_chunks

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Extract and chunk PDFs without "
            "embeddings or DB writes."
        ),
    )

    parser.add_argument(
        "--ingest",
        action="store_true",
        help=(
            "Extract, chunk, embed, and ingest "
            "all configured PDFs into PostgreSQL."
        ),
    )

    args = parser.parse_args()

    if args.dry_run and args.ingest:
        raise RuntimeError(
            "Use either --dry-run or --ingest, not both."
        )

    if not args.dry_run and not args.ingest:
        raise RuntimeError(
            "Specify either --dry-run or --ingest."
        )

    total_pages = 0
    total_chunks = 0
    total_ingested = 0

    for config in SOURCES:
        result = process_document(config)
        total_pages += result["pages_after_cleanup"]
        total_chunks += len(result["chunks"])

        if args.ingest:
            total_ingested += ingest_document(result)

    print("\n")
    print("=" * 70)

    if args.dry_run:
        print("DRY RUN COMPLETE")
    else:
        print("RAG INGESTION COMPLETE")

    print("=" * 70)
    print(f"Total cleaned pages : {total_pages}")
    print(f"Total chunks        : {total_chunks}")

    if args.ingest:
        print(f"Total ingested      : {total_ingested}")
        print("Cohere embeddings   : generated")
        print("Database writes     : completed")
    else:
        print("Gemini API calls    : 0")
        print("Database writes     : 0")

    print("=" * 70)

if __name__ == "__main__":
    main()