// Bundled (never executed) by test/treeshake.test.ts. Imports ONLY `createClient` and calls
// `query` - the data plane - so the bundle's eagerly-loaded chunk can be checked for the absence
// of the PromQL and Grafana dashboard modules. Do not add anything else here; see
// test/treeshake.test.ts for how to prove the resulting assertion can fail.
import { createClient } from "../../src/index.js";

const server = createClient({ baseUrl: "http://localhost:2480" });
const db = server.db("bench");
await db.query({ language: "sql", command: "select 1" });
