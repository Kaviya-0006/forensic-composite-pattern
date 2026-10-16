import { createContext, useContext } from 'react'
import { ActivityDTO, AnalysisResultDTO, CaseDTO, EvNode, StatsDTO, User } from './types'

export type Page = 'overview' | 'investigations' | 'case' | 'vault' | 'tree' | 'analysis' | 'custody' | 'activity' | 'reports' | 'settings'
export type ModalState = { kind: 'add' | 'group'; target: EvNode } | { kind: 'move' | 'remove'; node: EvNode } | { kind: 'analysis' } | { kind: 'newcase' } | { kind: 'report'; title: string; text: string } | null
export interface Settings { autoVerify: boolean; compact: boolean }
export interface Ctx {
  user: User; logout: () => void
  cases: CaseDTO[]; trees: Record<string, EvNode>; curCase: CaseDTO; cur: EvNode; sel: EvNode; page: Page; go: (p: Page) => void
  select: (n: EvNode) => void; openCase: (id: string) => void; reveal: (caseId: string, evidenceId: string) => void
  open: Set<string>; toggle: (id: string) => void; expand: (ids: string[]) => void; collapseAll: () => void
  reload: (select?: { caseId?: string; evidenceId?: string }) => Promise<void>; ver: number
  toast: (m: string, err?: boolean) => void; modal: (m: ModalState) => void
  run: { node: EvNode; result: AnalysisResultDTO } | null; analyze: (n: EvNode) => Promise<void>; verify: (n: EvNode) => Promise<void>
  activity: ActivityDTO[]; stats: StatsDTO | null
  arch: boolean; setArch: (b: boolean) => void; collapsed: boolean; setCollapsed: (b: boolean) => void
  settings: Settings; setSettings: (s: Settings) => void
}
export const AppCtx = createContext<Ctx | null>(null)
export const useApp = () => useContext(AppCtx)!
