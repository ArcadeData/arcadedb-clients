import { describe, expect, it } from "vitest";
import type { MessageInitShape } from "@bufbuild/protobuf";
import type {
  BeginTransactionRequestSchema,
  BeginTransactionResponseSchema,
  CommitTransactionRequestSchema,
  CommitTransactionResponseSchema,
  ExecuteQueryRequestSchema,
  RollbackTransactionRequestSchema,
  RollbackTransactionResponseSchema,
} from "../src/gen/arcadedb-server-26.9.1-SNAPSHOT_pb.js";
import { createTransaction } from "../src/transaction.js";

type BeginRequest = MessageInitShape<typeof BeginTransactionRequestSchema>;
type BeginResponse = MessageInitShape<typeof BeginTransactionResponseSchema>;
type CommitRequest = MessageInitShape<typeof CommitTransactionRequestSchema>;
type CommitResponse = MessageInitShape<typeof CommitTransactionResponseSchema>;
type RollbackRequest = MessageInitShape<typeof RollbackTransactionRequestSchema>;
type RollbackResponse = MessageInitShape<typeof RollbackTransactionResponseSchema>;
type ExecuteQueryRequest = MessageInitShape<typeof ExecuteQueryRequestSchema>;

/** Records every call made through a fake `raw` client, mimicking the subset of
 * `Client<typeof ArcadeDbService>` the transaction wrapper touches. */
function mockRaw(opts: { transactionId?: string; commitFails?: boolean } = {}) {
  const { transactionId = "tx-123", commitFails = false } = opts;

  const calls: {
    begin: BeginRequest[];
    commit: CommitRequest[];
    rollback: RollbackRequest[];
    executeQuery: ExecuteQueryRequest[];
  } = { begin: [], commit: [], rollback: [], executeQuery: [] };

  const raw = {
    beginTransaction: async (request: BeginRequest): Promise<BeginResponse> => {
      calls.begin.push(request);
      return { transactionId, timestamp: 0n };
    },
    commitTransaction: async (request: CommitRequest): Promise<CommitResponse> => {
      calls.commit.push(request);
      if (commitFails) throw new Error("commit failed");
      return { success: true, committed: true, message: "", timestamp: 0n };
    },
    rollbackTransaction: async (request: RollbackRequest): Promise<RollbackResponse> => {
      calls.rollback.push(request);
      return { success: true, rolledBack: true, message: "" };
    },
    executeQuery: async (request: ExecuteQueryRequest) => {
      calls.executeQuery.push(request);
      return { results: [], executionTimeMs: 0n, queryPlan: "" };
    },
    executeCommand: async (request: unknown) => {
      calls.executeQuery.push(request as ExecuteQueryRequest);
      return { success: true, message: "", affectedRecords: 0n, executionTimeMs: 0n, records: [], stats: undefined };
    },
    createRecord: async () => ({ rid: "" }),
    updateRecord: async () => ({ success: true, updated: true }),
    deleteRecord: async () => ({ success: true, deleted: true, message: "" }),
    lookupByRid: async () => ({ found: false, record: undefined }),
    bulkInsert: async () => ({
      received: 0n,
      inserted: 0n,
      updated: 0n,
      ignored: 0n,
      failed: 0n,
      errors: [],
      executionTimeMs: 0n,
      startedAt: undefined,
      finishedAt: undefined,
    }),
    streamQuery: async function* () {},
    insertStream: async () => ({
      received: 0n,
      inserted: 0n,
      updated: 0n,
      ignored: 0n,
      failed: 0n,
      errors: [],
      executionTimeMs: 0n,
      startedAt: undefined,
      finishedAt: undefined,
    }),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } as any;

  return { raw, calls };
}

describe("transaction", () => {
  it("calls BeginTransaction first and threads its transaction_id into every subsequent request", async () => {
    const { raw, calls } = mockRaw({ transactionId: "tx-abc" });
    const transaction = createTransaction(raw);

    await transaction("mydb", async (tx) => {
      await tx.executeQuery({ query: "SELECT FROM V" });
      await tx.executeQuery({ query: "SELECT FROM E" });
    });

    expect(calls.begin).toHaveLength(1);
    expect(calls.begin[0]?.database).toBe("mydb");
    expect(calls.executeQuery).toHaveLength(2);
    for (const request of calls.executeQuery) {
      expect(request.transaction?.transactionId).toBe("tx-abc");
    }
  });

  it("commits on normal return and does not roll back", async () => {
    const { raw, calls } = mockRaw();
    const transaction = createTransaction(raw);

    const result = await transaction("mydb", async (tx) => {
      await tx.executeQuery({ query: "SELECT FROM V" });
      return 42;
    });

    expect(result).toBe(42);
    expect(calls.commit).toHaveLength(1);
    expect(calls.rollback).toHaveLength(0);
  });

  it("rolls back when the body rejects, does not commit, and propagates the original error", async () => {
    const { raw, calls } = mockRaw();
    const transaction = createTransaction(raw);
    const originalError = new Error("boom - async rejection");

    await expect(
      transaction("mydb", async () => {
        await Promise.resolve();
        throw originalError;
      }),
    ).rejects.toBe(originalError);

    expect(calls.rollback).toHaveLength(1);
    expect(calls.commit).toHaveLength(0);
  });

  it("rolls back when the body throws synchronously, not only on a rejected promise", async () => {
    const { raw, calls } = mockRaw();
    const transaction = createTransaction(raw);
    const originalError = new Error("boom - synchronous throw");

    await expect(
      transaction("mydb", (): never => {
        throw originalError;
      }),
    ).rejects.toBe(originalError);

    expect(calls.rollback).toHaveLength(1);
    expect(calls.commit).toHaveLength(0);
  });

  it("issues a best-effort rollback and surfaces the commit error when commit fails", async () => {
    const { raw, calls } = mockRaw({ commitFails: true });
    const transaction = createTransaction(raw);

    await expect(
      transaction("mydb", async (tx) => {
        await tx.executeQuery({ query: "SELECT FROM V" });
      }),
    ).rejects.toThrow("commit failed");

    expect(calls.commit).toHaveLength(1);
    expect(calls.rollback).toHaveLength(1);
  });
});
