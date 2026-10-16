import { ChangeEvent, ReactNode, useState } from 'react'
import { EvNode } from '../types'
import { useApp } from '../context'
import * as api from '../services/api'
import { Field, Modal } from './ui'
import { Traversal } from './Visuals'

type Ch = ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
const LEAF_TYPES = ['Disk Image', 'Browser History', 'System Log', 'Device Image', 'Mobile Message', 'Call Record', 'Network PCAP', 'Firewall Log', 'DNS Log', 'Other']
const GROUP_KINDS = ['Computer Evidence', 'Mobile Evidence', 'Network Evidence', 'Forensic Collection', 'Custom Group']
const Sec = ({ t, children }: { t: string; children: ReactNode }) => <div className="sec"><h5>{t}</h5><div className="form">{children}</div></div>

/** Runs an API call; the UI only changes after the backend confirms. */
function useAction(onClose: () => void) {
  const c = useApp()
  const [busy, setBusy] = useState(false)
  const run = async (f: () => Promise<string | void>) => {
    setBusy(true)
    try { const msg = await f(); if (msg) c.toast(msg); onClose() } catch (e) { c.toast((e as Error).message || 'Unable to complete operation.', true) } finally { setBusy(false) }
  }
  return { busy, run }
}

export function AddEvidenceModal({ target, onClose }: { target: EvNode; onClose: () => void }) {
  const c = useApp(), { busy, run } = useAction(onClose)
  const [f, setF] = useState({ name: '', type: 'Disk Image', source_device: '', description: '', hash: '', file_size: '', collected_by: c.user.name, collected_at: new Date().toISOString().slice(0, 16) })
  const set = (k: string) => (e: Ch) => setF({ ...f, [k]: e.target.value })
  const submit = () => run(async () => {
    if (!f.name.trim()) throw new Error('Evidence name is required.')
    const created = await api.addChild(target.getId(), { ...f, status: c.settings.autoVerify ? 'VERIFIED' : 'PENDING', collected_at: f.collected_at || null })
    c.expand([target.getId()]); await c.reload({ evidenceId: created.id }); return `${created.name} added to ${target.getName()}`
  })
  return (
    <Modal title="Add Evidence" sub={`Intake into ${target.getName()} (POST /api/evidence/${target.getId()}/children)`} onClose={onClose} wide>
      <Sec t="Identification"><Field label="Evidence Name"><input value={f.name} onChange={set('name')} /></Field><Field label="Evidence Type"><select value={f.type} onChange={set('type')}>{LEAF_TYPES.map(t => <option key={t}>{t}</option>)}</select></Field><Field label="Description"><input value={f.description} onChange={set('description')} /></Field></Sec>
      <Sec t="Source"><Field label="Source Device"><input value={f.source_device} onChange={set('source_device')} /></Field><Field label="File Size"><input value={f.file_size} onChange={set('file_size')} placeholder="e.g. 512 GB" /></Field></Sec>
      <Sec t="Integrity"><Field label="SHA-256 Hash"><input value={f.hash} onChange={set('hash')} /></Field></Sec>
      <Sec t="Collection"><Field label="Collected By"><input value={f.collected_by} onChange={set('collected_by')} /></Field><Field label="Collection Date"><input type="datetime-local" value={f.collected_at} onChange={set('collected_at')} /></Field></Sec>
      <div className="mf"><button className="btn ghost" onClick={onClose}>Cancel</button><button className="btn" disabled={busy} onClick={submit}>{busy ? 'Saving...' : 'Add Evidence'}</button></div>
    </Modal>
  )
}

export function CreateGroupModal({ target, onClose }: { target: EvNode; onClose: () => void }) {
  const c = useApp(), { busy, run } = useAction(onClose)
  const [name, setName] = useState(''), [type, setType] = useState('Forensic Collection'), [desc, setDesc] = useState(''), [pid, setPid] = useState(target.getId())
  const groups = c.cur.all().filter(n => n.isComposite())
  const submit = () => run(async () => {
    if (!name.trim()) throw new Error('Group name is required.')
    const g = await api.createGroup({ parent_id: pid, name, type, description: desc })
    c.expand([pid]); await c.reload({ evidenceId: g.id }); return `Group ${g.name} created`
  })
  return (
    <Modal title="Create Evidence Group" sub="POST /api/evidence/groups" onClose={onClose}>
      <div className="form one"><Field label="Group Name"><input value={name} onChange={e => setName(e.target.value)} /></Field>
        <Field label="Group Type"><select value={type} onChange={e => setType(e.target.value)}>{GROUP_KINDS.map(k => <option key={k}>{k}</option>)}</select></Field>
        <Field label="Description"><input value={desc} onChange={e => setDesc(e.target.value)} /></Field>
        <Field label="Parent"><select value={pid} onChange={e => setPid(e.target.value)}>{groups.map(g => <option key={g.getId()} value={g.getId()}>{g.path().map(p => p.getName()).join(' → ')}</option>)}</select></Field></div>
      <div className="mf"><button className="btn ghost" onClick={onClose}>Cancel</button><button className="btn" disabled={busy} onClick={submit}>Create Group</button></div>
    </Modal>
  )
}

export function MoveModal({ node, onClose }: { node: EvNode; onClose: () => void }) {
  const c = useApp(), { busy, run } = useAction(onClose)
  const options = c.cur.all().filter(n => n.isComposite() && n !== node && n !== node.getParent())
  const [to, setTo] = useState(options[0]?.getId() ?? '')
  const submit = () => run(async () => {
    const dest = c.cur.find(to)!
    await api.moveEvidence(node.getId(), to)
    c.expand([to]); await c.reload({ evidenceId: node.getId() }); return `${node.getName()} moved from ${node.getParent()?.getName()} → ${dest.getName()}.`
  })
  return (
    <Modal title={`Move ${node.getName()}`} sub={`Current parent: ${node.getParent()?.getName() ?? 'None'}. The server rejects cycles and Leaf destinations.`} onClose={onClose}>
      <div className="form one"><Field label="New parent (any group, including nested)"><select value={to} onChange={e => setTo(e.target.value)}>
        {c.cur.all().filter(n => n.isComposite() && n !== node).map(g => <option key={g.getId()} value={g.getId()}>{g.path().map(p => p.getName()).join(' → ')}</option>)}</select></Field></div>
      <div className="mf"><button className="btn ghost" onClick={onClose}>Cancel</button><button className="btn" disabled={!to || busy} onClick={submit}>Move</button></div>
    </Modal>
  )
}

export function RemoveModal({ node, onClose }: { node: EvNode; onClose: () => void }) {
  const c = useApp(), { busy, run } = useAction(onClose), n = node.descendantCount()
  const go = (mode: 'cascade' | 'promote') => run(async () => {
    const parent = node.getParent()!
    await api.deleteEvidence(node.getId(), mode); await c.reload({ evidenceId: parent.getId() })
    return mode === 'promote' ? `${node.getName()} removed; its children moved to ${parent.getName()}.` : `${node.getName()} removed from ${parent.getName()}.`
  })
  return (
    <Modal title={`Remove ${node.getName()}?`} sub={node.isComposite() ? `This group contains ${n} evidence ${n === 1 ? 'object' : 'objects'}.` : 'This evidence item will be removed from its group.'} onClose={onClose}>
      <div className="mf"><button className="btn ghost" onClick={onClose}>Cancel</button>
        {n > 0 && <button className="btn ghost" disabled={busy} onClick={() => go('promote')}>Remove Group Only</button>}
        <button className="btn danger" disabled={busy} onClick={() => go('cascade')}>{n > 0 ? 'Remove Group & Children' : 'Remove'}</button></div>
    </Modal>
  )
}

export function NewCaseModal({ onClose }: { onClose: () => void }) {
  const c = useApp(), { busy, run } = useAction(onClose)
  const [f, setF] = useState({ name: '', description: '', investigator: c.user.name, priority: 'MEDIUM' })
  const set = (k: string) => (e: Ch) => setF({ ...f, [k]: e.target.value })
  const submit = () => run(async () => {
    if (!f.name.trim()) throw new Error('Case name is required.')
    const cs = await api.createCase(f); await c.reload({ caseId: cs.id, evidenceId: cs.root_id }); c.go('case'); return `${cs.id} created`
  })
  return (
    <Modal title="New Investigation" sub="Creates a new root EvidenceGroup (Composite) in the database." onClose={onClose}>
      <div className="form one"><Field label="Case Name"><input value={f.name} onChange={set('name')} /></Field><Field label="Description"><textarea rows={2} value={f.description} onChange={set('description')} /></Field>
        <Field label="Investigator"><input value={f.investigator} onChange={set('investigator')} /></Field><Field label="Priority"><select value={f.priority} onChange={set('priority')}>{['LOW', 'MEDIUM', 'HIGH'].map(p => <option key={p}>{p}</option>)}</select></Field></div>
      <div className="mf"><button className="btn ghost" onClick={onClose}>Cancel</button><button className="btn" disabled={busy} onClick={submit}>Create Investigation</button></div>
    </Modal>
  )
}

export function AnalysisModal({ onClose }: { onClose: () => void }) {
  const { run } = useApp()
  if (!run) return null
  const s = run.result.summary
  return (
    <Modal title={`ANALYZING ${run.node.getName().toUpperCase()}`} sub={`${run.node.isComposite() ? 'Composite' : 'Leaf'} → analyze() · one call: POST /api/evidence/${run.node.getId()}/analyze`} onClose={onClose} wide>
      <Traversal r={run.result} />
      <div className="done"><b>Analysis completed</b><span>{run.result.descendant_count} descendant evidence objects traversed · {s.network} network indicators · {s.suspicious} suspicious artifacts</span></div>
      <div className="mf"><button className="btn" onClick={onClose}>Close</button></div>
    </Modal>
  )
}
