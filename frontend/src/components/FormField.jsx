export function FormField({ label, error, match, id, ...inputProps }) {
  const cls = ['input']
  if (error) cls.push('is-error')
  else if (match) cls.push('is-match')

  return (
    <div className="field">
      {label && (
        <label className="field-label" htmlFor={id}>
          {label}
        </label>
      )}
      <input id={id} className={cls.join(' ')} {...inputProps} />
      {error && <span className="field-error">{error}</span>}
    </div>
  )
}
