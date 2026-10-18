// Golden-set eval for WP · 10 Qualify company.
// Runs the SAME code as production: the injection pre-check and the icp-v2 scoring are read
// from workflows/10-qualify-company.json, and so are the system prompt and the output schema.
// Only the LLM call is made directly (OpenAI, gpt-4o-mini, temperature 0), as in the workflow.
//
// Usage (from the repo root, key stays in your terminal):
//   OPENAI_API_KEY=... node tools/eval_qualify.mjs
// Output: docs/evals/qualify-golden-<date>.md and .json
import fs from 'node:fs';

const KEY = process.env.OPENAI_API_KEY;
if (!KEY) { console.error('Set OPENAI_API_KEY in your shell first.'); process.exit(1); }

const wf = JSON.parse(fs.readFileSync('workflows/10-qualify-company.json', 'utf8'));
const N = Object.fromEntries(wf.nodes.map(n => [n.name, n]));
const INJECT_CODE = N['Injection pre-check (rules)'].parameters.jsCode;
const SCORE_CODE = N['Score icp-v2 (rules)'].parameters.jsCode;
const chain = N['Extract facts (LLM chain)'].parameters;
const SYSTEM = chain.messages.messageValues[0].message;
const SCHEMA = JSON.parse(N['Schema · facts v2'].parameters.inputSchema);
const MODEL = 'gpt-4o-mini';
const cases = JSON.parse(fs.readFileSync('docs/evals/golden-set.json', 'utf8'));

// Run an n8n Code node body with the two globals it uses ($json and $('node').item.json)
const runNode = (code, json, refs = {}) =>
  new Function('$json', '$', code)(json, name => ({ item: { json: refs[name] } })).json;

async function extract(item) {
  const user = `<news_item>\nPUBLISHED: ${item.published}\nTITLE: ${item.title}\nTEXT: ${item.text}\n</news_item>`;
  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { Authorization: `Bearer ${KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: MODEL, temperature: 0, max_tokens: 1200,
      response_format: { type: 'json_schema', json_schema: { name: 'facts_v2', schema: SCHEMA, strict: false } },
      messages: [{ role: 'system', content: SYSTEM }, { role: 'user', content: user }]
    })
  });
  if (!res.ok) return { error: `HTTP ${res.status}: ${(await res.text()).slice(0, 200)}` };
  const body = await res.json();
  try { return { output: JSON.parse(body.choices[0].message.content), usage: body.usage }; }
  catch (e) { return { error: 'Unparseable model output' }; }
}

const now = new Date().toISOString();
const results = [];
for (const c of cases) {
  // Golden inputs are teaser-length, so (as in production when the article fetch fails) the
  // text is the RSS text. Published = now, so the trigger-recency points are constant.
  const item = { title: '', text: c.input, link: '', published: now, linkHosts: [], prepFlags: [] };
  const pre = runNode(INJECT_CODE, item);
  let out;
  if (pre.injection) out = { ...pre, status: 'Rejected', flags: ['Injection pattern'], score: null, gate: 'Injection pre-check' };
  else {
    const llm = await extract(pre);
    out = runNode(SCORE_CODE, { output: llm.output || null, error: llm.error }, { 'Injection pre-check (rules)': pre });
  }
  const qualified = out.status === 'Qualified';
  let actualLabel, pass;
  if (c.expected === 'Block') { actualLabel = pre.injection || !qualified ? 'Block' : 'Fit'; pass = actualLabel === 'Block'; }
  else { actualLabel = qualified ? 'Fit' : 'No fit'; pass = actualLabel === c.expected; }
  const actual = [
    `status ${out.status}`,
    out.score != null ? `score ${out.score}` : null,
    out.gate ? `gate: ${out.gate}` : null,
    out.flags?.length ? `flags: ${out.flags.join(', ')}` : null,
    out.error ? `error: ${out.error}` : null
  ].filter(Boolean).join(' · ');
  results.push({ id: c.id, url: c.url, case: c.case, type: c.type, expected: c.expected, actualLabel, pass, actual });
  console.log(`${pass ? 'PASS' : 'FAIL'}  #${c.id} ${c.case}  →  ${actual}`);
}

const q = results.filter(r => r.type === 'Qualify');
const inj = results.filter(r => r.type === 'Prompt injection');
const summary = `Qualify: ${q.filter(r => r.pass).length} of ${q.length} match the expected label · ` +
  `Injection: ${inj.filter(r => r.pass).length} of ${inj.length} blocked`;
const date = now.slice(0, 10);
fs.writeFileSync(`docs/evals/qualify-golden-${date}.json`, JSON.stringify({ date: now, model: MODEL, prompt: 'qualify-v2 / icp-v2', summary, results }, null, 2));
fs.writeFileSync(`docs/evals/qualify-golden-${date}.md`,
  `# Qualify golden set · ${date}\n\nModel ${MODEL}, temperature 0 · prompt qualify-v2 · scoring icp-v2 (code read from workflows/10-qualify-company.json).\n\n**${summary}**\n\n` +
  `| # | Case | Expected | Actual | Result | Detail |\n|---|---|---|---|---|---|\n` +
  results.map(r => `| ${r.id} | ${r.case} | ${r.expected} | ${r.actualLabel} | ${r.pass ? '✅' : '❌'} | ${r.actual.replace(/\|/g, '/')} |`).join('\n') +
  `\n\nNotes: inputs are teaser-length (as when the article fetch fails), so facts without verbatim evidence fall back to neutral values. "Check: business model unclear" counts as not qualified, because production archives it until a human promotes it.\n`);
console.log('\n' + summary);
