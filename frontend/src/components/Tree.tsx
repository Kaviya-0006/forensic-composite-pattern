import { useEffect, useState } from 'react'
import { ChevronRight, MoreVertical } from 'lucide-react'
import { EvNode as Evidence } from '../types'
import { useApp } from '../context'
import { iconFor, Pill, RoleTag } from './ui'

interface T { path: Set<string>; setHover: (id: string | null) => void; menu: string | null; setMenu: (id: string | null) => void }

function Menu({ node, close }: { node: Evidence; close: () => void }) {
  const c = useApp(), comp = node.isComposite()
  const items: [string, () => void][] = [
    [comp ? 'Analyze Group' : 'Analyze', () => c.analyze(node)],
    [comp ? 'View Group' : 'View Details', () => c.select(node)]]
  if (comp) items.push(['Add Evidence', () => c.modal({ kind: 'add', target: node })], [node.getParent() ? 'Create Subgroup' : 'Create Group', () => c.modal({ kind: 'group', target: node })])
  if (node.getParent()) items.push(['Move', () => c.modal({ kind: 'move', node })], ['Remove', () => c.modal({ kind: 'remove', node })])
  return <div className="menu" role="menu">{items.map(([l, f]) => <button key={l} role="menuitem" className={l === 'Remove' ? 'danger' : ''} onClick={e => { e.stopPropagation(); close(); f() }}>{l}</button>)}</div>
}

function Node({ node, t }: { node: Evidence; t: T }) {
  const c = useApp()
  const kids = node.getChildren(), comp = node.isComposite(), isOpen = c.open.has(node.getId()), I = iconFor(node, isOpen), id = node.getId()
  return (
    <li className={comp ? 'li-c' : 'li-l'}>
      <div className={'row' + (c.sel === node ? ' sel' : '') + (t.path.has(id) ? ' onpath' : '')} onMouseEnter={() => t.setHover(id)} onMouseLeave={() => t.setHover(null)}
        onClick={() => c.select(node)} onContextMenu={e => { e.preventDefault(); t.setMenu(id) }} title={`${node.getType()} · ${comp ? 'Composite' : 'Leaf'} · ${node.path().map(p => p.getName()).join(' → ')}`}>
        {comp ? <button className="chev" aria-label={isOpen ? 'Collapse group' : 'Expand group'} onClick={e => { e.stopPropagation(); c.toggle(id) }}><ChevronRight size={16} className={isOpen ? 'rot' : ''} /></button> : <span className="chev dia">◇</span>}
        <span className={'nico ' + (comp ? 'nc' : 'nl')}><I size={16} /></span>
        <span className="nm">{node.getName()}</span>
        <RoleTag n={node} />
        {comp ? <span className="cnt">{kids.length} {kids.length === 1 ? 'item' : 'items'}</span> : <Pill s={node.getStatus()} />}
        <button className="dots" aria-label="Actions" onClick={e => { e.stopPropagation(); t.setMenu(t.menu === id ? null : id) }}><MoreVertical size={16} /></button>
        {t.menu === id && <Menu node={node} close={() => t.setMenu(null)} />}
      </div>
      {comp && isOpen && <ul className="kids">{kids.map(k => <Node key={k.getId()} node={k} t={t} />)}{kids.length === 0 && <li className="emptyrow">No evidence in this group yet.</li>}</ul>}
    </li>
  )
}

export function EvidenceTree({ root }: { root: Evidence }) {
  const [hover, setHover] = useState<string | null>(null)
  const [menu, setMenu] = useState<string | null>(null)
  useEffect(() => { const h = () => setMenu(null); document.addEventListener('click', h); return () => document.removeEventListener('click', h) }, [])
  const hn = hover ? root.find(hover) : null
  const path = new Set(hn ? hn.path().map(p => p.getId()) : [])
  return <ul className="tree"><Node node={root} t={{ path, setHover, menu, setMenu }} /></ul>
}
