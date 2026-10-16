import { FormEvent, useState } from 'react'
import { User } from '../types'
import * as api from '../services/api'
import { Logo } from '../components/Shell'

export default function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [u, setU] = useState('kaviya'), [p, setP] = useState('forensic123'), [err, setErr] = useState(''), [busy, setBusy] = useState(false)
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setErr('')
    try { onLogin(await api.login(u, p)) } catch (x) { setErr((x as Error).message) } finally { setBusy(false) }
  }
  return (
    <div className="loginwrap">
      <form className="logincard" onSubmit={submit}>
        <div className="brand"><Logo /><div className="bt"><b>FORENSICVAULT</b><small>DIGITAL EVIDENCE INTELLIGENCE</small></div></div>
        <div className="secure"><i />SECURE INVESTIGATION ENVIRONMENT</div>
        <label className="field"><span>Investigator username</span><input value={u} onChange={e => setU(e.target.value)} autoFocus /></label>
        <label className="field"><span>Password</span><input type="password" value={p} onChange={e => setP(e.target.value)} /></label>
        {err && <div className="loginerr" role="alert">{err}</div>}
        <button className="btn" disabled={busy}>{busy ? 'Signing in...' : 'Sign in'}</button>
        <p className="muted small">Demo accounts: kaviya, arjun, meera · password forensic123</p>
      </form>
    </div>
  )
}
