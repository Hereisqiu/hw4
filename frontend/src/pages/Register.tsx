import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../api'
import { useAuth } from '../auth'

export default function Register() {
  const { setUser } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const field = (key: keyof typeof form) => ({
    value: form[key],
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, [key]: e.target.value })),
  })

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) {
      setError('Passwords do not match')
      return
    }
    setBusy(true)
    try {
      const { confirm: _confirm, ...body } = form
      setUser(await register(body))
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
        <h1>Create account</h1>
        <label>First name<input {...field('first_name')} required autoComplete="given-name" /></label>
        <label>Last name<input {...field('last_name')} required autoComplete="family-name" /></label>
        <label>Email<input type="email" {...field('email')} required autoComplete="email" /></label>
        <label>Password<input type="password" {...field('password')} required minLength={8} autoComplete="new-password" /></label>
        <label>Confirm password<input type="password" {...field('confirm')} required minLength={8} autoComplete="new-password" /></label>
        {error && <p className="error">{error}</p>}
        <button className="btn" type="submit" disabled={busy}>{busy ? 'Creating…' : 'Create account'}</button>
        <p className="muted">Already have an account? <Link to="/login" className="link">Log in</Link></p>
      </form>
    </section>
  )
}
