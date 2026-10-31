import { useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { Field, Highlight, Logo } from '../components/ui'
import { homeFor, useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import api, { errorMessage } from '../services/api'
import { passwordProblems } from '../utils/format'

const SCENES = [
  { icon: 'fa-users', title: 'Customers', tone: '#714b67' },
  { icon: 'fa-box', title: 'Products', tone: '#017e84' },
  { icon: 'fa-repeat', title: 'Plans', tone: '#fbb130' },
  { icon: 'fa-file-signature', title: 'Quotations', tone: '#1bb6f9' },
  { icon: 'fa-rotate', title: 'Subscriptions', tone: '#00ceb3' },
  { icon: 'fa-file-invoice', title: 'Invoices', tone: '#fc787d' },
  { icon: 'fa-percent', title: 'Discounts', tone: '#62dd8b' },
  { icon: 'fa-chart-line', title: 'Reports', tone: '#714b67' },
]

export function Landing() {
  return (
    <div>
      <header className="flex h-14 items-center justify-between border-b border-line px-4 lg:px-10">
        <Logo />
        <div className="flex items-center gap-3 text-sm">
          <Link to="/login" className="no-underline">Sign in</Link>
          <Link to="/register" className="btn btn-primary btn-sm">Try it free</Link>
        </div>
      </header>
      <section className="px-4 py-16 text-center lg:py-24">
        <h1 className="display display-1 mb-4">All your subscriptions <br /> on <Highlight>one platform.</Highlight></h1>
        <p className="mb-8 text-xl font-light">Plans, quotes, invoices and payments. Simple, automated and <Highlight color="#62dd8b">on time.</Highlight></p>
        <div className="flex justify-center gap-3">
          <Link to="/register" className="btn btn-primary">Start now<span className="hidden md:inline">&nbsp;- It's free</span></Link>
          <Link to="/login" className="btn btn-light">Sign in</Link>
        </div>
        <p className="mt-3 text-sm text-muted">No credit card required.</p>
      </section>
      <section className="bg-subtle px-4 py-16">
        <div className="mx-auto grid max-w-3xl grid-cols-3 gap-6 sm:grid-cols-4">
          {SCENES.map((scene) => (
            <div key={scene.title} className="app-tile">
              <span className="flex h-20 w-20 items-center justify-center rounded-md bg-white shadow-sm"><i className={`fa-solid ${scene.icon} text-3xl`} style={{ color: scene.tone }} aria-hidden="true" /></span>
              <span className="text-sm text-heading">{scene.title}</span>
            </div>
          ))}
        </div>
      </section>
      <footer className="bg-surface px-4 py-6 text-center text-sm text-heading">Brightloop Software. Built for the Odoo hackathon.</footer>
    </div>
  )
}

function AuthCard({ title, phrase, children, footer }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-subtle px-4 py-8">
      <Link to="/" className="mb-6 no-underline"><Logo className="text-5xl" /></Link>
      <div className="card w-full max-w-md">
        <h1 className="display display-3 mb-6 text-center">{title} <Highlight>{phrase}</Highlight></h1>
        {children}
      </div>
      {footer && <p className="mt-4 text-sm">{footer}</p>}
    </div>
  )
}

export function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to={homeFor(user)} replace />

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      navigate(homeFor(await login(form.email, form.password)))
    } catch (failure) {
      setError(failure.response?.status === 404 ? 'Sign-in is not available yet.' : errorMessage(failure))
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthCard title="Welcome" phrase="back." footer={<>New here? <Link to="/register">Create an account</Link></>}>
      <form onSubmit={submit}>
        <Field id="email" label="Email"><input id="email" type="email" required className="input" autoComplete="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></Field>
        <Field id="password" label="Password"><input id="password" type="password" required className="input" autoComplete="current-password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /></Field>
        {error && <p className="mb-3 text-sm text-danger" role="alert">{error}</p>}
        <button className="btn btn-primary w-full" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
        <p className="mt-3 text-center text-sm"><Link to="/forgot-password">Forgot your password?</Link></p>
      </form>
    </AuthCard>
  )
}

export function Register() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [form, setForm] = useState({ name: '', company: '', email: '', password: '' })
  const [error, setError] = useState('')
  const problems = form.password ? passwordProblems(form.password) : []
  const set = (name) => (event) => setForm({ ...form, [name]: event.target.value })

  async function submit(event) {
    event.preventDefault()
    if (passwordProblems(form.password).length) return setError(`Password needs ${passwordProblems(form.password).join(', ')}.`)
    try {
      await api.post('/auth/register/', form)
      toast('Account created. Please sign in.')
      navigate('/login')
    } catch (failure) {
      setError(failure.response?.status === 404 ? 'Sign-up is not available yet.' : errorMessage(failure))
    }
  }

  return (
    <AuthCard title="Start in" phrase="minutes." footer={<>Already have an account? <Link to="/login">Sign in</Link></>}>
      <form onSubmit={submit}>
        <Field id="name" label="Your name"><input id="name" required className="input" value={form.name} onChange={set('name')} /></Field>
        <Field id="company" label="Company"><input id="company" className="input" value={form.company} onChange={set('company')} /></Field>
        <Field id="email" label="Email"><input id="email" type="email" required className="input" value={form.email} onChange={set('email')} /></Field>
        <Field id="password" label="Password" error={problems.length ? `Needs ${problems.join(', ')}.` : ''}>
          <input id="password" type="password" required className="input" autoComplete="new-password" value={form.password} onChange={set('password')} />
        </Field>
        {error && <p className="mb-3 text-sm text-danger" role="alert">{error}</p>}
        <button className="btn btn-primary w-full">Create account</button>
      </form>
    </AuthCard>
  )
}

export function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  async function submit(event) {
    event.preventDefault()
    try {
      await api.post('/auth/password/forgot/', { email })
      setSent(true)
    } catch (failure) {
      setError(errorMessage(failure))
    }
  }

  return (
    <AuthCard title="Reset your" phrase="password." footer={<Link to="/login">Back to sign in</Link>}>
      {sent ? <p>If that email is registered, a reset link is on its way.</p> : (
        <form onSubmit={submit}>
          <Field id="email" label="Registered email"><input id="email" type="email" required className="input" value={email} onChange={(event) => setEmail(event.target.value)} /></Field>
          {error && <p className="mb-3 text-sm text-danger" role="alert">{error}</p>}
          <button className="btn btn-primary w-full">Send reset link</button>
        </form>
      )}
    </AuthCard>
  )
}

export function ResetPassword() {
  const { uid, token } = useParams()
  const navigate = useNavigate()
  const { toast } = useToast()
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const problems = password ? passwordProblems(password) : []

  async function submit(event) {
    event.preventDefault()
    try {
      await api.post('/auth/password/reset/', { uid, token, password })
      toast('Password changed. Please sign in.')
      navigate('/login')
    } catch (failure) {
      setError(errorMessage(failure))
    }
  }

  return (
    <AuthCard title="Choose a new" phrase="password.">
      <form onSubmit={submit}>
        <Field id="password" label="New password" error={problems.length ? `Needs ${problems.join(', ')}.` : ''}>
          <input id="password" type="password" required className="input" autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </Field>
        {error && <p className="mb-3 text-sm text-danger" role="alert">{error}</p>}
        <button className="btn btn-primary w-full" disabled={problems.length > 0}>Change password</button>
      </form>
    </AuthCard>
  )
}
