import { useAuth } from './useAuth'

/* Renders children only if the current user holds `perm`. UX gating only — the
   API is the real boundary (SENTRA_BUILD_SPEC.md §5). */
export function Can({ perm, fallback = null, children }) {
  const { hasPerm } = useAuth()
  return hasPerm(perm) ? children : fallback
}
