export interface Summary { items: number; analyzed: number; verified: number; flagged: number; network: number; suspicious: number }
export interface TreeDTO {
  id: string; case_id: string; parent_id: string | null; parent_name?: string | null; name: string; type: string; kind: 'group' | 'leaf'
  role: 'LEAF' | 'COMPOSITE'; class_name: string; status: string; description: string; hash: string; file_size: string; source_device: string
  collected_by: string; collected_at: string | null; descendant_count: number; summary: Summary; category?: string; children: TreeDTO[]
}
export interface CaseDTO { id: string; name: string; description: string; investigator: string; priority: string; status: string; created_at: string; evidence_count: number; group_count: number; root_id: string; last_activity_at: string }
export interface ActivityDTO { id: number; case_id: string | null; actor: string; action: string; entity_id: string | null; message: string; created_at: string }
export interface StatsDTO { active_cases: number; total_cases: number; total_evidence: number; evidence_groups: number; pending_analysis: number; verified_evidence: number; integrity: { verified: number; analyzed: number; flagged: number; pending: number } }
export interface CustodyDTO { evidence_id: string; evidence_name: string; action: string; actor: string; integrity: string; details: string; occurred_at: string }
export interface AnalysisResultDTO { evidence_id: string; name: string; type: string; class_name: string; role: 'LEAF' | 'COMPOSITE'; status: string; steps: string[]; findings: { network: number; suspicious: number }; children: AnalysisResultDTO[]; summary: Summary; descendant_count: number }
export interface SearchHit { id: string; name: string; type: string; role: string; status: string; case_id: string; hash: string; source_device: string; parent_name: string | null; path: string[] }
export interface ReportDTO { kind: string; title: string; case_id: string; generated_at: string; lines: string[] }
export interface User { username: string; name: string; title: string }

export const fmtDate = (iso: string | null) => (iso ? new Date(iso).toLocaleString([], { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—')
export const fmtTime = (iso: string) => new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
export function timeAgo(iso: string) {
  const m = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000))
  return m < 1 ? 'Just now' : m < 60 ? `${m} minutes ago` : m < 1440 ? `${Math.round(m / 60)} hours ago` : `${Math.round(m / 1440)} days ago`
}

/** Read-only view of the Composite tree returned by the backend. All behaviour (analyze, add, move...) happens server-side. */
export class EvNode {
  parent: EvNode | null
  children: EvNode[]
  constructor(readonly dto: TreeDTO, parent: EvNode | null = null) { this.parent = parent; this.children = dto.children.map(c => new EvNode(c, this)) }
  getId() { return this.dto.id }
  getName() { return this.dto.name }
  getType() { return this.dto.type }
  getParent() { return this.parent }
  getChildren() { return this.children }
  isComposite() { return this.dto.kind === 'group' }
  get className() { return this.dto.class_name }
  getStatus() { return this.dto.status }
  summary() { return this.dto.summary }
  descendantCount() { return this.dto.descendant_count }
  category(): string { for (let n: EvNode | null = this; n; n = n.parent) { const c = n.dto.category; if (c && c !== 'General') return c } return 'General' }
  path(): EvNode[] { return this.parent ? [...this.parent.path(), this] : [this] }
  root(): EvNode { return this.parent ? this.parent.root() : this }
  all(): EvNode[] { return [this, ...this.children.flatMap(c => c.all())] }
  find(id: string): EvNode | null { return this.all().find(n => n.getId() === id) ?? null }
  display(): { role: string; status: string; fields: [string, string][] } {
    const d = this.dto
    const fields: [string, string][] = this.isComposite()
      ? [['Children', String(this.children.length)], ['Descendants', String(d.descendant_count)], ['Evidence items', String(d.summary.items)], ['Analysis', d.summary.items ? 'READY' : 'EMPTY'], ['Group type', d.type], ['Category', d.category ?? 'General'], ['Parent', this.parent?.getName() ?? 'None (root)']]
      : [['Source device', d.source_device || '—'], ['Evidence type', d.type], ['File size', d.file_size || '—'], ['SHA-256', d.hash || '—'], ['Collected', fmtDate(d.collected_at)], ['Collected by', d.collected_by || '—'], ['Parent group', this.parent?.getName() ?? 'None']]
    return { role: d.role, status: d.status, fields }
  }
}
