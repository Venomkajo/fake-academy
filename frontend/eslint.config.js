// ESLint configuration — deliberately comment-focused.
//
// Goal: enforce the comment conventions from CONTRIBUTING.md, not a
// general code-style regime. Broader rules can be layered on later.
//
// Globally enforced:
//   spaced-comment                  — "//x"-style typos can't hide
//   jsdoc/no-multi-asterisks, jsdoc/check-alignment, jsdoc/empty-tags
//                                   — keep the /** */ doc blocks tidy
// Enforced in src/api/** only (the "library" layer other modules import):
//   jsdoc/require-jsdoc             — every exported function & interface
//                                     must have a JSDoc block
//
// React components are documented by their file-header comment block
// instead (see CONTRIBUTING.md), so they are exempt from require-jsdoc.

import tseslint from 'typescript-eslint'
import jsdoc from 'eslint-plugin-jsdoc'

export default [
  { ignores: ['dist/**', 'node_modules/**'] },
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    plugins: { jsdoc },
    rules: {
      // "always" = `// comment`, not `//comment`. Exceptions: `///` (TS
      // triple-slash directives, e.g. vite-env.d.ts) and `#!` shebangs.
      'spaced-comment': ['error', 'always', { line: { exceptions: ['/', '#'] } }],
      'jsdoc/no-multi-asterisks': 'error',
      'jsdoc/check-alignment': 'error',
      'jsdoc/empty-tags': 'error',
    },
  },
  {
    // Declaration files legitimately use TS triple-slash directives
    // (/// <reference ... />), which look like unspaced // comments.
    files: ['**/*.d.ts'],
    rules: {
      'spaced-comment': 'off',
    },
  },
  {
    files: ['src/api/**/*.ts'],
    rules: {
      'jsdoc/require-jsdoc': [
        'error',
        {
          publicOnly: true,
          contexts: ['FunctionDeclaration', 'TSInterfaceDeclaration'],
        },
      ],
    },
  },
]