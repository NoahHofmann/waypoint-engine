import json, uuid, sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from runlog import runlog_code, runlog_http_params, REMEMBER, apply_ids, WF_IDS, TG_APPROVALS
import os
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
CHAT='1170608781'
def mk():
    N=[];C={}
    def node(name,typ,ver,pos,params,**kw):
        n={"id":str(uuid.uuid4()),"name":name,"type":typ,"typeVersion":ver,"position":pos,"parameters":params}; n.update(kw); N.append(n); return name
    def link(a,b,out=0,inp=0):
        C.setdefault(a,{}).setdefault("main",[]); m=C[a]["main"]
        while len(m)<=out: m.append([])
        m[out].append({"node":b,"type":"main","index":inp})
    return N,C,node,link
NH={"sendHeaders":True,"headerParameters":{"parameters":[{"name":"Notion-Version","value":"2022-06-28"}]}}
def notion(node,name,pos,method,url,body=None,**kw):
    p={"method":method,"url":url,"authentication":"predefinedCredentialType","nodeCredentialType":"notionApi",**NH,"options":{}}
    if body: p.update({"sendBody":True,"specifyBody":"json","jsonBody":body})
    return node(name,"n8n-nodes-base.httpRequest",4.2,pos,p,**kw)
TG={"telegramApi":{"id":"x17tu5yr5xFWMSsZ","name":"Telegram approvals"}}   # IDs from n8n credentials (Noah, 16 Oct)
GM={"gmailOAuth2":{"id":"SZBYk0OCrdNe1W56","name":"Gmail account"}}
TXT='const txt = p => { if (!p) return \'\'; const a = p.title || p.rich_text; if (a) return a.map(t => t.plain_text).join(\'\').trim(); return p.url || p.email || p.select?.name || p.status?.name || (p.number ?? \'\') + \'\'; };'

# ---------------- 50 · Approval cards ----------------
N,C,node,link=mk()
node("Run manually","n8n-nodes-base.manualTrigger",1,[0,100],{})
node("When called by orchestrator","n8n-nodes-base.executeWorkflowTrigger",1.1,[0,300],{"inputSource":"passthrough"})
node("Config","n8n-nodes-base.code",2,[220,200],{"jsCode":f"""// 50 · Approval cards: config
// maxOpenCards: never more than this many unanswered approval cards in the chat (prevents stacking).
// maxWebsiteQuestions: at most this many 'which website?' questions per run.
return [{{ json: {{ chatId: '{CHAT}', notionContactsDb: '349e3747aa894088a833ca4a76d6a1b2', notionCompaniesDb: '1247998a78a8446993afa06d9811c436', maxOpenCards: 5, maxWebsiteQuestions: 3, startedAt: new Date().toISOString() }} }}];"""})
link("Run manually","Config"); link("When called by orchestrator","Config")
notion(node,"Notion · approved in Notion",[440,-160],"POST","=https://api.notion.com/v1/databases/{{ $json.notionContactsDb }}/query",
  '={{ JSON.stringify({ filter: { and: [ { property: "Approve in Notion", select: { is_not_empty: true } }, { or: [ { property: "Status", status: { equals: "Awaiting approval" } }, { property: "Status", status: { equals: "Draft ready" } }, { property: "Status", status: { equals: "Check manually" } }, { property: "Status", status: { equals: "Backlog" } } ] } ] }, page_size: 20 }) }}',executeOnce=True)
link("Config","Notion · approved in Notion")
NAPP=TXT+r"""
// NOTION FALLBACK: you picked A/B/C/Skip in the column 'Approve in Notion' instead of tapping in Telegram.
// Each row is handed to WP · 51, which treats it exactly like a Telegram tap (same idempotency + legal-basis gate).
return ($input.first().json.results || []).map(pg => ({ json: {
  source: 'notion', contactPageId: pg.id, choice: txt(pg.properties['Approve in Notion']),
  cardMessageId: txt(pg.properties['Telegram message ID']) || null } }));"""
node("Notion approvals → 51",'n8n-nodes-base.code',2,[660,-160],{"jsCode":NAPP})
link("Notion · approved in Notion","Notion approvals → 51")
node("Run WP · 51 for each",'n8n-nodes-base.executeWorkflow',1.2,[880,-160],{"source":"database","workflowId":{"__rl":True,"value":WF_IDS["51"],"mode":"id"},"mode":"each","options":{"waitForSubWorkflow":True}},onError="continueRegularOutput")
link("Notion approvals → 51","Run WP · 51 for each")
notion(node,"Notion · cards still open",[440,200],"POST","=https://api.notion.com/v1/databases/{{ $json.notionContactsDb }}/query",
  '={{ JSON.stringify({ filter: { or: ["Awaiting approval", "Approved", "Gmail draft created", "Sent", "Replied", "Meeting booked"].map(n => ({ property: "Status", status: { equals: n } })) }, page_size: 100 }) }}',executeOnce=True)
link("Config","Notion · cards still open")  # runs after the Notion-approval branch (canvas order, top first)
notion(node,"Notion · drafts ready",[660,200],"POST","=https://api.notion.com/v1/databases/{{ $('Config').first().json.notionContactsDb }}/query",
  '={{ JSON.stringify({ filter: { property: "Status", status: { equals: "Draft ready" } }, sorts: [{ timestamp: "created_time", direction: "ascending" }], page_size: 20 }) }}',executeOnce=True)
link("Notion · cards still open","Notion · drafts ready")
node("Pick drafts","n8n-nodes-base.code",2,[880,200],{"jsCode":TXT+"""
// STACK GUARD: only top up to maxOpenCards unanswered cards. If the chat is full, send nothing new
// (the drafts stay 'Draft ready' and go out after you answer the open ones).
const cfg = $('Config').first().json;
// ONE COMPANY, ONE CONVERSATION: a draft for a company that already has a card open or an email out
// (or a second draft for the same company in this batch) goes to BACKLOG: kept with its drafts as the
// second contact if the first doesn't reply. Not an error; nothing is sent.
const inFlight = $('Notion · cards still open').first().json.results || [];
const open = inFlight.filter(pg => pg.properties.Status?.status?.name === 'Awaiting approval').length;
const busy = {}; inFlight.forEach(pg => { const co = pg.properties.Company?.relation?.[0]?.id; if (co) busy[co] = txt(pg.properties.Name); });
const room = Math.max(0, cfg.maxOpenCards - open);
const all = ($input.first().json.results || []).filter(pg => pg.properties.Company?.relation?.[0]?.id);
const dups = [], ready = [];
all.forEach(pg => { const co = pg.properties.Company.relation[0].id;
  if (busy[co]) dups.push({ pg, other: busy[co] }); else { busy[co] = txt(pg.properties.Name); ready.push(pg); } });
const take = ready.slice(0, room);
const dupItems = dups.map(d => ({ json: { duplicate: true, contactPageId: d.pg.id, name: txt(d.pg.properties.Name), other: d.other } }));
return dupItems.concat(take.map((pg, i) => { const P = pg.properties; return { json: { duplicate: false,
  cardNo: open + i + 1, cardTotal: open + take.length, waiting: ready.length - take.length,
  contactPageId: pg.id, name: txt(P.Name), role: txt(P.Role), channel: txt(P.Channel) || 'Email', language: txt(P['Draft language']),
  offer: txt(P.Offer), email: txt(P.Email), linkedin: txt(P.LinkedIn), legalBasis: txt(P['Legal basis']) || 'None - draft only',
  passed: txt(P['Variants passed']), A: txt(P['Variant A']), B: txt(P['Variant B']), C: txt(P['Variant C']),
  companyPageId: P.Company?.relation?.[0]?.id || null } }; }));"""})
link("Notion · drafts ready","Pick drafts")
node("Duplicate company?","n8n-nodes-base.if",2.2,[990,200],{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose","version":2},"conditions":[{"id":str(uuid.uuid4()),"leftValue":"={{ $json.duplicate }}","rightValue":True,"operator":{"type":"boolean","operation":"true","singleValue":True}}],"combinator":"and"},"options":{}})
link("Pick drafts","Duplicate company?")
notion(node,"Notion · move to Backlog",[1210,20],"PATCH","=https://api.notion.com/v1/pages/{{ $json.contactPageId }}",
  '={{ JSON.stringify({ properties: { Status: { status: { name: "Backlog" } }, "Approval log": { rich_text: [{ type: "text", text: { content: new Date().toISOString().slice(0,16) + " backlog: " + $json.other + " at this company is already in conversation. Second contact if there is no reply (set Approve in Notion to use now)." } }] } } }) }}',onError="continueRegularOutput")
link("Duplicate company?","Notion · move to Backlog",0)
notion(node,"Notion · get company",[1320,200],"GET","=https://api.notion.com/v1/pages/{{ $json.companyPageId }}")
link("Duplicate company?","Notion · get company",1)
STACK=TXT+r"""
// One short notice when drafts are waiting because 5 cards are still unanswered (otherwise this would be silent).
const cfg = $('Config').first().json;
const open = ($('Notion · cards still open').first().json.results || []).filter(pg => pg.properties.Status?.status?.name === 'Awaiting approval');
const ready = ($input.first().json.results || []).length;
if (open.length < cfg.maxOpenCards || ready === 0) return [];
const h = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
return [{ json: { text: `⏸ <b>QUEUE FULL · ${open.length} cards waiting for you</b>\n━━━━━━━━━━━━━━━━\n<b>${ready} new draft(s)</b> are queued behind them. Each card you answer pulls in the next one immediately.\n<b>Open:</b> ` + open.map(pg => h(txt(pg.properties.Name))).join(', ') } }];"""
node("Queue full notice","n8n-nodes-base.code",2,[880,420],{"jsCode":STACK})
link("Notion · drafts ready","Queue full notice")
M50=r"""const inFlight = $('Notion · cards still open').first().json.results || [];
const open = inFlight.filter(pg => pg.properties.Status?.status?.name === 'Awaiting approval').length;
const ready = ($input.first().json.results || []).length;
let nApp = 0; try { nApp = ($('Notion · approved in Notion').first().json.results || []).length; } catch (e) {}
const room = Math.max(0, $('Config').first().json.maxOpenCards - open);
const c = { ready, nApp, cards: Math.min(room, ready) };
const x = { open, full: room === 0 && ready > 0 };
const view = (c, x) => ({ in: c.ready + c.nApp, out: c.cards + c.nApp, errors: 0, costEur: 0, skip: c.ready === 0 && c.nApp === 0,
  notes: `${x.open} cards open before this run, ${c.ready} drafts ready, up to ${c.cards} new card(s) (second contacts at the same company go to Backlog), ${c.nApp} approval(s) from Notion handed to 51.` + (x.full ? ' QUEUE FULL.' : '') });"""
node("Build run log","n8n-nodes-base.code",2,[880,640],{"jsCode":runlog_code("Config","Approval cards","Approval",M50)})
link("Notion · drafts ready","Build run log")
node("Notion · log run","n8n-nodes-base.httpRequest",4.2,[1100,640],runlog_http_params(),onError="continueRegularOutput")
link("Build run log","Notion · log run")
node("Remember run log","n8n-nodes-base.code",2,[1320,640],{"jsCode":REMEMBER})
link("Notion · log run","Remember run log")
node("Telegram · queue full","n8n-nodes-base.telegram",1.2,[1100,420],{"chatId":"={{ $('Config').first().json.chatId }}","text":"={{ $json.text }}","additionalFields":{"appendAttribution":False,"parse_mode":"HTML"}},credentials=TG,onError="continueRegularOutput")
link("Queue full notice","Telegram · queue full")
CARD=TXT+r"""
// Build the approval card (Telegram HTML: bold headers, escaped content, max 4096 chars) and the callback keys.
const h = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const c = $('Pick drafts').item.json;
const P = $json.properties || {};
const key = c.contactPageId.replace(/-/g, '');
const GREEN = ['Consent', 'Existing relationship', 'Inbound'];
const what = c.channel === 'LinkedIn' ? '<b>Tap = </b>I send you the text to paste into LinkedIn.'
  : GREEN.includes(c.legalBasis) ? '<b>Tap = SENT</b> from hello@ immediately.'
  : '<b>Tap = Gmail DRAFT</b> in hello@ (cold lead): you check and send it yourself.';
const clip = (s, n) => s.length > n ? s.slice(0, n) + '…' : s;
// First line is parsed by WP · 51 (company · name) — keep the format "📨 APPROVE n/m · Company · Name".
const head = [
  `📨 <b>APPROVE ${c.cardNo}/${c.cardTotal} · ${h(txt(P.Company))} · ${h(c.name)}</b>${c.role ? ' (' + h(c.role) + ')' : ''}`,
  '━━━━━━━━━━━━━━━━',
  `<b>${h(c.channel)}</b> · ${h(c.language || 'EN')} · ICP ${h(txt(P['ICP score']))} · <b>Offer:</b> ${h(c.offer)}`,
  `<b>Signal:</b> ${h(txt(P['Signal summary']))}`,
  `<b>To:</b> ${h(c.channel === 'Email' ? c.email : c.linkedin)}`,
  what,
  `<b>Passed review:</b> ${h(c.passed || 'none')}`
].join('\n');
const variants = ['A', 'B', 'C'].map(id => `<b>— ${id} —</b>\n${h(clip(c[id] || '(empty)', 1000))}`).join('\n\n');
const foot = '✏️ <b>Own version:</b> swipe left on this card (Reply) and send the text (first line "Subject: …" for emails).' + (c.waiting ? `\n⏸ ${c.waiting} more draft(s) queued: each answer pulls in the next.` : '');
const text = clip(head + '\n\n' + variants + '\n\n' + foot, 3900);
return { json: { ...c, key, text, company: txt(P.Company) } };"""
node("Build card","n8n-nodes-base.code",2,[1540,200],{"jsCode":CARD,"mode":"runOnceForEachItem"})
link("Notion · get company","Build card")
btn=lambda t,d: {"text":t,"additionalFields":{"callback_data":d}}
node("Telegram · send card","n8n-nodes-base.telegram",1.2,[1760,200],{
  "chatId":"={{ $('Config').first().json.chatId }}","text":"={{ $json.text }}",
  "replyMarkup":"inlineKeyboard",
  "inlineKeyboard":{"rows":[{"row":{"buttons":[btn("Send A","={{ 'v|' + $json.key + '|A' }}"),btn("Send B","={{ 'v|' + $json.key + '|B' }}"),btn("Send C","={{ 'v|' + $json.key + '|C' }}")]}},
                            {"row":{"buttons":[btn("✏️ Edit","={{ 'e|' + $json.key }}"),btn("⏭ Skip","={{ 's|' + $json.key }}")]}}]},
  "additionalFields":{"appendAttribution":False,"disable_web_page_preview":True,"parse_mode":"HTML"}},credentials=TG,onError="continueRegularOutput")
link("Build card","Telegram · send card")
node("Build Notion update","n8n-nodes-base.code",2,[1980,200],{"jsCode":"""// Awaiting approval + the card's message id (idempotency key: a tap is only acted on while the status is Awaiting approval).
const c = $('Build card').item.json;
const id = $json.result?.message_id;
const t = s => [{ type: 'text', text: { content: String(s).slice(0, 1990) } }];
if (!id) return { json: { skip: true, contactPageId: c.contactPageId, error: JSON.stringify($json.error || $json).slice(0, 200) } };
return { json: { contactPageId: c.contactPageId, name: c.name, company: c.company, body: { properties: {
  'Status': { status: { name: 'Awaiting approval' } },
  'Telegram message ID': { rich_text: t(String(id)) },
  'Approval log': { rich_text: t(`${new Date().toISOString().slice(0, 16)} card sent (message ${id})`) } } } } };""","mode":"runOnceForEachItem"})
link("Telegram · send card","Build Notion update")
notion(node,"Notion · awaiting approval",[2200,200],"PATCH","=https://api.notion.com/v1/pages/{{ $json.contactPageId }}","={{ JSON.stringify($json.body) }}")
link("Build Notion update","Notion · awaiting approval")
notion(node,"Notion · companies without website",[440,620],"POST","=https://api.notion.com/v1/databases/{{ $('Config').first().json.notionCompaniesDb }}/query",
  '={{ JSON.stringify({ filter: { property: "Domain source", select: { equals: "Not found" } }, page_size: $("Config").first().json.maxWebsiteQuestions }) }}',executeOnce=True)
link("Config","Notion · companies without website")
WQ=TXT+r"""
// HUMAN FALLBACK for the website (last resort, kept rare): 30 tried ~30 likely domains and rejected all.
const h = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
// One short question per company; reply with the domain. 'ref w|<key>' lets 51 find the company again.
return ($input.first().json.results || []).map(pg => { const P = pg.properties; const key = pg.id.replace(/-/g, '');
  const q = encodeURIComponent(txt(P.Company) + ' ' + txt(P['Signal summary']).slice(0, 60));
  return { json: { companyPageId: pg.id, key, company: txt(P.Company), google: 'https://www.google.com/search?q=' + q,
    text: [`🌐 <b>WEBSITE? · ${h(txt(P.Company))}</b>`, '━━━━━━━━━━━━━━━━', h(txt(P['Signal summary'])), `<b>Article:</b> ${h(txt(P['Signal source']))}`, '',
      'I could not verify a website (all likely domains were parked, unrelated or empty).',
      '↩️ <b>Swipe left on this message (Reply)</b> and send the domain, e.g. <code>acme.ai</code>. I save it and re-run email search for its contacts.',
      `ref w|${key}`].join('\n') } }; });"""
node("Build website question","n8n-nodes-base.code",2,[660,620],{"jsCode":WQ})
link("Notion · companies without website","Build website question")
node("Telegram · ask website","n8n-nodes-base.telegram",1.2,[880,620],{
  "chatId":"={{ $('Config').first().json.chatId }}","text":"={{ $json.text }}","replyMarkup":"inlineKeyboard",
  "inlineKeyboard":{"rows":[{"row":{"buttons":[{"text":"🔎 Search","additionalFields":{"url":"={{ $json.google }}"}},btn("🚫 No website","={{ 'w|' + $json.key + '|none' }}")]}}]},
  "additionalFields":{"appendAttribution":False,"disable_web_page_preview":True,"parse_mode":"HTML"}},credentials=TG,onError="continueRegularOutput")
link("Build website question","Telegram · ask website")
notion(node,"Notion · mark asked",[1100,620],"PATCH","=https://api.notion.com/v1/pages/{{ $('Build website question').item.json.companyPageId }}",
  '={{ JSON.stringify({ properties: { "Domain source": { select: { name: "Asked in Telegram" } } } }) }}',onError="continueRegularOutput")
link("Telegram · ask website","Notion · mark asked")
node("Note · 50 notion",'n8n-nodes-base.stickyNote',1,[400,-420],{"width":760,"height":220,"content":"""### 0 · Approvals made in Notion (runs first)
**In:** contacts where you set *Approve in Notion* (A/B/C/Skip) and Status is Awaiting approval, Draft ready or Check manually.
**Nodes:** Notion · approved in Notion → Notion approvals → 51 → Run WP · 51 for each (WP · 51 preset by ID).
**Why:** if you miss a Telegram card you can decide in the dashboard; 51 applies the same lock and legal-basis gate, and confirms in Telegram."""})
node("Note · 50 websites","n8n-nodes-base.stickyNote",1,[400,820],{"width":900,"height":240,"content":"""### Website questions (human fallback, rare by design)
**In:** companies where WP · 30 rejected every candidate domain (Domain source = *Not found*). Max 3 per run.
**Out:** one 🌐 WEBSITE? message each (🔎 Search opens Google; 🚫 No website closes it). Domain source → *Asked in Telegram*, so it is asked once.
**Your reply** (the domain) is handled by WP · 51: Domain saved as *Manual*, and that company's *Not reachable* / *Check manually* contacts go back to *Needs email*, so the next WP · 30 run tries again with the right domain.
**Why:** a wrong website means emails to the wrong people. One 5-second answer from you beats a guess."""})
node("Note · 50","n8n-nodes-base.stickyNote",1,[0,-380],{"width":900,"height":300,"content":"""## WP · 50 Approval cards: what and why
**Input:** contacts with Status *Draft ready* (from WP · 40). **Stack guard:** at most 5 unanswered cards in the chat; extra drafts wait for the next run. Cards are numbered "APPROVE 2/5".
Sends one Telegram card per contact with Status **Draft ready**: company, person, channel, ICP score, offer, signal, **what Approve will do** (send / Gmail draft / LinkedIn text), which variants passed review, and all three variants. Buttons: **Send A · Send B · Send C · ✏️ Edit · ⏭ Skip**. Replying to the card with your own text sends that version.
Sets Status **Awaiting approval** and stores the card's message id. The taps are handled by **WP · 51** (Telegram trigger).
**Why Telegram:** approval in seconds from the phone; nothing leaves without a human tap. **Why show the action on the card:** the legal-basis gate is visible before you decide.
Docs: docs/50-approval.md"""})
wf50={"name":"WP · 50 Approval cards (sub-workflow)","nodes":apply_ids(N),"connections":C,"settings":{"executionOrder":"v1","timezone":"Europe/Berlin","saveManualExecutions":True},"pinData":{}}
json.dump(wf50,open(R+'workflows/50-approval-cards.json','w'),indent=2,ensure_ascii=False)
n50=len(N)

# ---------------- 51 · Approval handler ----------------
# v3 (16 Oct): every tap/reply gets a visible answer; decided cards are CLOSED (edited, buttons removed);
# HTML formatting; unmatched messages get a help reply instead of silence.
N,C,node,link=mk()
H_JS = "const h = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');"
HTML = {"parse_mode":"HTML"}
node("When called by 50 (Notion approval)","n8n-nodes-base.executeWorkflowTrigger",1.1,[-220,620],{"inputSource":"passthrough"})
FROMN=f"""// Turn a Notion approval into the same shape as a Telegram tap, so ONE code path decides.
const k = String($json.contactPageId || '').replace(/-/g, '');
const c = String($json.choice || '');
const data = c === 'Skip' ? 's|' + k : 'v|' + k + '|' + c;
return {{ json: {{ fromNotion: true, callback_query: {{ id: 'notion', data, message: {{ message_id: $json.cardMessageId ? Number($json.cardMessageId) : null, chat: {{ id: {CHAT} }}, text: '' }} }} }} }};"""
node("Notion approval as tap","n8n-nodes-base.code",2,[0,620],{"jsCode":FROMN,"mode":"runOnceForEachItem"})
link("When called by 50 (Notion approval)","Notion approval as tap")
link("Notion approval as tap","Parse update (rules)")
node("Telegram trigger","n8n-nodes-base.telegramTrigger",1.1,[0,300],{"updates":["callback_query","message"],"additionalFields":{}},credentials=TG,webhookId=str(uuid.uuid4()))
PARSE=rf"""// Parse the Telegram update (rules). Only Noah's chat is accepted; everything else is ignored silently (security).
// Every message FROM Noah gets an answer: tap, reply to a card, reply to a 🌐 question, or a help note ('unmatched').
const u = $json; const ALLOWED = '{CHAT}';
const cb = u.callback_query; const msg = u.message;
const chatId = String(cb?.message?.chat?.id ?? msg?.chat?.id ?? '');
const uuidOf = key => key ? key.replace(/(.{{8}})(.{{4}})(.{{4}})(.{{4}})(.{{12}})/, '$1-$2-$3-$4-$5') : null;
const titleOf = t => String(t || '').split('\n')[0].replace(/^📨 APPROVE \d+\/\d+ · /, '').replace(/^🌐 WEBSITE\? · /, '');
if (chatId !== ALLOWED) return {{ json: {{ ok: false, kind: 'ignore', reason: 'unauthorized chat ' + chatId }} }};
if (cb) {{
  const [k, key, v] = String(cb.data || '').split('|');
  const kind = k === 'v' ? 'choose' : k === 'e' ? 'edit' : k === 's' ? 'skip' : k === 'w' ? 'website_none' : 'unmatched';
  return {{ json: {{ ok: true, fromNotion: !!u.fromNotion, kind, variant: v || null,
    contactPageId: k === 'w' ? null : uuidOf(key), companyPageId: k === 'w' ? uuidOf(key) : null,
    callbackId: cb.id, cardMessageId: cb.message?.message_id ?? null, cardTitle: titleOf(cb.message?.text), chatId }} }};
}}
const replyTo = msg?.reply_to_message;
const ref = String(replyTo?.text || '').match(/ref w\|([0-9a-f]{{32}})/);
if (msg && ref && msg.text) {{
  const dom = String(msg.text).trim().toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').split(/[\/\s]/)[0];
  const okDom = /^[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{{2,}}$/.test(dom);
  return {{ json: {{ ok: true, kind: okDom ? 'website' : 'website_bad', domain: dom, companyPageId: uuidOf(ref[1]),
    cardMessageId: replyTo.message_id, replyMessageId: msg.message_id, cardTitle: titleOf(replyTo.text), chatId }} }};
}}
if (msg && replyTo && msg.text) {{
  return {{ json: {{ ok: true, kind: 'reply', text: msg.text, cardMessageId: replyTo.message_id, replyMessageId: msg.message_id, cardTitle: titleOf(replyTo.text), chatId }} }};
}}
return {{ json: {{ ok: true, kind: 'unmatched', replyMessageId: msg?.message_id ?? null, chatId }} }};"""
node("Parse update (rules)","n8n-nodes-base.code",2,[220,300],{"jsCode":PARSE,"mode":"runOnceForEachItem"})
link("Telegram trigger","Parse update (rules)")
P_ = "$('Parse update (rules)').item.json"
def cond(left,op,right=""):
    o={"type":"string","operation":op} if op not in ("true",) else {"type":"boolean","operation":"true","singleValue":True}
    return {"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose","version":2},"conditions":[{"id":str(uuid.uuid4()),"leftValue":left,"rightValue":right,"operator":o}],"combinator":"and"},"options":{}}
node("Authorized?","n8n-nodes-base.if",2.2,[440,300],cond("={{ $json.ok }}","true"))
link("Parse update (rules)","Authorized?")
node("Telegram · answer tap","n8n-nodes-base.telegram",1.2,[660,300],{"resource":"callback","operation":"answerQuery","queryId":"={{ $json.callbackId || 'none' }}","additionalFields":{"text":"Got it ✔"}},credentials=TG,onError="continueRegularOutput",alwaysOutputData=True)
link("Authorized?","Telegram · answer tap",0)
node("Route update","n8n-nodes-base.switch",3.2,[880,300],{"mode":"rules","rules":{"values":[
  {"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose","version":2},"conditions":[{"leftValue":"={{ "+P_+".kind }}","rightValue":rv,"operator":{"type":"string","operation":op}}],"combinator":"and"},"renameOutput":True,"outputKey":key}
  for key,op,rv in [("website","startsWith","website"),("reply","equals","reply"),("tap","regex","^(choose|edit|skip)$"),("unmatched","equals","unmatched")]]},"options":{}})
link("Telegram · answer tap","Route update")
# --- unmatched: never silent
UNM=H_JS+r"""
return { json: { chatId: $('Parse update (rules)').item.json.chatId, replyTo: $('Parse update (rules)').item.json.replyMessageId,
  text: '🤔 <b>Not matched to a card.</b>\nTo answer a card: <b>swipe left on it (Reply)</b> and send your text, or tap its buttons.\nTo give a website: reply to the 🌐 question.' } };"""
node("Help text","n8n-nodes-base.code",2,[1100,820],{"jsCode":UNM,"mode":"runOnceForEachItem"})
link("Route update","Help text",3)
def tgsend(name,pos,text,chat,reply_to):
    node(name,"n8n-nodes-base.telegram",1.2,pos,{"chatId":chat,"text":text,"additionalFields":{"appendAttribution":False,"disable_web_page_preview":True,"parse_mode":"HTML","reply_to_message_id":reply_to}},credentials=TG,onError="continueRegularOutput")
def tgedit(name,pos,text,chat,mid):
    node(name,"n8n-nodes-base.telegram",1.2,pos,{"resource":"message","operation":"editMessageText","messageType":"message","chatId":chat,"messageId":mid,"text":text,"replyMarkup":"none","additionalFields":{"disable_web_page_preview":True,"parse_mode":"HTML"}},credentials=TG,onError="continueRegularOutput")
tgsend("Telegram · help",[1320,820],"={{ $json.text }}","={{ $json.chatId }}","={{ $json.replyTo }}")
link("Help text","Telegram · help")
# --- website answers
WEB=H_JS+r"""
// Website answer from Noah -> what to write to the company + how to close the 🌐 question.
const p = $('Parse update (rules)').item.json;
const co = h(p.cardTitle || 'Company');
if (p.kind === 'website_bad') return { json: { ...p, valid: false,
  notice: `⚠️ <b>"${h(p.domain)}" doesn't look like a domain.</b>\nReply to the 🌐 question again, e.g. <code>acme.ai</code>` } };
const props = p.kind === 'website'
  ? { 'Domain': { url: 'https://' + p.domain }, 'Domain source': { select: { name: 'Manual' } } }
  : { 'Domain source': { select: { name: 'No website' } } };
return { json: { ...p, valid: true, notionBody: { properties: props },
  closeText: p.kind === 'website'
    ? `✅ <b>WEBSITE SAVED · ${co}</b>\n${h(p.domain)} · its contacts go back to email search on the next run.`
    : `🚫 <b>NO WEBSITE · ${co}</b>\nContacts stay LinkedIn-only.` } };"""
node("Build website update","n8n-nodes-base.code",2,[1100,560],{"jsCode":WEB,"mode":"runOnceForEachItem"})
link("Route update","Build website update",0)
node("Valid domain?","n8n-nodes-base.if",2.2,[1320,560],cond("={{ $json.valid }}","true"))
link("Build website update","Valid domain?")
notion(node,"Notion · save website",[1540,500],"PATCH","=https://api.notion.com/v1/pages/{{ $json.companyPageId }}","={{ JSON.stringify($json.notionBody) }}",retryOnFail=True,maxTries=3,waitBetweenTries=1500)
link("Valid domain?","Notion · save website",0)
tgedit("Telegram · close website question",[1760,440],"={{ $('Build website update').item.json.closeText }}","={{ $('Build website update').item.json.chatId }}","={{ $('Build website update').item.json.cardMessageId }}")
link("Notion · save website","Telegram · close website question")
notion(node,"Notion · contacts of company",[1760,620],"POST","https://api.notion.com/v1/databases/349e3747aa894088a833ca4a76d6a1b2/query",
  '={{ JSON.stringify({ filter: { and: [ { property: "Company", relation: { contains: $("Build website update").item.json.companyPageId } }, { or: [ { property: "Status", status: { equals: "Not reachable" } }, { property: "Status", status: { equals: "Check manually" } } ] } ] }, page_size: 20 }) }}',onError="continueRegularOutput")
link("Notion · save website","Notion · contacts of company")
REOPEN=r"""// Only when a domain was given: send this company's stuck contacts back to WP · 30 (Status Needs email).
const w = $('Build website update').item.json;
const rows = w.kind === 'website' ? ($input.first().json.results || []) : [];
return rows.map(pg => ({ json: { contactPageId: pg.id } }));"""
node("Contacts to retry","n8n-nodes-base.code",2,[1980,620],{"jsCode":REOPEN})
link("Notion · contacts of company","Contacts to retry")
notion(node,"Notion · back to Needs email",[2200,620],"PATCH","=https://api.notion.com/v1/pages/{{ $json.contactPageId }}",
  '={{ JSON.stringify({ properties: { Status: { status: { name: "Needs email" } } } }) }}',onError="continueRegularOutput")
link("Contacts to retry","Notion · back to Needs email")
tgsend("Telegram · website retry",[1540,680],"={{ $json.notice }}","={{ $json.chatId }}","={{ $json.replyMessageId }}")
link("Valid domain?","Telegram · website retry",1)
# --- find the contact
notion(node,"Notion · get contact",[1100,200],"GET","=https://api.notion.com/v1/pages/{{ "+P_+".contactPageId }}",onError="continueRegularOutput")
link("Route update","Notion · get contact",2)
notion(node,"Notion · find contact by card",[1100,380],"POST","https://api.notion.com/v1/databases/349e3747aa894088a833ca4a76d6a1b2/query",
  '={{ JSON.stringify({ filter: { property: "Telegram message ID", rich_text: { equals: String('+P_+'.cardMessageId) } }, page_size: 1 }) }}',onError="continueRegularOutput")
link("Route update","Notion · find contact by card",1)
node("First match","n8n-nodes-base.code",2,[1320,380],{"jsCode":"// Reply path: the replied-to card identifies the contact.\nconst pg = ($json.results || [])[0];\nreturn { json: pg || { notFound: true } };","mode":"runOnceForEachItem"})
link("Notion · find contact by card","First match")
DECIDE=TXT+H_JS+r"""
// Decide what to do (rules). Idempotent: acts only while Status is "Awaiting approval".
// Legal-basis gate: only Consent / Existing relationship / Inbound may be sent automatically.
const p = $('Parse update (rules)').item.json;
const pg = $json;
const base0 = { chatId: p.chatId, cardMessageId: p.cardMessageId, replyTo: p.replyMessageId || p.cardMessageId, cardTitle: p.cardTitle, fromNotion: !!p.fromNotion };
if (pg.notFound || !pg.properties) return { json: { ...base0, action: 'notice',
  notice: '🤔 <b>No contact found for this message.</b>\nReply directly to a 📨 card (not to a confirmation).' } };
const P = pg.properties;
const status = txt(P.Status);
const company = (p.cardTitle || '').split(' · ')[0] || '';
const base = { ...base0, contactPageId: pg.id, name: txt(P.Name), company, channel: txt(P.Channel) || 'Email',
  email: txt(P.Email), linkedin: txt(P.LinkedIn), legalBasis: txt(P['Legal basis']) || 'None - draft only', log: txt(P['Approval log']) };
const allowed = p.fromNotion ? ['Awaiting approval', 'Draft ready', 'Check manually', 'Backlog'] : ['Awaiting approval'];
// Already decided (double tap, or decided in Notion): close the card so no buttons are left, nothing sent again.
if (!allowed.includes(status)) return { json: { ...base, action: 'closed',
  closeText: `☑️ <b>ALREADY HANDLED · ${h(base.name)}</b>\nStatus: ${h(status)}. Nothing was sent again.` } };
if (p.kind === 'skip') return { json: { ...base, action: 'skip' } };
if (p.kind === 'edit') return { json: { ...base, action: 'notice',
  notice: `✏️ <b>Edit ${h(base.name)}</b>\nSwipe left on the card (Reply) and send your version. First line <code>Subject: …</code> for emails.` } };
let raw = p.kind === 'choose' ? txt(P['Variant ' + p.variant]) : p.text;
raw = String(raw || '').replace(/\n*\[did not pass review\]\s*$/, '').trim();
let subject = txt(P['Draft subject']), body = raw;
const m = raw.match(/^subject:\s*(.+)\n+/i);
if (m) { subject = m[1].trim(); body = raw.slice(m[0].length).trim(); }
if (!body) return { json: { ...base, action: 'notice', notice: '⚠️ <b>That variant is empty.</b> Pick another one or reply with your text.' } };
const chosen = p.kind === 'choose' ? p.variant : 'Edited';
const GREEN = ['Consent', 'Existing relationship', 'Inbound'];
const action = base.channel === 'LinkedIn' ? 'linkedin' : (GREEN.includes(base.legalBasis) ? 'send' : 'gmail_draft');
if (action !== 'linkedin' && !base.email) return { json: { ...base, action: 'notice', notice: `⚠️ <b>No email address for ${h(base.name)}.</b>` } };
return { json: { ...base, action, chosen, subject, body } };"""
node("Decide action (rules)","n8n-nodes-base.code",2,[1540,300],{"jsCode":DECIDE,"mode":"runOnceForEachItem"})
link("Notion · get contact","Decide action (rules)"); link("First match","Decide action (rules)")
node("Route","n8n-nodes-base.switch",3.2,[1760,300],{"mode":"rules","rules":{"values":[
  {"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"strict","version":2},"conditions":[{"leftValue":"={{ $json.action }}","rightValue":v,"operator":{"type":"string","operation":"equals"}}],"combinator":"and"},"renameOutput":True,"outputKey":v}
  for v in ["send","gmail_draft","linkedin","skip","notice","closed"]]},"options":{}})
link("Decide action (rules)","Route")
node("Gmail · send","n8n-nodes-base.gmail",2.1,[2000,60],{"resource":"message","operation":"send","sendTo":"={{ $json.email }}","subject":"={{ $json.subject }}","emailType":"text","message":"={{ $json.body }}","options":{"appendAttribution":False,"senderName":"Noah Hofmann"}},credentials=GM,onError="continueRegularOutput")
link("Route","Gmail · send",0)
node("Gmail · create draft","n8n-nodes-base.gmail",2.1,[2000,220],{"resource":"draft","operation":"create","subject":"={{ $json.subject }}","emailType":"text","message":"={{ $json.body }}","options":{"sendTo":"={{ $json.email }}"}},credentials=GM,onError="continueRegularOutput")
link("Route","Gmail · create draft",1)
OUT=H_JS+r"""
// Result -> Notion update + how to close the card. A decided card is EDITED into a one-line result and loses its
// buttons, so an open card (with buttons) always means "still needs you". Errors keep the card open + ❌ reply.
const d = $('Decide action (rules)').item.json;
const now = new Date().toISOString();
const hhmm = new Date().toLocaleTimeString('de-DE', { timeZone: 'Europe/Berlin', hour: '2-digit', minute: '2-digit' });
const t = s => [{ type: 'text', text: { content: String(s).slice(0, 1990) } }];
const err = $json.error ? String($json.error.message || $json.error).slice(0, 200) : null;
const who = `${h(d.name)}${d.company ? ' · ' + h(d.company) : ''}`;
const via = d.fromNotion ? ' · approved in Notion' : '';
let status, closeText = null, replyText = null, extra = {};
if (d.action === 'send') { status = err ? 'Awaiting approval' : 'Sent';
  if (err) replyText = `❌ <b>Sending failed · ${who}</b>\n${h(err)}\nThe card stays open: tap again later.`;
  else { closeText = `✅ <b>SENT · ${who}</b>\nVariant ${d.chosen} · ${hhmm}${via} · from hello@`; extra['Sent at'] = { date: { start: now } }; } }
else if (d.action === 'gmail_draft') { status = err ? 'Awaiting approval' : 'Gmail draft created';
  if (err) replyText = `❌ <b>Gmail draft failed · ${who}</b>\n${h(err)}\nThe card stays open: tap again later.`;
  else closeText = `📝 <b>GMAIL DRAFT · ${who}</b>\nVariant ${d.chosen} · ${hhmm}${via}\n👉 Open Gmail drafts (hello@), check, send.`; }
else if (d.action === 'linkedin') { status = 'Approved';
  closeText = `🔗 <b>LINKEDIN · ${who}</b>\nVariant ${d.chosen} · ${hhmm}${via} · text below 👇`;
  replyText = `🔗 <b>Paste into LinkedIn</b> (${h(d.linkedin)})\n\n${h(d.body)}`; }
else if (d.action === 'skip') { status = 'Skipped'; closeText = `⏭ <b>SKIPPED · ${who}</b>\n${hhmm}${via} · nothing will be sent.`; }
const props = { 'Status': { status: { name: status } },
  'Approval log': { rich_text: t(`${d.log ? d.log + '\n' : ''}${now.slice(0, 16)} ${d.action}${d.chosen ? ' ' + d.chosen : ''}${d.fromNotion ? ' (Notion)' : ''}${err ? ' ERROR ' + err : ''}`) } };
if (d.chosen && !err) Object.assign(props, { 'Chosen variant': { select: { name: d.chosen } }, 'Draft subject': { rich_text: t(d.subject || '') },
  'Draft body': { rich_text: t(d.body) }, 'Approved at': { date: { start: now } } });
Object.assign(props, extra);
return { json: { contactPageId: d.contactPageId, chatId: d.chatId, cardMessageId: d.cardMessageId, replyTo: d.replyTo,
  closeText, replyText, ok: !err, notionBody: { properties: props } } };"""
node("Build outcome","n8n-nodes-base.code",2,[2240,260],{"jsCode":OUT,"mode":"runOnceForEachItem"})
for src in ["Gmail · send","Gmail · create draft"]: link(src,"Build outcome")
link("Route","Build outcome",2); link("Route","Build outcome",3)
notion(node,"Notion · save outcome",[2460,260],"PATCH","=https://api.notion.com/v1/pages/{{ $json.contactPageId }}","={{ JSON.stringify($json.notionBody) }}",retryOnFail=True,maxTries=3,waitBetweenTries=2000)
link("Build outcome","Notion · save outcome")
B_ = "$('Build outcome').item.json"
node("Close card?","n8n-nodes-base.if",2.2,[2680,180],cond("={{ "+B_+".closeText || '' }}","notEmpty"))
link("Notion · save outcome","Close card?")
tgedit("Telegram · close card",[2900,120],"={{ "+B_+".closeText }}","={{ "+B_+".chatId }}","={{ "+B_+".cardMessageId }}")
link("Close card?","Telegram · close card",0)
node("Extra message?","n8n-nodes-base.if",2.2,[2680,380],cond("={{ "+B_+".replyText || '' }}","notEmpty"))
link("Notion · save outcome","Extra message?")
tgsend("Telegram · extra message",[2900,380],"={{ "+B_+".replyText }}","={{ "+B_+".chatId }}","={{ "+B_+".replyTo }}")
link("Extra message?","Telegram · extra message",0)
REFILL=r"""// ONE OUT, ONE IN: after you decided a card in Telegram, top up the queue right away (runs WP · 50).
// Not after Notion approvals (those come FROM 50: no loop), not after notices or errors.
const d = $('Decide action (rules)').first().json;
const ok = $('Build outcome').first().json.ok;
return (!d.fromNotion && ok && ['send', 'gmail_draft', 'linkedin', 'skip'].includes(d.action)) ? [{ json: { refill: true } }] : [];"""
node("Refill queue?","n8n-nodes-base.code",2,[3120,120],{"jsCode":REFILL})
link("Telegram · close card","Refill queue?")
node("Run WP · 50 (next card)","n8n-nodes-base.executeWorkflow",1.2,[3340,120],{"source":"database","workflowId":{"__rl":True,"value":WF_IDS["50"],"mode":"id"},"mode":"once","options":{"waitForSubWorkflow":False}},onError="continueRegularOutput")
link("Refill queue?","Run WP · 50 (next card)")
tgsend("Telegram · notice",[2000,520],"={{ $json.notice }}","={{ $json.chatId }}","={{ $json.replyTo }}")
link("Route","Telegram · notice",4)
tgedit("Telegram · close handled card",[2000,680],"={{ $json.closeText }}","={{ $json.chatId }}","={{ $json.cardMessageId }}")
link("Route","Telegram · close handled card",5)
node("Note · 51","n8n-nodes-base.stickyNote",1,[0,-420],{"width":1200,"height":380,"content":"""## WP · 51 Approval handler (Telegram trigger): what and why
**Input:** every tap and message in the approvals chat (and Notion approvals handed over by WP · 50). **Must be published.**
**Rule: you always get an answer.** Tap → toast "Got it ✔" + the card is **closed** (edited into a one-line result, buttons removed). Reply → result or a clear note. Anything unmatched → 🤔 help note. No answer = bug.
1. **Gate:** only Noah's chat id; anything else is ignored silently (security).
2. **Route update:** 🌐 website answers · replies to a card (own text) · taps (A/B/C/Edit/Skip) · unmatched.
3. **Idempotent:** acts only while the contact is *Awaiting approval*. A late/double tap closes the card as "Already handled", never a second email.
4. **Legal-basis gate:** Email + Consent/Existing relationship/Inbound → **sent**. Email + *None - draft only* (all article leads) → **Gmail draft** in hello@. LinkedIn → text to paste.
5. **Close + log:** Notion gets Status, Chosen variant, final text, timestamps, Approval log; the card is edited (✅/📝/🔗/⏭). Errors keep the card open with a ❌ reply.
6. **One out, one in:** after a decision, WP · 50 runs at once so the next card arrives.
Docs: docs/50-approval.md"""})
wf51={"name":"WP · 51 Approval handler (Telegram trigger)","nodes":apply_ids(N),"connections":C,"settings":{"executionOrder":"v1","timezone":"Europe/Berlin","saveManualExecutions":True},"pinData":{}}
json.dump(wf51,open(R+'workflows/51-approval-handler.json','w'),indent=2,ensure_ascii=False)
print(n50,len(N))
