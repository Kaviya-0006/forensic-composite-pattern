import { useEffect, useState } from 'react'
import { Play, ShieldCheck, FileDown, Trash2, Move, FolderPlus, FilePlus, Clock, ChevronDown } from 'lucide-react'
import { CustodyDTO, EvNode } from '../types'
import { useApp } from '../context'
import * as api from '../services/api'
import { iconFor, Pill, RoleTag } from './ui'
import { SummaryCards, Traversal } from './Visuals'

export function ChainOfCustody({ node }: { node: EvNode }) {
  const c = useApp()
  const [ev, setEv] = useState<CustodyDTO[] | null>(null)
  const [err, setErr] = useState('')
  useEffect(() => { let live = true; setErr(''); api.getCustody(node.getId()).then(r => live && setEv(r)).catch(e => live && setErr(e.message)); return () => { live = false } }, [node.getId(), c.ver])
  if (err) return <p className="muted">Unable to load chain of custody: {err}</p>
  if (!ev) return <p className="muted">Loading chain of custody...</p>
  return (
    <div>
      <p className="muted">{node.isComposite() ? `${node.getName()}: ${ev.length} custody records across ${node.summary().items} evidence items` : `${node.getId()} · ${ev.length} custody records`}</p>
      <ol className="ctl">{ev.map((e, i) => { const d = new Date(e.occurred_at); return (
        <li key={i}><div className="cdate"><b>{d.toLocaleDateString([], { day: '2-digit', month: 'short' }).toUpperCase()}</b><span>{d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></div><span className="cdot" />
          <div className="ccard"><div><b>{e.action}</b> <Pill s={e.integrity} /></div><div className="muted">{e.evidence_name} · <code>{e.evidence_id}</code></div><div className="muted">Actor: {e.actor}{e.details ? ` · ${e.details}` : ''}</div></div></li>) })}</ol>
    </div>
  )
}

export function NodeDetails({ node }: { node: EvNode }) {
  const c = useApp()
  const [tab, setTab] = useState('overview')
  const [busy, setBusy] = useState(false)
  useEffect(() => setTab('overview'), [node.getId()])
  const info = node.display(), kids = node.getChildren(), comp = node.isComposite(), I = iconFor(node, true), s = node.summary()
  const exp = () => {
    const lines = node.all().map(n => `${'  '.repeat(n.path().length - 1)}${n.getName()} [${n.dto.role}] ${n.getStatus()}`).join('\n')
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([`FORENSICVAULT EXPORT\nCase: ${node.root().getId()}\n\n${lines}\n`], { type: 'text/plain' })); a.download = `${node.getId()}-export.txt`; a.click(); c.toast('Export downloaded')
  }
  const runAnalyze = async () => { setBusy(true); await c.analyze(node); setBusy(false) }
  const tabs: [string, string][] = [['overview', 'Overview'], ['metadata', 'Metadata'], ['analysis', 'Analysis'], ['custody', 'Custody']]
  return (
    <div className="card details">
      <div className={'rolecard ' + (comp ? 'rc-c' : 'rc-l')}>
        <span className="nico big"><I size={22} /></span>
        <div><b>{node.getName().toUpperCase()}</b><small>{comp ? `COMPOSITE · ${kids.length} children` : `LEAF · ${info.status === 'PENDING' ? 'SHA-256 not yet verified' : 'SHA-256 verified'}`}</small></div>
        <div className="rcnote">{comp ? <><ChevronDown size={14} /> Contains Evidence</> : 'No child evidence'}</div>
      </div>
      <div className="dh"><div><h3>{node.getName()}</h3><code>{node.getId()}</code></div><Pill s={info.status} /></div>
      <div className="acts">
        <button className="btn" disabled={busy} onClick={runAnalyze}><Play size={15} /> {comp ? 'Analyze Group' : 'Analyze'}</button>
        <button className="btn ghost" onClick={() => c.verify(node)}><ShieldCheck size={15} /> Verify Hash</button>
        <button className="btn ghost" onClick={() => setTab('custody')}><Clock size={15} /> Chain of Custody</button>
        <button className="btn ghost" onClick={exp}><FileDown size={15} /> Export</button>
        {comp && <button className="btn ghost" onClick={() => c.modal({ kind: 'add', target: node })}><FilePlus size={15} /> Add Evidence</button>}
        {comp && <button className="btn ghost" onClick={() => c.modal({ kind: 'group', target: node })}><FolderPlus size={15} /> Create Subgroup</button>}
        {node.getParent() && <button className="btn ghost" onClick={() => c.modal({ kind: 'move', node })}><Move size={15} /> Move</button>}
        {node.getParent() && <button className="btn danger" onClick={() => c.modal({ kind: 'remove', node })}><Trash2 size={15} /> Remove</button>}
      </div>
      <div className="tabs" role="tablist">{tabs.map(([k, l]) => <button key={k} role="tab" className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{l}</button>)}</div>
      {tab === 'overview' && (
        <div>
          <div className="strip"><div><b>{s.items}</b><span>Items</span></div><div><b>{s.verified}</b><span>Verified</span></div><div><b>{s.analyzed}</b><span>Analyzed</span></div><div><b>{node.descendantCount()}</b><span>Descendants</span></div></div>
          <div className="kv"><div><span>Pattern role</span><b>{info.role} <RoleTag n={node} /></b></div><div><span>Parent</span><b>{node.getParent()?.getName() ?? 'None (root)'}</b></div></div>
          <h4>Child evidence</h4>
          {kids.map(k => { const KI = iconFor(k); return <button key={k.getId()} className="citem" onClick={() => { c.expand([node.getId()]); c.select(k) }}><KI size={15} /><b>{k.getName()}</b><RoleTag n={k} /><Pill s={k.getStatus()} /></button> })}
          {kids.length === 0 && <p className="muted">{comp ? 'No evidence in this group yet.' : 'This is a Leaf: it has no child evidence.'}</p>}
        </div>
      )}
      {tab === 'metadata' && <div className="kv">{[['Evidence ID', node.getId()], ...info.fields].map(([k, v]) => <div key={k}><span>{k}</span><b className={/SHA|MD5/.test(k) ? 'mono' : ''}>{v}</b></div>)}{node.dto.description && <div className="wide"><span>Description</span><b>{node.dto.description}</b></div>}</div>}
      {tab === 'analysis' && (
        <div><SummaryCards node={node} />
          {c.run?.node.getId() === node.getId()
            ? <><p className="muted">Analysis propagated through {c.run.result.descendant_count} descendant evidence objects.</p><Traversal r={c.run.result} />
                {c.run.result.role === 'LEAF' && <div className="chips">{c.run.result.steps.map(x => <span key={x}>{x}</span>)}</div>}</>
            : <p className="muted">Press {comp ? 'Analyze Group' : 'Analyze'}: the same POST /api/evidence/{node.getId()}/analyze call is used for any evidence object.</p>}</div>
      )}
      {tab === 'custody' && <ChainOfCustody node={node} />}
    </div>
  )
}
