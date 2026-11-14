// Shared query-state presentation pieces: the muted "Ładowanie…" notice every
// data view shows while its query is in flight (QueryStatus) and the red
// inline error line (ErrorMessage). Extracted from a pattern copy-pasted
// across ~13 views — this one place owns it; the danger color lives in
// global.css (.error-message), not in inline styles.
import type { ReactNode } from 'react'

import { apiErrorMessage } from '../../api/auth'

interface QueryStatusProps {
  /** Render the notice only while true; otherwise render nothing. */
  isLoading: boolean
  /** Notice text; the default fits every plain data view. */
  label?: string
}

/** The "Ładowanie…" line shown while a query is in flight. */
export function QueryStatus({ isLoading, label = 'Ładowanie…' }: QueryStatusProps) {
  return isLoading ? <p className="muted">{label}</p> : null
}

interface ErrorMessageProps {
  /** A thrown error (query/mutation result) translated via apiErrorMessage. */
  error?: unknown
  /** A ready-made message (client-side validation); wins over `error`. */
  children?: ReactNode
  /** Extra classes (e.g. "span-2" in a grid form, "is-spaced" for breathing room). */
  className?: string
  /** Compact variant for tight spots (gradebook cells). */
  small?: boolean
}

/**
 * The red inline error line (role="alert"). Renders nothing without a
 * message, so callers may hand it a value that can be null.
 */
export function ErrorMessage({ error, children, className, small }: ErrorMessageProps) {
  const message = children ?? (error != null ? apiErrorMessage(error) : null)
  if (message == null) return null
  const classes = ['error-message', small ? 'is-small' : '', className]
    .filter(Boolean)
    .join(' ')
  return <p role="alert" className={classes}>{message}</p>
}