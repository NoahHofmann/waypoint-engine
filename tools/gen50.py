import json, uuid
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
TG={"telegramApi":{"id":"","name":"Telegram approvals"}}
GM={"gmailOAuth2":{"id":"","name":"Gmail account"}}
TXT='const txt = p => { if (!p) return \'\'; const a = p.title || p.rich_text; if (a) return a.map(t => t.plain_text).join(\'\').trim(); return p.url || p.email || p.select?.name || p.status?.name || (p.number ?? \'\') + \'\'; };'

# ---------------- 50 · Approval cards ----------------
N,C,node,link=mk()
node("Run manually","n8n-nodes-base.manualTrigger",1,[0,100],{})
node("When called by orchestrator","n8n-nodes-base.executeWorkflowTrigger",1.1,[0,300],{"inputSource":"passthrough"})
node("Config","n8n-nodes-base.code",2,[220,200],{"jsCode":f"""// 50 · Approval cards: config
// maxOpenCards: never more than this many unanswered approval cards in the chat (prevents stacking).
// maxWebsiteQuestions: at most this many 'which website?' questions per run.
return [{{ json: {{ chatId: '{CHAT}', notionContactsDb: '349e3747aa894088a833ca4a76d6a1b2', notionCompaniesDb: '1247998a78a8446993afa06d9811c436', maxOpenCards: 5, maxWebsiteQuestions: 3 }} }}];"""})
link("Run manually","Config"); link("When called by orchestrator","Config")
notion(node,"Notion · approved in Notion",[440,-160],"POST","=https://api.notion.com/v1/databases/{{ $json.notionContactsDb }}/query",
  '={{ JSON.stringify({ filter: { and: [ { property: "Approve in Notion", select: { is_not_empty: true } }, { or: [ { property: "Status", status: { equals: "Awaiting approval" } }, { property: "Status", status: { equals: "Draft ready" } }, { property: "Status", status: { equals: "Check manually" } } ] } ] }, page_size: 20 }) }}',executeOnce=True)
link("Config","Notion · approved in Notion")
NAPP=TXT+r"""
// NOTION FALLBACK: you picked A/B/C/Skip in the column 'Approve in Notion' instead of tapping in Telegram.
// Each row is handed to WP · 51, which treats it exactly like a Telegram tap (same idempotency + legal-basis gate).
return ($input.first().json.results || []).map(pg => ({ json: {
  source: 'notion', contactPageId: pg.id, choice: txt(pg.properties['Approve in Notion']),
  cardMessageId: txt(pg.properties['Telegram message ID']) || null } }));"""
node("Notion approvals → 51",'n8n-nodes-base.code',2,[660,-160],{"jsCode":NAPP})
link("Notion · approved in Notion","Notion approvals → 51")
node("Run WP · 51 for each",'n8n-nodes-base.executeWorkflow',1.2,[880,-160],{"source":"database","workflowId":{"__rl":True,"value":"","mode":"list"},"mode":"each","options":{"waitForSubWorkflow":True}},onError="continueRegularOutput")
link("Notion approvals → 51","Run WP · 51 for each")
notion(node,"Notion · cards still open",[440,200],"POST","=https://api.notion.com/v1/databases/{{ $json.notionContactsDb }}/query",
  '={{ JSON.stringify({ filter: { property: "Status", status: { equals: "Awaiting approval" } }, page_size: 100 }) }}',executeOnce=True)
link("Config","Notion · cards still open")  # runs after the Notion-approval branch (canvas order, top first)
notion(node,"Notion · drafts ready",[660,200],"POST","=https://api.notion.com/v1/databases/{{ $('Config').first().json.notionContactsDb }}/query",
  '={{ JSON.stringify({ filter: { property: "Status", status: { equals: "Draft ready" } }, sorts: [{ timestamp: "created_time", direction: "ascending" }], page_size: 20 }) }}',executeOnce=True)
link("Notion · cards still open","Notion · drafts ready")
node("Pick drafts","n8n-nodes-base.code",2,[880,200],{"jsCode":TXT+"""
// STACK GUARD: only top up to maxOpenCards unanswered cards. If the chat is full, send nothing new
// (the drafts stay 'Draft ready' and go out after you answer the open ones).
const cfg = $('Config').first().json;
const open = ($('Notion · cards still open').first().json.results || []).length;
const room = Math.max(0, cfg.maxOpenCards - open);
const ready = ($input.first().json.results || []);
const take = ready.slice(0, room);
return take.map((pg, i) => { const P = pg.properties; return { json: {
  cardNo: open + i + 1, cardTotal: open + take.length, waiting: ready.length - take.length,
  contactPageId: pg.id, name: txt(P.Name), role: txt(P.Role), channel: txt(P.Channel) || 'Email', language: txt(P['Draft language']),
  offer: txt(P.Offer), email: txt(P.Email), linkedin: txt(P.LinkedIn), legalBasis: txt(P['Legal basis']) || 'None - draft only',
  passed: txt(P['Variants passed']), A: txt(P['Variant A']), B: txt(P['Variant B']), C: txt(P['Variant C']),
  companyPageId: P.Company?.relation?.[0]?.id || null } }; }).filter(i => i.json.companyPageId);"""})
link("Notion · drafts ready","Pick drafts")
notion(node,"Notion · get company",[1100,200],"GET","=https://api.notion.com/v1/pages/{{ $json.companyPageId }}")
link("Pick drafts","Notion · get company")
CARD=TXT+r"""
// Build the approval card (plain text, max 4096 chars) and the callback keys.
const c = $('Pick drafts').item.json;
const P = $json.properties || {};
const key = c.contactPageId.replace(/-/g, '');
const GREEN = ['Consent', 'Existing relationship', 'Inbound'];
const what = c.channel === 'LinkedIn' ? 'Approve = I send you the text to paste into LinkedIn (manual send).'
  : GREEN.includes(c.legalBasis) ? 'Approve = SENT from hello@ immediately.'
  : 'Approve = Gmail DRAFT in hello@ (legal basis "' + c.legalBasis + '"): you review and send it yourself.';
const clip = (s, n) => s.length > n ? s.slice(0, n) + '…' : s;
const head = [
  `📨 APPROVE ${c.cardNo}/${c.cardTotal} · ${txt(P.Company)} · ${c.name}${c.role ? ' (' + c.role + ')' : ''}`,
  '━━━━━━━━━━━━━━━━',
  `${c.channel} · ${c.language || 'EN'} · ICP ${txt(P['ICP score'])} · Offer: ${c.offer}`,
  `Signal: ${txt(P['Signal summary'])}`,
  `To: ${c.channel === 'Email' ? c.email : c.linkedin}`,
  what,
  `Passed review: ${c.passed || 'none'}`
].join('\n');
const variants = ['A', 'B', 'C'].map(id => `— ${id} —\n${clip(c[id] || '(empty)', 1000)}`).join('\n\n');
const foot = '✏️ Own version: reply to THIS card with the text (first line "Subject: …" for emails).' + (c.waiting ? `\n⏸ ${c.waiting} more draft(s) wait until open cards are answered.` : '');
const text = clip(head + '\n\n' + variants + '\n\n' + foot, 4000);
return { json: { ...c, key, text, company: txt(P.Company) } };"""
node("Build card","n8n-nodes-base.code",2,[1320,200],{"jsCode":CARD,"mode":"runOnceForEachItem"})
link("Notion · get company","Build card")
btn=lambda t,d: {"text":t,"additionalFields":{"callback_data":d}}
node("Telegram · send card","n8n-nodes-base.telegram",1.2,[1540,200],{
  "chatId":"={{ $('Config').first().json.chatId }}","text":"={{ $json.text }}",
  "replyMarkup":"inlineKeyboard",
  "inlineKeyboard":{"rows":[{"row":{"buttons":[btn("Send A","={{ 'v|' + $json.key + '|A' }}"),btn("Send B","={{ 'v|' + $json.key + '|B' }}"),btn("Send C","={{ 'v|' + $json.key + '|C' }}")]}},
                            {"row":{"buttons":[btn("✏️ Edit","={{ 'e|' + $json.key }}"),btn("⏭ Skip","={{ 's|' + $json.key }}")]}}]},
  "additionalFields":{"appendAttribution":False,"disable_web_page_preview":True}},credentials=TG,onError="continueRegularOutput")
link("Build card","Telegram · send card")
node("Build Notion update","n8n-nodes-base.code",2,[1760,200],{"jsCode":"""// Awaiting approval + the card's message id (idempotency key: a tap is only acted on while the status is Awaiting approval).
const c = $('Build card').item.json;
const id = $json.result?.message_id;
const t = s => [{ type: 'text', text: { content: String(s).slice(0, 1990) } }];
if (!id) return { json: { skip: true, contactPageId: c.contactPageId, error: JSON.stringify($json.error || $json).slice(0, 200) } };
return { json: { contactPageId: c.contactPageId, name: c.name, company: c.company, body: { properties: {
  'Status': { status: { name: 'Awaiting approval' } },
  'Telegram message ID': { rich_text: t(String(id)) },
  'Approval log': { rich_text: t(`${new Date().toISOString().slice(0, 16)} card sent (message ${id})`) } } } } };""","mode":"runOnceForEachItem"})
link("Telegram · send card","Build Notion update")
notion(node,"Notion · awaiting approval",[1980,200],"PATCH","=https://api.notion.com/v1/pages/{{ $json.contactPageId }}","={{ JSON.stringify($json.body) }}")
link("Build Notion update","Notion · awaiting approval")
notion(node,"Notion · companies without website",[440,620],"POST","=https://api.notion.com/v1/databases/{{ $('Config').first().json.notionCompaniesDb }}/query",
  '={{ JSON.stringify({ filter: { property: "Domain source", select: { equals: "Not found" } }, page_size: $("Config").first().json.maxWebsiteQuestions }) }}',executeOnce=True)
link("Config","Notion · companies without website")
WQ=TXT+r"""
// HUMAN FALLBACK for the website (last resort, kept rare): 30 tried ~30 likely domains and rejected all.
// One short question per company; reply with the domain. 'ref w|<key>' lets 51 find the company again.
return ($input.first().json.results || []).map(pg => { const P = pg.properties; const key = pg.id.replace(/-/g, '');
  const q = encodeURIComponent(txt(P.Company) + ' ' + txt(P['Signal summary']).slice(0, 60));
  return { json: { companyPageId: pg.id, key, company: txt(P.Company), google: 'https://www.google.com/search?q=' + q,
    text: [`🌐 WEBSITE? · ${txt(P.Company)}`, '━━━━━━━━━━━━━━━━', txt(P['Signal summary']), `Article: ${txt(P['Signal source'])}`, '',
      'I could not verify a website (all likely domains were parked, unrelated or empty).',
      '↩️ Reply to THIS message with the domain (e.g. acme.ai). I save it and re-run email search for its contacts.',
      `ref w|${key}`].join('\n') } }; });"""
node("Build website question","n8n-nodes-base.code",2,[660,620],{"jsCode":WQ})
link("Notion · companies without website","Build website question")
node("Telegram · ask website","n8n-nodes-base.telegram",1.2,[880,620],{
  "chatId":"={{ $('Config').first().json.chatId }}","text":"={{ $json.text }}","replyMarkup":"inlineKeyboard",
  "inlineKeyboard":{"rows":[{"row":{"buttons":[{"text":"🔎 Search","additionalFields":{"url":"={{ $json.google }}"}},btn("🚫 No website","={{ 'w|' + $json.key + '|none' }}")]}}]},
  "additionalFields":{"appendAttribution":False,"disable_web_page_preview":True}},credentials=TG,onError="continueRegularOutput")
link("Build website question","Telegram · ask website")
notion(node,"Notion · mark asked",[1100,620],"PATCH","=https://api.notion.com/v1/pages/{{ $('Build website question').item.json.companyPageId }}",
  '={{ JSON.stringify({ properties: { "Domain source": { select: { name: "Asked in Telegram" } } } }) }}',onError="continueRegularOutput")
link("Telegram · ask website","Notion · mark asked")
node("Note · 50 notion",'n8n-nodes-base.stickyNote',1,[400,-420],{"width":760,"height":220,"content":"""### 0 · Approvals made in Notion (runs first)
**In:** contacts where you set *Approve in Notion* (A/B/C/Skip) and Status is Awaiting approval, Draft ready or Check manually.
**Nodes:** Notion · approved in Notion → Notion approvals → 51 → Run WP · 51 for each (**select WP · 51 in this node once after import**).
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
wf50={"name":"WP · 50 Approval cards (sub-workflow)","nodes":N,"connections":C,"settings":{"executionOrder":"v1","timezone":"Europe/Berlin","saveManualExecutions":True},"pinData":{}}
json.dump(wf50,open(R+'workflows/50-approval-cards.json','w'),indent=2,ensure_ascii=False)
n50=len(N)

# ---------------- 51 · Approval handler ----------------
N,C,node,link=mk()
node("When called by 50 (Notion approval)","n8n-nodes-base.executeWorkflowTrigger",1.1,[-220,520],{"inputSource":"passthrough"})
FROMN=f"""// Turn a Notion approval into the same shape as a Telegram tap, so ONE code path decides.
const k = String($json.contactPageId || '').replace(/-/g, '');
const c = String($json.choice || '');
const data = c === 'Skip' ? 's|' + k : 'v|' + k + '|' + c;
return {{ json: {{ fromNotion: true, callback_query: {{ id: 'notion', data, message: {{ message_id: $json.cardMessageId ? Number($json.cardMessageId) : null, chat: {{ id: {CHAT} }} }} }} }} }};"""
node("Notion approval as tap","n8n-nodes-base.code",2,[0,520],{"jsCode":FROMN,"mode":"runOnceForEachItem"})
link("When called by 50 (Notion approval)","Notion approval as tap")
link("Notion approval as tap","Parse update (rules)")
node("Telegram trigger","n8n-nodes-base.telegramTrigger",1.1,[0,300],{"updates":["callback_query","message"],"additionalFields":{}},credentials=TG,webhookId=str(uuid.uuid4()))
PARSE=rf"""// Parse the Telegram update (rules). Only Noah's chat is accepted; everything else is ignored.
const u = $json; const ALLOWED = '{CHAT}';
const cb = u.callback_query; const msg = u.message;
const chatId = String(cb?.message?.chat?.id ?? msg?.chat?.id ?? '');
if (chatId !== ALLOWED) return {{ json: {{ ok: false, reason: 'unauthorized chat ' + chatId }} }};
if (cb) {{
  const [k, key, v] = String(cb.data || '').split('|');
  const kind = k === 'v' ? 'choose' : k === 'e' ? 'edit' : k === 's' ? 'skip' : k === 'w' ? 'website_none' : 'unknown';
  const id = key ? key.replace(/(.{{8}})(.{{4}})(.{{4}})(.{{4}})(.{{12}})/, '$1-$2-$3-$4-$5') : null;
  return {{ json: {{ ok: kind !== 'unknown' && !!id, fromNotion: !!u.fromNotion, kind, variant: v || null, contactPageId: kind === 'website_none' ? null : id, companyPageId: kind === 'website_none' ? id : null, callbackId: cb.id, cardMessageId: cb.message?.message_id, chatId }} }};
}}
// Reply to a 🌐 WEBSITE? question: the question carries 'ref w|<company key>'
const ref = String(msg?.reply_to_message?.text || '').match(/ref w\|([0-9a-f]{{32}})/);
if (msg && ref && msg.text) {{
  const dom = String(msg.text).trim().toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').split(/[\/\s]/)[0];
  const okDom = /^[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{{2,}}$/.test(dom);
  return {{ json: {{ ok: true, kind: okDom ? 'website' : 'website_bad', domain: dom, companyPageId: ref[1].replace(/(.{{8}})(.{{4}})(.{{4}})(.{{4}})(.{{12}})/, '$1-$2-$3-$4-$5'), cardMessageId: msg.message_id, chatId }} }};
}}
if (msg && msg.reply_to_message && msg.text) {{
  return {{ json: {{ ok: true, kind: 'reply', text: msg.text, cardMessageId: msg.reply_to_message.message_id, chatId }} }};
}}
return {{ json: {{ ok: false, reason: 'not a button tap or a reply to a card' }} }};"""
node("Parse update (rules)","n8n-nodes-base.code",2,[220,300],{"jsCode":PARSE,"mode":"runOnceForEachItem"})
link("Telegram trigger","Parse update (rules)")
node("Authorized?","n8n-nodes-base.if",2.2,[440,300],{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose","version":2},"conditions":[{"id":str(uuid.uuid4()),"leftValue":"={{ $json.ok }}","rightValue":True,"operator":{"type":"boolean","operation":"true","singleValue":True}}],"combinator":"and"},"options":{}})
link("Parse update (rules)","Authorized?")
node("Button or reply?","n8n-nodes-base.if",2.2,[660,300],{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose","version":2},"conditions":[{"id":str(uuid.uuid4()),"leftValue":"={{ $json.kind }}","rightValue":"reply","operator":{"type":"string","operation":"notEquals"}}],"combinator":"and"},"options":{}})
node("Website answer?","n8n-nodes-base.if",2.2,[550,560],{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose","version":2},"conditions":[{"id":str(uuid.uuid4()),"leftValue":"={{ $json.kind }}","rightValue":"website","operator":{"type":"string","operation":"startsWith"}}],"combinator":"and"},"options":{}})
link("Authorized?","Website answer?",0)
link("Website answer?","Button or reply?",1)
WEB=r"""// Website answer from Noah -> what to write to the company.
const p = $json;
if (p.kind === 'website_bad') return { json: { ...p, valid: false, notice: `"${p.domain}" doesn't look like a domain. Reply again with e.g. acme.ai` } };
const props = p.kind === 'website'
  ? { 'Domain': { url: 'https://' + p.domain }, 'Domain source': { select: { name: 'Manual' } } }
  : { 'Domain source': { select: { name: 'No website' } } };
return { json: { ...p, valid: true, notionBody: { properties: props },
  notice: p.kind === 'website' ? `✅ Saved ${p.domain}. Its contacts go back to email search on the next run.` : '🚫 Noted: no website. Contacts stay LinkedIn-only.' } };"""
node("Build website update","n8n-nodes-base.code",2,[770,620],{"jsCode":WEB,"mode":"runOnceForEachItem"})
link("Website answer?","Build website update",0)
node("Valid domain?","n8n-nodes-base.if",2.2,[990,620],{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose","version":2},"conditions":[{"id":str(uuid.uuid4()),"leftValue":"={{ $json.valid }}","rightValue":True,"operator":{"type":"boolean","operation":"true","singleValue":True}}],"combinator":"and"},"options":{}})
link("Build website update","Valid domain?")
notion(node,"Notion · save website",[1210,560],"PATCH","=https://api.notion.com/v1/pages/{{ $json.companyPageId }}","={{ JSON.stringify($json.notionBody) }}",onError="continueRegularOutput")
link("Valid domain?","Notion · save website",0)
notion(node,"Notion · contacts of company",[1430,560],"POST","https://api.notion.com/v1/databases/349e3747aa894088a833ca4a76d6a1b2/query",
  '={{ JSON.stringify({ filter: { and: [ { property: "Company", relation: { contains: $("Build website update").item.json.companyPageId } }, { or: [ { property: "Status", status: { equals: "Not reachable" } }, { property: "Status", status: { equals: "Check manually" } } ] } ] }, page_size: 20 }) }}',onError="continueRegularOutput")
link("Notion · save website","Notion · contacts of company")
REOPEN=r"""// Only when a domain was given: send this company's stuck contacts back to WP · 30 (Status Needs email).
const w = $('Build website update').item.json;
const rows = w.kind === 'website' ? ($input.first().json.results || []) : [];
return rows.map(pg => ({ json: { contactPageId: pg.id } }));"""
node("Contacts to retry","n8n-nodes-base.code",2,[1650,560],{"jsCode":REOPEN})
link("Notion · contacts of company","Contacts to retry")
notion(node,"Notion · back to Needs email",[1870,560],"PATCH","=https://api.notion.com/v1/pages/{{ $json.contactPageId }}",
  '={{ JSON.stringify({ properties: { Status: { status: { name: "Needs email" } } } }) }}',onError="continueRegularOutput")
link("Contacts to retry","Notion · back to Needs email")
node("Telegram · website reply","n8n-nodes-base.telegram",1.2,[1430,760],{"chatId":"={{ $('Build website update').item.json.chatId }}","text":"={{ $('Build website update').item.json.notice }}","additionalFields":{"appendAttribution":False,"disable_web_page_preview":True,"reply_to_message_id":"={{ $('Build website update').item.json.cardMessageId }}"}},credentials=TG,onError="continueRegularOutput")
link("Notion · save website","Telegram · website reply")
link("Valid domain?","Telegram · website reply",1)
node("Telegram · answer tap","n8n-nodes-base.telegram",1.2,[880,200],{"resource":"callback","operation":"answerQuery","queryId":"={{ $json.callbackId }}","additionalFields":{"text":"Got it"}},credentials=TG,onError="continueRegularOutput")
link("Button or reply?","Telegram · answer tap",0)
notion(node,"Notion · get contact",[1100,200],"GET","=https://api.notion.com/v1/pages/{{ $('Parse update (rules)').item.json.contactPageId }}")
link("Telegram · answer tap","Notion · get contact")
notion(node,"Notion · find contact by card",[880,420],"POST","https://api.notion.com/v1/databases/349e3747aa894088a833ca4a76d6a1b2/query",
  '={{ JSON.stringify({ filter: { property: "Telegram message ID", rich_text: { equals: String($json.cardMessageId) } }, page_size: 1 }) }}')
link("Button or reply?","Notion · find contact by card",1)
node("First match","n8n-nodes-base.code",2,[1100,420],{"jsCode":"// Reply path: the replied-to card identifies the contact.\nconst pg = ($json.results || [])[0];\nreturn { json: pg || { notFound: true } };","mode":"runOnceForEachItem"})
link("Notion · find contact by card","First match")
DECIDE=TXT+r"""
// Decide what to do (rules). Idempotent: acts only while Status is "Awaiting approval".
// Legal-basis gate: only Consent / Existing relationship / Inbound may be sent automatically.
const p = $('Parse update (rules)').item.json;
const pg = $json;
if (pg.notFound || !pg.properties) return { json: { action: 'notice', chatId: p.chatId, cardMessageId: p.cardMessageId, notice: 'Could not find the contact for this card.' } };
const P = pg.properties;
const status = txt(P.Status);
const base = { contactPageId: pg.id, chatId: p.chatId, cardMessageId: p.cardMessageId, name: txt(P.Name), channel: txt(P.Channel) || 'Email',
  email: txt(P.Email), linkedin: txt(P.LinkedIn), legalBasis: txt(P['Legal basis']) || 'None - draft only', log: txt(P['Approval log']) };
// From Notion you may also approve a draft before its card went out, or a 'Check manually' draft.
const allowed = p.fromNotion ? ['Awaiting approval', 'Draft ready', 'Check manually'] : ['Awaiting approval'];
if (!allowed.includes(status)) return { json: { ...base, action: 'notice', notice: `Already handled: ${base.name} is "${status}". Nothing was sent again.` } };
if (p.kind === 'skip') return { json: { ...base, action: 'skip' } };
if (p.kind === 'edit') return { json: { ...base, action: 'notice', notice: `Reply to the card for ${base.name} with your text (first line "Subject: …" for emails). I'll send that version.` } };
// The chosen text: a variant, or Noah's own reply
let raw = p.kind === 'choose' ? txt(P['Variant ' + p.variant]) : p.text;
raw = String(raw || '').replace(/\n*\[did not pass review\]\s*$/, '').trim();
let subject = txt(P['Draft subject']), body = raw;
const m = raw.match(/^subject:\s*(.+)\n+/i);
if (m) { subject = m[1].trim(); body = raw.slice(m[0].length).trim(); }
if (!body) return { json: { ...base, action: 'notice', notice: 'That variant is empty. Pick another one or reply with your text.' } };
const chosen = p.kind === 'choose' ? p.variant : 'Edited';
base.via = p.fromNotion ? ' (approved in Notion)' : '';
const GREEN = ['Consent', 'Existing relationship', 'Inbound'];
const action = base.channel === 'LinkedIn' ? 'linkedin' : (GREEN.includes(base.legalBasis) ? 'send' : 'gmail_draft');
if (action !== 'linkedin' && !base.email) return { json: { ...base, action: 'notice', notice: `No email address for ${base.name}.` } };
return { json: { ...base, action, chosen, subject, body } };"""
node("Decide action (rules)","n8n-nodes-base.code",2,[1320,300],{"jsCode":DECIDE,"mode":"runOnceForEachItem"})
link("Notion · get contact","Decide action (rules)"); link("First match","Decide action (rules)")
node("Route","n8n-nodes-base.switch",3.2,[1540,300],{"mode":"rules","rules":{"values":[
  {"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"strict","version":2},"conditions":[{"leftValue":"={{ $json.action }}","rightValue":v,"operator":{"type":"string","operation":"equals"}}],"combinator":"and"},"renameOutput":True,"outputKey":v}
  for v in ["send","gmail_draft","linkedin","skip","notice"]]},"options":{}})
link("Decide action (rules)","Route")
node("Gmail · send","n8n-nodes-base.gmail",2.1,[1780,0],{"resource":"message","operation":"send","sendTo":"={{ $json.email }}","subject":"={{ $json.subject }}","emailType":"text","message":"={{ $json.body }}","options":{"appendAttribution":False,"senderName":"Noah Hofmann"}},credentials=GM,onError="continueRegularOutput")
link("Route","Gmail · send",0)
node("Gmail · create draft","n8n-nodes-base.gmail",2.1,[1780,160],{"resource":"draft","operation":"create","subject":"={{ $json.subject }}","emailType":"text","message":"={{ $json.body }}","options":{"sendTo":"={{ $json.email }}"}},credentials=GM,onError="continueRegularOutput")
link("Route","Gmail · create draft",1)
OUT=r"""// Result -> Notion update + Telegram confirmation. One node for all outcomes keeps the log consistent.
const d = $('Decide action (rules)').item.json;
const now = new Date().toISOString();
const t = s => [{ type: 'text', text: { content: String(s).slice(0, 1990) } }];
const err = $json.error ? String($json.error.message || $json.error).slice(0, 200) : null;
let status, msg, extra = {};
if (d.action === 'send') { status = err ? 'Awaiting approval' : 'Sent'; msg = err ? `❌ Sending failed for ${d.name}: ${err}` : `✅ Sent to ${d.name} (${d.email}), variant ${d.chosen}${d.via || ''}.`; if (!err) extra['Sent at'] = { date: { start: now } }; }
else if (d.action === 'gmail_draft') { status = err ? 'Awaiting approval' : 'Gmail draft created'; msg = err ? `❌ Gmail draft failed for ${d.name}: ${err}` : `📝 Gmail draft for ${d.name} is ready in hello@ (variant ${d.chosen}${d.via || ''}). Open Gmail, check it, send it yourself.`; }
else if (d.action === 'linkedin') { status = 'Approved'; msg = `🔗 LinkedIn for ${d.name}: ${d.linkedin}\nCopy and paste (variant ${d.chosen}):\n\n${d.body}`; }
else if (d.action === 'skip') { status = 'Skipped'; msg = `⏭ Skipped ${d.name}. No message will be sent.`; }
const props = { 'Status': { status: { name: status } },
  'Approval log': { rich_text: t(`${d.log ? d.log + '\n' : ''}${now.slice(0, 16)} ${d.action}${d.chosen ? ' ' + d.chosen : ''}${err ? ' ERROR ' + err : ''}`) } };
if (d.chosen && !err) Object.assign(props, { 'Chosen variant': { select: { name: d.chosen } }, 'Draft subject': { rich_text: t(d.subject || '') },
  'Draft body': { rich_text: t(d.body) }, 'Approved at': { date: { start: now } } });
Object.assign(props, extra);
return { json: { contactPageId: d.contactPageId, chatId: d.chatId, cardMessageId: d.cardMessageId, message: msg, notionBody: { properties: props } } };"""
node("Build outcome","n8n-nodes-base.code",2,[2020,200],{"jsCode":OUT,"mode":"runOnceForEachItem"})
for src,o in [("Gmail · send",None),("Gmail · create draft",None)]: link(src,"Build outcome")
link("Route","Build outcome",2); link("Route","Build outcome",3)
notion(node,"Notion · save outcome",[2240,200],"PATCH","=https://api.notion.com/v1/pages/{{ $json.contactPageId }}","={{ JSON.stringify($json.notionBody) }}",retryOnFail=True,maxTries=3,waitBetweenTries=2000)
link("Build outcome","Notion · save outcome")
def tgsend(name,pos,textexpr,src_chat):
    node(name,"n8n-nodes-base.telegram",1.2,pos,{"chatId":src_chat,"text":textexpr,"additionalFields":{"appendAttribution":False,"disable_web_page_preview":True,"reply_to_message_id":"={{ $json.cardMessageId }}"}},credentials=TG,onError="continueRegularOutput")
tgsend("Telegram · confirm",[2460,200],"={{ $('Build outcome').item.json.message }}","={{ $('Build outcome').item.json.chatId }}")
link("Notion · save outcome","Telegram · confirm")
tgsend("Telegram · notice",[1780,480],"={{ $json.notice }}","={{ $json.chatId }}")
link("Route","Telegram · notice",4)
node("Note · 51","n8n-nodes-base.stickyNote",1,[0,-380],{"width":1100,"height":330,"content":"""## WP · 51 Approval handler (Telegram trigger): what and why
Handles taps on the cards from WP · 50 and replies to them. **Must be published (active)** so Telegram can reach it.
1. **Only Noah's chat** (id in *Parse update*) is accepted; anything else is ignored.
2. **Idempotent:** acts only while the contact is *Awaiting approval*. A double tap or a late tap gets "Already handled", never a second email.
3. **Legal-basis gate:** Email + Consent / Existing relationship / Inbound → **sent** from hello@. Email + *None - draft only* (all article-sourced leads) → **Gmail draft** in hello@ that you send yourself. LinkedIn → the text comes back to you to paste (LinkedIn has no sending API for this).
4. **Edit:** reply to the card with your own text (first line "Subject: …"); that version goes through the same gate as *Chosen variant = Edited*.
5. **🌐 WEBSITE? answers** (bottom branch): reply with a domain → Companies.Domain (*Manual*) + that company's *Not reachable*/*Check manually* contacts back to *Needs email*. 🚫 No website → Domain source *No website*.
6. Every outcome writes Status, Chosen variant, final subject/body, Approved/Sent at and an *Approval log* line to Notion, and confirms in Telegram.
Docs: docs/50-approval.md"""})
wf51={"name":"WP · 51 Approval handler (Telegram trigger)","nodes":N,"connections":C,"settings":{"executionOrder":"v1","timezone":"Europe/Berlin","saveManualExecutions":True,"errorWorkflow":""},"pinData":{}}
json.dump(wf51,open(R+'workflows/51-approval-handler.json','w'),indent=2,ensure_ascii=False)
print(n50,len(N))
