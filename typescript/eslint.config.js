// @ts-check
import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    ignores: ['**/dist/**', '**/coverage/**', '**/node_modules/**'],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    // Type-checked, not just syntactic, and scoped to the library's own source - not its tests,
    // e2e suite, or config files. This library's central hazard is a forgotten `await` on a
    // Promise-returning method (a dropped `db.transaction(...)`, a `query()` whose rejection
    // never surfaces) inside the library's own implementation or in code written against it;
    // `no-floating-promises` needs type information to see that a given expression's type is a
    // Promise, which the plain `recommended` config above does not provide. Scoped to `src/**`
    // specifically because `packages/client/tsconfig.json` only `include`s "src" - widening
    // type-aware linting to test/e2e/config files would need a second tsconfig project or
    // `projectService`'s single-file fallback, and test files here deliberately do things
    // (`async () => new Response(...)` mocks with no internal `await`, `as` narrowings on values
    // vitest's runtime already narrowed) that trip type-checked rules for reasons that have
    // nothing to do with a forgotten await.
    files: ['packages/client/src/**/*.ts'],
    extends: [...tseslint.configs.recommendedTypeChecked],
    languageOptions: {
      parserOptions: {
        project: './packages/client/tsconfig.json',
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
);
