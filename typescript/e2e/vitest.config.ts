import { defineConfig } from "vitest/config";

/**
 * Config for `npm run e2e`, kept out of the default `vitest.config.ts` so
 * this suite never runs as part of `npm test`. These tests start a real
 * ArcadeDB server in a Testcontainers-managed Docker container; image pull
 * plus server startup can comfortably exceed vitest's 5s default timeout,
 * so both the per-test and per-hook timeouts are raised well past what a
 * healthy run needs.
 */
export default defineConfig({
  test: {
    include: ["e2e/**/*.test.ts"],
    testTimeout: 60_000,
    hookTimeout: 90_000,
  },
});
