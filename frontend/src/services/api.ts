import { ActivityDTO, AnalysisResultDTO, CaseDTO, CustodyDTO, ReportDTO, SearchHit, StatsDTO, TreeDTO, User } from '../types'

const KEY = 'fv_token'
let token: string | null = sessionStorage.getItem(KEY)
let onUnauthorized: () => void = () => {}
export const setUnauthorizedHandler = (f: () => void) => { onUnauthorized = f }
export const hasToken = () => !!token

export class ApiError extends Error { constructor(msg: string, public status: number) { super(msg) } }

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response
  try {
    res = await fetch('/api' + path, { ...init, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init.headers } })
  } catch {
    throw new ApiError('Cannot reach the backend. Is it running on port 8000?', 0)
  }
  if (!res.ok) {
    let msg = 'Unable to complete operation.'
    try { const b = await res.json(); msg = typeof b.detail === 'string' ? b.detail : b.detail?.[0]?.msg ?? msg } catch { /* keep default */ }
    if (res.status === 401 && token) { token = null; sessionStorage.removeItem(KEY); onUnauthorized() }
    throw new ApiError(msg, res.status)
  }
  return res.json() as Promise<T>
}
const send = <T>(method: string, path: string, body?: unknown) => request<T>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) })

// auth
export async function login(username: string, password: string): Promise<User> {
  const r = await send<{ token: string; user: User }>('POST', '/auth/login', { username, password })
  token = r.token; sessionStorage.setItem(KEY, token); return r.user
}
export const me = () => send<User>('GET', '/auth/me')
export const logout = () => { token = null; sessionStorage.removeItem(KEY) }

// cases
export const getCases = () => send<CaseDTO[]>('GET', '/cases')
export const getCase = (id: string) => send<CaseDTO>('GET', `/cases/${id}`)
export const createCase = (d: { name: string; description: string; investigator: string; priority: string }) => send<CaseDTO>('POST', '/cases', d)
export const deleteCase = (id: string) => send('DELETE', `/cases/${id}`)
export const getReport = (caseId: string, kind: string) => send<ReportDTO>('GET', `/cases/${caseId}/reports/${kind}`)

// evidence (leaf or group, same endpoints)
export const getEvidenceTree = (caseId: string) => send<TreeDTO>('GET', `/cases/${caseId}/evidence`)
export const getEvidence = (id: string) => send<TreeDTO>('GET', `/evidence/${id}`)
export const createEvidence = (d: Record<string, unknown>) => send<TreeDTO>('POST', '/evidence', d)
export const addChild = (parentId: string, d: Record<string, unknown>) => send<TreeDTO>('POST', `/evidence/${parentId}/children`, d)
export const createGroup = (d: { parent_id: string; name: string; type: string; description: string }) => send<TreeDTO>('POST', '/evidence/groups', d)
export const moveEvidence = (id: string, parentId: string) => send<TreeDTO>('PUT', `/evidence/${id}/move`, { parent_id: parentId })
export const deleteEvidence = (id: string, mode: 'cascade' | 'promote') => send('DELETE', `/evidence/${id}?mode=${mode}`)
export const analyzeEvidence = (id: string) => send<AnalysisResultDTO>('POST', `/evidence/${id}/analyze`)
export const verifyEvidence = (id: string) => send<TreeDTO>('POST', `/evidence/${id}/verify`)
export const getCustody = (id: string) => send<CustodyDTO[]>('GET', `/evidence/${id}/custody`)

// search, activity, dashboard
export const searchEvidence = (q: string) => send<SearchHit[]>('GET', `/search?q=${encodeURIComponent(q)}`)
export const getActivity = (limit = 50) => send<ActivityDTO[]>('GET', `/activity?limit=${limit}`)
export const getDashboardStats = () => send<StatsDTO>('GET', '/dashboard/stats')
