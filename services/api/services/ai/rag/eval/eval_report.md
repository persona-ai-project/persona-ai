# RAG Eval Report — PersonaAI
**Date:** May 2026  
**Evaluator:** Person 1 (AI/ML Engineer)

## Recall@5 Results

| Metric | Value |
|---|---|
| Total queries | 20 |
| Hits | 20 |
| Misses | 0 |
| **Recall@5** | **1.00** ✅ |

## Target
- Required: recall@5 ≥ 0.8
- Achieved: recall@5 = 1.00 ✅

## Query Results

| Query | Result |
|---|---|
| what food does the user like? | ✅ |
| where does the user live? | ✅ |
| what is the user's profession? | ✅ |
| what sport does the user follow? | ✅ |
| what is the user currently learning? | ✅ |
| what university did the user attend? | ✅ |
| what does the user eat every day? | ✅ |
| what city is the user from? | ✅ |
| what matches does the user follow? | ✅ |
| what field does the user work in? | ✅ |
| what is the user excited about learning? | ✅ |
| what does the user like to eat daily? | ✅ |
| where has the user lived their whole life? | ✅ |
| what game does the user love? | ✅ |
| what is the user's job? | ✅ |
| what technology is the user studying? | ✅ |
| what does the user find exciting to study? | ✅ |
| what is the user's favorite meal? | ✅ |
| which college did the user graduate from? | ✅ |
| what sport does the user watch closely? | ✅ |

## Notes
- Hybrid search (dense + sparse + RRF) used
- Recency boost applied (1.5x for chunks < 14 days old)
- Collection: persona_chunks on Qdrant Cloud