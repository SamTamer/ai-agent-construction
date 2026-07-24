"""
Ingestion script — reads PDFs from data/procedures/, chunks them, and loads
into a ChromaDB collection.

Usage:
    python agent/ingest.py                        # creates construction_procedures_v2
    python agent/ingest.py --collection my_name   # custom collection name
    python agent/ingest.py --chunk-size 500 --chunk-overlap 100

Default settings (recommended for RAG):
    chunk_size    = 500 chars
    chunk_overlap = 100 chars
    min_length    = 100 chars  (filters garbage fragments)
"""

import argparse
import os
import uuid
from pathlib import Path

import chromadb
from pypdf import PdfReader


# ---------------------------------------------------------------------------
# Text splitter (no LangChain dependency)
# ---------------------------------------------------------------------------

def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Recursively split text on paragraph -> line -> word boundaries,
    targeting chunk_size characters with chunk_overlap carry-over.
    """
    separators = ["\n\n", "\n", " ", ""]

    def _split(text: str, separators: list[str]) -> list[str]:
        sep = separators[0]
        next_seps = separators[1:]

        if sep == "":
            splits = list(text)
        else:
            splits = text.split(sep)

        chunks = []
        current = ""

        for part in splits:
            candidate = (current + sep + part).strip() if current else part.strip()
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(part.strip()) > chunk_size and next_seps:
                    chunks.extend(_split(part.strip(), next_seps))
                    current = ""
                else:
                    current = part.strip()

        if current:
            chunks.append(current)

        return chunks

    raw_chunks = _split(text, separators)

    # Apply overlap: carry the tail of the previous chunk into the next
    if chunk_overlap == 0 or len(raw_chunks) <= 1:
        return raw_chunks

    overlapped = [raw_chunks[0]]
    for i in range(1, len(raw_chunks)):
        prev_tail = overlapped[-1][-chunk_overlap:]
        overlapped.append((prev_tail + " " + raw_chunks[i]).strip())

    return overlapped


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------

def extract_pages(pdf_path: str) -> list[dict]:
    """Return list of {page, text} dicts from a PDF."""
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append({"page": i, "text": text})
    return pages


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------

def ingest(
    pdf_dir: str = "data/procedures",
    chroma_path: str = "./chroma_db",
    collection_name: str = "construction_procedures_v2",
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    min_length: int = 100,
    append: bool = False,
):
    pdf_dir = Path(pdf_dir)
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDFs found in {pdf_dir}")
        return

    print(f"Found {len(pdf_files)} PDF(s): {[f.name for f in pdf_files]}")
    print(f"Settings: chunk_size={chunk_size}, overlap={chunk_overlap}, min_length={min_length}")
    print(f"Target collection: {collection_name}")
    print(f"Mode: {'append' if append else 'overwrite'}\n")

    client = chromadb.PersistentClient(path=chroma_path)
    existing = [c.name for c in client.list_collections()]

    if append:
        if collection_name not in existing:
            print(f"Collection '{collection_name}' not found — creating it.")
            collection = client.create_collection(collection_name)
        else:
            collection = client.get_collection(collection_name)
            print(f"Appending to existing collection '{collection_name}' ({collection.count()} chunks already)")
    else:
        if collection_name in existing:
            client.delete_collection(collection_name)
            print(f"Deleted existing collection '{collection_name}'")
        collection = client.create_collection(collection_name)

    total_chunks = 0
    skipped = 0

    for pdf_path in pdf_files:
        doc_id = pdf_path.stem
        print(f"Processing: {pdf_path.name}")

        pages = extract_pages(str(pdf_path))
        print(f"  Extracted {len(pages)} pages")

        doc_chunks = 0
        for page_data in pages:
            page_num = page_data["page"]
            page_text = page_data["text"]

            splits = split_text(page_text, chunk_size, chunk_overlap)

            for chunk_text in splits:
                if len(chunk_text) < min_length:
                    skipped += 1
                    continue

                chunk_id = str(uuid.uuid4())
                collection.add(
                    ids=[chunk_id],
                    documents=[chunk_text],
                    metadatas=[{
                        "doc_id": doc_id,
                        "source_file": pdf_path.name,
                        "page": page_num,
                    }],
                )
                doc_chunks += 1
                total_chunks += 1

        print(f"  Added {doc_chunks} chunks")

    print(f"\n{'='*50}")
    print(f"Ingestion complete!")
    print(f"  Total chunks added : {total_chunks}")
    print(f"  Fragments skipped  : {skipped} (below {min_length} chars)")
    print(f"  Collection         : '{collection_name}'")
    print(f"  ChromaDB path      : {chroma_path}")
    print(f"\nTo evaluate this collection run:")
    print(f"  python evaluate_quick.py --collection {collection_name}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PDFs into ChromaDB")
    parser.add_argument("--pdf-dir", default="data/procedures", help="Folder with PDFs")
    parser.add_argument("--chroma-path", default="./chroma_db", help="ChromaDB path")
    parser.add_argument("--collection", default="construction_procedures_v2", help="Collection name")
    parser.add_argument("--chunk-size", type=int, default=500, help="Target chunk size in chars")
    parser.add_argument("--chunk-overlap", type=int, default=100, help="Overlap between chunks in chars")
    parser.add_argument("--min-length", type=int, default=100, help="Min chunk length (filters garbage)")
    parser.add_argument("--append", action="store_true", help="Append to existing collection instead of overwriting")
    args = parser.parse_args()

    ingest(
        pdf_dir=args.pdf_dir,
        chroma_path=args.chroma_path,
        collection_name=args.collection,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        min_length=args.min_length,
        append=args.append,
    )
