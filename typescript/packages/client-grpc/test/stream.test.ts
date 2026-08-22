import { describe, expect, it } from "vitest";
import type { MessageInitShape, MessageShape } from "@bufbuild/protobuf";
import {
  InsertChunkSchema,
  InsertSummarySchema,
  QueryResultSchema,
  StreamQueryRequest_RetrievalMode,
  StreamQueryRequestSchema,
} from "../src/gen/arcadedb-server-26.9.1-SNAPSHOT_pb.js";
import { createInsertStream, createStreamQuery } from "../src/stream.js";

type QueryResult = MessageShape<typeof QueryResultSchema>;
type InsertChunk = MessageInitShape<typeof InsertChunkSchema>;
type InsertSummary = MessageShape<typeof InsertSummarySchema>;

/** Builds a minimal `QueryResult`-shaped object, only the fields these tests exercise. */
function queryResult(records: QueryResult["records"]): QueryResult {
  return {
    $typeName: "com.arcadedb.grpc.QueryResult",
    records,
    totalRecordsInBatch: records.length,
    runningTotalEmitted: 0n,
    isLastBatch: false,
  };
}

function record(rid: string): QueryResult["records"][number] {
  return { $typeName: "com.arcadedb.grpc.GrpcRecord", rid, type: "V", properties: {} };
}

/** Builds a full `InsertSummary`-shaped object (all fields the schema declares), so fixtures
 * used across these tests reflect the real wire shape rather than an invented one. */
function insertSummary(overrides: Partial<InsertSummary> = {}): InsertSummary {
  return {
    $typeName: "com.arcadedb.grpc.InsertSummary",
    received: 0n,
    inserted: 0n,
    updated: 0n,
    ignored: 0n,
    failed: 0n,
    errors: [],
    executionTimeMs: 0n,
    startedAt: undefined,
    finishedAt: undefined,
    ...overrides,
  };
}

describe("streamQuery", () => {
  it("yields each row from the server stream, flattened across batches", async () => {
    async function* fakeServerStream(): AsyncGenerator<QueryResult> {
      yield queryResult([record("#1:0"), record("#1:1")]);
      yield queryResult([record("#1:2")]);
    }

    const raw = { streamQuery: () => fakeServerStream() };
    const streamQuery = createStreamQuery(raw);

    const rows: string[] = [];
    for await (const row of streamQuery({ database: "mydb", query: "SELECT FROM V" })) {
      rows.push(row.rid);
    }

    expect(rows).toEqual(["#1:0", "#1:1", "#1:2"]);
  });

  it("passes retrievalMode and batchSize through unchanged, without defaulting", async () => {
    let seenRequest: MessageInitShape<typeof StreamQueryRequestSchema> | undefined;

    const raw = {
      streamQuery: (request: MessageInitShape<typeof StreamQueryRequestSchema>) => {
        seenRequest = request;
        return (async function* () {})();
      },
    };
    const streamQuery = createStreamQuery(raw);

    const request = {
      database: "mydb",
      query: "SELECT FROM V",
      retrievalMode: StreamQueryRequest_RetrievalMode.PAGED,
      batchSize: 250,
    };
    // Drain the generator without binding an unused loop variable.
    const rows = streamQuery(request);
    for (let step = await rows.next(); !step.done; step = await rows.next());

    expect(seenRequest?.retrievalMode).toBe(StreamQueryRequest_RetrievalMode.PAGED);
    expect(seenRequest?.batchSize).toBe(250);
  });
});

describe("insertStream", () => {
  /** Drives `raw.insertStream`'s async iterable to completion and records every chunk sent,
   * mimicking what a real Connect transport would consume off the wire. */
  function mockRaw(summary: InsertSummary) {
    const sent: InsertChunk[] = [];
    const raw = {
      insertStream: async (request: AsyncIterable<InsertChunk>): Promise<InsertSummary> => {
        for await (const chunk of request) sent.push(chunk);
        return summary;
      },
    };
    return { raw, sent };
  }

  async function* rowBatches(): AsyncGenerator<InsertChunk["rows"]> {
    yield [{ rid: "", type: "V", properties: {} }];
    yield [{ rid: "", type: "V", properties: {} }];
    yield [{ rid: "", type: "V", properties: {} }];
  }

  it("uses exactly one non-empty session_id for the whole stream", async () => {
    const { raw, sent } = mockRaw(insertSummary({ received: 3n }));
    const insertStream = createInsertStream(raw);

    await insertStream({ database: "mydb", chunks: rowBatches() });

    expect(sent).toHaveLength(3);
    const sessionIds = new Set(sent.map((chunk) => chunk.sessionId));
    expect(sessionIds.size).toBe(1);
    expect([...sessionIds][0]).toBeTruthy();
  });

  it("starts chunk_seq at 1 and increments by 1", async () => {
    const { raw, sent } = mockRaw(insertSummary());
    const insertStream = createInsertStream(raw);

    await insertStream({ database: "mydb", chunks: rowBatches() });

    expect(sent.map((chunk) => chunk.chunkSeq)).toEqual([1n, 2n, 3n]);
  });

  it("sets database on the first chunk only", async () => {
    const { raw, sent } = mockRaw(insertSummary());
    const insertStream = createInsertStream(raw);

    await insertStream({ database: "mydb", chunks: rowBatches() });

    expect(sent[0]?.database).toBe("mydb");
    expect(sent[1]?.database).toBeUndefined();
    expect(sent[2]?.database).toBeUndefined();
  });

  it("marks only the final chunk as last", async () => {
    const { raw, sent } = mockRaw(insertSummary());
    const insertStream = createInsertStream(raw);

    await insertStream({ database: "mydb", chunks: rowBatches() });

    expect(sent.map((chunk) => chunk.last)).toEqual([false, false, true]);
  });

  it("returns the server's InsertSummary", async () => {
    const summary = insertSummary({ inserted: 42n });
    const { raw } = mockRaw(summary);
    const insertStream = createInsertStream(raw);

    const result = await insertStream({ database: "mydb", chunks: rowBatches() });

    expect(result).toBe(summary);
  });
});
