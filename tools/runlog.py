# Shared: one row per execution in Notion › Runs. Used by gen30/40/50.
RUNS_DB='84a655097a4449588604e918ae009c1b'
def runlog_code(cfg_node, wf_label, select_name, mapping_js):
    """mapping_js must define: const m = { in, out, errors, costEur, notes, skip };"""
    return r"""// RUN LOG: one row per execution in Notion › Runs (runtime, volume, errors, estimated cost).
// Why: the dashboard's System health table showed only Intake; sub-workflows were invisible.
const started = $('%CFG%').first().json.startedAt;
%MAP%
if (m.skip) return [];   // nothing happened (e.g. a refill run with no new cards): no row
const dur = started ? Math.round((Date.now() - new Date(started).getTime()) / 1000) : null;
const t = x => [{ type: 'text', text: { content: String(x ?? '').slice(0, 1900) } }];
return [{ json: { parent: { database_id: '%DB%' }, properties: {
  'Run': { title: t(`%WF% ${new Date(started || Date.now()).toISOString().slice(0, 16).replace('T', ' ')}`) },
  'Workflow': { select: { name: '%SEL%' } },
  'Status': { select: { name: m.errors ? (m.out > 0 ? 'Partial' : 'Failed') : 'Success' } },
  'Started': { date: { start: started || new Date().toISOString() } },
  'Duration s': { number: dur },
  'Execution ID': { rich_text: t($execution.id) },
  'Items in': { number: m.in ?? null }, 'Items out': { number: m.out ?? null },
  'Errors': { number: m.errors || 0 }, 'Cost EUR': { number: m.costEur ?? null },
  'Notes': { rich_text: t(m.notes) } } } }];""".replace('%CFG%',cfg_node).replace('%MAP%',mapping_js).replace('%DB%',RUNS_DB).replace('%WF%',wf_label).replace('%SEL%',select_name)
