// @ts-check
import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    // Generated output is excluded globally rather than per-block. Both packages carry a
    // generated directory (`client/src/generated` from openapi-typescript, `client-grpc/src/gen`
    // from protoc-gen-es); neither is ever hand-edited, so a finding in one is not actionable -
    // the only fix is to regenerate, and the drift gate already guarantees they match the
    // contract. protoc-gen-es also emits its own `/* eslint-disable */` header, which this
    // config's unused-directive reporting flagged as a warning: a permanent, unfixable warning
    // in lint output is how real findings start getting scrolled past.
    ignores: ['**/dist/**', '**/coverage/**', '**/node_modules/**', '**/src/gen/**', '**/src/generated/**'],
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
  {
    // Same rationale as the block above, for `@arcadedb/client-grpc`: `transaction.ts` and
    // `stream.ts` are almost entirely promise plumbing (begin/commit/rollback sequencing, manual
    // async-iterator draining) - exactly the shape where a forgotten `await` is both easy to write
    // and easy to miss in review. This package shipped with no type-aware lint coverage at all:
    // `files: ['packages/client/src/**/*.ts']` above never matched anything under
    // `packages/client-grpc`. `src/gen/**` needs no exclusion here - the global `ignores` at the
    // top of this file already covers every generated directory in the workspace.
    files: ['packages/client-grpc/src/**/*.ts'],
    extends: [...tseslint.configs.recommendedTypeChecked],
    languageOptions: {
      parserOptions: {
        project: './packages/client-grpc/tsconfig.json',
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
);
