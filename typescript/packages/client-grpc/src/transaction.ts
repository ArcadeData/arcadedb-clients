import type { CallOptions, Client } from "@connectrpc/connect";
import type { MessageInitShape } from "@bufbuild/protobuf";
import type { ArcadeDbService } from "./gen/arcadedb-server-26.9.1-SNAPSHOT_pb.js";
import { TransactionContextSchema } from "./gen/arcadedb-server-26.9.1-SNAPSHOT_pb.js";
import { createInsertStream, createStreamQuery } from "./stream.js";

/** The generated Connect client for `com.arcadedb.grpc.ArcadeDbService`. */
type RawClient = Client<typeof ArcadeDbService>;

type TransactionContextInit = MessageInitShape<typeof TransactionContextSchema>;

/**
 * The data-plane calls available inside a {@link createTransaction} callback, each with the
 * transaction's context bound in automatically - the caller never sets `database` or
 * `transaction` itself. Deliberately excludes `beginTransaction` / `commitTransaction` /
 * `rollbackTransaction` (owned by the wrapper) and the two RPCs the design spec keeps
 * unwrapped (`insertBidirectional`, `graphBatchLoad` - reachable, unwrapped, via `client.raw`).
 */
export interface TransactionHandle {
  executeQuery: RawClient["executeQuery"];
  executeCommand: RawClient["executeCommand"];
  createRecord: RawClient["createRecord"];
  updateRecord: RawClient["updateRecord"];
  deleteRecord: RawClient["deleteRecord"];
  lookupByRid: RawClient["lookupByRid"];
  bulkInsert: RawClient["bulkInsert"];
  /** See {@link createStreamQuery}; bound to this transaction. */
  streamQuery: ReturnType<typeof createStreamQuery>;
  /** See {@link createInsertStream}; bound to this transaction. */
  insertStream: ReturnType<typeof createInsertStream>;
}

/**
 * Forces `database` and `transaction` onto `request`, overriding whatever the caller supplied.
 * This is the mechanism that makes `transaction()` safe: a caller cannot forget, drop, or
 * mismatch the transaction id the way the 2026-07 gRPC audit found three times (#5040-#5042) -
 * every request made through a `TransactionHandle` carries the bound transaction's id, always.
 */
function bindTransaction<T extends { database?: string; transaction?: TransactionContextInit }>(
  request: T,
  database: string,
  transactionId: string,
): T {
  return { ...request, database, transaction: { transactionId, database } };
}

/** Same as {@link bindTransaction}, but for the per-chunk stream `insertStream` sends. */
async function* bindTransactionToChunks<T extends { transaction?: TransactionContextInit }>(
  chunks: AsyncIterable<T>,
  database: string,
  transactionId: string,
): AsyncGenerator<T> {
  for await (const chunk of chunks) {
    yield { ...chunk, transaction: { transactionId, database } };
  }
}

function createHandle(raw: RawClient, database: string, transactionId: string): TransactionHandle {
  const bound = <T extends { database?: string; transaction?: TransactionContextInit }, R>(
    call: (request: T, options?: CallOptions) => R,
  ) => {
    return (request: T, options?: CallOptions): R => call(bindTransaction(request, database, transactionId), options);
  };

  // `streamQuery`/`insertStream`'s ergonomic wrappers (batch flattening, chunk envelope
  // bookkeeping) are reused as-is; only the underlying raw calls they forward to are bound to
  // this transaction.
  const streamRaw: Parameters<typeof createStreamQuery>[0] = { streamQuery: bound(raw.streamQuery) };
  const insertStreamRaw: Parameters<typeof createInsertStream>[0] = {
    insertStream: (chunks, options) => raw.insertStream(bindTransactionToChunks(chunks, database, transactionId), options),
  };

  return {
    executeQuery: bound(raw.executeQuery),
    executeCommand: bound(raw.executeCommand),
    createRecord: bound(raw.createRecord),
    updateRecord: bound(raw.updateRecord),
    deleteRecord: bound(raw.deleteRecord),
    lookupByRid: bound(raw.lookupByRid),
    bulkInsert: bound(raw.bulkInsert),
    streamQuery: createStreamQuery(streamRaw),
    insertStream: createInsertStream(insertStreamRaw),
  };
}

/** Best-effort: releases the server-side transaction. Its own failure is deliberately swallowed
 * so it never masks the caller's real error (the body's throw, or a failed commit). */
async function safeRollback(raw: RawClient, database: string, transactionId: string): Promise<void> {
  try {
    await raw.rollbackTransaction({ transaction: { transactionId, database } });
  } catch {
    // Discarded - see the doc comment above.
  }
}

/**
 * Builds the `transaction(database, fn)` method: begins a server-side transaction, hands `fn` a
 * {@link TransactionHandle} whose calls all carry the transaction's id automatically, and ends
 * the transaction on both the success and failure paths.
 *
 * - `fn` resolving normally commits.
 * - `fn` throwing or rejecting - synchronously or otherwise - rolls back and re-throws `fn`'s
 *   original error unchanged. If the rollback itself fails, that failure is attached as `cause`
 *   on `fn`'s error (only when `fn`'s error is an `Error` with no `cause` already, so a
 *   caller-set causal chain is never overwritten), and swallowed if attaching it throws - some
 *   errors are frozen/non-extensible, and assigning `cause` on those throws under strict-mode
 *   ESM. `fn`'s error is re-thrown as itself either way.
 * - A failing commit issues a best-effort rollback (its own failure is swallowed - the server
 *   would otherwise hold the transaction open until it's reaped) and re-throws the commit error.
 */
export function createTransaction(raw: RawClient) {
  return async function transaction<T>(database: string, fn: (tx: TransactionHandle) => Promise<T>): Promise<T> {
    const begun = await raw.beginTransaction({ database });
    const tx = createHandle(raw, database, begun.transactionId);

    let result: T;
    try {
      result = await fn(tx);
    } catch (err) {
      try {
        await raw.rollbackTransaction({ transaction: { transactionId: begun.transactionId, database } });
      } catch (rollbackErr) {
        if (err instanceof Error) {
          try {
            if (err.cause === undefined) err.cause = rollbackErr;
          } catch {
            // err is frozen/non-extensible - assigning `cause` would throw in strict-mode ESM.
            // The rollback failure is dropped in that case; err is re-thrown as itself below.
          }
        }
      }
      throw err;
    }

    try {
      await raw.commitTransaction({ transaction: { transactionId: begun.transactionId, database } });
    } catch (commitErr) {
      await safeRollback(raw, database, begun.transactionId);
      throw commitErr;
    }

    return result;
  };
}
