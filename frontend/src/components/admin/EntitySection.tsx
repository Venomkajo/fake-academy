// One entity section of the admin panels: an add/edit form plus the
// entity's rows as a table. Fully generic — the page describes each
// entity (field defs, current rows, create/update API calls, the cache
// key to invalidate) and this component renders it: 'text'/'textarea'
// fields become inputs, 'ref' fields become selects over the given
// options and display as the referenced entity's label. One form doubles
// as "add" and "edit" (Edytuj loads a row into it); entities without a
// create endpoint (users today) only show the form while editing. Saving
// is a useMutation invalidating the given cache key, so tables refetch
// after every save.
import { useState, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { apiErrorMessage } from '../../api/auth'

/** Values of one entity form, keyed by field key — inputs are strings. */
export type FormValues = Record<string, string>

/** One form field (and table column) of an admin entity. */
export interface EntityFieldDef {
  key: string
  label: string
  kind: 'text' | 'textarea' | 'ref'
  /** 'ref' fields: the referenced entities as select options. */
  options?: readonly { value: string; label: string }[]
  /** Optional fields skip the required check (e.g. subject description). */
  optional?: boolean
}

interface Props {
  title: string
  fields: readonly EntityFieldDef[]
  rows: readonly Record<string, string | number | null>[]
  /** Cache key invalidated after a successful save (refetches the table). */
  cacheKey: readonly unknown[]
  /** Create callback; when absent the form only appears in edit mode. */
  create?: (values: FormValues) => Promise<unknown>
  update: (id: number, values: FormValues) => Promise<unknown>
}

/** Render one field's cell: refs as labels, nulls/empties as a dash. */
function displayValue(field: EntityFieldDef, row: Record<string, string | number | null>): string {
  const raw = row[field.key]
  if (raw === null || raw === '') return '—'
  if (field.kind === 'ref') {
    return field.options?.find((option) => option.value === String(raw))?.label ?? `#${raw}`
  }
  return String(raw)
}

export default function EntitySection({ title, fields, rows, cacheKey, create, update }: Props) {
  const queryClient = useQueryClient()

  // One form for both modes: editingId === null means "add", otherwise the
  // form edits that row (Edytuj loads the row's raw values into it).
  const [values, setValues] = useState<FormValues>({})
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const saveMutation = useMutation({
    // Without a create callback the form never renders in add mode, so
    // the mutation is unreachable there — resolve instead of pretending.
    mutationFn: () => {
      if (editingId === null) return create ? create(values) : Promise.resolve()
      return update(editingId, values)
    },
    onSuccess: async () => {
      // Refetch the entity list the table renders from.
      await queryClient.invalidateQueries({ queryKey: cacheKey })
      setValues({})
      setEditingId(null)
      setError(null)
    },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  function setField(key: string, value: string) {
    setValues((prev) => ({ ...prev, [key]: value }))
  }

  function startEdit(row: Record<string, string | number | null>) {
    setEditingId(Number(row.id))
    // Prefill from the raw row — null (e.g. no description) becomes ''.
    setValues(
      Object.fromEntries(
        fields.map((field): [string, string] => [
          field.key,
          row[field.key] === null ? '' : String(row[field.key]),
        ]),
      ),
    )
    setError(null)
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    // Cheap Polish required-field check; the backend (Pydantic + unique
    // constraints) stays the real validator — its 422/409 details surface
    // through apiErrorMessage below.
    const missing = fields.find((field) => !field.optional && !(values[field.key] ?? '').trim())
    if (missing) {
      setError(`Pole „${missing.label}” jest wymagane.`)
      return
    }
    saveMutation.mutate()
  }

  const inputStyle = { display: 'block', width: '100%', padding: '0.5rem' } as const
  const thStyle = {
    textAlign: 'left',
    padding: '0.4rem',
    borderBottom: '2px solid var(--color-border)',
  } as const
  const tdStyle = { padding: '0.4rem', borderBottom: '1px solid var(--color-border)' } as const

  return (
    <section className="card" style={{ marginTop: '1rem' }}>
      <h2>{title}</h2>

      {/* Entities without a create callback (users today) only show the
          form while a row is being edited. */}
      {(create || editingId !== null) && (
        <form onSubmit={handleSubmit} style={{ maxWidth: 480, display: 'grid', gap: '0.6rem' }}>
          <h3>{editingId === null ? 'Dodaj nowy wpis' : `Edytuj wpis #${editingId}`}</h3>
          {fields.map((field) => (
            <label key={field.key}>
              {field.label}
              {field.kind === 'textarea' ? (
                <textarea
                  value={values[field.key] ?? ''}
                  onChange={(e) => setField(field.key, e.target.value)}
                  rows={2}
                  style={inputStyle}
                />
              ) : field.kind === 'ref' ? (
                <select
                  value={values[field.key] ?? ''}
                  onChange={(e) => setField(field.key, e.target.value)}
                  style={inputStyle}
                >
                  <option value="">— wybierz —</option>
                  {field.options?.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  value={values[field.key] ?? ''}
                  onChange={(e) => setField(field.key, e.target.value)}
                  style={inputStyle}
                />
              )}
            </label>
          ))}
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button type="submit" className="btn" disabled={saveMutation.isPending}>
              {saveMutation.isPending ? 'Zapisywanie…' : editingId === null ? 'Dodaj' : 'Zapisz zmiany'}
            </button>
            {editingId !== null && (
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => {
                  setEditingId(null)
                  setValues({})
                  setError(null)
                }}
              >
                Anuluj
              </button>
            )}
          </div>
          {error && (
            <p role="alert" style={{ color: 'var(--color-danger)', margin: 0 }}>
              {error}
            </p>
          )}
        </form>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1.25rem' }}>
        <thead>
          <tr>
            {fields.map((field) => (
              <th key={field.key} style={thStyle}>
                {field.label}
              </th>
            ))}
            <th style={thStyle}>Akcje</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={String(row.id)}>
              {fields.map((field) => (
                <td key={field.key} style={tdStyle}>
                  {displayValue(field, row)}
                </td>
              ))}
              <td style={tdStyle}>
                <button type="button" className="btn btn-ghost" onClick={() => startEdit(row)}>
                  Edytuj
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && <p className="muted">Brak wpisów.</p>}
    </section>
  )
}