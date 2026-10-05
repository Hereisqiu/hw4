import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '../api'
import { useAuth } from '../auth'

export default function Login() {
  const { setUser } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      setUser(await login(email, password))
      navigate('/products')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="page">
      <form className="auth" onSubmit={onSubmit}>
        <h1>Log in</h1>
        <label>Email<input type="email" value={email} onChange={e => setEmail(e.target.value)} required autoComplete="email" /></label>
        <label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} required autoComplete="current-password" /></label>
        {error && <p className="error">{error}</p>}
        <button className="btn" type="submit" disabled={busy}>{busy ? 'Logging in…' : 'Log in'}</button>
        <p className="muted">New here? <Link to="/register" className="link">Create an account</Link></p>
      </form>
    </section>
  )
}
