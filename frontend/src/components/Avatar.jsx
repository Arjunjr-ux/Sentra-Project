import { initials } from '../lib/format'

export function Avatar({ name, email, small }) {
  return <span className={small ? 'avatar avatar-sm' : 'avatar'}>{initials(name || email)}</span>
}
