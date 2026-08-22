import { defineConfig } from "vitest/config";

/**
 * Default config, used by `npm test` (`vitest run`). Excludes `e2e/`: those
 * tests spin up a real ArcadeDB server via Testcontainers (Docker required,
 * container pull/startup measured in tens of seconds), so they run only via
 * `npm run e2e` (`e2e/vitest.config.ts`), never as part of the fast, offline
 * unit suite.
 */
export default defineConfig({
  test: {
    exclude: ["**/node_modules/**", "**/dist/**", "e2e/**"],
  },
});
