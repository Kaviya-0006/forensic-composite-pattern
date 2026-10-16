import { useCallback, useEffect, useRef, useState } from 'react'
import { ActivityDTO, CaseDTO, EvNode, StatsDTO, User } from './types'
import { AppCtx, Ctx, ModalState, Page, Settings } from './context'
import * as api from './services/api'
import { ArchDrawer } from './components/Shell'
import AppLayout from './layouts/AppLayout'
import { Modal } from './components/ui'
import { AddEvidenceModal, AnalysisModal, CreateGroupModal, MoveModal, NewCaseModal, RemoveModal } from './components/Modals'
import { ActivityPage, AnalysisPage, CaseDetails, CustodyPage, Investigations, Overview, Reports, SettingsPage, Vault } from './pages/Pages'
import Login from './pages/Login'

export default function App() {
  const [user, setUser] = useState<User | null>(null)
  const [booting, setBooting] = useState(api.hasToken())
  useEffect(() => {
    api.setUnauthorizedHandler(() => setUser(null))
    if (api.hasToken()) api.me().then(setUser).catch(() => api.logout()).finally(() => setBooting(false))
  }, [])
  if (booting) return <div className="loading"><span className="spinner" />Restoring session...</div>
  if (!user) return <Login onLogin={setUser} />
  return <Workbench user={user} logout={() => { api.logout(); setUser(null) }} />
}

function Workbench({ user, logout }: { user: User; logout: () => void }) {
  const [cases, setCases] = useState<CaseDTO[]>([])
  const [trees, setTrees] = useState<Record<string, EvNode>>({})
  const [stats, setStats] = useState<StatsDTO | null>(null)
  const [activity, setActivity] = useState<ActivityDTO[]>([])
  const [curId, setCurId] = useState('')
  const [selId, setSelId] = useState('')
  const [page, setPage] = useState<Page>('overview')
  const [open, setOpen] = useState(new Set<string>())
  const [modal, setModal] = useState<ModalState>(null)
  const [run, setRun] = useState<Ctx['run']>(null)
  const [arch, setArch] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const [settings, setSettings] = useState<Settings>({ autoVerify: false, compact: false })
  const [msg, setMsg] = useState<{ t: string; err: boolean } | null>(null)
  const [loadErr, setLoadErr] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [ver, setVer] = useState(0)
  const tt = useRef<number | undefined>(undefined)

  const toast = useCallback((t: string, err = false) => { setMsg({ t, err }); window.clearTimeout(tt.current); tt.current = window.setTimeout(() => setMsg(null), 3500) }, [])

  /** Re-reads everything from the backend (the source of truth). */
  const reload = useCallback(async (s?: { caseId?: string; evidenceId?: string }) => {
    const [cs, st, act] = await Promise.all([api.getCases(), api.getDashboardStats(), api.getActivity(50)])
    const entries = await Promise.all(cs.map(async c => [c.id, new EvNode(await api.getEvidenceTree(c.id))] as const))
    setCases(cs); setStats(st); setActivity(act); setTrees(Object.fromEntries(entries)); setVer(v => v + 1)
    if (s?.caseId) setCurId(s.caseId)
    if (s?.evidenceId) setSelId(s.evidenceId)
    setCurId(id => (cs.some(c => c.id === id) ? id : cs[0]?.id ?? ''))
    return Object.fromEntries(entries)
  }, [])

  useEffect(() => {
    reload().then(t => {
      const first = Object.values(t)[0]
      if (first) { setSelId(first.getId()); setOpen(new Set([first.getId(), ...first.getChildren().filter(c => c.isComposite()).map(c => c.getId())])) }
      setLoaded(true)
    }).catch(e => setLoadErr(e.message))
  }, [reload])

  const curCase = cases.find(c => c.id === curId) ?? cases[0]
  const cur = curCase ? trees[curCase.id] : undefined
  if (loadErr) return <div className="loading">Unable to load data: {loadErr} <button className="btn" onClick={() => location.reload()}>Retry</button></div>
  if (!loaded || !curCase || !cur) return <div className="loading"><span className="spinner" />Loading evidence hierarchy...</div>
  const sel = cur.find(selId) ?? cur

  const ctx: Ctx = {
    user, logout, cases, trees, curCase, cur, sel, page, go: setPage, open, modal: setModal, run, activity, stats, arch, setArch, collapsed, setCollapsed, settings, setSettings, reload, ver, toast,
    select: n => setSelId(n.getId()),
    openCase: id => { const t = trees[id]; setCurId(id); setSelId(t.getId()); setOpen(new Set([t.getId(), ...t.getChildren().filter(c => c.isComposite()).map(c => c.getId())])) },
    reveal: (caseId, evidenceId) => { const n = trees[caseId]?.find(evidenceId); setCurId(caseId); setSelId(evidenceId); setOpen(s => new Set([...s, ...(n ? n.path().map(p => p.getId()) : [])])); setPage('tree') },
    toggle: id => setOpen(s => { const t = new Set(s); if (t.has(id)) t.delete(id); else t.add(id); return t }),
    expand: ids => setOpen(s => new Set([...s, ...ids])),
    collapseAll: () => setOpen(new Set([cur.getId()])),
    analyze: async n => {
      try {
        const result = await api.analyzeEvidence(n.getId())          // identical call for a Leaf, a group or a case
        await reload(); setRun({ node: n, result }); setModal({ kind: 'analysis' })
      } catch (e) { toast((e as Error).message || 'Unable to complete operation.', true) }
    },
    verify: async n => {
      try { await api.verifyEvidence(n.getId()); await reload(); toast('Hash verification completed') } catch (e) { toast((e as Error).message, true) }
    },
  }
  const pages: Record<Page, JSX.Element> = { overview: <Overview />, investigations: <Investigations />, case: <CaseDetails />, vault: <Vault />, tree: <CaseDetails full />, analysis: <AnalysisPage />, custody: <CustodyPage />, activity: <ActivityPage />, reports: <Reports />, settings: <SettingsPage /> }
  const close = () => setModal(null)
  return (
    <AppCtx.Provider value={ctx}>
      <AppLayout pageKey={page}>{pages[page]}</AppLayout>
      <ArchDrawer />
      {modal?.kind === 'add' && <AddEvidenceModal target={modal.target} onClose={close} />}
      {modal?.kind === 'group' && <CreateGroupModal target={modal.target} onClose={close} />}
      {modal?.kind === 'move' && <MoveModal node={modal.node} onClose={close} />}
      {modal?.kind === 'remove' && <RemoveModal node={modal.node} onClose={close} />}
      {modal?.kind === 'newcase' && <NewCaseModal onClose={close} />}
      {modal?.kind === 'analysis' && <AnalysisModal onClose={close} />}
      {modal?.kind === 'report' && <Modal title={modal.title} onClose={close} wide><pre className="rep">{modal.text}</pre></Modal>}
      {msg && <div className={'toast' + (msg.err ? ' err' : '')} role="status">{msg.t}</div>}
    </AppCtx.Provider>
  )
}
