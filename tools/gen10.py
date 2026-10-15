import json, uuid
import os
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
old=json.load(open(R+'workflows/10-qualify-company.json'))
oldn={n['name']:n for n in old['nodes']}
N=[]; C={}
def node(name,typ,ver,pos,params,**kw):
    n={"id":str(uuid.uuid4()),"name":name,"type":typ,"typeVersion":ver,"position":pos,"parameters":params}; n.update(kw); N.append(n); return name
def link(a,b,out=0,inp=0,kind="main"):
    C.setdefault(a,{}).setdefault(kind,[])
    m=C[a][kind]
    while len(m)<=out: m.append([])
    m[out].append({"node":b,"type":kind,"index":inp})
NOTION_H={"sendHeaders":True,"headerParameters":{"parameters":[{"name":"Notion-Version","value":"2022-06-28"}]}}
def notion(name,pos,method,url,body=None,**kw):
    p={"method":method,"url":url,"authentication":"predefinedCredentialType","nodeCredentialType":"notionApi",**NOTION_H,"options":{}}
    if body: p.update({"sendBody":True,"specifyBody":"json","jsonBody":body})
    return node(name,"n8n-nodes-base.httpRequest",4.2,pos,p,**kw)

node("When called by orchestrator","n8n-nodes-base.executeWorkflowTrigger",1.1,[0,200],{"inputSource":"passthrough"})
node("Fetch full article","n8n-nodes-base.httpRequest",4.2,[220,200],{
  "method":"GET","url":"={{ $json.link }}",
  "sendHeaders":True,"headerParameters":{"parameters":[{"name":"User-Agent","value":"Mozilla/5.0 (compatible; WaypointResearch/1.0; +https://noahhofmann.com)"}]},
  "options":{"response":{"response":{"neverError":True,"responseFormat":"text","outputPropertyName":"html"}},"timeout":15000}},
  onError="continueRegularOutput")
link("When called by orchestrator","Fetch full article")

PREP=r"""// Rules, no LLM: turn the article HTML into clean text + outbound link candidates.
// Falls back to the RSS text if the page can't be fetched.
const src = $('When called by orchestrator').item.json;
let html = typeof $json.html === 'string' ? $json.html : '';
const flags = [];
const decode = s => s.replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&quot;/g, '"')
  .replace(/&#8217;|&rsquo;/g, "'").replace(/&#8216;|&lsquo;/g, "'").replace(/&#8220;|&#8221;|&ldquo;|&rdquo;/g, '"')
  .replace(/&#8211;|&ndash;/g, '-').replace(/&#8212;|&mdash;/g, '-').replace(/&euro;/g, '€').replace(/&pound;/g, '£')
  .replace(/&#(\d+);/g, (m, n) => String.fromCharCode(+n)).replace(/&[a-z]+;/gi, ' ');
let paras = [];
if (html.length > 500) {
  html = html.replace(/<(script|style|noscript|svg|nav|header|footer|aside|form)[\s\S]*?<\/\1>/gi, ' ');
  // Article body = the real paragraphs. Teasers, menus and "related news" are short and get dropped.
  paras = [...html.matchAll(/<p[^>]*>([\s\S]*?)<\/p>/gi)].map(m => m[1])
    .filter(p => decode(p.replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim().length >= 60);
} else flags.push('Article fetch failed');
const srcHost = (() => { try { return new URL(src.link).hostname.replace(/^www\./, ''); } catch (e) { return ''; } })();
const SKIP = /(^|\.)(linkedin|twitter|x|facebook|instagram|youtube|crunchbase|dealroom|google|apple|wordpress|gravatar|tech|eu-startups|mailchimp|bit|t|medium|substack|wikipedia|tiktok|spotify|cookiebot|onetrust)\.[a-z]+$/i;
// Only links INSIDE article paragraphs: that's where the company's own site is linked
const links = paras.flatMap(p => [...p.matchAll(/href=["'](https?:\/\/[^"'#?]+)/gi)].map(m => m[1]))
  .map(u => { try { return new URL(u).hostname.replace(/^www\./, '').toLowerCase(); } catch (e) { return null; } })
  .filter(h => h && h !== srcHost && !SKIP.test(h));
const text = decode(paras.join(' \n').replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
const full = text.length > 400 ? text.slice(0, 9000) : src.text;
if (text && text.length <= 400) flags.push('Article fetch failed');
return { json: { ...src, rssText: src.text, text: full, linkHosts: [...new Set(links)].slice(0, 25), prepFlags: flags } };"""
node("Prepare article (rules)","n8n-nodes-base.code",2,[440,200],{"jsCode":PREP,"mode":"runOnceForEachItem"})
link("Fetch full article","Prepare article (rules)")

inj=oldn["Injection pre-check (rules)"]; node("Injection pre-check (rules)","n8n-nodes-base.code",2,[660,200],inj["parameters"])
link("Prepare article (rules)","Injection pre-check (rules)")
node("Injection found?","n8n-nodes-base.if",oldn["Injection found?"]["typeVersion"],[880,200],oldn["Injection found?"]["parameters"])
link("Injection pre-check (rules)","Injection found?")
node("Mark as blocked","n8n-nodes-base.code",2,[1120,0],{"jsCode":"""return { json: { ...$json, facts: null, score: 0, breakdown: null, gate: 'Injection pattern', status: 'Rejected',
  flags: ['Injection pattern'], error: `Blocked before LLM: ${$json.injectionPattern}`, tokensEst: 0, domain: null, dedupeKey: null } };""","mode":"runOnceForEachItem"})
link("Injection found?","Mark as blocked",0)

PROMPT=open(R+'prompts/qualify-v2.md').read()
node("Extract facts (LLM chain)","@n8n/n8n-nodes-langchain.chainLlm",1.5,[1120,300],{"promptType":"define",
  "text":"=<news_item>\nPUBLISHED: {{ $json.published }}\nTITLE: {{ $json.title }}\nTEXT: {{ $json.text }}\n</news_item>",
  "hasOutputParser":True,"messages":{"messageValues":[{"type":"SystemMessagePromptTemplate","message":PROMPT}]}},onError="continueRegularOutput")
link("Injection found?","Extract facts (LLM chain)",1)
node("OpenAI · gpt-4o-mini","@n8n/n8n-nodes-langchain.lmChatOpenAi",1.2,[1060,520],{"model":{"__rl":True,"value":"gpt-4o-mini","mode":"list","cachedResultName":"gpt-4o-mini"},"options":{"temperature":0,"maxTokens":1200,"timeout":60000,"maxRetries":2}})
link("OpenAI · gpt-4o-mini","Extract facts (LLM chain)",kind="ai_languageModel")
def E(desc): return {"type":["string","null"],"description":desc}
SCHEMA={"type":"object",
 "required":["company","article_type","round","business_model","tech_core","use_of_funds","evidence","summary"],
 "properties":{
  "company":{"type":"string"},
  "website":E("Only if a URL or domain of the company is literally in the text"),
  "hq_country":E("ISO-2 code of HQ if stated"),
  "expansion_targets":{"type":["array","null"],"items":{"type":"string"},"description":"ISO-2 codes or DACH / Europe explicitly named as expansion targets"},
  "article_type":E("One of: single_company_equity_round, debt_only, fund_close, acquisition, roundup, other"),
  "round":E("One of: Pre-seed, Seed, Series A, Series B, Series C+, Unknown"),
  "amount":{"type":["number","null"],"description":"Round size as a plain number in the stated currency, e.g. 3000000"},
  "currency":E("ISO currency code as stated, e.g. EUR, USD, GBP"),
  "business_model":E("One of: B2B, B2B2C, Mixed, B2C, Unknown"),
  "tech_core":E("One of: core_tech, tech_assisted_service, no_tech, unknown"),
  "use_of_funds":E("One of: commercial, mixed, rnd_only, unknown"),
  "product_live":{"type":["boolean","null"]},
  "customers_or_pilots":{"type":["boolean","null"]},
  "senior_commercial_lead_named":{"type":["boolean","null"]},
  "sector":E("Short sector label"),
  "mission_flags":{"type":["array","null"],"items":{"type":"string"},"description":"Any of: defense, gambling, tobacco, speculative_crypto, fast_fashion, fossil_energy"},
  "decision_makers":{"type":["array","null"],"items":{"type":"object","properties":{"name":{"type":"string"},"role":{"type":["string","null"]}}}},
  "investors":{"type":["array","null"],"items":{"type":"string"}},
  "evidence":{"type":"object","properties":{k:E("Verbatim quote") for k in ["round","geography","business_model","use_of_funds","traction"]}},
  "summary":{"type":"string"}}}
node("Schema · facts v2","@n8n/n8n-nodes-langchain.outputParserStructured",1.2,[1280,520],{"schemaType":"manual","inputSchema":json.dumps(SCHEMA,indent=2)})
link("Schema · facts v2","Extract facts (LLM chain)",kind="ai_outputParser")

SCORE=r"""// icp-v2 scoring IN CODE. The LLM only extracted facts; every fact must be backed by
// verbatim evidence or it falls back to the neutral/unknown value. Mirrors Notion › ICP & Rules.
const ICP_VERSION = 'icp-v2';
const src = $('Injection pre-check (rules)').item.json;
const raw = $json.output || null;
// Normalise model output (schema is loose on purpose so it never rejects the whole answer)
const pick = (v, allowed, dflt) => allowed.find(a => a.toLowerCase() === String(v ?? '').toLowerCase().replace(/[\s-]+/g, a.includes('_') ? '_' : a.includes(' ') ? ' ' : '-')) || allowed.find(a => a.toLowerCase() === String(v ?? '').toLowerCase()) || dflt;
const f = raw ? { ...raw,
  article_type: pick(raw.article_type, ['single_company_equity_round','debt_only','fund_close','acquisition','roundup','other'], 'other'),
  round: pick(raw.round, ['Pre-seed','Seed','Series A','Series B','Series C+','Unknown'], 'Unknown'),
  business_model: pick(raw.business_model, ['B2B','B2B2C','Mixed','B2C','Unknown'], 'Unknown'),
  tech_core: pick(raw.tech_core, ['core_tech','tech_assisted_service','no_tech','unknown'], 'unknown'),
  use_of_funds: pick(raw.use_of_funds, ['commercial','mixed','rnd_only','unknown'], 'unknown'),
  expansion_targets: raw.expansion_targets || [], mission_flags: (raw.mission_flags || []).filter(m => ['defense','gambling','tobacco','speculative_crypto','fast_fashion','fossil_energy'].includes(m)),
  decision_makers: raw.decision_makers || [], investors: raw.investors || [], evidence: raw.evidence || {},
  senior_commercial_lead_named: raw.senior_commercial_lead_named === true } : null;
const flags = [...(src.prepFlags || [])];
if (!f) {
  return { json: { ...src, facts: null, score: null, breakdown: null, gate: null, status: 'New',
    flags: [...flags, 'Model error'], error: String($json.error?.message || $json.error || 'No valid structured output'),
    tokensEst: 0, domain: null, dedupeKey: null } };
}
const norm = s => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/\s+/g, ' ').trim();
// Verbatim check ignores punctuation / quote style (’ vs ', – vs -), never words
const loose = s => norm(s).replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
const hay = norm(src.title + ' ' + src.text);
const hayL = loose(src.title + ' ' + src.text);
// Near-verbatim: >= 80% of the quote's word pairs must appear in the article (tolerates a dropped
// word or changed tense, rejects invented quotes)
const pairs = x => { const w = loose(x).split(' '); return w.slice(1).map((t, i) => w[i] + ' ' + t); };
const ok = e => { if (!e || loose(e).length < 6) return false; if (hayL.includes(loose(e))) return true;
  const p = pairs(e); return p.length >= 3 && p.filter(x => hayL.includes(x)).length / p.length >= 0.8; };
const ev = {}; let dropped = 0;
for (const [k, v] of Object.entries(f.evidence || {})) { if (v && !ok(v)) dropped++; ev[k] = ok(v) ? v : null; }
if (dropped) flags.push('Evidence dropped');
// Facts without grounded evidence fall back to neutral
const bm = ev.business_model ? f.business_model : 'Unknown';
const uof = ev.use_of_funds ? f.use_of_funds : 'unknown';
const round = ev.round ? f.round : 'Unknown';
const traction = ev.traction ? (f.product_live || f.customers_or_pilots) : false;
// Amount → EUR (fixed, conservative rates; good enough for a 3-band score)
const FX = { EUR: 1, USD: 0.92, GBP: 1.17, CHF: 1.05, SEK: 0.087, DKK: 0.134, NOK: 0.085, PLN: 0.23, CZK: 0.04, HUF: 0.0025 };
const amountEur = f.amount && FX[(f.currency || '').toUpperCase()] ? Math.round(f.amount * FX[f.currency.toUpperCase()]) : null;
// Geography
const DACH = ['DE','AT','CH'], BENELUX = ['NL','BE','LU'];
const EUROPE = ['FR','ES','IT','PT','IE','DK','SE','FI','NO','IS','LI','PL','CZ','EE','LV','LT','SK','SI','HR','RO','BG','HU','GR','CY','MT', ...DACH, ...BENELUX];
const hq = (f.hq_country || '').toUpperCase().replace('GB', 'UK');
const targets = (f.expansion_targets || []).map(t => t.toUpperCase());
const geoOf = c => DACH.includes(c) || c === 'DACH' ? 15 : BENELUX.includes(c) ? 12 : (EUROPE.includes(c) || c === 'EUROPE' || c === 'EU') ? 8 : 0;
const geo = Math.max(geoOf(hq), ...targets.map(geoOf), 0);
// Hard gates (any one = Rejected)
let gate = null;
if (f.article_type !== 'single_company_equity_round') gate = `Not a single-company equity round (${f.article_type})`;
else if (['Series B', 'Series C+'].includes(f.round) || (amountEur && amountEur > 20e6)) gate = `Too late / too large (${f.round}, €${amountEur ?? '?'})`;
else if ((hq === 'UK' || (hq && !EUROPE.includes(hq))) && geo === 0) gate = `HQ ${hq}, no Europe expansion`;
else if ((f.mission_flags || []).length) gate = `Mission gate: ${f.mission_flags.join(', ')}`;
else if (bm === 'B2C') gate = 'B2C (consumer business, outside ICP)';
// Scoring (100)
const days = (Date.now() - new Date(src.published).getTime()) / 864e5;
const b = {
  trigger: days <= 30 ? 10 : days <= 60 ? 5 : 0,
  stage: amountEur == null ? 8 : amountEur < 750e3 ? 3 : amountEur <= 15e6 ? 15 : 8,
  b2b: { B2B: 15, B2B2C: 8, Mixed: 8, B2C: 0, Unknown: 4 }[bm] ?? 4,
  geography: hq || targets.length ? geo : 4,
  useOfFunds: { commercial: 15, mixed: 8, rnd_only: 4, unknown: 4 }[uof] ?? 4,
  capacityGap: (traction ? 5 : 0) + (f.senior_commercial_lead_named ? 0 : 5),
  tech: { core_tech: 10, tech_assisted_service: 5, no_tech: 0, unknown: 5 }[f.tech_core] ?? 5,
  reachability: 0
};
const people = (f.decision_makers || []).slice(0, 5).filter(p => p.name && p.name.split(' ').length >= 2 && hayL.includes(loose(p.name)));
if (people.length) b.reachability += 6;
const NETWORK = /\b(techstars|antler|ewor|apx|heartfelt|redstone|sigma squared)\b/i;
if (NETWORK.test((f.investors || []).filter(x => hayL.includes(loose(x))).join(' '))) { b.reachability += 4; flags.push('Network investor'); }
const score = Object.values(b).reduce((a, x) => a + x, 0);
// B2B must be shown, not assumed: an unconfirmed business model can't qualify (human can promote it)
const bmUnclear = !gate && score >= 60 && !['B2B', 'B2B2C', 'Mixed'].includes(bm);
if (bmUnclear) flags.push('Check: business model unclear');
const status = gate ? 'Rejected' : (score >= 60 && !bmUnclear) ? 'Qualified' : 'Archived';
if (!gate && score >= 75) flags.push('Strong');
// Domain: the company's own site from article links (rules), else LLM website if literally in text
const tr = x => norm(x).replace(/æ/g, 'ae').replace(/ø/g, 'o').replace(/œ/g, 'oe').replace(/ß/g, 'ss').replace(/ł/g, 'l');
const core = tr(f.company).replace(/\b(gmbh|ag|ug|se|kg|bv|nv|sas|sa|srl|ltd|inc|oy|ab|as|aps)\b/g, '').replace(/[^a-z0-9]/g, '');
const stem = h => h.split('.').slice(0, -1).join('').replace(/[^a-z0-9]/g, '');
let domain = (src.linkHosts || []).find(h => core.length >= 3 && (stem(h).includes(core) || core.includes(stem(h)) && stem(h).length >= 4)) || null;
if (!domain && f.website && hay.includes(norm(f.website).replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0])) {
  domain = norm(f.website).replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0];
}
const dedupeKey = tr(f.company).replace(/\b(gmbh|ag|ug|se|kg|bv|nv|sas|sa|srl|ltd|inc|oy|ab|as|aps)\b/g, '').replace(/[^a-z0-9]/g, '');
const tokensEst = Math.round((src.title.length + src.text.length + 4500) / 4) + 400;
return { json: { ...src, facts: f, evidence: ev, amountEur, people, score, breakdown: b, gate, status, flags,
  error: null, tokensEst, droppedEvidence: dropped, domain, dedupeKey, icpVersion: ICP_VERSION } };"""
node("Score icp-v2 (rules)","n8n-nodes-base.code",2,[1500,300],{"jsCode":SCORE,"mode":"runOnceForEachItem"})
link("Extract facts (LLM chain)","Score icp-v2 (rules)")

notion("Notion · same company?",[1740,200],"POST","=https://api.notion.com/v1/databases/{{ $json.cfg.notionCompaniesDb }}/query",
  '={{ JSON.stringify({ filter: { property: "Dedupe key", rich_text: { equals: $json.dedupeKey || "__none__" } }, page_size: 1 }) }}',
  onError="continueRegularOutput")
link("Mark as blocked","Notion · same company?")
link("Score icp-v2 (rules)","Notion · same company?")

BUILD=r"""// Build the Notion company page. Skip creation if the same company already exists
// (same company reported by two feeds or on two days).
const d = $('Notion · same company?').item.json; // paired: the query result
let s;
try { s = $('Score icp-v2 (rules)').item.json; } catch (e) { s = null; }
if (!s || s.link === undefined) s = $('Mark as blocked').item.json;
const existing = (d.results || [])[0] || null;
const cfg = s.cfg;
const f = s.facts || {};
const t = x => [{ type: 'text', text: { content: String(x ?? '').slice(0, 1900) } }];
const countryMap = { DE:'DE', AT:'AT', CH:'CH', NL:'NL', GB:'UK', UK:'UK' };
const EU = ['FR','ES','IT','PT','BE','LU','IE','DK','SE','FI','NO','PL','CZ','EE','LV','LT','SK','SI','HR','RO','BG','HU','GR','CY','MT'];
const c = (f.hq_country || '').toUpperCase();
const country = countryMap[c] || (EU.includes(c) ? 'Other EU' : c ? 'Non-EU' : null);
const roundMap = { 'Pre-seed':'Pre-seed', 'Seed':'Seed', 'Series A':'Series A', 'Series B':'Series B', 'Series C+':'Later' };
const b = s.breakdown;
const reasons = s.error ? `ERROR: ${s.error}` : [
  s.gate ? `GATE: ${s.gate}` : `Score ${s.score}/100 (${s.icpVersion})`,
  b ? `trigger ${b.trigger} · stage ${b.stage} · B2B ${b.b2b} · geo ${b.geography} · funds ${b.useOfFunds} · gap ${b.capacityGap} · tech ${b.tech} · reach ${b.reachability}` : '',
  f.summary || ''
].filter(Boolean).join('\n');
const props = {
  'Company': { title: t(f.company || s.title) },
  'Status': { status: { name: s.status } },
  'Signal': { select: { name: 'Funding' } },
  'Signal source': { url: s.link },
  'Signal summary': { rich_text: t(`${s.title} (${s.source})`) },
  'Signal date': { date: { start: s.published } },
  'Dedupe key': { rich_text: t(s.dedupeKey || s.link) },
  'Qualify reasons': { rich_text: t(reasons) },
  'Evidence': { rich_text: t(Object.entries(s.evidence || {}).filter(([k, v]) => v).map(([k, v]) => `${k}: "${v}"`).join('\n')) },
  'Round': { select: { name: roundMap[f.round] || 'Unknown' } },
  'Sector': { rich_text: t(f.sector || '') },
  'Flags': { multi_select: s.flags.map(name => ({ name })) },
  'Prompt version': { rich_text: t(`qualify-v2 / ${s.icpVersion || 'icp-v2'}`) }
};
if (s.score !== null) props['ICP score'] = { number: s.score };
if (s.amountEur) props['Amount EUR'] = { number: s.amountEur };
if (s.domain) props['Domain'] = { url: `https://${s.domain}` };
if (country) props['Country'] = { select: { name: country } };
return { json: { ...s, duplicateOf: existing ? existing.id : null,
  notionBody: { parent: { database_id: cfg.notionCompaniesDb }, properties: props } } };"""
node("Build company page","n8n-nodes-base.code",2,[1960,200],{"jsCode":BUILD,"mode":"runOnceForEachItem"})
link("Notion · same company?","Build company page")
node("Already in CRM?","n8n-nodes-base.if",2.2,[2180,200],{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose","version":2},"conditions":[{"id":str(uuid.uuid4()),"leftValue":"={{ $json.duplicateOf }}","rightValue":"","operator":{"type":"string","operation":"notEmpty","singleValue":True}}],"combinator":"and"},"options":{}})
link("Build company page","Already in CRM?")
node("Return duplicate","n8n-nodes-base.code",2,[2420,40],{"jsCode":"""// Same company already stored: don't create a second row, don't find people again.
const b = $json;
return { json: { ok: true, companyPageId: null, company: b.facts?.company || b.title, score: b.score,
  status: 'Duplicate', flags: [...b.flags, 'Duplicate'], error: null, tokensEst: b.tokensEst,
  droppedEvidence: b.droppedEvidence || 0, duplicateOf: b.duplicateOf, link: b.link, title: b.title, text: b.text, cfg: b.cfg } };""","mode":"runOnceForEachItem"})
link("Already in CRM?","Return duplicate",0)
notion("Notion · create company",[2420,300],"POST","https://api.notion.com/v1/pages","={{ JSON.stringify($json.notionBody) }}",retryOnFail=True,maxTries=3,waitBetweenTries=2000)
link("Already in CRM?","Notion · create company",1)
node("Return result","n8n-nodes-base.code",2,[2660,300],{"jsCode":"""// Contract back to the orchestrator (unchanged shape). text = full article, so 20 can find people.
const b = $('Build company page').item.json;
const ok = $json.object === 'page';
return { json: {
  ok, companyPageId: ok ? $json.id : null, company: b.facts?.company || b.title,
  score: b.score, status: b.status, flags: b.flags, error: ok ? b.error : (b.error || $json.message || 'Notion write failed'),
  tokensEst: b.tokensEst, droppedEvidence: b.droppedEvidence || 0, domain: b.domain,
  link: b.link, title: b.title, text: b.text, cfg: b.cfg
}};""","mode":"runOnceForEachItem"})
link("Notion · create company","Return result")

notes=[("Note · Before the LLM (rules)",[180,-260],"## Before the LLM (rules)\nFetch the full article (RSS only has a teaser, which is why 20 found no people) → strip HTML → collect outbound links for the company domain → regex injection pre-check. Fetch fails → falls back to RSS text + flag."),
("Note · The LLM (extracts facts)",[1060,-260],"## The LLM extracts facts only\ngpt-4o-mini, temp 0, strict JSON schema. No score from the model. Every fact group needs a verbatim evidence quote."),
("Note · After the LLM (rules decide)",[1700,-260],"## Rules decide (icp-v2)\nUngrounded facts → neutral. Hard gates → Rejected. 100-point score from Notion › ICP & Rules: ≥60 Qualified, ≥75 Strong. Company-level dedupe on normalized name.")]
for nm,pos,txt in notes: node(nm,"n8n-nodes-base.stickyNote",1,pos,{"width":560,"height":200,"content":txt})

wf={"name":"WP · 10 Qualify company (sub-workflow)","nodes":N,"connections":C,"settings":old.get("settings",{"executionOrder":"v1"}),"pinData":{}}
json.dump(wf,open(R+'workflows/10-qualify-company.json','w'),indent=2,ensure_ascii=False)
print(len(N))
