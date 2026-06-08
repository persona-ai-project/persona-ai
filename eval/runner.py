"""
eval/runner.py
==============
Persona AI eval runner.

Loads seed.jsonl → calls POST /chat → scores responses →
emits markdown report to eval/reports/YYYY-MM-DD.md

Usage:
    python eval/runner.py
    python eval/runner.py --url http://localhost:8001 --voice-id en_US-lessac-medium
"""
from __future__ import annotations

import json
import time
import argparse
import statistics
import requests
import numpy as np
from datetime import date
from pathlib import Path
from typing import Optional


# ── Config ────────────────────────────────────────────────────────────────────

SEED_PATH    = Path(__file__).parent / "golden" / "seed.jsonl"
REPORTS_DIR  = Path(__file__).parent / "reports"
PASS_THRESHOLD = 0.75       # cosine similarity threshold for pass
MODEL_NAME     = "BAAI/bge-small-en-v1.5"


# ── Embedding ─────────────────────────────────────────────────────────────────

_embed_model = None

def get_embedder():
    global _embed_model
    if _embed_model is None:
        from fastembed import TextEmbedding
        _embed_model = TextEmbedding(MODEL_NAME)
    return _embed_model


def embed(text: str) -> np.ndarray:
    model = get_embedder()
    vectors = list(model.embed([text]))
    return np.array(vectors[0])


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_response(
    actual: str,
    ideal: str,
    expected_traits: list[str],
) -> dict:
    """
    Score actual response against ideal.

    Returns:
        {
            "similarity": float,  # cosine similarity 0-1
            "trait_hits": int,    # how many traits found in response
            "trait_total": int,   # total expected traits
            "pass": bool,         # similarity >= PASS_THRESHOLD
        }
    """
    # Embedding similarity
    vec_actual = embed(actual)
    vec_ideal  = embed(ideal)
    similarity = cosine_similarity(vec_actual, vec_ideal)

    # Trait keyword check
    actual_lower = actual.lower()
    trait_hits = sum(
        1 for trait in expected_traits
        if any(word in actual_lower for word in trait.lower().split())
    )

    return {
        "similarity":   round(similarity, 4),
        "trait_hits":   trait_hits,
        "trait_total":  len(expected_traits),
        "pass":         similarity >= PASS_THRESHOLD,
    }


# ── Chat call ─────────────────────────────────────────────────────────────────

def call_chat(base_url: str, prompt: str, user_id: str) -> tuple[str, int]:
    """
    Call POST /chat and return (response_text, latency_ms).
    Falls back to a mock if /chat doesn't exist yet.
    """
    start = time.perf_counter()
    try:
        resp = requests.post(
            f"{base_url}/chat",
            json={"message": prompt, "user_id": user_id},
            timeout=30,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("response", data.get("text", str(data))), latency_ms
        else:
            return f"[HTTP {resp.status_code}]", latency_ms
    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return f"[ERROR: {e}]", latency_ms


# ── Report generation ─────────────────────────────────────────────────────────

def generate_report(results: list[dict], report_path: Path) -> None:
    """Generate markdown report from eval results."""
    today = date.today().isoformat()
    total = len(results)
    passed = sum(1 for r in results if r["score"]["pass"])
    avg_sim = statistics.mean(r["score"]["similarity"] for r in results)
    latencies = [r["latency_ms"] for r in results]
    p50 = statistics.median(latencies)
    p95 = sorted(latencies)[int(len(latencies) * 0.95)]

    lines = [
        f"# Persona AI Eval Report — {today}",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total tuples | {total} |",
        f"| Passed | {passed}/{total} ({100*passed//total}%) |",
        f"| Avg similarity | {avg_sim:.4f} |",
        f"| Pass threshold | {PASS_THRESHOLD} |",
        f"| p50 latency | {p50:.0f}ms |",
        f"| p95 latency | {p95:.0f}ms |",
        f"",
        f"## Results",
        f"",
        f"| # | Prompt | Similarity | Traits | Latency | Pass |",
        f"|---|---|---|---|---|---|",
    ]

    for i, r in enumerate(results, 1):
        prompt_short = r["prompt"][:40] + "..." if len(r["prompt"]) > 40 else r["prompt"]
        sim = r["score"]["similarity"]
        traits = f"{r['score']['trait_hits']}/{r['score']['trait_total']}"
        latency = r["latency_ms"]
        status = "✅" if r["score"]["pass"] else "❌"
        lines.append(f"| {i} | {prompt_short} | {sim:.4f} | {traits} | {latency}ms | {status} |")

    lines += [
        f"",
        f"## Actual vs Ideal (failures only)",
        f"",
    ]

    for i, r in enumerate(results, 1):
        if not r["score"]["pass"]:
            lines += [
                f"### #{i} — {r['prompt'][:60]}",
                f"**Ideal:** {r['ideal_response']}",
                f"",
                f"**Actual:** {r['actual_response']}",
                f"",
                f"**Similarity:** {r['score']['similarity']} (threshold: {PASS_THRESHOLD})",
                f"",
            ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✅ Report written to: {report_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Persona AI Eval Runner")
    parser.add_argument("--url", default="http://localhost:8001", help="API base URL")
    parser.add_argument("--user-id", default="c1b86221-ff7a-439b-bc6f-11a59bf50175", help="Demo user UUID")
    parser.add_argument("--dry-run", action="store_true", help="Score without calling /chat (uses ideal as actual)")
    args = parser.parse_args()

    # Load seed
    if not SEED_PATH.exists():
        print(f"Error: {SEED_PATH} not found. Run the eval session first.")
        return

    tuples = []
    with open(SEED_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tuples.append(json.loads(line))

    print(f"Loaded {len(tuples)} tuples from {SEED_PATH}")
    print(f"API: {args.url}")
    print(f"Dry run: {args.dry_run}")
    print(f"\nRunning eval...\n")

    results = []
    for i, t in enumerate(tuples, 1):
        prompt = t["prompt"]
        ideal  = t["ideal_response"]
        traits = t.get("expected_persona_traits", [])

        print(f"[{i}/{len(tuples)}] {prompt[:50]}...")

        if args.dry_run:
            actual     = ideal  # use ideal as actual for dry run
            latency_ms = 0
        else:
            actual, latency_ms = call_chat(args.url, prompt, args.user_id)

        score = score_response(actual, ideal, traits)
        status = "✅ PASS" if score["pass"] else "❌ FAIL"
        print(f"         sim={score['similarity']:.4f} traits={score['trait_hits']}/{score['trait_total']} latency={latency_ms}ms {status}")

        results.append({
            "prompt":          prompt,
            "ideal_response":  ideal,
            "actual_response": actual,
            "score":           score,
            "latency_ms":      latency_ms,
        })

    # Generate report
    report_path = REPORTS_DIR / f"{date.today().isoformat()}.md"
    generate_report(results, report_path)

    # Print summary
    passed = sum(1 for r in results if r["score"]["pass"])
    print(f"\nPassed: {passed}/{len(results)}")


if __name__ == "__main__":
    main()