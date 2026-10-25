# Contributing — comment & documentation conventions

This project enforces a small, opinionated set of comment/docstring rules
with linters, so the conventions hold without code review vigilance.

## Universal rules

- **Language**: comments and docstrings in **English**. User-facing strings
  (UI text, API error messages) stay in **Polish** — those are product
  content, not developer documentation.
- **Generated files are exempt**: Alembic migrations, `env.py`, `vite-env.d.ts`
  style declaration files — never hand-write comments in generated code.

## Python (backend/)

| Thing | Required | Enforced by |
| --- | --- | --- |
| Module docstring (`"""..."""` at the top of the file) | yes — one or two lines: what lives here | Ruff `D100` |
| Class docstring | yes — what the class represents, one line unless it needs more | Ruff `D101` |
| Function/method docstring | yes — imperative summary ("Return the..."), ends with a period | Ruff `D102`, `D103` |
| Package `__init__.py` docstring | yes — what the package bundles | Ruff `D104` |
| Inline notes (`# ...`) | optional — for field-level explanations, stepping stones, warnings | not linted |
| Multi-line docstrings | summary line, blank line, then the description | Ruff `D205` etc. |

Docstrings are **prose, not Google/NumPy-format**: no `Args:`/`Returns:`
scaffolding unless a function genuinely needs it. PEP 257 mechanics only
(period at the end, imperative first line, quotes placement) — enforced via
Ruff's pydocstyle rules (`D*`) with the `pep257` convention.

## TypeScript / React (frontend/src)

Two documentation styles, split by role:

| Kind of file | Documentation style |
| --- | --- |
| **Library layer** (`src/api/**`) | `/** */` JSDoc on **every exported function and interface** — enforced by ESLint (`jsdoc/require-jsdoc`, `publicOnly`). Types are documented too (convention, not linted). |
| **React components & pages** | a `//` file-header block at the top of the file (1–10 lines) explaining what the component is and any non-obvious behavior. The function itself is NOT JSDoc'd — that would duplicate the header. |
| Config files (`vite.config.ts`, `main.tsx`, ...) | same `//` file-header block at the top. |

Other rules:

- Inline explanations use `// ...`; inside JSX use `{/* ... */}`.
- Section banners like `// --- token storage ---...` are optional; if used,
  pad the dashes to the same width (see `src/api/auth.ts`).
- `spaced-comment` is enforced: `// comment`, never `//comment`
  (`///` triple-slash directives excepted).

## CSS (frontend/src/styles/global.css)

- One file-header banner at the top (the `=====` block).
- Section separators use `/* --- name ------- */`, dashes padded to
  column 79. Design tokens in `:root` are grouped under short category
  comments (`/* palette */`, `/* geometry */`, ...), not one per token.

## Running the linters

Backend (Ruff — installs into the repo-root venv):

```powershell
pip install -r backend/requirements-dev.txt   # once
cd backend
ruff check .
```

Frontend (ESLint — devDependencies of frontend/package.json):

```powershell
cd frontend
npm run lint
```

Run both before committing; both must report zero problems. The configs:

- `backend/pyproject.toml` — Ruff rule selection (`E4,E7,E9,F,D`) and the
  `alembic/**` exemptions.
- `frontend/eslint.config.js` — comment-focused ESLint setup.
