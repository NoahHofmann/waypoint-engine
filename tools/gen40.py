import json, uuid, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runlog import runlog_code, runlog_http_params, REMEMBER, apply_ids, WF_ERROR
import os
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
N=[]; C={}
def node(name,typ,ver,pos,params,**kw):
    n={"id":str(uuid.uuid4()),"name":name,"type":typ,"typeVersion":ver,"position":pos,"parameters":params}; n.update(kw); N.append(n); return name
def link(a,b,out=0,inp=0,kind="main"):
    C.setdefault(a,{}).setdefault(kind,[]); m=C[a][kind]
    while len(m)<=out: m.append([])
    m[out].append({"node":b,"type":kind,"index":inp})
NH={"sendHeaders":True,"headerParameters":{"parameters":[{"name":"Notion-Version","value":"2022-06-28"}]}}
def notion(name,pos,method,url,body=None,**kw):
    p={"method":method,"url":url,"authentication":"predefinedCredentialType","nodeCredentialType":"notionApi",**NH,"options":{}}
    if body: p.update({"sendBody":True,"specifyBody":"json","jsonBody":body})
    return node(name,"n8n-nodes-base.httpRequest",4.2,pos,p,**kw)
def ifnode(name,pos,left,op,right=""):
    o={"type":"boolean","operation":"true","singleValue":True} if op=="true" else {"type":"string","operation":op,"singleValue":True}
    return node(name,"n8n-nodes-base.if",2.2,pos,{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose","version":2},"conditions":[{"id":str(uuid.uuid4()),"leftValue":left,"rightValue":right,"operator":o}],"combinator":"and"},"options":{}})

node("Run manually","n8n-nodes-base.manualTrigger",1,[0,100],{})
node("When called by orchestrator","n8n-nodes-base.executeWorkflowTrigger",1.1,[0,300],{"inputSource":"passthrough"})
CONFIG=r"""// 40 · Draft + judge: configuration. Everything a reviewer may want to change lives here.
return [{ json: {
  startedAt: new Date().toISOString(),
  notionContactsDb: '349e3747aa894088a833ca4a76d6a1b2',
  notionOffersDb: '5618b11e453a4704a41fb530812f110a',
  maxDraftsPerRun: 8,
  // Models are preset in the model nodes (sub-nodes under each Draft/Judge chain). These lines document them.
  draftModel: 'claude-sonnet-5-5', // 'Claude · draft 1/2'. Change here AND in the two sub-nodes when switching models
  judgeModel: 'gpt-5-mini',         // 'OpenAI · judge 1/2', reasoning effort low. Why: a different model family grades the draft (no self-grading)
  calLink: 'https://cal.com/book-a-call-with-noah/30min',
  promptVersion: 'draft-v7 / judge-v5',
  playbookPageId: '3fa64e3c573c81bb9e99da3b6be520c1',   // Notion › Sales Playbook (edit there)
  // NOAH PROFILE: the ONLY facts about Noah a draft may use (canonical metrics, project instructions).
  profile: [
    'Noah Hofmann, Berlin. Works with early-stage B2B startups on market entry, go-to-market and partnerships (Waypoint).',
    'Techstars, Partnerships Manager EMEA & APAC: built a $14M partnership pipeline in 24 months; ran market-entry campaigns incl. Japan, CEE, South Africa, Nigeria and the Gulf region.',
    'Hive, Senior Account Manager: 94–99% quota attainment in Q3/Q4.',
    'Qualas, co-founder & CEO (B2B SaaS): two prototypes in under nine months, 3 LOIs before launch, 130+ Product Hunt upvotes.',
    'Sigma Squared Summit, co-managing director: €100K-value conference for 300 attendees over 3 days on zero cash budget.'
  ]
} }];"""
node("Config","n8n-nodes-base.code",2,[220,200],{"jsCode":CONFIG})
link("Run manually","Config"); link("When called by orchestrator","Config")
notion("Notion · active offers",[440,200],"POST","=https://api.notion.com/v1/databases/{{ $json.notionOffersDb }}/query",
  '={{ JSON.stringify({ filter: { property: "Active", checkbox: { equals: true } }, sorts: [{ property: "Priority", direction: "ascending" }] }) }}',executeOnce=True)
link("Config","Notion · active offers")
notion("Notion · sales playbook",[440,0],"GET","=https://api.notion.com/v1/blocks/{{ $('Config').first().json.playbookPageId }}/children?page_size=100",executeOnce=True)
notion("Notion · contacts to draft",[660,200],"POST","=https://api.notion.com/v1/databases/{{ $('Config').first().json.notionContactsDb }}/query",
  '={{ JSON.stringify({ filter: { or: [ { property: "Status", status: { equals: "Ready to draft" } }, { property: "Status", status: { equals: "LinkedIn only" } } ] }, sorts: [{ timestamp: "created_time", direction: "ascending" }], page_size: $("Config").first().json.maxDraftsPerRun }) }}',executeOnce=True)
link("Notion · active offers","Notion · sales playbook")
link("Notion · sales playbook","Notion · contacts to draft")
PICK=r"""// One item per contact that has a verified channel and no draft yet.
const txt = p => { if (!p) return ''; const a = p.title || p.rich_text; if (a) return a.map(t => t.plain_text).join('').trim(); return p.url || p.email || p.select?.name || p.status?.name || (p.number ?? '') + ''; };
return ($input.first().json.results || []).map(pg => {
  const P = pg.properties;
  const name = txt(P.Name).replace(/^((dr|prof)\.?\s+)+/i, '');
  return { json: {
    contactPageId: pg.id, name, first: name.split(' ')[0], role: txt(P.Role),
    email: txt(P.Email), linkedin: txt(P.LinkedIn), status: txt(P.Status),
    draftVersion: Number(txt(P['Draft version'])) || 0,
    companyPageId: P.Company?.relation?.[0]?.id || null
  } };
}).filter(i => i.json.companyPageId);"""
node("Pick contacts","n8n-nodes-base.code",2,[880,200],{"jsCode":PICK})
link("Notion · contacts to draft","Pick contacts")
notion("Notion · get company",[1100,200],"GET","=https://api.notion.com/v1/pages/{{ $json.companyPageId }}")
link("Pick contacts","Notion · get company")
for nm,x,url in [("Fetch article",1100,"={{ $json.properties?.['Signal source']?.url || 'https://invalid.invalid' }}"),("Fetch homepage",1320,"={{ $('Notion · get company').item.json.properties?.Domain?.url || 'https://invalid.invalid' }}")]:
    node(nm,"n8n-nodes-base.httpRequest",4.2,[x,420],{"method":"GET","url":url,
      "sendHeaders":True,"headerParameters":{"parameters":[{"name":"User-Agent","value":"Mozilla/5.0 (compatible; WaypointResearch/1.0; +https://noahhofmann.com)"}]},
      "options":{"timeout":10000,"response":{"response":{"neverError":True,"responseFormat":"text","outputPropertyName":"html"}}}},onError="continueRegularOutput")
BRIEF=r"""// Build the BRIEF (rules, no LLM): channel, language, offer and the only facts the draft may use.
const cfg = $('Config').first().json;
const c = $('Pick contacts').item.json;
const P = $('Notion · get company').item.json.properties || {};
// Article + homepage text give the model real hooks (product, customers, plans). Paragraphs only, capped.
const decode = s => String(s || '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&#8217;|&rsquo;/g, "'").replace(/&#8220;|&#8221;|&ldquo;|&rdquo;/g, '"').replace(/&#(\d+);/g, (m, n) => String.fromCharCode(+n)).replace(/&[a-z]+;/gi, ' ');
const paras = html => [...String(html || '').replace(/<(script|style|nav|header|footer|aside|form)[\s\S]*?<\/\1>/gi, ' ').matchAll(/<p[^>]*>([\s\S]*?)<\/p>/gi)]
  .map(m => decode(m[1].replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim()).filter(t => t.length >= 60);
const articleText = paras($('Fetch article').item.json.html).join(' ').slice(0, 3500);
const hp = String($('Fetch homepage').item.json.html || '');
const hpTitle = decode((hp.match(/<title[^>]*>([\s\S]*?)<\/title>/i) || [])[1] || '').trim();
const hpDesc = decode((hp.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']+)/i) || hp.match(/<meta[^>]+property=["']og:description["'][^>]+content=["']([^"']+)/i) || [])[1] || '').trim();
const homepageText = [hpTitle, hpDesc, paras(hp).slice(0, 3).join(' ')].filter(Boolean).join(' · ').slice(0, 800);
const txt = p => { if (!p) return ''; const a = p.title || p.rich_text; if (a) return a.map(t => t.plain_text).join('').trim(); return p.url || p.email || p.select?.name || (p.number ?? '') + ''; };
const company = txt(P.Company), country = txt(P.Country);
const reasons = txt(P['Qualify reasons']);
const summary = reasons.split('\n').filter(Boolean).pop() || '';
const evidence = txt(P.Evidence);
// Channel follows the verified data: valid email -> Email, verified LinkedIn only -> LinkedIn
const channel = c.status === 'Ready to draft' && c.email ? 'Email' : 'LinkedIn';
const language = ['DE', 'AT', 'CH'].includes(country) ? 'DE' : 'EN';
// Sales playbook from Notion (headings, paragraphs, bullets), read live on every run
const playbook = ($('Notion · sales playbook').first().json.results || []).map(b => {
  const rt = b[b.type]?.rich_text || []; const t = rt.map(r => r.plain_text).join('');
  return !t ? '' : b.type.startsWith('heading') ? '\n## ' + t : (b.type.includes('list') ? '- ' + t : t);
}).filter(Boolean).join('\n');
// Offer by rules (see docs/40-draft-judge.md): partnerships signal -> Fractional Partnerships Lead;
// DACH company -> GTM Strategy & ICP Sprint; everyone else -> Market Entry & Expansion (into DACH)
const offers = ($('Notion · active offers').first().json.results || []).map(o => ({
  name: txt(o.properties.Offer), promise: txt(o.properties.Promise), forWhom: txt(o.properties['For whom']) }));
const hay = (evidence + ' ' + summary).toLowerCase();
const want = /partner|channel|distribution|resell/.test(hay) ? 'Fractional Partnerships Lead'
  : ['DE', 'AT', 'CH'].includes(country) ? 'GTM Strategy & ICP Sprint' : 'Market Entry & Expansion';
const offer = offers.find(o => o.name === want) || offers[0] || { name: want, promise: '', forWhom: '' };
const bookingLink = `${cfg.calLink}?metadata[contact]=${c.contactPageId.replace(/-/g, '')}`;
const facts = [
  `Recipient: ${c.name}${c.role ? ', ' + c.role : ''} at ${company}`,
  `Company: ${company}${country ? ' (HQ: ' + country + ')' : ''}${txt(P.Sector) ? ', sector: ' + txt(P.Sector) : ''}`,
  txt(P.Round) && txt(P.Round) !== 'Unknown' ? `Round: ${txt(P.Round)}${txt(P['Amount EUR']) ? ', about €' + Math.round(Number(txt(P['Amount EUR'])) / 1e5) / 10 + 'M' : ''}` : '',
  `News: ${txt(P['Signal summary'])} (${txt(P['Signal date']) || P['Signal date']?.date?.start || ''})`,
  summary ? `Summary: ${summary}` : '',
  evidence ? `Verbatim quotes from the article:\n${evidence}` : '',
  articleText ? `Article excerpt (source: ${txt(P['Signal source'])}):\n${articleText}` : '',
  homepageText ? `Company homepage (${txt(P.Domain)}): ${homepageText}` : ''
].filter(Boolean).join('\n');
const briefText = [
  `CHANNEL: ${channel}`, `LANGUAGE: ${language}`,
  channel === 'Email' ? `BOOKING LINK (use exactly): ${bookingLink}` : 'NO LINK (LinkedIn connection note)',
  '', 'COMPANY FACTS:', facts,
  '', 'NOAH PROFILE:', ...cfg.profile.map(p => '- ' + p),
  '', `OFFER: ${offer.name}. Outcome: ${offer.promise} For: ${offer.forWhom}`,
  '', 'SALES PLAYBOOK:', playbook || '(playbook not loaded: follow the rules in the system prompt)'
].join('\n');
return { json: { ...c, company, country, channel, language, offer: offer.name, bookingLink, briefText, playbookLoaded: !!playbook,
  allowedText: facts + ' ' + cfg.profile.join(' ') + ' ' + bookingLink, feedback: '', attempt: 1 } };"""
node("Build brief (rules)","n8n-nodes-base.code",2,[1320,200],{"jsCode":BRIEF,"mode":"runOnceForEachItem"})
link("Notion · get company","Fetch article")
link("Fetch article","Fetch homepage")
link("Fetch homepage","Build brief (rules)")

DRAFT_SYS=open(R+'prompts/draft.md').read()
JUDGE_SYS=open(R+'prompts/judge.md').read()
DSCHEMA=json.dumps({"type":"object","required":["variants"],"properties":{"company_one_liner":{"type":["string","null"]},"variants":{"type":"array","items":{"type":"object","properties":{"id":{"type":"string"},"subject":{"type":["string","null"]},"body":{"type":"string"}}}}}},indent=2)
JSCHEMA=json.dumps({"type":"object","required":["variants"],"properties":{"variants":{"type":"array","items":{"type":"object","properties":{"id":{"type":"string"},"unsupported_claims":{"type":["array","null"],"items":{"type":"string"}},"names_ok":{"type":["boolean","null"]},"language_ok":{"type":["boolean","null"]},"specific_opening":{"type":["boolean","null"]},"tone_ok":{"type":["boolean","null"]},"playbook_violations":{"type":["array","null"],"items":{"type":"string"}},"notes":{"type":["string","null"]},"score_hook":{"type":["number","null"]},"score_relevance":{"type":["number","null"]},"score_natural":{"type":["number","null"]},"score_ask":{"type":["number","null"]}}}}}},indent=2)

CHECK=r"""// Code checks for EACH variant before the judge: format, link, opt-out, no number outside the brief,
// and Noah's rule that the funding round is never the headline.
const b = $('Build brief (rules)').item.json;
const prev = %PREV%;
// Tolerant JSON parse: Claude often writes real line breaks inside JSON strings (valid prose, invalid JSON).
// v6 used n8n's structured parser -> every multi-paragraph email failed to parse -> 'Variant missing' (16 Oct).
function parseLoose(t) {
  if (t && typeof t === 'object') return t;
  t = String(t || ''); const a = t.indexOf('{'), z = t.lastIndexOf('}');
  if (a < 0 || z < a) return {};
  const j = t.slice(a, z + 1);
  try { return JSON.parse(j); } catch (e) {}
  let out = '', inStr = false, esc = false;
  for (const ch of j) {
    if (inStr) {
      if (esc) { esc = false; out += ch; continue; }
      if (ch === '\\') { esc = true; out += ch; continue; }
      if (ch === '"') { inStr = false; out += ch; continue; }
      if (ch === '\n') { out += '\\n'; continue; }
      if (ch === '\r') continue;
      if (ch === '\t') { out += '\\t'; continue; }
      out += ch;
    } else { if (ch === '"') inStr = true; out += ch; }
  }
  try { return JSON.parse(out); } catch (e) { return {}; }
}
// draft-v7: plain-text sections (=== A === / SUBJECT: / body). JSON broke on Claude's quotes and newlines.
function parseSections(t) {
  t = String(t || '').replace(/\r/g, '').replace(/^```[a-z]*\n?|```\s*$/gm, '');
  if (!/===\s*A\s*===/i.test(t)) return null;
  const one = (t.match(/ONE-LINER:\s*(.+)/i) || [])[1] || '';
  const variants = [];
  const re = /===\s*([ABC])\s*===\s*\n([\s\S]*?)(?====\s*(?:[ABC]|END)\s*===|$)/gi;
  let m;
  while ((m = re.exec(t))) {
    let block = m[2].replace(/^\s*\n/, '');
    let subject = '';
    const sm = block.match(/^\s*SUBJECT:[ \t]*(.*)\n?/i);
    if (sm) { subject = sm[1].trim(); block = block.slice(sm[0].length); }
    variants.push({ id: m[1].toUpperCase(), subject, body: block.trim() });
  }
  return { company_one_liner: one.trim(), variants };
}
const rawText = String($json.text ?? (typeof $json.output === 'string' ? $json.output : '') ?? '');
const parsed = $json.output?.variants ? $json.output : (parseSections(rawText) || parseLoose(rawText || $json.output || $json.response));
const raw = (parsed.variants || []).filter(v => v && v.body);
const words = s => String(s).trim().split(/\s+/).filter(Boolean).length;
const HYPE = /(revolutionary|game[- ]changing|synergy|leverage|unlock|skyrocket|hope this (email )?finds you|congratulations|congrats|herzlichen glückwunsch|gratuliere|startups like yours|companies like yours|teams like yours|i specialize in|is exciting|impressive)/i;
const FUNDING = /(rais|funding|round|series [a-c]|seed|investment|finanzierung|runde|investor|€|\$|million|mio)/i;
const allowed = b.allowedText.replace(/[.,\s]/g, '');
const variants = ['A', 'B', 'C'].map(id => {
  const v = raw.find(x => String(x.id).toUpperCase().startsWith(id)) || null;
  const issues = [];
  if (!v) return { id, subject: '', body: '', issues: ['Variant missing' + (id === 'A' ? ' · model output: ' + (rawText ? rawText.slice(0, 300).replace(/\s+/g, ' ') : ($json.error ? 'ERROR ' + JSON.stringify($json.error).slice(0, 300) : 'empty')) : '')] };
  const body = String(v.body), subject = b.channel === 'Email' ? String(v.subject || '') : '';
  if (b.channel === 'Email') {
    if (words(subject) < 3 || words(subject) > 7) issues.push(`Subject has ${words(subject)} words (3-7)`);
    if (FUNDING.test(subject)) issues.push('Subject mentions the funding round');
    const core = body.split(b.bookingLink)[0];
    const [lo, hi] = id === 'C' ? [25, 60] : [55, 120];
    if (words(core) < lo || words(core) > hi) issues.push(`Body has ${words(core)} words before the link (${id === 'C' ? '25-55' : '60-110'})`);
    if (!body.includes(b.bookingLink)) issues.push('Booking link missing or altered');
    // Formatting: greeting, 2+ paragraphs and the ask must be separated by blank lines (one GPT draft arrived as a wall of text)
    if ((core.match(/\n[ \t]*\n/g) || []).length < 2) issues.push('Formatting: no blank lines between greeting, paragraphs and ask');
    if (!/won't follow up|melde ich mich nicht wieder/i.test(body)) issues.push('Opt-out line missing');
    if (!body.includes('noahhofmann.com/waypoint')) issues.push('Sign-off missing');
  } else {
    if (body.length > 200) issues.push(`LinkedIn note has ${body.length} characters (max 200, aim for 180)`);
    if ((body.match(/\?/g) || []).length) issues.push('LinkedIn note asks a question; the connect request is the ask');
    if (/https?:\/\//.test(body)) issues.push('LinkedIn note must not contain a link');
  }
  if (!body.includes(b.first)) issues.push(`First name "${b.first}" not used`);
  if (b.language === 'DE' && /(?<=[a-zäöüß,] )(Sie|Ihnen|Ihr|Ihre|Ihrem|Ihren|Ihres)\b/.test(body)) issues.push('German draft uses "Sie" instead of "du"');
  // First sentence after the greeting must not be about the funding round
  const firstSentence = (body.replace(/^\s*(hi|hallo|hey)[^,\n]*,?\s*/i, '').split(/(?<=[.!?])\s/)[0] || '');
  if (FUNDING.test(firstSentence)) issues.push('Opens with the funding round');
  if (HYPE.test(body + ' ' + subject)) issues.push('Hype, flattery or filler: ' + (body + ' ' + subject).match(HYPE)[0]);
  const nums = (subject + ' ' + body.replace(b.bookingLink, '')).match(/\d[\d.,]*/g) || [];
  const bad = [...new Set(nums.map(n => n.replace(/[.,]$/, '')))].filter(n => n && !allowed.includes(n.replace(/[.,]/g, '')) && !['1', '2', '3', '20', '30'].includes(n));
  if (bad.length) issues.push('Numbers not in the brief: ' + bad.join(', '));
  return { id, subject, body, issues };
});
// The three variants must not all end with the same ask
const asks = variants.map(v => (v.body.match(/[^.!?\n]*\?/g) || []).pop() || '');
// No-oriented question ("bad idea", "crazy") allowed in at most one variant: in v4 it was in nearly every email
let noSeen = 0;
variants.forEach((v, i) => { if (/bad idea|crazy|schlechte idee|verrückt/i.test(asks[i])) { noSeen++; if (noSeen > 1) v.issues.push('Same no-oriented question as another variant ("bad idea"/"crazy"); use a plain, specific question'); } });
// Template self-intro (was in every v4 email)
variants.forEach(v => { if (/\bI help (funded |early[- ]stage )?(B2B )?(founders|CEOs|teams|startups)\b/i.test(v.body)) v.issues.push('Generic self-intro "I help funded B2B …"; say what Noah would do for THIS company'); });
return { json: { ...prev, variants, parseFailed: raw.length === 0, oneLiner: String(parsed.company_one_liner || '').slice(0, 200) } };"""
DECIDE=r"""// Combine code checks and judge per variant. A variant passes only if BOTH are clean.
// The contact is ready if at least one variant passes; Noah picks which one to send in 50.
const p = $('%CHECK%').item.json;
// Judge 2 is Claude without an output parser (n8n's parser broke on Claude's JSON): parse the text tolerantly.
function parseLoose(t) {
  if (t && typeof t === 'object') return t;
  t = String(t || ''); const a = t.indexOf('{'), z = t.lastIndexOf('}');
  if (a < 0 || z < a) return {};
  const j = t.slice(a, z + 1);
  try { return JSON.parse(j); } catch (e) {}
  let out = '', inStr = false, esc = false;
  for (const ch of j) {
    if (inStr) {
      if (esc) { esc = false; out += ch; continue; }
      if (ch === '\\') { esc = true; out += ch; continue; }
      if (ch === '"') { inStr = false; out += ch; continue; }
      if (ch === '\n') { out += '\\n'; continue; }
      if (ch === '\r') continue;
      if (ch === '\t') { out += '\\t'; continue; }
      out += ch;
    } else { if (ch === '"') inStr = true; out += ch; }
  }
  try { return JSON.parse(out); } catch (e) { return {}; }
}
const jv = $json.output?.variants || parseLoose($json.text).variants || [];
const clean = arr => (arr || []).filter(x => x && !/^\s*(none|n\/a|keine|-)\s*\.?$/i.test(String(x)));
// Code owns length/format. The judge still sometimes counts words; those remarks are dropped here.
const LENGTH = /(\bwords?\b|\bcharacters?\b|\bchars?\b|too long|too short|length|wortanzahl|zeichen)/i;
// LinkedIn connection notes deliberately have no proof point, metric, question or ask.
const LI_OK = /(proof|metric|number|question|ask|call to action|cta|offer|booking|link|pitch)/i;
const judgeKeep = x => !LENGTH.test(String(x)) && !(p.channel === 'LinkedIn' && LI_OK.test(String(x)));
const variants = p.variants.map(v => {
  const j = jv.find(x => String(x.id).toUpperCase().startsWith(v.id)) || null;
  const judgeIssues = !j ? ['Judge returned no verdict' + ($json.error ? ': ' + String($json.error.message || $json.error).slice(0, 120) : '')] : [
    ...clean(j.unsupported_claims).map(x => 'Unsupported: ' + x),
    ...(j.names_ok === false ? ['Wrong name or company'] : []),
    ...(j.language_ok === false ? ['Wrong language or Sie/du'] : []),
    ...(j.specific_opening === false ? ['Opening not specific to this company'] : []),
    ...(j.tone_ok === false && judgeKeep(j.notes || 'tone') ? ['Tone: ' + (j.notes || 'not plain/respectful')] : []),
    ...clean(j.playbook_violations).filter(judgeKeep).map(x => 'Playbook: ' + x)];
  // OWN BENCHMARK: rubric score 0-10 from the (fixed) judge: hook 0-3, relevance 0-3, natural 0-2, ask 0-2.
  const cl = (x, hi) => Math.max(0, Math.min(hi, Number(x) || 0));
  const missing = v.issues.some(x => String(x).startsWith('Variant missing'));
  const quality = (j && !missing) ? cl(j.score_hook, 3) + cl(j.score_relevance, 3) + cl(j.score_natural, 2) + cl(j.score_ask, 2) : null;
  return { ...v, judgeIssues, judgeNote: j?.notes || '', quality, pass: v.issues.length === 0 && judgeIssues.length === 0 };
});
const passed = variants.filter(v => v.pass).map(v => v.id);
const notes = `Attempt ${p.attempt}: ${passed.length ? 'passed ' + passed.join(', ') : 'no variant passed'}\n` + variants.map(v =>
  `${v.id}: ${v.pass ? 'PASS' : 'FAIL'}${v.quality != null ? ' (' + v.quality + '/10)' : ''}${[...v.issues, ...v.judgeIssues].length ? ' · ' + [...v.issues, ...v.judgeIssues].join(' · ') : ''}`).join('\n');
return { json: { ...p, variants, passedIds: passed, pass: passed.length > 0,
  judgeNotes: (p.judgeNotes ? p.judgeNotes + '\n' : '') + notes,
  feedback: variants.map(v => `Variant ${v.id}: ` + [...v.issues, ...v.judgeIssues].join('; ')).join('\n') } };"""

def stage(n,x,inp,prev_expr):
    dn=f"Draft (attempt {n})"; on=f"Claude · draft {n}"; sn=f"Schema · draft {n}"
    node(dn,"@n8n/n8n-nodes-langchain.chainLlm",1.7,[x,200],{"promptType":"define",
      "text":"={{ $json.briefText }}{{ $json.feedback ? '\\n\\nNONE OF YOUR PREVIOUS VARIANTS PASSED REVIEW. Write three new variants that fix ALL of these:\\n' + $json.feedback : '' }}",
      "hasOutputParser":False,"batching":{"batchSize":4,"delayBetweenBatches":0},"messages":{"messageValues":[{"type":"SystemMessagePromptTemplate","message":DRAFT_SYS}]}},onError="continueRegularOutput")
    # Draft model: Claude Sonnet 5.5 (16 Oct, docs/model-choice.md). Mid-price tier: ~$0.026 per attempt.
    # To compare models later: swap this sub-node; the judge stays GPT-5 mini so Quality scores stay comparable.
    # 16 Oct: 2500 max tokens produced empty/cut emails (Sonnet 5.5 spends output tokens before the text) -> 8000.
    # Attempt 2 = fallback on GPT-5.1 (the proven drafter), so one model failing never leaves Noah without cards.
    if n==1:
        node(on,"@n8n/n8n-nodes-langchain.lmChatAnthropic",1.3,[x-60,420],{"model":{"__rl":True,"value":"claude-sonnet-5-5","mode":"id"},"options":{"maxTokensToSample":8000,"temperature":0.6}})
    else:
        on=f"OpenAI · draft {n} (fallback)"
        node(on,"@n8n/n8n-nodes-langchain.lmChatOpenAi",1.2,[x-60,420],{"model":{"__rl":True,"value":"gpt-5.1","mode":"id"},"options":{"timeout":120000,"maxRetries":2,"reasoningEffort":"low"}},
             credentials={"openAiApi":{"id":"","name":"OpenAi account"}})
    # No output-parser sub-node for the draft: 'Check rules' parses the JSON tolerantly (see parseLoose).
    link(on,dn,kind="ai_languageModel")
    link(inp,dn)
    cn=f"Check rules {n}"
    node(cn,"n8n-nodes-base.code",2,[x+240,200],{"jsCode":CHECK.replace("%PREV%",prev_expr),"mode":"runOnceForEachItem"})
    link(dn,cn)
    jn=f"Judge (attempt {n})"; ojn=f"OpenAI · judge {n}" if n==1 else f"Claude · judge {n}"; sjn=f"Schema · judge {n}"
    # Cross-family judging: attempt 1 = Claude draft judged by GPT-5 mini; attempt 2 = GPT-5.1 draft judged by Claude.
    jsys = JUDGE_SYS if n==1 else JUDGE_SYS + "\n\n## Output format\nReturn ONLY one JSON object, no code fences, no text before or after. Keep every string on one line. Schema:\n" + JSCHEMA
    node(jn,"@n8n/n8n-nodes-langchain.chainLlm",1.7,[x+480,200],{"promptType":"define",
      "text":"={{ 'BRIEF:\\n' + $json.briefText + '\\n\\nDRAFTS:\\n' + $json.variants.map(v => '--- Variant ' + v.id + ' ---\\nSubject: ' + v.subject + '\\n' + v.body).join('\\n\\n') }}",
      "hasOutputParser":n==1,"batching":{"batchSize":4,"delayBetweenBatches":0},"messages":{"messageValues":[{"type":"SystemMessagePromptTemplate","message":jsys}]}},onError="continueRegularOutput")
    if n==1:
        node(ojn,"@n8n/n8n-nodes-langchain.lmChatOpenAi",1.2,[x+420,420],{"model":{"__rl":True,"value":"gpt-5-mini","mode":"id"},"options":{"timeout":120000,"maxRetries":2,"reasoningEffort":"low"}},
             credentials={"openAiApi":{"id":"","name":"OpenAi account"}})
        node(sjn,"@n8n/n8n-nodes-langchain.outputParserStructured",1.2,[x+560,420],{"schemaType":"manual","inputSchema":JSCHEMA})
        link(sjn,jn,kind="ai_outputParser")
    else:
        node(ojn,"@n8n/n8n-nodes-langchain.lmChatAnthropic",1.3,[x+420,420],{"model":{"__rl":True,"value":"claude-sonnet-5-5","mode":"id"},"options":{"maxTokensToSample":8000,"temperature":0}})
    link(ojn,jn,kind="ai_languageModel")
    link(cn,jn)
    den=f"Decide {n}"
    node(den,"n8n-nodes-base.code",2,[x+720,200],{"jsCode":DECIDE.replace("%CHECK%",cn),"mode":"runOnceForEachItem"})
    link(jn,den)
    return den
d1=stage(1,1560,"Build brief (rules)","$('Build brief (rules)').item.json")
ifnode("Passed?",[2520,200],"={{ $json.pass }}","true")
link(d1,"Passed?")
node("Prepare retry","n8n-nodes-base.code",2,[2760,420],{"jsCode":"// One retry: same brief, plus the concrete issues from rules + judge as feedback.\nreturn { json: { ...$json, attempt: 2 } };","mode":"runOnceForEachItem"})
link("Passed?","Prepare retry",1)
d2=stage(2,3000,"Prepare retry","$('Prepare retry').item.json")
UPDATE=r"""// Write all three variants to Notion. Default draft = first passing variant (A > B > C);
// Noah chooses the one to send in Telegram (50) or sets "Chosen variant" here. Nothing is sent from 40.
const r = $json;
const t = s => [{ type: 'text', text: { content: String(s ?? '').slice(0, 1990) } }];
const fmt = v => v ? ((v.subject ? 'Subject: ' + v.subject + '\n\n' : '') + v.body + (v.pass ? '' : '\n\n[did not pass review]')) : '';
const byId = id => (r.variants || []).find(v => v.id === id);
const best = (r.variants || []).find(v => v.pass) || null;
const qs = (r.variants || []).map(v => v.quality).filter(q => q != null);
const quality = qs.length ? Math.round(qs.reduce((a, b) => a + b, 0) / qs.length * 10) / 10 : null;
const props = {
  'Status': { status: { name: r.pass ? 'Draft ready' : 'Check manually' } },
  'Quality score': { number: quality },
  'Company one-liner': { rich_text: t(r.oneLiner || '') },
  'Variant A': { rich_text: t(fmt(byId('A'))) },
  'Variant B': { rich_text: t(fmt(byId('B'))) },
  'Variant C': { rich_text: t(fmt(byId('C'))) },
  'Variants passed': { rich_text: t(r.passedIds.length ? r.passedIds.join(', ') : 'none') },
  'Draft subject': { rich_text: t(best?.subject || '') },
  'Draft body': { rich_text: t(best?.body || '') },
  'Draft version': { number: (r.draftVersion || 0) + 1 },
  'Judge result': { select: { name: r.pass ? 'Pass' : 'Fail' } },
  'Judge notes': { rich_text: t(r.judgeNotes) },
  'Channel': { select: { name: r.channel } },
  'Offer': { rich_text: t(r.offer) },
  'Draft language': { select: { name: r.language } },
  'Angle': { select: { name: 'Funding trigger' } },
  // For the later analytics agent: which model + prompt wrote this, so reply rates can be compared per model/variant
  'Draft model': { rich_text: t(r.attempt === 2 ? 'gpt-5.1 (fallback)' : $('Config').first().json.draftModel) },
  'Prompt version': { rich_text: t($('Config').first().json.promptVersion + (r.attempt === 2 ? ' · judged by Claude' : ' · judged by GPT-5 mini')) }
};
if (r.channel === 'Email') props['Booking link'] = { url: r.bookingLink };
return { json: { contactPageId: r.contactPageId, name: r.name, company: r.company, channel: r.channel, pass: r.pass,
  passed: r.passedIds, attempts: r.attempt, quality, notionBody: { properties: props } } };"""
node("Build draft update","n8n-nodes-base.code",2,[3960,100],{"jsCode":UPDATE,"mode":"runOnceForEachItem"})
link("Passed?","Build draft update",0); link(d2,"Build draft update")
notion("Notion · save draft",[4200,100],"PATCH","=https://api.notion.com/v1/pages/{{ $json.contactPageId }}","={{ JSON.stringify($json.notionBody) }}",retryOnFail=True,maxTries=3,waitBetweenTries=2000)
link("Build draft update","Notion · save draft")
node("Run summary","n8n-nodes-base.code",2,[4440,100],{"jsCode":"""// Summary for the orchestrator / manual run.
const rows = $('Build draft update').all().map(i => i.json);
return [{ json: { drafted: rows.length, passed: rows.filter(r => r.pass).length,
  firstTry: rows.filter(r => r.pass && r.attempts === 1).length, failed: rows.filter(r => !r.pass).length,
  qSum: rows.reduce((a, r) => a + (r.quality || 0), 0), qN: rows.filter(r => r.quality != null).length,
  drafts: rows.map(r => ({ name: r.name, company: r.company, channel: r.channel, passed: r.passed, attempts: r.attempts, quality: r.quality })) } }];"""})
link("Notion · save draft","Run summary")
M40=r"""const r = $json;
const c = { in: r.drafted, out: r.passed, firstTry: r.firstTry, failed: r.failed, attempts: (r.drafts || []).reduce((a, d) => a + (d.attempts || 1), 0), qSum: r.qSum || 0, qN: r.qN || 0 };
const x = { model: $('Config').first().json.draftModel, prompt: $('Config').first().json.promptVersion };
const view = (c, x) => ({ in: c.in, out: c.out, errors: 0, costEur: Math.round(c.attempts * 0.024 * 1000) / 1000, skip: !c.in,
  quality: c.qN ? Math.round(c.qSum / c.qN * 10) / 10 : null, model: x.model,
  notes: `${c.out}/${c.in} passed (${c.firstTry} on the first try), ${c.failed} to Check manually. ${c.attempts} draft attempts. Model ${x.model}, ${x.prompt}. Avg quality ${c.qN ? (c.qSum / c.qN).toFixed(1) : 'n/a'}/10. Cost estimated (~€0.024 per attempt).` });"""
node("Build run log","n8n-nodes-base.code",2,[4660,100],{"jsCode":runlog_code("Config","Draft","Draft",M40)})
link("Run summary","Build run log")
node("Notion · log run","n8n-nodes-base.httpRequest",4.2,[4880,100],runlog_http_params(),onError="continueRegularOutput")
link("Build run log","Notion · log run")
node("Remember run log","n8n-nodes-base.code",2,[5100,100],{"jsCode":REMEMBER})
link("Notion · log run","Remember run log")

notes=[
("Note · 0 Overview",[-40,-820],900,560,"""## WP · 40 Draft + judge
**Purpose:** turn every contact with a verified channel into **three draft messages** (A problem-first, B insight-first, C short) that follow your Notion Sales Playbook, are checked twice, and wait for your pick in Telegram (WP · 50). **Nothing is sent from this workflow.**

**Input:** Contacts with Status *Ready to draft* (verified email → Email) or *LinkedIn only* (→ 200-character connection note). Max 8 per run (Config).
**Output (per contact, in Notion):** Variant A/B/C, Variants passed, Draft subject/body (= first passing variant), Judge result + notes, Channel, Offer, Language, Booking link. Status → *Draft ready* (≥1 passed) or *Check manually* (none passed after 2 attempts).

**Flow:** Config → read Offers + Sales Playbook + contacts (once) → per contact: company, article, homepage → brief → draft → code check → judge → decide → (retry once) → save.
**Models (preset in the sub-nodes):** draft = GPT-5.1, reasoning low (interim; model decision pending) · judge = GPT-5 mini, reasoning low. Only the credentials need selecting after import.
**Runtime:** ~2–3 min for 8 contacts (chains run 4 contacts in parallel). v3 took 6:31 with GPT-5.1 reasoning.
Docs: docs/40-draft-judge.md"""),
("Note · 1 Load context",[180,-240],700,220,"""### 1 · Load context (runs once per execution)
**In:** Config. **Nodes:** *active offers* → *sales playbook* → *contacts to draft*.
**Why:** the playbook is read live from Notion on every run, so you edit rules in Notion, not in n8n. If the page can't be read, the brief says so and the system prompt rules still apply.
**Fails when:** the Notion integration loses access to the page → no playbook text (visible as playbookLoaded=false in Build brief)."""),
("Note · 2 Build brief",[900,-240],760,220,"""### 2 · Research and brief (rules, no LLM)
**Per contact:** get company → fetch the funding article → fetch the homepage → *Build brief*.
**Logic:** Channel = Email if verified email, else LinkedIn. Language DE (*du*) for DE/AT/CH companies, else EN. Offer by rules (partnerships signal → Fractional Partnerships Lead; DACH → GTM Sprint; others → Market Entry into DACH). Booking link gets ?metadata[contact]=<id> so a booking can be matched back.
**Why:** the brief is the ONLY source of facts the model may use: article excerpt, homepage text, your canonical profile, the offer and the playbook. Anything else counts as invented."""),
("Note · 3 Draft and check",[1520,-240],900,220,"""### 3 · Draft → code check (attempt 1)
**Draft:** GPT-5.1 (reasoning low; swap the sub-node to change model), prompts/draft.md. Three variants in one call.
**Code check per variant:** email subject 3–7 words and not about funding; body A/B 55–120 words, C 25–60; booking link unchanged; opt-out line; sign-off; first name used; DE uses *du*; first sentence not about the round; no hype/congrats; **every number must exist in the brief**. LinkedIn: ≤200 characters, no link, no question.
**Why code, not the model:** counting and exact matching are deterministic. The model is bad at counting its own words."""),
("Note · 4 Judge and decide",[2000,-240],820,220,"""### 4 · Judge → decide
**Judge:** GPT-5 mini (different model family than the drafter, so it isn't grading itself), prompts/judge.md. Yes/no per variant: unsupported claims, names, language, specific opening, tone, playbook violations.
**Decide (code):** variant passes only if the code check AND the judge are clean. Judge remarks about length are dropped (code owns length); for LinkedIn, demands for a proof point or question are dropped (a connect note has neither by design).
**Contact passes** if ≥1 variant passed → straight to save. Otherwise → retry."""),
("Note · 5 Retry and save",[2900,-240],1100,220,"""### 5 · Retry once, then save
**Retry:** same brief + the concrete issues of every variant as feedback ("Variant C: Body has 68 words…"). Same draft → check → judge → decide chain.
**Save:** *Build draft update* writes all three variants (failed ones marked "[did not pass review]"), default draft = first passing variant, Status *Draft ready* or *Check manually*. *Run summary* returns counts to the orchestrator.
**Failure modes:** model/API error → node continues, contact shows "Judge returned no verdict" and lands in *Check manually*; Notion save retries 3×. Re-run safe: only *Ready to draft* / *LinkedIn only* contacts are picked, so drafted contacts are never redrafted.""")]
for nm,pos,wd,ht,txt in notes: node(nm,"n8n-nodes-base.stickyNote",1,pos,{"width":wd,"height":ht,"content":txt})
wf={"name":"WP · 40 Draft + judge (sub-workflow)","nodes":apply_ids(N),"connections":C,"settings":{"executionOrder":"v1","timezone":"Europe/Berlin","saveManualExecutions":True,"errorWorkflow":WF_ERROR},"pinData":{}}
json.dump(wf,open(R+'workflows/40-draft-judge.json','w'),indent=2,ensure_ascii=False)
print(len(N))
