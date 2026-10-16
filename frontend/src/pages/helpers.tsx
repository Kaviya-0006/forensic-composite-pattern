import { useApp } from '../context'

/** Lets the user pick ANY evidence object (leaf, group or the case itself) the same way. */
export function NodePicker() {
  const c = useApp()
  return (
    <select value={c.sel.getId()} onChange={e => { const n = c.cur.find(e.target.value); if (n) c.select(n) }} aria-label="Select evidence object">
      {c.cur.all().map(n => <option key={n.getId()} value={n.getId()}>{n.isComposite() ? '[Group] ' : '[Item] '}{n.path().map(p => p.getName()).join(' → ')}</option>)}
    </select>
  )
}
