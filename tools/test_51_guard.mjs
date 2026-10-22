// Regression fixture for WP · 51 (H0, 22 Oct): draft-only mode + Gmail duplicate guard.
// Runs the real node code from workflows/51-approval-handler.json against mocked n8n globals.
// Usage: node tools/test_51_guard.mjs   (exit 1 on any failure)
import { readFileSync } from 'node:fs';
const wf = JSON.parse(readFileSync(new URL('../workflows/51-approval-handler.json', import.meta.url)));
const code = name => wf.nodes.find(n => n.name === name).parameters.jsCode;
const run = (name, g) => new Function('$', '$input', '$json', '$execution', '$now', `return (function(){${code(name)}})()`)(
  g.$, g.$input, g.$json, g.$execution || { id: 'exec1' }, g.$now);
let fail = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fail++; };
const d = { action: 'gmail_draft', chosen: 'A', name: 'Test Person', company: 'Acme', email: 't@acme.com', subject: 'S', body: 'B', log: '', contactPageId: 'pg1', chatId: '1', cardMessageId: '2' };
const $d = n => ({ first: () => ({ json: d }), item: { json: d } });
const guard = items => run('Duplicate guard', { $: $d, $input: { all: () => items.map(json => ({ json })) } })[0].json;

// 1. Guard
ok(guard([{}]).guard === 'clear', 'no Gmail hit (empty item) -> clear');
ok(guard([]).guard === 'clear', 'no items at all -> clear');
let g = guard([{ id: 'm1', labelIds: ['DRAFT'] }]);
ok(g.guard === 'exists' && g.foundSent === false, 'existing draft -> exists, not sent');
g = guard([{ id: 'm1', labelIds: ['DRAFT'] }, { id: 'm2', labelIds: ['SENT'], internalDate: '1792673368000' }]);
ok(g.guard === 'exists' && g.foundSent && g.sentAt === new Date(1792673368000).toISOString(), 'sent mail -> exists, foundSent + sentAt');
g = guard([{ id: 'm3', labels: [{ id: 'SENT', name: 'SENT' }] }]);
ok(g.foundSent, 'simple-mode label objects are read too');
g = guard([{ error: { message: '401 invalid_grant' } }]);
ok(g.guard === 'error' && /duplicate check failed/.test(g.error.message), 'search error -> fail closed');
ok(guard([{}]).email === 't@acme.com', 'clear passes the draft fields through');

// 2. Build outcome
const $now = { setZone: () => ({ toFormat: () => '2026-10-22 16:00' }) };
const outcome = json => run('Build outcome', { $: $d, $json: json, $now }).json;
let o = outcome({ ...d, guard: 'exists', foundSent: false });
let P = o.notionBody.properties;
ok(P.Status.status.name === 'Gmail draft created' && /ALREADY IN GMAIL/.test(o.closeText), 'existing draft -> card closed, status Gmail draft created');
ok(!P['Chosen variant'] && /NOT CREATED: draft already in Gmail/.test(P['Approval log'].rich_text[0].text.content), 'duplicate does not overwrite chosen text; log says why');
o = outcome({ ...d, guard: 'exists', foundSent: true, sentAt: '2026-10-22T12:49:28.000Z' });
P = o.notionBody.properties;
ok(P.Status.status.name === 'Sent' && P['Sent at'].date.start === '2026-10-22T12:49:28.000Z', 'already sent -> Status Sent + Sent at from Gmail');
o = outcome({ ...d, guard: 'error', error: { message: 'Gmail duplicate check failed: x' } });
ok(o.notionBody.properties.Status.status.name === 'Awaiting approval' && /failed/.test(o.replyText) && !o.closeText, 'guard error -> card stays open, Awaiting approval');
o = outcome({ id: 'r123', message: { id: 'abc' } });
ok(o.notionBody.properties.Status.status.name === 'Gmail draft created' && /draft r123/.test(o.notionBody.properties['Approval log'].rich_text[0].text.content), 'new draft -> draft id logged');

// 3. Draft-only: a green legal basis must still become a draft
const rt = v => ({ rich_text: [{ plain_text: v }] });
const page = { id: 'pg1', properties: { Status: { status: { name: 'Awaiting approval' } }, Name: { title: [{ plain_text: 'X' }] }, Channel: { select: { name: 'Email' } },
  Email: { email: 'x@acme.com' }, 'Legal basis': { select: { name: 'Consent' } }, 'Variant A': rt('Subject: Hi\n\nBody'), 'Draft subject': rt('Hi'), Lock: rt(''), 'Approval log': rt('') } };
const parse = { chatId: '1', cardMessageId: '2', kind: 'choose', variant: 'A', cardTitle: 'Acme · X' };
const dec = run('Decide action (rules)', { $: () => ({ item: { json: parse } }), $json: page }).json;
ok(dec.action === 'gmail_draft', 'Legal basis Consent -> gmail_draft (draft-only), not send');
console.log(fail ? `\n${fail} FAILED` : '\nall passed'); process.exit(fail ? 1 : 0);
