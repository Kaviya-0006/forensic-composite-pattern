import { useEffect, useRef, useState } from 'react'
import { LayoutDashboard, Briefcase, Database, FolderTree, Fingerprint, Lock, Activity as Pulse, FileText, Settings, Search, Bell, PanelLeftClose, PanelLeft, Layers, Shield, X, ChevronRight, LogOut } from 'lucide-react'
import { SearchHit } from '../types'
import { Page, useApp } from '../context'
import * as api from '../services/api'
import { useDebounced } from '../hooks/useDebounced'
import { Pill } from './ui'

const NAV: [Page, string, typeof Settings][] = [['overview', 'Overview', LayoutDashboard], ['investigations', 'Investigations', Briefcase], ['vault', 'Evidence Vault', Database], ['tree', 'Evidence Tree', FolderTree], ['analysis', 'Analysis', Fingerprint], ['custody', 'Chain of Custody', Lock], ['activity', 'Activity', Pulse], ['reports', 'Reports', FileText]]
export const Logo = () => <span className="logo"><Shield size={30} /><Fingerprint size={14} /></span>

export function Sidebar() {
  const c = useApp()
  const active = (p: Page) => c.page === p || (p === 'investigations' && c.page === 'case')
  const initials = c.user.name.split(' ').map(x => x[0]).join('')
  return (
    <aside className={'sidebar' + (c.collapsed ? ' min' : '')}>
      <div className="brand"><Logo /><div className="bt"><b>FORENSICVAULT</b><small>DIGITAL EVIDENCE INTELLIGENCE</small></div></div>
      <nav>{NAV.map(([p, l, I]) => <button key={p} className={active(p) ? 'on' : ''} onClick={() => c.go(p)} title={l}><I size={18} /><span>{l}</span></button>)}</nav>
      <div className="sbot">
        <button className={c.page === 'settings' ? 'on' : ''} onClick={() => c.go('settings')} title="Settings"><Settings size={18} /><span>Settings</span></button>
        <button onClick={() => c.setArch(true)} title="Architecture"><Layers size={18} /><span>Architecture</span></button>
        <button className="collapse" onClick={() => c.setCollapsed(!c.collapsed)} aria-label="Collapse sidebar">{c.collapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}<span>Collapse</span></button>
        <div className="profile"><span className="av">{initials}</span><div className="pt"><b>{c.user.name}</b><small>{c.user.title}</small></div></div>
      </div>
    </aside>
  )
}

export function Header() {
  const c = useApp()
  const [q, setQ] = useState('')
  const [hits, setHits] = useState<SearchHit[] | null>(null)
  const ref = useRef<HTMLInputElement>(null)
  const dq = useDebounced(q.trim(), 250)
  useEffect(() => { const k = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); ref.current?.focus() } }; window.addEventListener('keydown', k); return () => window.removeEventListener('keydown', k) }, [])
  useEffect(() => { let live = true; if (!dq) { setHits(null); return } api.searchEvidence(dq).then(r => live && setHits(r)).catch(e => c.toast(e.message, true)); return () => { live = false } }, [dq])
  const crumbs = c.page === 'case' || c.page === 'tree' ? ['Investigations', c.curCase.id, c.sel === c.cur ? '' : c.sel.getName()] : [NAV.find(n => n[0] === c.page)?.[1] ?? 'Settings']
  return (
    <header className="top">
      <div className="crumb">{crumbs.filter(Boolean).map((x, i, a) => <span key={i} className={i === a.length - 1 ? 'cur' : ''}>{x}{i < a.length - 1 && <ChevronRight size={13} />}</span>)}</div>
      <div className="search"><Search size={16} /><input ref={ref} value={q} onChange={e => setQ(e.target.value)} placeholder="Search cases, evidence IDs, hashes..." aria-label="Search" /><kbd>Ctrl K</kbd>
        {q.trim() && <div className="results">
          {hits === null && <div className="emptyrow">Searching...</div>}
          {hits?.length === 0 && <div className="emptyrow">No evidence matches "{q}".</div>}
          {hits?.map(h => <button key={h.id} onClick={() => { c.reveal(h.case_id, h.id); setQ('') }}><div><b>{h.name}</b> <code>{h.id}</code> <span className={'role ' + (h.role === 'COMPOSITE' ? 'r-c' : 'r-l')}>{h.role === 'COMPOSITE' ? 'GROUP' : 'LEAF'}</span> <Pill s={h.status} />
            <div className="muted">{h.path.join(' → ')}</div></div></button>)}
        </div>}
      </div>
      <div className="secure"><i />SECURE INVESTIGATION ENVIRONMENT</div>
      <button className="iconbtn" aria-label="Notifications" onClick={() => c.toast(`${c.stats?.pending_analysis ?? 0} evidence items are awaiting analysis.`)}><Bell size={18} /><i className="ping" /></button>
      <button className="iconbtn" aria-label="Sign out" title="Sign out" onClick={c.logout}><LogOut size={18} /></button>
    </header>
  )
}

export function ArchDrawer() {
  const c = useApp()
  if (!c.arch) return null
  const n = c.sel, info = n.display()
  return (
    <div className="overlay right" onClick={() => c.setArch(false)}>
      <aside className="drawer" onClick={e => e.stopPropagation()}>
        <div className="mh"><h3>Architecture · Composite Pattern</h3><button className="x" onClick={() => c.setArch(false)} aria-label="Close"><X size={18} /></button></div>
        {[['Component', 'Evidence', 'Abstract class: analyze(), display(), add(), remove(), get_children()'], ['Leaf', 'IndividualEvidence', 'DiskImage, BrowserHistory, SystemLog, NetworkPCAP ... acts on itself; add() raises 400'], ['Composite', 'EvidenceGroup', 'InvestigationCase, Computer/Mobile/Network groups ... delegates to children'], ['Client', 'Forensic Investigation System', 'Service layer calls evidence.analyze() without checking the type']].map(([r, k, d]) => (
          <div key={r} className="arow"><span className={'role ' + (r === 'Composite' ? 'r-c' : r === 'Leaf' ? 'r-l' : 'r-x')}>{r.toUpperCase()}</span><div><b>{k}</b><div className="muted">{d}</div></div></div>))}
        <h4>Selected object</h4>
        <div className="kv one"><div><span>Object</span><b>{n.getName()}</b></div><div><span>Backend class</span><b className="mono">{n.className}</b></div><div><span>Pattern role</span><b>{info.role}</b></div><div><span>Children</span><b>{n.getChildren().length}</b></div><div><span>Parent</span><b>{n.getParent()?.getName() ?? 'None'}</b></div></div>
      </aside>
    </div>
  )
}
