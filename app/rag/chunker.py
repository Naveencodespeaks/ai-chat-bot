"""Text chunking strategies for RAG document ingestion."""

from typing import List, Optional


def chunk_by_size(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
) -> List[str]:
    """Split text into fixed-size chunks with optional overlap.

    Args:
        text: Full document text to chunk
        chunk_size: Target chunk size in characters (not tokens)
        overlap: Number of overlapping characters between chunks

    Returns:
        List of text chunks
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")

    chunks = []
    start = 0

    while start < len(text):
        # Calculate end, ensuring we don't exceed text length
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])

        # Move start position forward by (chunk_size - overlap)
        start += chunk_size - overlap

        # If we've reached the end, break to avoid empty chunks
        if end == len(text):
            break

    return [chunk for chunk in chunks if chunk.strip()]


def chunk_by_sentences(
    text: str,
    sentences_per_chunk: int = 3,
    overlap_sentences: int = 1,
) -> List[str]:
    """Split text into sentence-based chunks.

    Simple sentence detection using common delimiters. For production,
    consider spaCy or NLTK.

    Args:
        text: Full document text to chunk
        sentences_per_chunk: Number of sentences per chunk
        overlap_sentences: Number of overlapping sentences between chunks

    Returns:
        List of text chunks
    """
    # Simple regex-based sentence splitting
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]

    if not sentences:
        return []

    chunks = []
    step = max(1, sentences_per_chunk - overlap_sentences)

    for i in range(0, len(sentences), step):
        chunk_sentences = sentences[i : i + sentences_per_chunk]
        chunk_text = ". ".join(chunk_sentences)
        if chunk_text.strip():
            chunks.append(chunk_text + ".")

    return chunks


def chunk_by_delimiter(
    text: str,
    delimiter: str = "\n\n",
    max_chunk_size: Optional[int] = None,
) -> List[str]:
    """Split text by delimiter, optionally enforcing max chunk size.

    Useful for structured documents (e.g., markdown with double-newlines
    as section breaks).

    Args:
        text: Full document text to chunk
        delimiter: String to split on (e.g., "\n\n" for paragraphs)
        max_chunk_size: If set, further split chunks exceeding this size

    Returns:
        List of text chunks
    """
    chunks = [c.strip() for c in text.split(delimiter) if c.strip()]

    if max_chunk_size:
        refined = []
        for chunk in chunks:
            if len(chunk) > max_chunk_size:
                # Fall back to fixed-size chunking for oversized sections
                refined.extend(
                    chunk_by_size(chunk, chunk_size=max_chunk_size, overlap=50)
                )
            else:
                refined.append(chunk)
        return refined

    return chunks


__all__ = [
    "chunk_by_size",
    "chunk_by_sentences",
    "chunk_by_delimiter",
]
 
