import { randomUUID } from "node:crypto";
import type { CallOptions, Client } from "@connectrpc/connect";
import type { MessageInitShape, MessageShape } from "@bufbuild/protobuf";
import type { ArcadeDbService } from "./gen/arcadedb-server-26.9.1-SNAPSHOT_pb.js";
import {
  DatabaseCredentialsSchema,
  GrpcRecordSchema,
  InsertChunkSchema,
  InsertOptionsSchema,
  InsertSummarySchema,
  QueryResultSchema,
  StreamQueryRequestSchema,
  TransactionContextSchema,
} from "./gen/arcadedb-server-26.9.1-SNAPSHOT_pb.js";

/** The generated Connect client for `com.arcadedb.grpc.ArcadeDbService`. */
type RawClient = Client<typeof ArcadeDbService>;

type GrpcRecordInit = MessageInitShape<typeof GrpcRecordSchema>;
type QueryResult = MessageShape<typeof QueryResultSchema>;
type InsertSummary = MessageShape<typeof InsertSummarySchema>;
type InsertChunkInit = MessageInitShape<typeof InsertChunkSchema>;

/**
 * `StreamQuery` request. `retrievalMode` (CURSOR / MATERIALIZE_ALL / PAGED) and `batchSize`
 * pass through to the server unchanged - this wrapper never picks a default for the caller,
 * since the three retrieval modes have materially different memory and consistency behaviour
 * that only the caller can judge.
 */
export type StreamQueryRequestInit = MessageInitShape<typeof StreamQueryRequestSchema>;

/**
 * Wraps `ArcadeDbService.StreamQuery` (server-streaming): iterates the server's stream of
 * `QueryResult` batches and yields each `GrpcRecord` row individually, flattening the batching
 * the wire protocol uses. Thin by design - no batch-size or retrieval-mode defaulting happens
 * here, both pass through to the server as given.
 */
export function createStreamQuery(raw: Pick<RawClient, "streamQuery">) {
  return async function* streamQuery(
    request: StreamQueryRequestInit,
    options?: CallOptions,
  ): AsyncGenerator<QueryResult["records"][number], void, undefined> {
    for await (const result of raw.streamQuery(request, options)) {
      yield* result.records;
    }
  };
}

/**
 * `InsertStream` request. `chunks` is the sequence of row batches the caller wants to send -
 * each element becomes exactly one wire `InsertChunk`. This wrapper owns the envelope
 * bookkeeping around those batches (`session_id`, `chunk_seq`, first-chunk-only `database`,
 * final-chunk `last`); it does not decide how rows are batched, that's the caller's call.
 */
export interface InsertStreamRequest {
  /** Sent on the first chunk only; the server caches it for the rest of the session. */
  database: string;
  credentials?: MessageInitShape<typeof DatabaseCredentialsSchema>;
  options?: MessageInitShape<typeof InsertOptionsSchema>;
  transaction?: MessageInitShape<typeof TransactionContextSchema>;
  /** One element per wire chunk. */
  chunks: AsyncIterable<GrpcRecordInit[]>;
}

/**
 * Wraps `ArcadeDbService.InsertStream` (client-streaming): turns `request.chunks` into the
 * `AsyncIterable<InsertChunk>` the generated client expects, adding the envelope bookkeeping a
 * caller would otherwise have to hand-roll:
 * - one `session_id` (a fresh UUID), stable for the whole stream
 * - `chunk_seq` starting at 1 and incrementing by 1
 * - `database` set on the first chunk only (omitted afterwards - the server caches it)
 * - `last: true` on the final chunk only
 *
 * Awaits and returns the server's single `InsertSummary` response.
 */
export function createInsertStream(raw: Pick<RawClient, "insertStream">) {
  return function insertStream(request: InsertStreamRequest, options?: CallOptions): Promise<InsertSummary> {
    return raw.insertStream(envelopeChunks(request, randomUUID()), options);
  };
}

async function* envelopeChunks(request: InsertStreamRequest, sessionId: string): AsyncGenerator<InsertChunkInit> {
  const iterator = request.chunks[Symbol.asyncIterator]();

  let current = await iterator.next();
  if (current.done === true) {
    throw new Error("insertStream: chunks must yield at least one batch of rows");
  }

  let chunkSeq = 1n;
  for (;;) {
    const next = await iterator.next();
    const isLast = next.done === true;

    yield {
      ...(chunkSeq === 1n ? { database: request.database } : {}),
      credentials: request.credentials,
      options: request.options,
      transaction: request.transaction,
      sessionId,
      chunkSeq,
      rows: current.value,
      last: isLast,
    };

    if (isLast) return;
    current = next;
    chunkSeq += 1n;
  }
}
