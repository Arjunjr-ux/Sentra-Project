import { useCallback, useMemo, useRef, useState } from 'react'
import { IconAlert, IconCheck } from './icons'
import { ToastContext } from './toastContext'

const DISMISS_MS = 3500

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const idRef = useRef(0)

  const remove = useCallback((id) => {
    setToasts((list) => list.filter((t) => t.id !== id))
  }, [])

  const push = useCallback(
    (message, tone) => {
      const id = ++idRef.current
      setToasts((list) => [...list, { id, message, tone }])
      setTimeout(() => remove(id), DISMISS_MS)
    },
    [remove]
  )

  const api = useMemo(
    () => ({
      success: (m) => push(m, 'success'),
      error: (m) => push(m, 'error'),
    }),
    [push]
  )

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="toast-stack" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={t.tone === 'error' ? 'toast error' : 'toast'} role="status">
            <span className="check">{t.tone === 'error' ? <IconAlert /> : <IconCheck />}</span>
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
