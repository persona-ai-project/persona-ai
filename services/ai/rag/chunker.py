import nltk

nltk.download('punkt_tab')

from nltk.tokenize import sent_tokenize


def chunk_text(text, max_tokens=512, overlap=0.2):
    """
    Splits long text into overlapping chunks for vector storage.

    Args:
        text: Raw input text to chunk
        max_tokens: Maximum words per chunk (default 512)
        overlap: Fraction of chunk to repeat in next chunk (default 20%)

    Returns:
        List of text chunks
    """
    # Split full text into individual sentences
    sentences = sent_tokenize(text)

    chunks = []
    current_chunk = []
    current_length = 0
    overlap_size = int(max_tokens * overlap)  # e.g. 512 * 0.2 = ~102 words

    for sentence in sentences:
        words = sentence.split()
        sentence_length = len(words)

        # If adding this sentence exceeds max tokens, save current chunk
        if current_length + sentence_length > max_tokens:
            chunks.append(" ".join(current_chunk))

            # Keep last N words as overlap for next chunk
            overlap_words = " ".join(current_chunk).split()[-overlap_size:]
            current_chunk = overlap_words
            current_length = len(overlap_words)

        current_chunk.extend(words)
        current_length += sentence_length

    # Save the final remaining chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# Quick test
# if __name__ == "__main__":
#     sample_text = """
#     I live in Lahore and have been here my whole life. I love cricket and follow every match.
#     I am a software engineer and graduated from GCU Lahore.
#     I have two brothers and we are very close.
#     My favorite food is biryani, I could eat it every day.
#     I wake up early every morning and exercise for 30 minutes.
#     Mathematics was my favorite subject back in school.
#     I love traveling and have visited Dubai, Turkey and Thailand.
#     My favorite book is The Alchemist, I try to read every day.
#     My dream is to start my own company someday.
#     I am currently learning machine learning and finding it exciting.
#     I prefer remote work over going to the office.
#     My favorite season is winter, especially in Lahore.
#     I am a huge tea lover and drink it three times a day.
#     I enjoy cooking desi food, especially on weekends.
#     My friends are very important to me, we meet every weekend.
#     """ * 5
#
#     result = chunk_text(sample_text)
#
#     print(f"Total chunks: {len(result)}")
#     for i, chunk in enumerate(result):
#         print(f"\nChunk {i + 1} ({len(chunk.split())} words):")
#         print(chunk[:100], "...")
