import json, uuid, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runlog import runlog_code, runlog_http_params, REMEMBER, apply_ids
N=[]; C={}
def node(name,typ,ver,pos,params,**kw):
    n={"id":str(uuid.uuid4()),"name":name,"type":typ,"typeVersion":ver,"position":pos,"parameters":params}; n.update(kw); N.append(n); return name
def link(a,b,out=0,inp=0):
    C.setdefault(a,{"main":[]}); m=C[a]["main"]
    while len(m)<=out: m.append([])
    m[out].append({"node":b,"type":"main","index":inp})
NOTION_H={"sendHeaders":True,"headerParameters":{"parameters":[{"name":"Notion-Version","value":"2022-06-28"}]}}
def notion(name,pos,method,url,body=None,**kw):
    p={"method":method,"url":url,"authentication":"predefinedCredentialType","nodeCredentialType":"notionApi",**NOTION_H,"options":{}}
    if body: p.update({"sendBody":True,"specifyBody":"json","jsonBody":body})
    return node(name,"n8n-nodes-base.httpRequest",4.2,pos,p,**kw)

node("Run manually","n8n-nodes-base.manualTrigger",1,[0,100],{})
node("When called by orchestrator","n8n-nodes-base.executeWorkflowTrigger",1.1,[0,460],{"inputSource":"passthrough"})

CONFIG=r"""// 30 · Enrich contacts: config + monthly budget guard.
// Free tiers: Brave $5 credit/month (~1,000 searches), Hunter 50 credits/month.
// We stay well below both. Counters live in workflow static data and are
// only persisted on ACTIVE (production) runs, not on manual test runs.
const cfg = {
  notionContactsDb: '349e3747aa894088a833ca4a76d6a1b2',
  maxContactsPerRun: 8,
  braveMonthlyCap: 300,     // searches; worst case 3 per contact (website + 2 LinkedIn)
  hunterMonthlyCap: 40,     // credits; finder 1 (only if found) + verifier 0.5
  personaOrder: [
    /\b(ceo|chief executive|geschäftsführer|managing director)\b/i,
    /\b(founder|co-founder|cofounder|gründer)\b/i,
    /\b(cro|chief revenue|head of sales|vp sales|sales director)\b/i,
    /\b(partnership|growth|business development|bd)\b/i
  ].map(String)
};
const s = $getWorkflowStaticData('global');
const month = new Date().toISOString().slice(0, 7);
if (s.month !== month) { s.month = month; s.brave = 0; s.hunter = 0; }
const braveLeft = cfg.braveMonthlyCap - (s.brave || 0);
const hunterLeft = cfg.hunterMonthlyCap - (s.hunter || 0);
// worst case per contact: 2 Brave searches, 1.5 Hunter credits
const allowed = Math.max(0, Math.min(cfg.maxContactsPerRun, Math.floor(braveLeft / 3), Math.floor(hunterLeft / 1.5)));
return [{ json: { ...cfg, startedAt: new Date().toISOString(), month, braveUsed: s.brave || 0, hunterUsed: s.hunter || 0, allowed } }];"""
node("Config + budget","n8n-nodes-base.code",2,[240,280],{"jsCode":CONFIG})
for t in ["Run manually","When called by orchestrator"]: link(t,"Config + budget")

node("Budget left?","n8n-nodes-base.if",2.2,[460,280],{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"strict","version":2},"conditions":[{"id":str(uuid.uuid4()),"leftValue":"={{ $json.allowed }}","rightValue":0,"operator":{"type":"number","operation":"gt"}}],"combinator":"and"},"options":{}})
link("Config + budget","Budget left?")

notion("Notion · contacts needing email",[700,200],"POST","=https://api.notion.com/v1/databases/{{ $json.notionContactsDb }}/query",
 '={{ JSON.stringify({ filter: { property: "Status", or: ["Needs email", "Ready to draft", "LinkedIn only", "Draft ready", "Awaiting approval", "Approved", "Gmail draft created", "Sent", "Replied", "Meeting booked"].map(n => ({ property: "Status", status: { equals: n } })) }, sorts: [{ timestamp: "created_time", direction: "ascending" }], page_size: 100 }) }}')
link("Budget left?","Notion · contacts needing email",0)

PICK=r"""// Turn Notion rows into clean items, order by persona priority, cap by budget.
const cfg = $('Config + budget').first().json;
const txt = p => {
  if (!p) return '';
  const arr = p.title || p.rich_text;
  if (arr) return arr.map(t => t.plain_text).join('').trim();
  return p.url || p.email || p.select?.name || '';
};
const rank = role => {
  const i = cfg.personaOrder.findIndex(r => new RegExp(r.slice(1, r.lastIndexOf('/')), 'i').test(role || ''));
  return i === -1 ? 9 : i;
};
const all = $input.first().json.results || [];
const statusOf = pg => pg.properties.Status?.status?.name;
// Companies that already have a contact with a verified email (or further down the funnel): skip them.
const covered = new Set(all.filter(pg => statusOf(pg) !== 'Needs email')
  .map(pg => pg.properties.Company?.relation?.[0]?.id).filter(Boolean));
const rows = all.filter(pg => statusOf(pg) === 'Needs email').map(pg => {
  const name = txt(pg.properties.Name).replace(/\s+/g, ' ');
  const clean = name.replace(/^((dr|prof|ing|mag|dipl)\.?\s+)+/i, '').trim();
  const parts = clean.split(' ');
  return {
    contactPageId: pg.id,
    name, first: parts[0], last: parts[parts.length - 1],
    role: txt(pg.properties.Role),
    companyPageId: pg.properties.Company?.relation?.[0]?.id || null,
  };
}).filter(r => r.companyPageId && !covered.has(r.companyPageId) && r.first && r.last && r.first !== r.last);
rows.sort((a, b) => rank(a.role) - rank(b.role));
// Budget: only the best persona per company is enriched in a run. Others wait (stay "Needs email").
const perCompany = new Set();
const picked = rows.filter(r => !perCompany.has(r.companyPageId) && perCompany.add(r.companyPageId));
return picked.slice(0, cfg.allowed).map(r => ({ json: r }));"""
node("Pick contacts (persona order, budget cap)","n8n-nodes-base.code",2,[920,200],{"jsCode":PICK})
link("Notion · contacts needing email","Pick contacts (persona order, budget cap)")

notion("Notion · get company",[1140,200],"GET","=https://api.notion.com/v1/pages/{{ $json.companyPageId }}")
link("Pick contacts (persona order, budget cap)","Notion · get company")

PREP=r"""// Attach company name + domain, build search query for attempt 1.
const c = $('Pick contacts (persona order, budget cap)').item.json;
const txt = p => {
  if (!p) return '';
  const arr = p.title || p.rich_text;
  if (arr) return arr.map(t => t.plain_text).join('').trim();
  return p.url || p.email || '';
};
const company = txt($json.properties?.Company);
const countryTld = ({ DE: 'de', AT: 'at', CH: 'ch', NL: 'nl', UK: 'co.uk' })[$json.properties?.Country?.select?.name] || null;
let domain = txt($json.properties?.Domain).toLowerCase()
  .replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0];
if (!/^[a-z0-9.-]+\.[a-z]{2,}$/.test(domain)) domain = '';
// Core company token for matching: strip legal forms, keep the distinctive word(s)
const core = company.toLowerCase().replace(/æ/g, 'ae').replace(/ø/g, 'o').replace(/œ/g, 'oe').replace(/ß/g, 'ss').replace(/ł/g, 'l').normalize('NFD').replace(/[̀-ͯ]/g, '')
  .replace(/\b(gmbh|ag|ug|se|kg|bv|b\.v\.|nv|sas|sa|srl|ltd|limited|inc|oy|ab|as|aps|haftungsbeschrankt)\b/g, '')
  .replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
const q3 = company;  // plain name: the quoted "official website" query returned 0 results in every live run
const q1 = `site:linkedin.com/in "${c.first} ${c.last}" "${company}"`;
const q2 = `site:linkedin.com/in "${c.first} ${c.last}" ${domain ? domain.split('.')[0] : core} ${c.role || ''}`.trim();
// Topic words: what the company does, from the funding article summary + sector. Used by the website
// fail-safe to check that a candidate homepage is about the SAME business (holo.pl sold hologram stickers).
const STOP = new Set(['raises','raise','million','funding','round','seed','series','startup','company','based','launches','launch','scale','scaling','platform','europe','european','first','their','about','with','from','into','that','this','for','the','and','its','new','backed','secures','closes','lands','helps','small','businesses','business','powered','tech','eu-startups','tech.eu','sifted']);
const topicWords = [...new Set((txt($json.properties?.['Signal summary']) + ' ' + txt($json.properties?.Sector))
  .toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\(.*?\)/g, ' ').split(/[^a-z0-9-]+/)
  .filter(w => w.length >= 4 && !STOP.has(w) && !/^\d/.test(w) && !core.split(' ').includes(w)))].slice(0, 12);
return { json: { ...c, company, companyCore: core, domain, domainSource: domain ? 'Article' : null, countryTld, topicWords, q1, q2, q3, braveCalls: 0 } };"""
node("Prep search","n8n-nodes-base.code",2,[1360,200],{"jsCode":PREP,"mode":"runOnceForEachItem"})
link("Notion · get company","Prep search")

def brave(name,pos,q):
    return node(name,"n8n-nodes-base.httpRequest",4.2,pos,{
        "method":"GET","url":"https://api.search.brave.com/res/v1/web/search",
        "authentication":"genericCredentialType","genericAuthType":"httpHeaderAuth",
        "sendQuery":True,"queryParameters":{"parameters":[{"name":"q","value":q},{"name":"count","value":"5"},{"name":"result_filter","value":"web"}]},
        "sendHeaders":True,"headerParameters":{"parameters":[{"name":"Accept","value":"application/json"}]},
        "options":{"batching":{"batch":{"batchSize":1,"batchInterval":1500}}}},
        credentials={"httpHeaderAuth":{"id":"","name":"Brave Search API"}},onError="continueRegularOutput",
        retryOnFail=True,maxTries=3,waitBetweenTries=2000)

VERIFY=r"""// Deterministic LinkedIn verification. Accept only a linkedin.com/in profile whose
// title contains first AND last name AND whose title/snippet mentions the company.
const prev = $('%PREV%').item.json;
const n = s => String(s || '').toLowerCase().replace(/æ/g, 'ae').replace(/ø/g, 'o').replace(/œ/g, 'oe').replace(/ß/g, 'ss').replace(/ł/g, 'l').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/<[^>]+>/g, ' ');
const first = n(prev.first), last = n(prev.last);
const coTokens = [prev.companyCore, prev.domain ? prev.domain.split('.')[0] : '']
  .filter(t => t && t.length >= 3).map(n);
const results = $json.web?.results || [];
const cands = results.filter(r => /linkedin\.com\/in\//.test(r.url || '')).map(r => {
  const title = n(r.title), hay = title + ' ' + n(r.description);
  const nameOk = title.includes(first) && title.includes(last);
  const coOk = coTokens.some(t => hay.includes(t));
  return { url: r.url.split('?')[0], title: r.title, nameOk, coOk };
});
const hit = cands.find(c => c.nameOk && c.coOk);
const out = { ...prev, braveCalls: (prev.braveCalls || 0) + 1,
  braveError: ($json.error || $json.type === 'ErrorResponse') ? JSON.stringify($json.error || $json).slice(0, 200) : (prev.braveError || null) };
if (hit) {
  out.linkedin = hit.url;
  out.linkedinCandidate = null;
  out.linkedinMatch = `%ATTEMPT%: name + company matched in "${hit.title}"`;
} else {
  out.linkedin = null;
  const cand = cands.find(c => c.nameOk);
  out.linkedinCandidate = cand ? cand.url : (prev.linkedinCandidate || null);
  out.linkedinMatch = `%ATTEMPT%: no verified match (${cands.length} LinkedIn results, ${cands.filter(c => c.nameOk).length} name-only)` + (cand ? ` · check manually: ${cand.url}` : '');
}
return { json: out };"""
brave("Brave · LinkedIn attempt 1",[1580,200],"={{ $json.q1 }}")
link("Prep search","Brave · LinkedIn attempt 1")
node("Verify attempt 1","n8n-nodes-base.code",2,[1800,200],{"jsCode":VERIFY.replace("%PREV%","Prep search").replace("%ATTEMPT%","Attempt 1"),"mode":"runOnceForEachItem"})
link("Brave · LinkedIn attempt 1","Verify attempt 1")

node("LinkedIn found?","n8n-nodes-base.if",2.2,[2020,200],{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose","version":2},"conditions":[{"id":str(uuid.uuid4()),"leftValue":"={{ $json.linkedin }}","rightValue":"","operator":{"type":"string","operation":"notEmpty","singleValue":True}}],"combinator":"and"},"options":{}})
link("Verify attempt 1","LinkedIn found?")
brave("Brave · LinkedIn attempt 2",[2240,380],"={{ $json.q2 }}")
link("LinkedIn found?","Brave · LinkedIn attempt 2",1)
node("Verify attempt 2","n8n-nodes-base.code",2,[2460,380],{"jsCode":VERIFY.replace("%PREV%","Verify attempt 1").replace("%ATTEMPT%","Attempt 2").replace("prev.braveCalls || 0","prev.braveCalls || 1").replace("out.linkedinMatch = `Attempt 2: no","out.linkedinMatch = prev.linkedinMatch + ` | Attempt 2: no").replace("`Attempt 2: no verified match","`no verified match"),"mode":"runOnceForEachItem"})
link("Brave · LinkedIn attempt 2","Verify attempt 2")

def hunter(name,pos,path,params):
    return node(name,"n8n-nodes-base.httpRequest",4.2,pos,{
        "method":"GET","url":"https://api.hunter.io/v2/"+path,
        "authentication":"genericCredentialType","genericAuthType":"httpQueryAuth",
        "sendQuery":True,"queryParameters":{"parameters":params},
        "options":{"response":{"response":{"neverError":True}}}},
        credentials={"httpQueryAuth":{"id":"","name":"Hunter API"}},onError="continueRegularOutput")

hunter("Hunter · email finder",[4140,100],"email-finder",[
  {"name":"={{ $json.domain ? 'domain' : 'company' }}","value":"={{ $json.domain || $json.company }}"},
  {"name":"first_name","value":"={{ $json.first }}"},
  {"name":"last_name","value":"={{ $json.last }}"}])
node("Has domain?","n8n-nodes-base.if",2.2,[2460,100],{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose","version":2},"conditions":[{"id":str(uuid.uuid4()),"leftValue":"={{ $json.domain }}","rightValue":"","operator":{"type":"string","operation":"notEmpty","singleValue":True}}],"combinator":"and"},"options":{}})
link("LinkedIn found?","Has domain?",0)
link("Verify attempt 2","Has domain?")
CANDS=r"""// WEBSITE FAIL-SAFE, step 1 (rules): when the article gave no website, generate likely domains
// from the company name and check each one by opening its homepage (next node). Free, no search API.
// Runs once for ALL items: one contact in, up to 32 candidate items out. (Per-item mode can't return
// several items -> "A 'json' property isn't an object", the same bug we fixed in 20.)
const out = [];
$input.all().forEach((it, idx) => {
const p = it.json;
const tr = x => String(x || '').toLowerCase().replace(/æ/g, 'ae').replace(/ø/g, 'o').replace(/œ/g, 'oe').replace(/ß/g, 'ss').replace(/ł/g, 'l').normalize('NFD').replace(/[̀-ͯ]/g, '');
const words = tr(p.companyCore).split(/\s+/).filter(Boolean);
const joined = words.join(''), hyph = words.join('-'), first = words[0] || '';
const tlds = ['com', 'ai', 'io', 'co', 'eu', 'de', 'tech', 'app'];
if (p.countryTld && !tlds.includes(p.countryTld)) tlds.unshift(p.countryTld);
const set = [];
const add = d => { if (d && /^[a-z0-9-]+(\.[a-z]{2,}){1,2}$/.test(d) && !set.includes(d)) set.push(d); };
tlds.forEach(t => add(`${joined}.${t}`));
if (words.length > 1) { ['com', 'ai', 'io'].forEach(t => add(`${hyph}.${t}`)); if (first.length >= 4) ['com', 'ai', 'io'].forEach(t => add(`${first}.${t}`)); }
// Common startup patterns: get<name>.com, <name>hq.com, <name>app.com
// (tryholo.ai was the real Holo site; v2 never tried it)
['try', 'get', 'use'].forEach(pre => ['com', 'ai', 'io'].forEach(t => add(`${pre}${joined}.${t}`)));
[joined + 'hq.com', joined + 'app.com', joined + 'ai.com', joined + 'labs.com', joined + '.app'].forEach(add);
// Other European ccTLDs last (HQ country is often only known as 'Other EU')
['fi', 'se', 'dk', 'no', 'pl', 'cz', 'fr', 'es', 'it', 'be', 'pt', 'ee'].forEach(t => add(`${joined}.${t}`));
set.slice(0, 32).forEach((d, i) => out.push({ json: { ...p, candidate: d, candidateRank: i }, pairedItem: { item: idx } }));
});
return out;"""
node("Website candidates","n8n-nodes-base.code",2,[2460,-200],{"jsCode":CANDS})
link("Has domain?","Website candidates",1)
node("Fetch candidate homepage","n8n-nodes-base.httpRequest",4.2,[2700,-200],{
  "method":"GET","url":"={{ 'https://' + $json.candidate }}",
  "sendHeaders":True,"headerParameters":{"parameters":[{"name":"User-Agent","value":"Mozilla/5.0 (compatible; WaypointResearch/1.0; +https://noahhofmann.com)"}]},
  "options":{"batching":{"batch":{"batchSize":8,"batchInterval":200}},"timeout":8000,"redirect":{"redirect":{"followRedirects":True,"maxRedirects":4}},
             "response":{"response":{"neverError":True,"responseFormat":"text","outputPropertyName":"html"}}}},onError="continueRegularOutput")
link("Website candidates","Fetch candidate homepage")
PICKWEB=r"""// WEBSITE FAIL-SAFE, step 2 (rules). INPUT: one fetched homepage per candidate domain (same order as
// 'Website candidates'). OUTPUT: one item per contact with domain = best verified candidate or ''.
// A candidate is ACCEPTED only if all three hold:
//   1. Not parked / for sale / placeholder (broker phrases, "coming soon", tiny pages).
//   2. Company name appears as a WHOLE WORD in title/meta or text ("holo" must not match "holographic").
//   3. At least one topic word from the funding article appears on the page (same business, not a namesake).
// WHY: v2 accepted ambio.com (a for-sale page), holo.pl (a hologram sticker shop) and miracly.com
// (coming-soon placeholder). A wrong domain is worse than none: Hunter then finds wrong people's emails.
// If no candidate passes, domainSource = 'Not found' -> the company shows in 'Companies that need a look'
// and gets one Telegram question (WP · 50) instead of a guess.
const cands = $('Website candidates').all();
const tr = x => String(x || '').toLowerCase().replace(/æ/g, 'ae').replace(/ø/g, 'o').replace(/œ/g, 'oe').replace(/ß/g, 'ss').replace(/ł/g, 'l').normalize('NFD').replace(/[̀-ͯ]/g, '');
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const PARKED = new RegExp([
  'domain (is )?for sale', 'buy this domain', 'this domain (name )?(may be|is) for sale', 'interested in (buying|purchasing|acquiring) this domain',
  'contact the (seller|owner)', 'message the seller', 'make (an|me an|a) offer', 'listed by', 'vip seller', 'domain broker',
  'parked (free|domain|by)', 'sedo', 'dan\\.com', 'afternic', 'hugedomains', 'brandbucket', 'squadhelp', 'atom\\.com', 'efty', 'undeveloped\\.com',
  'godaddy\\.com/domainsearch', 'domain has expired', 'coming soon', 'launching soon', 'under construction', 'website is (currently )?under',
  'this site can.?t be reached', 'default web page', 'welcome to nginx', 'it works!', 'index of /'].join('|'), 'i');
const byContact = {};
$input.all().forEach((it, i) => {
  const c = cands[i].json; const html = typeof it.json.html === 'string' ? it.json.html : '';
  const k = c.contactPageId; byContact[k] = byContact[k] || { base: c, firstIdx: i, hits: [], tried: 0, rejected: [] };
  const g = byContact[k]; g.tried++;
  if (html.length < 300) return;
  const text = html.replace(/<(script|style|noscript)[\s\S]*?<\/\1>/gi, ' ').replace(/<[^>]+>/g, ' ').replace(/&nbsp;|&#160;/g, ' ').replace(/\s+/g, ' ').slice(0, 40000);
  if (PARKED.test(text.slice(0, 15000)) || text.trim().length < 200) { g.rejected.push(`${c.candidate} (parked/placeholder)`); return; }
  const title = (html.match(/<title[^>]*>([\s\S]*?)<\/title>/i) || [])[1] || '';
  const meta = [...html.matchAll(/<meta[^>]+(?:og:site_name|og:title|application-name|description)[^>]+content=["']([^"']+)/gi)].map(m => m[1]).join(' ');
  const name = tr(c.companyCore).trim();
  if (name.length < 3) return;
  const nameRe = new RegExp('(^|[^a-z0-9])' + esc(name).replace(/ /g, '[\\s-]?') + '($|[^a-z0-9])', 'i');
  const inTitle = nameRe.test(tr(title + ' ' + meta));
  const inText = inTitle || nameRe.test(tr(text));
  if (!inText) return;
  const page = tr(title + ' ' + meta + ' ' + text);
  const topicHits = (c.topicWords || []).filter(w => page.includes(w.replace(/s$/, '')));
  if ((c.topicWords || []).length && topicHits.length === 0) { g.rejected.push(`${c.candidate} (name found, but nothing about: ${(c.topicWords || []).slice(0, 4).join(', ')})`); return; }
  g.hits.push({ rank: c.candidateRank, domain: c.candidate, inTitle, topicHits: topicHits.length, html });
});
return Object.values(byContact).map(g => {
  // Rank: name in title/meta, then more topic words, then candidate order (.com first)
  const best = g.hits.sort((a, b) => (b.inTitle - a.inTitle) || (b.topicHits - a.topicHits) || (a.rank - b.rank))[0] || null;
  const { candidate, candidateRank, ...base } = g.base;
  const why = best ? ` | Website: ${best.domain} (name in ${best.inTitle ? 'title' : 'text'}, ${best.topicHits} topic words)`
    : ` | Website: not found among ${g.tried} likely domains` + (g.rejected.length ? `; rejected ${g.rejected.slice(0, 3).join('; ')}` : '');
  return { json: { ...base, domain: best ? best.domain : '', domainSource: best ? 'Website check' : 'Not found',
      homepageHtml: best ? best.html.slice(0, 200000) : '', websiteRejected: g.rejected, linkedinMatch: base.linkedinMatch + why },
    pairedItem: { item: g.firstIdx } };
});"""
node("Pick verified website","n8n-nodes-base.code",2,[2940,-200],{"jsCode":PICKWEB})
link("Fetch candidate homepage","Pick verified website")
notion("Notion · save company domain",[3180,-380],"PATCH","=https://api.notion.com/v1/pages/{{ $json.companyPageId }}",
  '={{ JSON.stringify({ properties: { Domain: { url: $json.domain ? "https://" + $json.domain : null }, "Domain source": { select: { name: $json.domainSource } } } }) }}',onError="continueRegularOutput")
link("Pick verified website","Notion · save company domain")
node("Ready for Hunter","n8n-nodes-base.code",2,[3180,100],{"jsCode":"// Join point: domain from the article, or from the website fail-safe, or none.\nreturn { json: $json };","mode":"runOnceForEachItem"})
link("Has domain?","Ready for Hunter",0)
link("Pick verified website","Ready for Hunter")
PAGES=r"""// EMAIL FAIL-SAFE, step 1: list the company's own pages that usually publish addresses
// (Impressum is legally required in DACH). One item per page; homepage HTML is reused if we have it.
// Runs once for ALL items (several pages per contact).
const paths = ['', '/impressum', '/imprint', '/legal-notice', '/contact', '/kontakt', '/about', '/team'];
const out = [];
$input.all().forEach((it, idx) => {
  const p = it.json;
  if (!p.domain) out.push({ json: { ...p, pageUrl: '' }, pairedItem: { item: idx } });
  else paths.forEach(path => out.push({ json: { ...p, pageUrl: `https://${p.domain}${path}` }, pairedItem: { item: idx } }));
});
return out;"""
node("Site pages to scan","n8n-nodes-base.code",2,[3420,100],{"jsCode":PAGES})
link("Ready for Hunter","Site pages to scan")
node("Fetch site page","n8n-nodes-base.httpRequest",4.2,[3660,100],{
  "method":"GET","url":"={{ $json.pageUrl || 'https://invalid.invalid' }}",
  "sendHeaders":True,"headerParameters":{"parameters":[{"name":"User-Agent","value":"Mozilla/5.0 (compatible; WaypointResearch/1.0; +https://noahhofmann.com)"}]},
  "options":{"batching":{"batch":{"batchSize":8,"batchInterval":200}},"timeout":8000,"redirect":{"redirect":{"followRedirects":True,"maxRedirects":4}},
             "response":{"response":{"neverError":True,"responseFormat":"text","outputPropertyName":"html"}}}},onError="continueRegularOutput")
link("Site pages to scan","Fetch site page")
EMAILS=r"""// EMAIL FAIL-SAFE, step 2 (rules): collect addresses published on the company's own domain.
// Personal address that matches the contact's name -> candidate (Hunter verifies it later).
// Generic inbox (info@, hello@ ...) -> saved on the company as a fallback channel, never as the person's email.
const pages = $('Site pages to scan').all();
const tr = x => String(x || '').toLowerCase().replace(/æ/g, 'ae').replace(/ø/g, 'o').replace(/œ/g, 'oe').replace(/ß/g, 'ss').replace(/ł/g, 'l').normalize('NFD').replace(/[̀-ͯ]/g, '');
const GENERIC = /^(info|hello|hallo|hi|contact|kontakt|office|team|mail|sales|vertrieb|business|partners?|partnerships|press|presse|support|service)$/;
const SKIPLOCAL = /^(privacy|datenschutz|dpo|gdpr|jobs|careers|karriere|bewerbung|noreply|no-reply|webmaster|abuse)$/;
const groups = {};
$input.all().forEach((it, i) => {
  const p = pages[i].json; const k = p.contactPageId;
  groups[k] = groups[k] || { base: p, firstIdx: i, emails: new Set() };
  let html = typeof it.json.html === 'string' ? it.json.html : '';
  if (p.pageUrl === `https://${p.domain}` && !html && p.homepageHtml) html = p.homepageHtml;
  if (!p.domain || !html) return;
  const clean = html.replace(/\s*(\[at\]|\(at\)|\{at\}| at )\s*/gi, '@').replace(/\s*(\[dot\]|\(dot\)| dot )\s*/gi, '.').replace(/&#64;|&#x40;/g, '@');
  for (const m of clean.matchAll(/[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/gi)) {
    const e = m[0].toLowerCase().replace(/\.$/, '');
    if (e.endsWith('@' + p.domain) || e.endsWith('.' + p.domain)) groups[k].emails.add(e);
  }
});
return Object.values(groups).map(g => {
  const p = g.base; const first = tr(p.first), last = tr(p.last);
  const all = [...g.emails];
  const local = e => tr(e.split('@')[0]);
  const personal = all.find(e => last.length >= 3 && local(e).includes(last)) || all.find(e => first.length >= 3 && local(e).replace(/[^a-z]/g, '') === first) || null;
  const inbox = all.filter(e => GENERIC.test(local(e))).sort((a, b) => { const o = ['hello', 'info', 'contact', 'kontakt']; const r = x => { const i = o.indexOf(local(x)); return i === -1 ? 99 : i; }; return r(a) - r(b); })[0] || null;
  const { pageUrl, homepageHtml, ...base } = p;
  return { json: { ...base, siteEmails: all.filter(e => !SKIPLOCAL.test(local(e))).slice(0, 10), sitePersonalEmail: personal, companyInbox: inbox,
      linkedinMatch: p.linkedinMatch + (p.domain ? ` | Site emails: ${all.length ? all.slice(0, 4).join(', ') : 'none published'}` : '') },
    pairedItem: { item: g.firstIdx } };
});"""
node("Extract site emails","n8n-nodes-base.code",2,[3900,100],{"jsCode":EMAILS})
link("Fetch site page","Extract site emails")
node("Has company inbox?","n8n-nodes-base.if",2.2,[4140,-120],{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose","version":2},"conditions":[{"id":str(uuid.uuid4()),"leftValue":"={{ $json.companyInbox }}","rightValue":"","operator":{"type":"string","operation":"notEmpty","singleValue":True}}],"combinator":"and"},"options":{}})
link("Extract site emails","Has company inbox?")
notion("Notion · save company inbox",[4380,-120],"PATCH","=https://api.notion.com/v1/pages/{{ $json.companyPageId }}",
  '={{ JSON.stringify({ properties: { "Company inbox": { email: $json.companyInbox } } }) }}',onError="continueRegularOutput")
link("Has company inbox?","Notion · save company inbox",0)
link("Extract site emails","Hunter · email finder")

DECIDE=r"""// Read Hunter finder result. Verify only when the finder isn't already sure.
// Paired item points back to whichever verify node fed this branch.
const prev = $('Extract site emails').item.json;
const d = $json.data || {};
const tr = x => String(x || '').toLowerCase().replace(/æ/g, 'ae').replace(/ø/g, 'o').replace(/œ/g, 'oe').replace(/ß/g, 'ss').replace(/ł/g, 'l').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]/g, '');
const core = tr(prev.companyCore);
const stemOf = h => tr(String(h || '').split('.').slice(0, -1).join(''));
const domainOk = h => !!h && core.length >= 3 && (stemOf(h).includes(core) || (stemOf(h).length >= 4 && core.includes(stemOf(h))));
// If WE gave Hunter the domain, trust it. If Hunter guessed the domain from the company name, it must match.
const wrongDomain = !prev.domain && d.domain && !domainOk(d.domain);
const hunterEmail = wrongDomain ? null : (d.email || null);
// Fallback: an address the company itself publishes for this person (then always verified)
const email = hunterEmail || prev.sitePersonalEmail || null;
const emailSource = hunterEmail ? 'Hunter' : (prev.sitePersonalEmail ? 'Website' : null);
const finderStatus = d.verification?.status || null;
const hunterDomain = d.domain || null;
return { json: { ...prev,
  email, emailSource, emailScore: hunterEmail ? (d.score ?? null) : null, finderStatus: hunterEmail ? finderStatus : null,
  hunterCredits: d.email ? 1 : 0, hunterDomain, wrongDomain,
  hunterError: $json.errors ? JSON.stringify($json.errors).slice(0, 200) : null,
  needVerify: !!email && !(hunterEmail && finderStatus === 'valid') } };"""
node("Decide verify","n8n-nodes-base.code",2,[4380,200],{"jsCode":DECIDE,"mode":"runOnceForEachItem"})
link("Hunter · email finder","Decide verify")
node("Needs verification?","n8n-nodes-base.if",2.2,[4620,200],{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose","version":2},"conditions":[{"id":str(uuid.uuid4()),"leftValue":"={{ $json.needVerify }}","rightValue":True,"operator":{"type":"boolean","operation":"true","singleValue":True}}],"combinator":"and"},"options":{}})
link("Decide verify","Needs verification?")
hunter("Hunter · verify (no email sent)",[4860,380],"email-verifier",[{"name":"email","value":"={{ $json.email }}"}])
link("Needs verification?","Hunter · verify (no email sent)",0)

BUILD=r"""// Final decision + Notion update. Only 'valid' (or accept_all with score >= 90)
// becomes 'Ready to draft'. Nothing is ever sent from this workflow.
const d = $('Decide verify').item.json;
const v = $json.data && $json.data.status && $json.data.email === d.email ? $json.data : null;
let status = !d.email ? 'not found' : (v ? v.status : (d.finderStatus || 'unknown'));
if (!['valid','accept_all','unknown','invalid','not found'].includes(status)) status = 'unknown';
const credits = d.hunterError ? 0 : d.hunterCredits + (v ? 0.5 : 0);
const ok = status === 'valid' || (status === 'accept_all' && (d.emailScore || 0) >= 90);
// Auth / quota / network errors say nothing about the person: keep "Needs email" so the next run retries.
const apiError = !!d.hunterError || (!!d.braveError && !d.linkedin && !d.email);
// Outcome = which VERIFIED channels exist. Never a vague "no email": the Reach column in Notion shows the same in words.
//   verified email            -> Ready to draft (email; LinkedIn may exist too)
//   verified LinkedIn only    -> LinkedIn only (Thursday: LinkedIn message draft)
//   unconfirmed lead only     -> Check manually (accept_all email or name-only LinkedIn candidate)
//   nothing                   -> Not reachable
//   API / auth error          -> stays Needs email, retried next run
const unconfirmed = (status === 'accept_all' && !ok) || !!d.linkedinCandidate;
const nextStatus = apiError ? 'Needs email' : ok ? 'Ready to draft' : d.linkedin ? 'LinkedIn only' : unconfirmed ? 'Check manually' : 'Not reachable';
const t = s => [{ type: 'text', text: { content: String(s ?? '').slice(0, 1900) } }];
const props = {
  'Status': { status: { name: nextStatus } },
  'LinkedIn match': { rich_text: t(d.linkedinMatch + (d.hunterDomain && !d.domain ? ` | Hunter guessed domain: ${d.hunterDomain}${d.wrongDomain ? ' (does not match company, result discarded)' : ''}` : '') + (d.braveError ? ` | Brave error: ${d.braveError}` : '') + (d.hunterError ? ` | Hunter error: ${d.hunterError}` : '')) },
  'Enriched at': { date: { start: new Date().toISOString() } }
};
if (d.linkedin) props['LinkedIn'] = { url: d.linkedin };
if (d.linkedinCandidate && !d.linkedin) props['LinkedIn candidate'] = { url: d.linkedinCandidate };
if (d.email && status !== 'invalid') { props['Email'] = { email: d.email }; if (d.emailSource) props['Email source'] = { select: { name: d.emailSource } }; }
if (d.emailScore !== null) props['Email score'] = { number: d.emailScore };
if (!apiError) props['Email status'] = { select: { name: status } };
return { json: { contactPageId: d.contactPageId, name: d.name, company: d.company,
  linkedin: d.linkedin, email: d.email, status: apiError ? 'api error' : status, ready: ok, apiError,
  braveCalls: d.braveCalls, hunterCredits: credits,
  notionBody: { properties: props } } };"""
node("Build contact update","n8n-nodes-base.code",2,[5100,200],{"jsCode":BUILD,"mode":"runOnceForEachItem"})
link("Needs verification?","Build contact update",1)
link("Hunter · verify (no email sent)","Build contact update")

notion("Notion · update contact",[5340,200],"PATCH","=https://api.notion.com/v1/pages/{{ $json.contactPageId }}","={{ JSON.stringify($json.notionBody) }}")
link("Build contact update","Notion · update contact")

SUMMARY=r"""// Book usage against the monthly budget and return a summary to the caller.
const rows = $('Build contact update').all().map(i => i.json);
const brave = rows.reduce((a, r) => a + (r.braveCalls || 0), 0);
const hunter = rows.reduce((a, r) => a + (r.hunterCredits || 0), 0);
const s = $getWorkflowStaticData('global');
s.brave = (s.brave || 0) + brave;
s.hunter = (s.hunter || 0) + hunter;
return [{ json: {
  enriched: rows.length,
  readyToDraft: rows.filter(r => r.ready).length,
  apiErrors: rows.filter(r => r.apiError).length,
  linkedinFound: rows.filter(r => r.linkedin).length,
  braveCallsThisRun: brave, hunterCreditsThisRun: hunter,
  braveUsedThisMonth: s.brave, hunterUsedThisMonth: s.hunter,
  contacts: rows.map(r => ({ name: r.name, company: r.company, status: r.status, linkedin: !!r.linkedin }))
} }];"""
node("Run summary + budget","n8n-nodes-base.code",2,[5580,200],{"jsCode":SUMMARY})
link("Notion · update contact","Run summary + budget")

M30=r"""const r = $json;
const c = { in: r.enriched, ready: r.readyToDraft, li: r.linkedinFound, apiErr: r.apiErrors, brave: r.braveCallsThisRun, hunter: r.hunterCreditsThisRun };
const x = { braveMonth: r.braveUsedThisMonth, hunterMonth: r.hunterUsedThisMonth };
const view = (c, x) => ({ in: c.in, out: c.ready + c.li, errors: c.apiErr, costEur: 0, skip: !c.in,
  notes: `${c.ready} ready to draft, ${c.li} with LinkedIn, ${c.apiErr} API errors. Brave ${c.brave} (month ${x.braveMonth}/300), Hunter ${c.hunter} (month ${x.hunterMonth}/40). Free tiers: cost 0.` });"""
node("Build run log","n8n-nodes-base.code",2,[5800,200],{"jsCode":runlog_code("Config + budget","Enrich","Enrich",M30)})
link("Run summary + budget","Build run log")
node("Notion · log run","n8n-nodes-base.httpRequest",4.2,[6020,200],runlog_http_params(),onError="continueRegularOutput")
link("Build run log","Notion · log run")
node("Remember run log","n8n-nodes-base.code",2,[6240,200],{"jsCode":REMEMBER})
link("Notion · log run","Remember run log")

STICKIES=[
("Note · 30 overview",[0,-560],720,330,"""## WP · 30 Enrich contacts: what and why
**Job:** turn a named person (from 20) into a reachable contact: verified LinkedIn and/or verified email.
**Called by:** WP · 00 once per run, after the run log. Can be run alone (Test workflow) to retry.
**Outcome per contact (Status):** Ready to draft (verified email) · LinkedIn only · Check manually (unconfirmed lead) · Not reachable · stays Needs email on API errors.
**Design rules:** rules decide, never an LLM (a wrong person is worse than no person) · every accept/reject writes its reason to *LinkedIn match* · budget guard before any paid call.
Full docs: docs/30-enrich-contacts.md in the GitHub repo."""),
("Note · Selection",[240,-200],560,240,"""### 1 · Selection + budget
Loads Needs email contacts AND contacts further down the funnel. A company that already has a reachable contact is skipped, so credits go to new companies.
Order: CEO/MD → founders → sales → partnerships. One contact per company per run, max 8 per run.
Budget: monthly counters (300 Brave, 40 Hunter) live in workflow static data; only active (published) runs count."""),
("Note · LinkedIn",[1560,-200],620,240,"""### 2 · LinkedIn (Brave search, 2 attempts)
Accepted only if the result title has first AND last name AND the company name (or domain) appears in title/snippet. Name-only hits are stored as *LinkedIn candidate* for you to check, never used automatically.
Why so strict: two people with the same name are common; a wrong profile poisons the draft."""),
("Note · Website",[2440,-680],820,360,"""### 3 · Website fail-safe v3 (only if the article gave no website)
**In:** contact + company core name + topic words from the funding article. **Nodes:** Website candidates → Fetch candidate homepage → Pick verified website → Notion · save company domain.
**Logic:** ~30 likely domains (name.com/.ai/.io…, country TLD, try/get/use<name>, <name>ai.com, EU ccTLDs). Each homepage must pass ALL of: **(1)** not parked / for sale / placeholder ("contact the seller", "make an offer", "coming soon"…), **(2)** company name as a WHOLE word, **(3)** ≥1 topic word from the article on the page (same business, not a namesake).
**Out:** Domain + Domain source *Website check*, or *Not found* → you get one 🌐 question in Telegram (WP · 50).
**Why:** v2 accepted ambio.com (for sale), holo.pl (hologram stickers) and miracly.com (coming soon). A wrong domain means emails to the wrong people."""),
("Note · Email",[3420,-380],900,260,"""### 4 · Email: site scan + Hunter
**Site scan (free):** homepage, /impressum, /imprint, /legal-notice, /contact, /kontakt, /about, /team. Addresses on the company's own domain are collected. A personal address matching the contact's name becomes a fallback candidate; a generic inbox (hello@, info@) is saved on the **company** as *Company inbox*, never as the person's email.
**Hunter:** finder (1 credit, only when found) → verifier (0.5) unless already sure. Website-found addresses are **always** verified. **No email is ever sent.** If Hunter guessed the domain itself, it must match the company name. API errors keep Needs email for a retry.""")]
for nm,pos,wd,ht,txt in STICKIES: node(nm,"n8n-nodes-base.stickyNote",1,pos,{"width":wd,"height":ht,"content":txt})

wf={"name":"WP · 30 Enrich contacts (sub-workflow)","nodes":apply_ids(N),"connections":C,"settings":{"executionOrder":"v1","timezone":"Europe/Berlin","saveManualExecutions":True},"pinData":{}}
json.dump(wf,open("/home/claude/waypoint-engine/workflows/30-enrich-contacts.json","w"),indent=2,ensure_ascii=False)
print(len(N),"nodes")
