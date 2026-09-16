# Workshop Introduction — Slide Outline (10 slides)

1. **Title** — RAG Battle Royale: Build the best Acme Cloud knowledge assistant
2. **Mission** — you are the new AI team at Acme Corp
3. **The API contract** — `POST /ask` → `{ answer, sources }`
4. **The corpus** — ~40 docs across engineering/security/product/people/operations
5. **The baseline** — intentionally mediocre (~65–70%), your job is to beat it
6. **What you can change** — chunking, retrieval, reranking, prompts, citations...
7. **What you can't do** — modify the corpus, hard-code answers, see hidden questions
8. **Budget constraints** — 3 LLM calls / 10 retrievals / 4,000 input tokens per question
9. **Scoring** — correctness 50%, retrieval 20%, groundedness 15%, citations 10%, latency 5%
10. **Timeline** — 60 min build, 20 min polish, code freeze, hidden evaluation, leaderboard
