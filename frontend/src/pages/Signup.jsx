import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { FormField } from '../components/FormField'
import { errorMessage, fieldErrors } from '../lib/apiError'

/* Client-side mirror of Django's default validators (SENTRA_BUILD_SPEC.md §8).
   The API remains the source of truth — server errors surface in the banner. */
function passwordRules(pw, { email, fullName }) {
  const lower = pw.toLowerCase()
  const similarTo = [email, fullName]
    .filter(Boolean)
    .map((s) => s.toLowerCase().split(/[@\s.]+/))
    .flat()
    .filter((p) => p.length >= 3)
  return [
    { label: 'At least 8 characters', ok: pw.length >= 8 },
    { label: 'Not entirely numeric', ok: pw.length > 0 && !/^\d+$/.test(pw) },
    {
      label: 'Not too similar to your name or email',
      ok: pw.length > 0 && !similarTo.some((p) => lower.includes(p)),
    },
  ]
}

export function Signup() {
  const { signup } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm: '' })
  const [banner, setBanner] = useState('')
  const [fields, setFields] = useState({})
  const [submitting, setSubmitting] = useState(false)

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const rules = useMemo(
    () => passwordRules(form.password, { email: form.email, fullName: form.full_name }),
    [form.password, form.email, form.full_name]
  )
  const confirmMatch = form.confirm.length > 0 && form.confirm === form.password
  const confirmMismatch = form.confirm.length > 0 && form.confirm !== form.password

  const onSubmit = async (e) => {
    e.preventDefault()
    setBanner('')
    setFields({})
    if (!confirmMatch) {
      setFields({ confirm: 'Passwords do not match.' })
      return
    }
    setSubmitting(true)
    try {
      await signup({ full_name: form.full_name, email: form.email, password: form.password })
      navigate('/', { replace: true })
    } catch (err) {
      setFields(fieldErrors(err))
      setBanner(errorMessage(err, 'Could not create the account.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div className="auth-brand">
          <span className="logo-mark">S</span>
          <span className="auth-wordmark">Sentra</span>
        </div>
        <h1>Create account</h1>
        <p className="auth-subtitle">New accounts start with the Viewer role</p>

        <form className="auth-form" onSubmit={onSubmit}>
          {banner && <div className="error-banner">{banner}</div>}

          <FormField
            id="full_name"
            label="Full name"
            value={form.full_name}
            onChange={set('full_name')}
            error={fields.full_name}
            required
          />
          <FormField
            id="email"
            label="Email"
            type="email"
            autoComplete="username"
            value={form.email}
            onChange={set('email')}
            error={fields.email}
            required
          />

          <div className="auth-grid-2">
            <FormField
              id="password"
              label="Password"
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={set('password')}
              error={fields.password}
              required
            />
            <FormField
              id="confirm"
              label="Confirm password"
              type="password"
              autoComplete="new-password"
              value={form.confirm}
              onChange={set('confirm')}
              error={confirmMismatch ? 'Does not match' : fields.confirm}
              match={confirmMatch}
              required
            />
          </div>

          <ul className="pw-rules">
            {rules.map((r) => (
              <li key={r.label} className={r.ok ? 'ok' : ''}>
                {r.ok ? '✓' : '•'} {r.label}
              </li>
            ))}
          </ul>

          <button className="btn btn-primary btn-block" type="submit" disabled={submitting}>
            {submitting ? 'Creating…' : 'Create account'}
          </button>
        </form>

        <div className="auth-footer">
          <span>Already have an account?</span>
          <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  )
}
