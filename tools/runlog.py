# Shared: ONE row per execution in Notion › Runs, even when the summary node runs several times
# (n8n runs a node once per arriving branch: 30 and 40 have joins, so v1 of this wrote 2–3 rows per run).
# Fix: counters are summed in $execution.customData; the first pass creates the row, later passes PATCH it.
RUNS_DB = '84a655097a4449588604e918ae009c1b'

def runlog_code(cfg_node, wf_label, select_name, mapping_js):
    """mapping_js must define:
         const c = { ...numbers for THIS pass, summed across passes... };
         const x = { ...latest values, not summed... };
         const view = (c, x) => ({ in, out, errors, costEur, notes, skip });"""
    return (r"""// RUN LOG (upsert): one row per execution in Notion › Runs: runtime, volume, errors, estimated cost.
// This node can run several times per execution (once per branch that reaches it). Counters are summed
// in the execution's custom data, and the same Notion row is updated instead of creating a new one.
const started = $('%CFG%').first().json.startedAt;
%MAP%
const cd = $execution.customData;
let acc = {}; try { acc = JSON.parse(cd.get('runlog') || '{}'); } catch (e) { acc = {}; }
acc.c = acc.c || {};
for (const k of Object.keys(c)) acc.c[k] = (acc.c[k] || 0) + (Number(c[k]) || 0);
const m = view(acc.c, x);
cd.set('runlog', JSON.stringify({ c: acc.c, pageId: acc.pageId || null }));
if (m.skip) return [];
const dur = started ? Math.round((Date.now() - new Date(started).getTime()) / 1000) : null;
const t = v => [{ type: 'text', text: { content: String(v ?? '').slice(0, 1900) } }];
const properties = {
  'Run': { title: t(`%WF% ${new Date(started || Date.now()).toISOString().slice(0, 16).replace('T', ' ')}`) },
  'Workflow': { select: { name: '%SEL%' } },
  'Status': { select: { name: m.errors ? (m.out > 0 ? 'Partial' : 'Failed') : 'Success' } },
  'Started': { date: { start: started || new Date().toISOString() } },
  'Duration s': { number: dur },
  'Execution ID': { rich_text: t($execution.id) },
  'Items in': { number: m.in ?? null }, 'Items out': { number: m.out ?? null },
  'Errors': { number: m.errors || 0 }, 'Cost EUR': { number: m.costEur ?? null },
  'Notes': { rich_text: t(m.notes) } };
if (m.quality != null) properties['Quality avg'] = { number: m.quality };
if (m.model) properties['Model'] = { rich_text: t(m.model) };
return [{ json: acc.pageId
  ? { method: 'PATCH', url: 'https://api.notion.com/v1/pages/' + acc.pageId, body: { properties } }
  : { method: 'POST', url: 'https://api.notion.com/v1/pages', body: { parent: { database_id: '%DB%' }, properties } } }];"""
    ).replace('%CFG%', cfg_node).replace('%MAP%', mapping_js).replace('%DB%', RUNS_DB).replace('%WF%', wf_label).replace('%SEL%', select_name)

REMEMBER = r"""// Remember the Runs row created in this execution, so a later pass updates it instead of adding a row.
const cd = $execution.customData;
let acc = {}; try { acc = JSON.parse(cd.get('runlog') || '{}'); } catch (e) {}
if (!acc.pageId && $json.id) { acc.pageId = $json.id; cd.set('runlog', JSON.stringify(acc)); }
return [{ json: { runLogPageId: acc.pageId || null } }];"""

NOTION_CRED = {"notionApi": {"id": "qrCZkB1IdXKr7Sp3", "name": "Notion account"}}

def runlog_http_params():
    return {"method": "={{ $json.method }}", "url": "={{ $json.url }}",
            "authentication": "predefinedCredentialType", "nodeCredentialType": "notionApi",
            "sendHeaders": True, "headerParameters": {"parameters": [{"name": "Notion-Version", "value": "2022-06-28"}]},
            "sendBody": True, "specifyBody": "json", "jsonBody": "={{ JSON.stringify($json.body) }}", "options": {}}

# ---- Credential + workflow IDs from Noah's n8n (16 Oct). Applied to every generated workflow so imports need no clicks.
CRED_IDS = {
    "notionApi":      {"id": "qrCZkB1IdXKr7Sp3", "name": "Notion account"},
    "openAiApi":      {"id": "pdSFtuDMCaKd3CHG", "name": "OpenAi account"},
    "gmailOAuth2":    {"id": "SZBYk0OCrdNe1W56", "name": "Gmail account"},
    "httpHeaderAuth": {"id": "LeyoiGdCQBySGpwl", "name": "Brave Search API"},
    "httpQueryAuth":  {"id": "Ijnmypzzm24UpmJD", "name": "Hunter API"},
}
ANTHROPIC = {"anthropicApi": {"id": "GZsdXTaGEKzuDNrl", "name": "Anthropic account"}}
WF_ERROR = "gx1X9dLMg8Hqn5lI"   # WP · 90 Error handler
TG_APPROVALS = {"telegramApi": {"id": "x17tu5yr5xFWMSsZ", "name": "Telegram approvals"}}
TG_ALERTS    = {"telegramApi": {"id": "GH3lzZFd7mdFuTUq", "name": "Telegram alerts"}}
WF_IDS = {"50": "nKdLZEFyebsDumCl", "51": "iwDMW5Mq4s7mlia4"}

def apply_ids(nodes):
    for n in nodes:
        t, p = n["type"], n["parameters"]
        if t == "n8n-nodes-base.httpRequest":
            if p.get("nodeCredentialType") == "notionApi": n["credentials"] = {"notionApi": CRED_IDS["notionApi"]}
            elif p.get("genericAuthType") == "httpHeaderAuth": n["credentials"] = {"httpHeaderAuth": CRED_IDS["httpHeaderAuth"]}
            elif p.get("genericAuthType") == "httpQueryAuth": n["credentials"] = {"httpQueryAuth": CRED_IDS["httpQueryAuth"]}
        elif t == "@n8n/n8n-nodes-langchain.lmChatOpenAi": n["credentials"] = {"openAiApi": CRED_IDS["openAiApi"]}
        elif t == "n8n-nodes-base.gmail": n["credentials"] = {"gmailOAuth2": CRED_IDS["gmailOAuth2"]}
        elif t == "@n8n/n8n-nodes-langchain.lmChatAnthropic": n["credentials"] = ANTHROPIC
    return nodes
