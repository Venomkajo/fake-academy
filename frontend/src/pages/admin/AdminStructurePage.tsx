// Admin structure panel (route "/admin/structure", README card A2): one
// tab per structure entity — kierunki, grupy, przedmioty, przypisania
// wykładowców i członkostwa grup. Rows come from GET /admin/structure,
// which carries only FK ids; teacher/student/field names are resolved
// client-side from the /admin/users list (that query also feeds the
// ref-field selects). Each tab is an EntitySection wired to the /admin
// POST/PATCH write endpoints.
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import {
  createFieldOfStudy,
  createGroupMembership,
  createStudentGroup,
  createSubject,
  createTeachingAssignment,
  fetchAllUsers,
  fetchStructure,
  updateFieldOfStudy,
  updateGroupMembership,
  updateStudentGroup,
  updateSubject,
  updateTeachingAssignment,
} from '../../api/admin'
import { apiErrorMessage } from '../../api/auth'

import EntitySection, {
  type EntityFieldDef,
  type FormValues,
} from '../../components/admin/EntitySection'

/** Everything one entity tab needs: field defs, current rows, API calls. */
interface EntityConfig {
  key: string
  title: string
  fields: readonly EntityFieldDef[]
  rows: readonly Record<string, string | number | null>[]
  create: (values: FormValues) => Promise<unknown>
  update: (id: number, values: FormValues) => Promise<unknown>
}

export default function AdminStructurePage() {
  const structureQuery = useQuery({ queryKey: ['admin_structure'], queryFn: fetchStructure })
  // Users are queried only to resolve FK ids into names (the structure
  // payload carries ids by design) — a missing user degrades to "#id".
  const usersQuery = useQuery({ queryKey: ['admin_users'], queryFn: fetchAllUsers })
  const [activeKey, setActiveKey] = useState('fields')

  const structure = structureQuery.data
  const users = usersQuery.data ?? []

  const fieldName = (id: number) =>
    structure?.fields.find((field) => field.id === id)?.name ?? `#${id}`
  const userLabel = (id: number) => {
    const user = users.find((u) => u.id === id)
    return user ? `${user.first_name} ${user.last_name}` : `#${id}`
  }

  // Ref-field options: referenced entities as select options. Group labels
  // carry the field name so same-named groups stay distinguishable.
  const fieldOptions = (structure?.fields ?? []).map((field) => ({
    value: String(field.id),
    label: field.name,
  }))
  const groupOptions = (structure?.groups ?? []).map((group) => ({
    value: String(group.id),
    label: `${group.name} — ${fieldName(group.field_id)}`,
  }))
  const subjectOptions = (structure?.subjects ?? []).map((subject) => ({
    value: String(subject.id),
    label: subject.name,
  }))
  const teacherOptions = users
    .filter((user) => user.role === 'teacher')
    .map((user) => ({ value: String(user.id), label: userLabel(user.id) }))
  const studentOptions = users
    .filter((user) => user.role === 'student')
    .map((user) => ({ value: String(user.id), label: userLabel(user.id) }))

  // The five tabs, in README A2's build order; create/update adapt the
  // string form values into each endpoint's typed payload.
  const entities: EntityConfig[] = [
    {
      key: 'fields',
      title: 'Kierunki',
      fields: [{ key: 'name', label: 'Nazwa', kind: 'text' }],
      rows: structure?.fields ?? [],
      create: (v) => createFieldOfStudy({ name: v.name.trim() }),
      update: (id, v) => updateFieldOfStudy(id, { name: v.name.trim() }),
    },
    {
      key: 'groups',
      title: 'Grupy studenckie',
      fields: [
        { key: 'name', label: 'Nazwa', kind: 'text' },
        { key: 'field_id', label: 'Kierunek', kind: 'ref', options: fieldOptions },
      ],
      rows: structure?.groups ?? [],
      create: (v) => createStudentGroup({ name: v.name.trim(), field_id: Number(v.field_id) }),
      update: (id, v) => updateStudentGroup(id, { name: v.name.trim(), field_id: Number(v.field_id) }),
    },
    {
      key: 'subjects',
      title: 'Przedmioty',
      fields: [
        { key: 'name', label: 'Nazwa', kind: 'text' },
        { key: 'description', label: 'Opis', kind: 'textarea', optional: true },
      ],
      rows: structure?.subjects ?? [],
      create: (v) => createSubject({ name: v.name.trim(), description: v.description || null }),
      update: (id, v) => updateSubject(id, { name: v.name.trim(), description: v.description || null }),
    },
    {
      key: 'teaching_assignments',
      title: 'Przypisania wykładowców',
      fields: [
        { key: 'subject_id', label: 'Przedmiot', kind: 'ref', options: subjectOptions },
        { key: 'teacher_id', label: 'Wykładowca', kind: 'ref', options: teacherOptions },
        { key: 'group_id', label: 'Grupa', kind: 'ref', options: groupOptions },
      ],
      rows: structure?.teaching_assignments ?? [],
      create: (v) =>
        createTeachingAssignment({
          subject_id: Number(v.subject_id),
          teacher_id: Number(v.teacher_id),
          group_id: Number(v.group_id),
        }),
      update: (id, v) =>
        updateTeachingAssignment(id, {
          subject_id: Number(v.subject_id),
          teacher_id: Number(v.teacher_id),
          group_id: Number(v.group_id),
        }),
    },
    {
      key: 'group_memberships',
      title: 'Członkostwa grup',
      fields: [
        { key: 'student_id', label: 'Student', kind: 'ref', options: studentOptions },
        { key: 'group_id', label: 'Grupa', kind: 'ref', options: groupOptions },
      ],
      rows: structure?.group_memberships ?? [],
      create: (v) => createGroupMembership({ student_id: Number(v.student_id), group_id: Number(v.group_id) }),
      update: (id, v) =>
        updateGroupMembership(id, { student_id: Number(v.student_id), group_id: Number(v.group_id) }),
    },
  ]

  if (structureQuery.isLoading) {
    return <p className="muted">Ładowanie…</p>
  }
  if (structureQuery.isError) {
    return (
      <p role="alert" style={{ color: 'var(--color-danger)' }}>
        {apiErrorMessage(structureQuery.error)}
      </p>
    )
  }

  const active = entities.find((entity) => entity.key === activeKey) ?? entities[0]

  return (
    <section>
      <h1>Struktura uczelni</h1>
      <p className="muted">
        Kolejność budowania: kierunek → grupa → przedmiot → przypisania (wykładowcy, studenci).
      </p>

      {/* Tabs: one button per entity; the active one renders below. */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {entities.map((entity) => (
          <button
            key={entity.key}
            type="button"
            className={entity.key === active.key ? 'btn' : 'btn btn-ghost'}
            onClick={() => setActiveKey(entity.key)}
          >
            {entity.title}
          </button>
        ))}
      </div>

      {/* key= resets the shared form's state whenever the tab switches. */}
      <EntitySection
        key={active.key}
        title={active.title}
        fields={active.fields}
        rows={active.rows}
        cacheKey={['admin_structure']}
        create={active.create}
        update={active.update}
      />
    </section>
  )
}