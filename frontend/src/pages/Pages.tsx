import { useState } from 'react'
import { FilePlus, FolderPlus, ChevronsDown, ChevronsUp, Plus, Play } from 'lucide-react'
import { CaseDTO, timeAgo } from '../types'
import { useApp } from '../context'
import * as api from '../services/api'
import { NodePicker } from './helpers'
import { Empty, Head, Pill, iconFor } from '../components/ui'
import { EvidenceTree } from '../components/Tree'
import { ChainOfCustody, NodeDetails } from '../components/Details'
import { ActivityFeed, EvidenceNetwork, SummaryCards, Traversal } from '../components/Visuals'

function CaseCard({ cs }: { cs: CaseDTO }) {
  const c = useApp()
  return (
    <button className="casecard" onClick={() => { c.openCase(cs.id); c.go('case') }}>
      <div className="cc-main"><code>{cs.id}</code><h3>{cs.name}</h3><p className="muted">{cs.description}</p></div>
      <div className="cc-stat"><span>Evidence</span><b>{cs.evidence_count} items</b></div>
      <div className="cc-stat"><span>Groups</span><b>{cs.group_count}</b></div>
      <div className="cc-stat"><span>Investigator</span><b>{cs.investigator}</b></div>
      <div className="cc-stat"><span>Last activity</span><b>{timeAgo(cs.last_activity_at)}</b></div>
      <div className="cc-stat"><Pill s={cs.status} /><span className={'prio pr-' + cs.priority.toLowerCase()}>{cs.priority}</span></div>
    </button>
  )
}

export function Overview() {
  const c = useApp(), s = c.stats
  if (!s) return <Empty t="No statistics available." />
  const pct = (n: number) => (s.total_evidence ? Math.round((n / s.total_evidence) * 100) : 0)
  const metrics: [string, string, string][] = [['Active cases', String(s.active_cases), `${s.total_cases} investigations in total`], ['Total evidence', String(s.total_evidence), `${s.integrity.analyzed} analyzed`], ['Evidence groups', String(s.evidence_groups), `across ${s.total_cases} cases`], ['Pending analysis', String(s.pending_analysis), `${pct(s.pending_analysis)}% of evidence`], ['Verified items', String(s.verified_evidence), `${pct(s.verified_evidence)}% of evidence`]]
  const seg: [string, number, string][] = [['Analyzed', s.integrity.analyzed, 'ib-blue'], ['Verified', s.integrity.verified, 'ib-green'], ['Pending', s.integrity.pending, 'ib-amber'], ['Flagged', s.integrity.flagged, 'ib-red']]
  return (
    <>
      <section className="hero">
        <div><span className="eyebrow">Secure investigation environment</span><h1>Digital Evidence Command Center</h1><p>Monitor investigations, evidence integrity and forensic analysis from one workspace.</p></div>
        <div className="metrics">{metrics.map(([k, v, t]) => <div key={k} className="metric"><span>{k}</span><b>{v}</b><em className="up">{t}</em></div>)}</div>
      </section>
      <div className="cols">
        <section className="panel"><h2>Evidence Network</h2><p className="muted">Composite hierarchy of {c.curCase.id}, built from the backend tree. Select a node to open it.</p><EvidenceNetwork root={c.cur} /></section>
        <div>
          <section className="panel"><h2>Evidence Integrity</h2><div className="intbar">{seg.map(([k, n, cl]) => n > 0 && <i key={k} className={cl} style={{ flex: n }} title={`${k}: ${n}`} />)}</div>
            <div className="intleg">{seg.map(([k, n, cl]) => <span key={k}><i className={cl} />{k} {n}</span>)}</div></section>
          <section className="panel"><h2>Recent Activity</h2><ActivityFeed items={c.activity.slice(0, 5)} /></section>
        </div>
      </div>
      <h2>Recent Investigations</h2>
      <div className="stack">{c.cases.map(cs => <CaseCard key={cs.id} cs={cs} />)}</div>
    </>
  )
}

export function Investigations() {
  const c = useApp()
  return (
    <>
      <Head t="Investigations" s="Each investigation is the root Composite of its evidence tree."><button className="btn" onClick={() => c.modal({ kind: 'newcase' })}><Plus size={15} /> New Investigation</button></Head>
      <div className="stack">{c.cases.map(cs => <CaseCard key={cs.id} cs={cs} />)}</div>
    </>
  )
}

function Workspace() {
  const c = useApp()
  const target = c.sel.isComposite() ? c.sel : c.sel.getParent() ?? c.cur
  return (
    <div className="work">
      <div className="card treecard">
        <div className="tbar"><b>Evidence Hierarchy</b>
          <div><button className="btn sm" onClick={() => c.modal({ kind: 'add', target })}><FilePlus size={14} /> Add Evidence</button>
            <button className="btn sm ghost" onClick={() => c.modal({ kind: 'group', target })}><FolderPlus size={14} /> Create Group</button>
            <button className="iconbtn" aria-label="Expand all" onClick={() => c.expand(c.cur.all().filter(n => n.isComposite()).map(n => n.getId()))}><ChevronsDown size={16} /></button>
            <button className="iconbtn" aria-label="Collapse all" onClick={c.collapseAll}><ChevronsUp size={16} /></button></div></div>
        <p className="muted small">Adding to: {target.path().map(p => p.getName()).join(' → ')}</p>
        <EvidenceTree root={c.cur} />
      </div>
      <NodeDetails node={c.sel} />
    </div>
  )
}

export function CaseDetails({ full }: { full?: boolean }) {
  const c = useApp(), cs = c.curCase
  return (
    <>
      {!full && <button className="btn ghost sm" onClick={() => c.go('investigations')}>← All investigations</button>}
      <div className="casehead">
        <div><code>{cs.id}</code><h1>{cs.name}</h1><p className="muted">{cs.description}</p></div>
        <div className="chmeta"><div><span>Status</span><Pill s={cs.status} /></div><div><span>Priority</span><span className={'prio pr-' + cs.priority.toLowerCase()}>{cs.priority}</span></div><div><span>Investigator</span><b>{cs.investigator}</b></div></div>
      </div>
      <Workspace />
    </>
  )
}

export function Vault() {
  const c = useApp()
  const [q, setQ] = useState(''), [f, setF] = useState('All')
  const rows = Object.values(c.trees).flatMap(t => t.all()).filter(n => !n.isComposite()).filter(n => (f === 'All' || n.category() === f || n.getStatus() === f.toUpperCase()) && [n.getId(), n.getName(), n.dto.hash, n.dto.source_device, n.dto.case_id, n.getType()].join(' ').toLowerCase().includes(q.toLowerCase()))
  return (
    <>
      <Head t="Evidence Vault" s="Every individual evidence item across investigations." />
      <div className="filters"><div className="chips">{['All', 'Computer', 'Mobile', 'Network', 'Verified', 'Pending', 'Analyzed'].map(x => <button key={x} className={f === x ? 'on' : ''} onClick={() => setF(x)}>{x}</button>)}</div>
        <input placeholder="Search evidence ID, hash, case or source" value={q} onChange={e => setQ(e.target.value)} aria-label="Filter evidence" /></div>
      <div className="card tablewrap"><table>
        <thead><tr><th>Evidence</th><th>Type</th><th>Case</th><th>Parent group</th><th>Hash</th><th>Status</th><th>Collected</th><th>Actions</th></tr></thead>
        <tbody>{rows.map(n => { const I = iconFor(n); const h = n.dto.hash; return (
          <tr key={n.getId()}><td><div className="ev"><I size={16} /><div><b>{n.getName()}</b><code>{n.getId()}</code></div></div></td><td>{n.getType()}</td><td>{n.dto.case_id}</td><td>{n.getParent()?.getName()}</td>
            <td className="mono">{h ? `${h.slice(0, 6)}…${h.slice(-4)}` : '—'}</td><td><Pill s={n.getStatus()} /></td><td>{n.dto.collected_at ? new Date(n.dto.collected_at).toLocaleDateString() : '—'}</td>
            <td className="rowacts"><button className="btn sm ghost" onClick={() => c.analyze(n)}>Analyze</button><button className="btn sm ghost" onClick={() => c.reveal(n.dto.case_id, n.getId())}>Open</button></td></tr>) })}
          {rows.length === 0 && <tr><td colSpan={8}><Empty t="No evidence matches these filters." /></td></tr>}</tbody>
      </table></div>
    </>
  )
}

export function AnalysisPage() {
  const c = useApp()
  const [busy, setBusy] = useState(false)
  return (
    <>
      <Head t="Forensic Analysis" s="One Analyze action for any evidence object: item, group or whole case.">
        <button className="btn" disabled={busy} onClick={async () => { setBusy(true); await c.analyze(c.sel); setBusy(false) }}><Play size={15} /> {c.sel.isComposite() ? 'Analyze Group' : 'Analyze'}</button></Head>
      <div className="ctx"><div><span>Current case</span><b>{c.curCase.id}</b></div><div><span>Selected evidence</span><NodePicker /></div></div>
      <div className="panel"><SummaryCards node={c.sel} />
        {c.run?.node.getId() === c.sel.getId()
          ? <><p className="muted">Analysis propagated through {c.run.result.descendant_count} descendant evidence objects.</p><Traversal r={c.run.result} /></>
          : <Empty t="Run an analysis to see the recursive traversal for the selected object." />}</div>
    </>
  )
}

export function CustodyPage() {
  const c = useApp()
  return (
    <>
      <Head t="Chain of Custody" s="Every collection, transfer and analysis event stored for the selected object." />
      <div className="ctx"><div><span>Selected evidence</span><NodePicker /></div></div>
      <div className="panel"><ChainOfCustody node={c.sel} /></div>
    </>
  )
}

export const ActivityPage = () => <><Head t="Activity" s="Investigation activity recorded by the backend." /><div className="panel"><ActivityFeed items={useApp().activity} /></div></>

export function Reports() {
  const c = useApp()
  const kinds: [string, string, string][] = [['investigation', 'Investigation Report', 'Case summary with the full evidence hierarchy.'], ['inventory', 'Evidence Inventory', 'Every evidence item with type, status and size.'], ['analysis', 'Analysis Summary', 'Aggregated analysis results for the case.'], ['custody', 'Chain of Custody', 'All custody events across the case.'], ['integrity', 'Integrity Report', 'SHA-256 and verification state per item.']]
  const load = async (k: string) => { const r = await api.getReport(c.curCase.id, k); return `${r.title.toUpperCase()}\n${r.case_id} · generated ${new Date(r.generated_at).toLocaleString()}\n\n${r.lines.join('\n')}` }
  const wrap = async (f: () => Promise<void>) => { try { await f() } catch (e) { c.toast((e as Error).message, true) } }
  return (
    <>
      <Head t="Reports" s={`Reports for ${c.curCase.id} · ${c.curCase.name}`} />
      <div className="grid2">{kinds.map(([k, t, d]) => (
        <div key={k} className="card pad"><h3>{t}</h3><p className="muted">{d}</p>
          <div className="acts"><button className="btn sm" onClick={() => wrap(async () => c.modal({ kind: 'report', title: t, text: await load(k) }))}>Preview</button>
            <button className="btn sm ghost" onClick={() => wrap(async () => { const text = await load(k); const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type: 'text/plain' })); a.download = `${c.curCase.id}-${k}.txt`; a.click(); c.toast('PDF export simulated: text report downloaded') })}>Export PDF</button></div></div>))}</div>
    </>
  )
}

export function SettingsPage() {
  const c = useApp(), s = c.settings
  return (
    <>
      <Head t="Settings" s={`Signed in as ${c.user.name} (${c.user.title})`} />
      <div className="card pad">
        <label className="sw"><input type="checkbox" checked={s.autoVerify} onChange={e => c.setSettings({ ...s, autoVerify: e.target.checked })} /> Mark new evidence as VERIFIED at intake</label>
        <label className="sw"><input type="checkbox" checked={s.compact} onChange={e => c.setSettings({ ...s, compact: e.target.checked })} /> Compact evidence tree</label>
      </div>
    </>
  )
}
