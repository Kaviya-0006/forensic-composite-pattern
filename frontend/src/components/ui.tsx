import { ReactNode } from 'react'
import { X, HardDrive, Globe, FileText, MessageSquare, Phone, Network, Shield, Database, File, Folder, FolderOpen, Briefcase, Monitor, Smartphone, LucideIcon } from 'lucide-react'
import { EvNode as Evidence } from '../types'

const LEAF: Record<string, LucideIcon> = { 'Disk Image': HardDrive, 'Device Image': Smartphone, 'Browser History': Globe, 'System Log': FileText, 'Mobile Message': MessageSquare, 'Call Record': Phone, 'Network PCAP': Network, 'Firewall Log': Shield, 'DNS Log': Database }
const GROUP: Record<string, LucideIcon> = { InvestigationCase: Briefcase, ComputerEvidenceGroup: Monitor, MobileEvidenceGroup: Smartphone, NetworkEvidenceGroup: Network }
export const iconFor = (n: Evidence, open = false): LucideIcon => n.isComposite() ? GROUP[n.className] ?? (open ? FolderOpen : Folder) : LEAF[n.getType()] ?? File
export const Pill = ({ s }: { s: string }) => <span className={'pill p-' + s.toLowerCase().replace(/ /g, '-')}>{s}</span>
export const RoleTag = ({ n }: { n: Evidence }) => <span className={'role ' + (n.isComposite() ? 'r-c' : 'r-l')}>{n.isComposite() ? 'GROUP' : 'LEAF'}</span>
export const Field = ({ label, children }: { label: string; children: ReactNode }) => <label className="field"><span>{label}</span>{children}</label>
export const Head = ({ t, s, children }: { t: string; s?: string; children?: ReactNode }) => <div className="ph"><div><h1>{t}</h1>{s && <p>{s}</p>}</div><div>{children}</div></div>
export function Modal({ title, sub, onClose, wide, children }: { title: string; sub?: string; onClose: () => void; wide?: boolean; children: ReactNode }) {
  return (
    <div className="overlay" onClick={onClose}>
      <div className={'modal' + (wide ? ' wide' : '')} role="dialog" aria-label={title} onClick={e => e.stopPropagation()}>
        <div className="mh"><div><h3>{title}</h3>{sub && <p className="muted">{sub}</p>}</div><button className="x" onClick={onClose} aria-label="Close"><X size={18} /></button></div>
        {children}
      </div>
    </div>
  )
}
export const Empty = ({ t }: { t: string }) => <div className="emptystate"><Folder size={26} /><p>{t}</p></div>
