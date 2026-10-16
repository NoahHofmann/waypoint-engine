# Draft model choice (to be decided by a blind bake-off)

**Question:** which model writes the most natural 60–110-word B2B emails in German and English, and what does it cost at our volume?

## Current writing benchmarks (checked 15 Oct 2026)
| Model | Arena Creative Writing (human votes, 15 Oct) | Arena Text overall (15 Oct) | Mazur short-story benchmark | Price per 1M tokens (in / out) | ≈ per month* |
|---|---|---|---|---|---|
| **Claude Opus 5.5** | **#1** (1517) | – | 74 (joint #1) | $4 / $20 | ~$14 |
| Gemini 4 Argon | #2 (1516) | #1 (1524, prelim.) | 50 | $2 / $10 (restricted preview, no public API) | – |
| **Gemini 3.8 Flash** | **#7** (1487) | #9 (1496, prelim.) | not listed | **$0.75 / $3.75** | **~$3** |
| GPT-6 Astra | – | #30 (1477) | 73 | $10 / $50 | ~$34 |
| GLM 5.3 | – | – | 70 | $1.40 / $4.40 | ~$4 |
| Kimi K3 | #30 | #18 (1487) | 66 | $3 / $15 | ~$10 |
| GPT-5.6 Sol | #21 | #21 (1485) | 66 | – | – |
| Claude Sonnet 5.5 | not in the top 20 | #36 (1475) | not listed | $2 / $10 | ~$7 |
| GPT-5.1 (current) | not listed | not listed | not listed | $1.25 / $10 | ~$5.5 |
| Mistral Large 4 / Medium 3.5 | – | #111 / #117 | – | low | – |

\*About 176 contacts a month × 1.5 attempts × (7k input + 1.2k output tokens).

## Reading
1. **The model we use (GPT-5.1) is not competitive on any current writing board.** It was chosen for following instructions, not for prose.
2. **Quality leader: Claude Opus 5.5.** It is #1 on human preference for creative writing and joint #1 on Mazur. It costs about $14/month at our volume, roughly $8/month more than GPT-5.1.
3. **Value leader: Gemini 3.8 Flash.** It is top 10 on human preference at about 1/5 of Opus's price. Caveat: its arena score is still marked preliminary.
4. **Not worth it:** GPT-6 Astra (2.5× the price of Opus, no better), Mistral (far behind), Gemini 4 Argon (no public API).
5. **Limits of the boards:** they measure chat and fiction preferences, not short German sales emails under hard rules. That is why the bake-off decides.

## Bake-off (Friday eval)
- **Candidates:** Claude Opus 5.5 (quality), Gemini 3.8 Flash (value), GPT-5.1 (baseline). Optional fourth: Claude Sonnet 5.5.
- **Setup:** 5 real contacts (3 EN, 2 DE), the same brief and prompt (draft-v5) for every model, and one OpenRouter key.
- **Blind rating:** outputs are labelled X/Y/Z in random order. Noah rates each draft "would send / would edit / would not send" before the key is revealed.
- **Decision rule:** most "would send" wins. On a tie, the cheaper or faster model wins. Also recorded: code-check pass rate and seconds per contact.

## Data location
- US providers (OpenAI, Anthropic, Google) are covered by the EU–US Data Privacy Framework (upheld by the EU General Court in Sept 2025).
- Chinese providers (Moonshot/Kimi, Z.ai/GLM, DeepSeek) have no adequacy decision.
- Low practical risk for public founders' names and roles. It becomes relevant if the engine is sold to clients.

## Decision (16 Oct, 13:30)
- **Draft model: Claude Sonnet 5.5** ($2/$10, ~€7/month at our volume).
- Not Opus 5.5: about 2× the cost.
- Not Haiku 5.5: unproven for prose.
- **Own benchmark from now on:** each draft is scored 0–10 by the fixed judge (GPT-5 mini, judge-v5 rubric). Runs record *Quality avg* + *Model*.
- **Baseline:** GPT-5.1 drafts from 15–16 Oct (no score yet). Run a few days per model, then compare Quality avg, code-check pass rate, cost and seconds per contact. Later add reply rate (roadmap).
