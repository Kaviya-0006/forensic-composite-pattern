import { CSSProperties } from 'react'
import { CalendarClock, CheckCircle2, FilePlus, FolderPlus, Move, Fingerprint, ShieldCheck, Trash2, Lock } from 'lucide-react'
import { ActivityDTO, AnalysisResultDTO, EvNode, fmtTime } from '../types'
import { useApp } from '../context'
import { iconFor } from './ui'

const AI: Record<string, { i: typeof Lock; c: string }> = {
  ANALYSIS_COMPLETED: { i: Fingerprint, c: 'analyze' }, ANALYSIS_STARTED: { i: Fingerprint, c: 'analyze' }, EVIDENCE_ADDED: { i: FilePlus, c: 'add' }, GROUP_CREATED: { i: FolderPlus, c: 'group' },
  CASE_CREATED: { i: FolderPlus, c: 'group' }, EVIDENCE_MOVED: { i: Move, c: 'move' }, HASH_VERIFIED: { i: ShieldCheck, c: 'verify' }, EVIDENCE_REMOVED: { i: Trash2, c: 'remove' }, CUSTODY_UPDATED: { i: Lock, c: 'custody' } }
export function ActivityFeed({ items }: { items: ActivityDTO[] }) {
  if (!items.length) return <p className="muted">No activity recorded yet.</p>
  return (
    <ol className="feed">{items.map(a => { const m = AI[a.action] ?? { i: CalendarClock, c: 'x' }; const I = m.i; return (
      <li key={a.id}><span className={'fi f-' + m.c}><I size={14} /></span><div><b>{a.message}</b><div className="muted">{a.actor}{a.case_id ? ` · ${a.case_id}` : ''}</div></div><time>{fmtTime(a.created_at)}</time></li>) })}</ol>
  )
}

/** Overview centerpiece, generated from the Composite tree returned by the backend. */
function NetNode({ n, root }: { n: EvNode; root?: boolean }) {
  const c = useApp()
  const kids = n.getChildren(), groups = kids.filter(k => k.isComposite()), I = iconFor(n)
  return (
    <div className={'on' + (root ? ' root' : '')}>
      <button className={'obox ' + (root ? 'oroot' : 'ogrp')} onClick={() => { c.select(n); c.go('tree') }}>
        <I size={18} /><b>{n.getName()}</b><small>{root ? `${n.summary().items} evidence items` : `${kids.length - groups.length} items${groups.length ? ` · ${groups.length} subgroup` : ''}`}</small>
      </button>
      {groups.length > 0 && <div className="ochildren">{groups.map(g => <NetNode key={g.getId()} n={g} />)}</div>}
    </div>
  )
}
export const EvidenceNetwork = ({ root }: { root: EvNode }) => <div className="scroll"><div className="otree"><NetNode n={root} root /></div></div>

/** Replays the recursive analyze() result produced by the backend Composite. */
function TNode({ r, i }: { r: AnalysisResultDTO; i: { n: number } }) {
  const idx = i.n++
  return (
    <div className="on">
      <div className={'obox tbox ' + (r.role === 'LEAF' ? 'tleaf' : 'tcomp')} style={{ '--i': idx } as CSSProperties} title={r.steps.join('  >  ')}>
        <b>{r.name}</b><small>{r.role === 'COMPOSITE' ? `${r.class_name}: analyze() on children` : `${r.class_name}: analyze() on itself`}</small>
        {r.role === 'LEAF' && <CheckCircle2 size={16} className="chk" />}
      </div>
      {r.children.length > 0 && <div className="ochildren">{r.children.map(ch => <TNode key={ch.evidence_id} r={ch} i={i} />)}</div>}
    </div>
  )
}
export const Traversal = ({ r }: { r: AnalysisResultDTO }) => <div className="scroll"><div className="otree"><TNode r={r} i={{ n: 0 }} /></div></div>

export function SummaryCards({ node }: { node: EvNode }) {
  const s = node.summary(), pct = s.items ? Math.round((s.analyzed / s.items) * 100) : 0
  const cards: [string, string, string][] = [
    ['Hash integrity', s.verified === s.items && s.items ? 'VERIFIED' : `${s.verified}/${s.items} VERIFIED`, 'c-blue'],
    ['Metadata', s.analyzed ? 'EXTRACTED' : 'PENDING', 'c-cyan'], ['File system', s.analyzed === s.items && s.items ? 'ANALYZED' : `${pct}% ANALYZED`, 'c-violet'],
    ['Network indicators', `${s.network} FOUND`, 'c-blue'], ['Suspicious artifacts', `${s.suspicious} FOUND`, s.suspicious ? 'c-amber' : 'c-cyan']]
  return (
    <>
      <div className="meter"><div><b>{pct}% complete</b><span className="muted"> · {s.analyzed} of {s.items} evidence items analyzed</span></div><div className="bar"><i style={{ width: pct + '%' }} /></div></div>
      <div className="acards">{cards.map(([k, v, c]) => <div key={k} className={'acard ' + c}><span>{k}</span><b>{v}</b></div>)}</div>
    </>
  )
}
