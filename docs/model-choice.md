# Draft model choice (open, decided by a blind bake-off)

**Question:** which model writes the most natural 60–110-word B2B emails in German and English, at what price?

## What the public benchmarks say (15 Oct 2026)
| Model | EQ-Bench Creative Writing v3 (LLM-judged, snapshot 24 Sep) | LMArena Creative Writing (human votes, 15 Oct) | Price per 1M tokens (in / out) | Est. cost per contact* |
|---|---|---|---|---|
| GPT-5.1 (current) | not listed (GPT-5: 1640, GPT-5.2: 1783) | not in the top 20 | $1.25 / $10 | ~$0.021 |
| Gemini 3.8 Flash | not listed | #7 (1487) | $0.75 / $3.75 | ~$0.010 |
| Claude Sonnet 5.5 | not listed (Sonnet 4.6: 1968, #5) | not listed (Sonnet 4.6: #22) | $2 / $10 | ~$0.026 |
| Kimi K2.6 | #8 (1782) | not in the top 20 (Kimi K3: #30) | $0.96 / $3.97 | ~$0.011 |
| Claude Haiku 5.5 | not listed | not listed | $0.10 / $0.50 | ~$0.001 |
| GPT-5.5 Instant | GPT-5.5: #2 (2035) | #19 in July | $5 / $30 | ~$0.071 |
| Mistral Medium 3.5 / Large | Mistral Large: 1402 | far below the top 25 | low | – |

\*About 7k input + 1.2k output tokens per attempt.

The top of both boards is held by expensive flagship models: Claude Opus, GPT-5.5 and Gemini Pro/Argon.

## Why the benchmarks don't settle it
1. **Wrong task.** Both boards measure fiction and creative writing. Ours is a short German/English sales email under hard rules.
2. **Missing models.** The newest mid-tier models (Sonnet 5.5, Gemini 3.8 Flash on EQ-Bench, GPT-5.6) are missing from at least one board.
3. **Cost isn't what decides it.** At ~8 contacts a day, the gap between the cheapest and the priciest candidate is about **$3–5 per month**. The only reason to choose a model is draft quality, plus speed.

## Decision method: blind bake-off (Friday eval)
- **Setup:**
  - 5 real contacts (3 EN, 2 DE).
  - The same brief and prompt for every model.
  - 3 candidates: GPT-5.1 (baseline), Gemini 3.8 Flash (best human-vote score per dollar), Claude Sonnet 5.5.
  - Calls go through **OpenRouter**: one key and one n8n credential cover all three.
- **Blinding:** the outputs are labelled X/Y/Z in random order, and the key stays hidden in the Evals DB. Noah rates each draft (would send / would edit / would not send) before the key is revealed.
- **Decision rule:** the most "would send" ratings wins. On a tie, choose the cheaper and faster model.
- **Also measured:** the code-check pass rate and the run time per model.

## Data location (for the record)
- US providers (OpenAI, Anthropic, Google) are covered by the EU–US Data Privacy Framework adequacy decision. The EU General Court upheld it in Sept 2025.
- Chinese providers (DeepSeek, Moonshot/Kimi) have no adequacy decision; Italy's regulator blocked DeepSeek in 2025.
- For public founders' names and roles the practical risk is low. It matters once this engine is sold to clients (offer: Commercial Automation with a GDPR-aware setup).
