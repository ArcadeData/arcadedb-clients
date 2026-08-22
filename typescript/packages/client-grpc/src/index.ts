import { createClient as createConnectClient } from "@connectrpc/connect";
import type { Client, Interceptor } from "@connectrpc/connect";
import { createGrpcTransport } from "@connectrpc/connect-node";
import { ArcadeDbService } from "./gen/arcadedb-server-26.9.1-SNAPSHOT_pb.js";
import { sendsPlaintextPassword } from "./auth.js";
import { createInsertStream, createStreamQuery } from "./stream.js";
import { createTransaction } from "./transaction.js";

export { bearerAuth, passwordAuth } from "./auth.js";
export type { Interceptor } from "@connectrpc/connect";
export type { InsertStreamRequest, StreamQueryRequestInit } from "./stream.js";
export type { TransactionHandle } from "./transaction.js";

/** The generated Connect client for `com.arcadedb.grpc.ArcadeDbService` (the data plane). */
type RawClient = Client<typeof ArcadeDbService>;

/**
 * Options for {@link createClient}.
 */
export interface CreateClientOptions {
  /** The gRPC server's base URL, e.g. `https://localhost:50051` or `http://localhost:50051`. */
  baseUrl: string;
  /** An auth interceptor, typically {@link bearerAuth} or {@link passwordAuth}. */
  auth?: Interceptor;
  /**
   * Opts into an `http://` (non-TLS) `baseUrl` paired with a plaintext-password auth
   * interceptor ({@link passwordAuth}). Without this, `createClient` throws rather than send a
   * password over an unencrypted channel. Has no effect otherwise (TLS `baseUrl`, no auth, or a
   * non-password auth interceptor such as {@link bearerAuth}).
   */
  insecure?: boolean;
}

/**
 * ArcadeDB's gRPC data-plane client. `raw` is the generated Connect client
 * (`createClient(ArcadeDbService, transport)`); higher-level convenience methods are added on
 * top of it by later tasks in this package.
 */
export interface ArcadeDBGrpcClient {
  /** The generated Connect client for the `ArcadeDbService` data plane. */
  raw: RawClient;
  /**
   * Streams a query's results row by row. `retrievalMode` and `batchSize` pass through to the
   * server unchanged - see {@link StreamQueryRequestInit}.
   */
  streamQuery: ReturnType<typeof createStreamQuery>;
  /**
   * Streams rows to the server in chunks, handling the `session_id` / `chunk_seq` / `database` /
   * `last` envelope bookkeeping - see {@link InsertStreamRequest}.
   */
  insertStream: ReturnType<typeof createInsertStream>;
  /**
   * Runs `fn` inside a server-side transaction: begins it, hands `fn` a {@link TransactionHandle}
   * whose calls all carry the transaction's id automatically, and ends the transaction on both
   * the success and failure paths - see `transaction.ts` for the full commit/rollback contract.
   * This is the safety net against the transaction-hijack, silent-data-loss and leaked-transaction
   * defects the 2026-07 gRPC audit filed as #5040-#5042.
   */
  transaction: ReturnType<typeof createTransaction>;
}

/**
 * Creates an ArcadeDB gRPC data-plane client over `@connectrpc/connect-node`'s gRPC transport.
 *
 * Refuses to pair a plaintext-password auth interceptor ({@link passwordAuth}) with a non-TLS
 * (`http://`) `baseUrl` unless `insecure: true` is passed explicitly - sending a password in
 * cleartext metadata is a credential-exposure hazard (see issue #5048).
 */
export function createClient(opts: CreateClientOptions): ArcadeDBGrpcClient {
  const { baseUrl, auth, insecure = false } = opts;

  if (!insecure && sendsPlaintextPassword(auth) && new URL(baseUrl).protocol === "http:") {
    throw new Error(
      `createClient: refusing to send a plaintext password over insecure baseUrl "${baseUrl}". ` +
        "Use an https:// baseUrl, switch to bearerAuth, or pass insecure: true to opt in explicitly.",
    );
  }

  const transport = createGrpcTransport({ baseUrl, interceptors: auth ? [auth] : [] });
  const raw = createConnectClient(ArcadeDbService, transport);

  return {
    raw,
    streamQuery: createStreamQuery(raw),
    insertStream: createInsertStream(raw),
    transaction: createTransaction(raw),
  };
}
