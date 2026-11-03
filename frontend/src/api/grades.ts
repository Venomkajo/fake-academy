import { api } from './client'

/**
 * Parse the API's decimal strings ("4.50") into numbers at the library
 * boundary, so pages deal with plain numbers. Two decimals in a float64
 * are exact enough for every display this app does.
 */
function toNumberOrNull(value: string | null): number | null {
  return value === null ? null : Number(value)
}

// --- wire shapes -------------------------------------------------------------
//
// The backend models these columns as SQLAlchemy Numeric (exact Decimal),
// and FastAPI serializes Decimal as a JSON STRING. The interfaces below
// mirror the wire one to one; the exported shapes further down are the
// parsed (number) versions the functions return.

/** Wire shape of GET /grades/me rows (decimals as strings). */
interface GradeForStudentWire {
  id: number
  value: string | null
  symbol: string | null
  created_at: string
  modified_at: string
  category_name: string
  category_weight: string
  subject_name: string
  teacher_first_name: string
  teacher_last_name: string
  group_name: string
}

/** Wire shape of a grade category (weight as a string). */
interface GradeCategoryWire {
  id: number
  assignment_id: number
  name: string
  weight: string
}

/** Wire shape of one gradebook cell (value as a string or null). */
interface SheetGradeWire {
  id: number
  student_id: number
  category_id: number
  value: string | null
  symbol: string | null
}

// --- exported shapes ---------------------------------------------------------

/**
 * One of the student's grades as fetchMyGrades returns it: the grade row
 * flattened with the category/subject/teacher/group names the view groups by.
 */
export interface GradeForStudent {
  id: number
  value: number | null
  symbol: string | null
  created_at: string
  modified_at: string
  category_name: string
  category_weight: number
  subject_name: string
  teacher_first_name: string
  teacher_last_name: string
  group_name: string
}

/** One grading bucket of a teaching assignment (name + percentage weight). */
export interface GradeCategory {
  id: number
  assignment_id: number
  name: string
  weight: number
}

/** One of the teacher's assignments: subject × group plus its grade categories. */
export interface TeachingAssignment {
  id: number
  subject_name: string
  group_name: string
  field_name: string
  categories: GradeCategory[]
}

/** One gradebook cell: the grade itself with its student and category ids. */
export interface SheetGrade {
  id: number
  student_id: number
  category_id: number
  value: number | null
  symbol: string | null
}

/** A student row of the gradebook (name only — no email, no hash). */
export interface SheetStudent {
  id: number
  first_name: string
  last_name: string
}

/** Payload of GET /grades/assignment/{id}/sheet: the group's students and their grades. */
export interface GradeSheet {
  students: SheetStudent[]
  grades: SheetGrade[]
}

/**
 * Body of POST /grades/categories. Weight is a percentage; sent as a string
 * so the backend's Decimal field parses it exactly (no float artifacts).
 */
export type GradeCategoryPayload = { assignment_id: number; name: string; weight: string }

/**
 * Body of POST /grades — exactly one of value/symbol must be set
 * (value: a decimal like '4.5'; symbol: 'ZAL' or 'NZAL').
 */
export type GradePayload = {
  student_id: number
  category_id: number
  value?: string | null
  symbol?: string | null
}

/**
 * Body of PATCH /grades/{id}; both keys are always sent — an explicit null
 * clears the other half of the value/symbol pair.
 */
export type GradeUpdatePayload = { value: string | null; symbol: string | null }

/** GET /grades/me — the calling student's grades with joined names. */
export async function fetchMyGrades(): Promise<GradeForStudent[]> {
  const response = await api.get<GradeForStudentWire[]>('/grades/me')
  return response.data.map((grade) => ({
    ...grade,
    value: toNumberOrNull(grade.value),
    category_weight: Number(grade.category_weight),
  }))
}

/** GET /grades/teaching — the calling teacher's assignments with categories. */
export async function fetchMyTeaching(): Promise<TeachingAssignment[]> {
  const response = await api.get<
    { id: number; subject_name: string; group_name: string; field_name: string; categories: GradeCategoryWire[] }[]
  >('/grades/teaching')
  return response.data.map((assignment) => ({
    ...assignment,
    categories: assignment.categories.map((category) => ({
      ...category,
      weight: Number(category.weight),
    })),
  }))
}

/** GET /grades/assignment/{id}/sheet — the gradebook of one assignment. */
export async function fetchGradeSheet(assignmentId: number): Promise<GradeSheet> {
  const response = await api.get<{ students: SheetStudent[]; grades: SheetGradeWire[] }>(
    `/grades/assignment/${assignmentId}/sheet`,
  )
  return {
    students: response.data.students,
    grades: response.data.grades.map((grade) => ({
      ...grade,
      value: toNumberOrNull(grade.value),
    })),
  }
}

/** POST /grades/categories — add a grade category to one of the caller's assignments. */
export async function createGradeCategory(payload: GradeCategoryPayload): Promise<GradeCategory> {
  const response = await api.post<GradeCategoryWire>('/grades/categories', payload)
  return { ...response.data, weight: Number(response.data.weight) }
}

/** DELETE /grades/categories/{id} — remove an empty category (409 if it has grades). */
export async function deleteGradeCategory(categoryId: number): Promise<void> {
  await api.delete(`/grades/categories/${categoryId}`)
}

/** POST /grades — issue one grade (value or symbol) to a student. */
export async function issueGrade(payload: GradePayload): Promise<SheetGrade> {
  const response = await api.post<SheetGradeWire>('/grades', payload)
  return { ...response.data, value: toNumberOrNull(response.data.value) }
}

/** PATCH /grades/{id} — edit an existing grade's value or symbol. */
export async function updateGrade(gradeId: number, payload: GradeUpdatePayload): Promise<SheetGrade> {
  const response = await api.patch<SheetGradeWire>(`/grades/${gradeId}`, payload)
  return { ...response.data, value: toNumberOrNull(response.data.value) }
}