# Ingestion System — Parser Guide

## Supported Sources

| Source | Route | File Type | Parser |
|---|---|---|---|
| File upload | POST /ingest/file | .pdf, .docx, .md, .txt | Auto-detected by extension |
| WhatsApp | POST /ingest/social/whatsapp | .txt | whatsapp parser |
| URL | POST /ingest/url | — | trafilatura |

---

## Parser Quirks & Limitations

### PDF
- **What works:** Text-based PDFs (reports, articles, e-books)
- **What doesn't:** Scanned PDFs (image-only) — pypdf returns empty text per page
- **Minimum content:** Pages with fewer than 50 characters are skipped
- **Large PDFs:** Each page becomes one chunk. A 100-page PDF = ~100 chunks
- **Encrypted PDFs:** Will fail with a parse error — ask user to decrypt first
- **Fix for scanned PDFs:** Would need OCR (Tesseract/AWS Textract) — not in scope for Sprint 2

### DOCX
- **What works:** Standard Word documents with paragraphs
- **What doesn't:** Tables, headers/footers, text boxes, images
- **Empty paragraphs:** Skipped automatically
- **Track changes:** Accepted/rejected changes are not handled — ask user to accept all first
- **Templates:** .dotx files not supported, only .docx

### Markdown
- **What works:** All standard markdown, emoji, code blocks, headers
- **Code blocks:** Treated as plain text — may split mid-block if > 512 words
- **Frontmatter:** YAML frontmatter (---) is included as text — not stripped

### Text (.txt)
- **What works:** Any UTF-8 text file
- **Encoding:** Files with non-UTF-8 encoding are read with `errors=replace` — garbled chars possible
- **Line endings:** Both CRLF (Windows) and LF (Unix) handled correctly

### WhatsApp
**Date format variations supported:**

- **System messages filtered:** "Messages are end-to-end encrypted", "X added you", "X left" etc.
- **Media omitted:** `<Media omitted>` messages are filtered out
- **owner_name must match exactly:** Case-sensitive, spaces matter
  - Export shows "John Smith" → pass `owner_name=John Smith`
  - If 0 chunks returned, check the exact name in the first few lines of the .txt file
- **Multi-line messages:** Continuation lines (no timestamp) are joined to the previous message
- **Group chats:** Only messages from `owner_name` are extracted
- **Emoji:** Fully supported, preserved in chunks
- **Short messages:** "ok", "👍", single-word replies are included as-is

### URL
- **What works:** News articles, blog posts, Wikipedia, documentation sites
- **What doesn't:**
  - JavaScript-heavy SPAs (React/Vue apps that render client-side)
  - Login-gated pages (Twitter/X, LinkedIn posts, paywalled articles)
  - PDFs served via URL — use the file upload route instead
- **Twitter/X:** trafilatura extracts some metadata but not tweet content
- **YouTube:** Returns transcript if available, otherwise empty
- **Paywalled sites:** May return partial content (the teaser text only)
- **Timeout:** 30 seconds — very slow sites will fail

---

## Progress States

| Status | progress_pct | Meaning |
|---|---|---|
| queued | 0 | Job created, waiting to start |
| parsing | 25 | Reading and extracting text from source |
| chunking | 50 | Splitting text into overlapping chunks |
| embedding | 75 | Generating vectors and storing in Qdrant |
| indexed | 100 | Complete — chunks searchable in RAG |
| failed | -1 | Error occurred — check `error` field |

---

## Polling the Job Status (for P3)

**Endpoint:** `GET /ingest/{job_id}`

**Response shape:**
```json
{
  "job_id": "uuid-string",
  "user_id": "uuid-string",
  "status": "indexed",
  "source": "ingestion/user-id/uuid/filename.pdf",
  "error": null,
  "created_at": "2026-05-23T10:00:00+00:00",
  "progress_pct": 100
}
```

**P3 polling pattern (suggested):**
```javascript
async function pollJobStatus(jobId, onProgress) {
  const interval = setInterval(async () => {
    const res = await fetch(`/api/ingest/${jobId}`);
    const data = await res.json();
    
    onProgress(data.progress_pct, data.status);
    
    // Stop polling when done or failed
    if (data.status === 'indexed' || data.status === 'failed') {
      clearInterval(interval);
    }
  }, 2000); // Poll every 2 seconds
}
```

**Progress bar mapping:**
```javascript
const progressColor = {
  queued:    'gray',
  parsing:   'blue',
  chunking:  'blue',
  embedding: 'blue',
  indexed:   'green',
  failed:    'red',
};
```

---

## Common Errors and Fixes

| Error | Cause | Fix |
|---|---|---|
| `Parser returned empty text` | WhatsApp owner_name mismatch OR scanned PDF | Check name exactly / use text PDF |
| `No module named trafilatura` | Not installed in Docker | Add to requirements.txt, rebuild |
| `Invalid endpoint` | R2 credentials missing | Add R2_ENDPOINT to .env and docker-compose.yml |
| `badly formed hexadecimal UUID string` | user_id format wrong | Must be UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx |
| `Chunker returned 0 chunks` | Empty file or all content filtered | Check file has real text content |