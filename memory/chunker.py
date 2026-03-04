# memory/chunker.py

def chunk_text(text, chunk_size=500, overlap=50):
    """
    Splits text into overlapping chunks.
    """

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks