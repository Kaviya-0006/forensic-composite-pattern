import { ReactNode } from 'react'
import { useApp } from '../context'
import { Header, Sidebar } from '../components/Shell'

export default function AppLayout({ children, pageKey }: { children: ReactNode; pageKey: string }) {
  const { collapsed, settings } = useApp()
  return (
    <div className={'app' + (collapsed ? ' min' : '') + (settings.compact ? ' compact' : '')}>
      <Sidebar />
      <div className="main"><Header /><main key={pageKey}>{children}</main></div>
    </div>
  )
}
