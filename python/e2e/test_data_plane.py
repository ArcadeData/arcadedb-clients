"""End-to-end tests against a real ArcadeDB server. Requires Docker."""

from __future__ import annotations

import pytest
from arcadedb_driver import ArcadeDBError, ArcadeDBServer, AsyncArcadeDBServer, basic_auth

from .conftest import ROOT_PASSWORD


def test_sync_round_trip(base_url: str, database: str) -> None:
    with ArcadeDBServer(base_url=base_url, auth=basic_auth("root", ROOT_PASSWORD)) as srv:
        assert srv.ready() is True
        assert database in srv.list_databases()
        assert srv.exists(database) is True

        db = srv.db(database)
        db.command(language="sql", command="CREATE VERTEX TYPE PersonSync IF NOT EXISTS")
        db.command(language="sql", command="INSERT INTO PersonSync SET name = 'Ada', age = 36")

        env = db.query(
            language="sql",
            command="SELECT FROM PersonSync WHERE age > :min",
            params={"min": 18},
        )
        assert [row["name"] for row in env.result] == ["Ada"]
        assert env.truncated is False


def test_a_transaction_commits(base_url: str, database: str) -> None:
    with ArcadeDBServer(base_url=base_url, auth=basic_auth("root", ROOT_PASSWORD)) as srv:
        db = srv.db(database)
        db.command(language="sql", command="CREATE VERTEX TYPE TxCommit IF NOT EXISTS")

        with db.transaction() as tx:
            tx.command(language="sql", command="INSERT INTO TxCommit SET n = 1")

        env = db.query(language="sql", command="SELECT count(*) AS c FROM TxCommit")
        assert env.result[0]["c"] == 1


def test_a_transaction_rolls_back_on_an_exception(base_url: str, database: str) -> None:
    with ArcadeDBServer(base_url=base_url, auth=basic_auth("root", ROOT_PASSWORD)) as srv:
        db = srv.db(database)
        db.command(language="sql", command="CREATE VERTEX TYPE TxRollback IF NOT EXISTS")

        with pytest.raises(RuntimeError), db.transaction() as tx:
            tx.command(language="sql", command="INSERT INTO TxRollback SET n = 1")
            raise RuntimeError("abort")

        env = db.query(language="sql", command="SELECT count(*) AS c FROM TxRollback")
        assert env.result[0]["c"] == 0


def test_a_bad_query_raises_arcadedb_error_with_a_request_id(base_url: str, database: str) -> None:
    with (
        ArcadeDBServer(base_url=base_url, auth=basic_auth("root", ROOT_PASSWORD)) as srv,
        pytest.raises(ArcadeDBError) as caught,
    ):
        srv.db(database).query(language="sql", command="SELCT nonsense")

    assert caught.value.status >= 400
    assert caught.value.request_id is not None


@pytest.mark.asyncio
async def test_async_round_trip(base_url: str, database: str) -> None:
    async with AsyncArcadeDBServer(base_url=base_url, auth=basic_auth("root", ROOT_PASSWORD)) as srv:
        assert await srv.ready() is True

        db = srv.db(database)
        await db.command(language="sql", command="CREATE VERTEX TYPE PersonAsync IF NOT EXISTS")

        async with db.transaction() as tx:
            await tx.command(language="sql", command="INSERT INTO PersonAsync SET name = 'Grace'")

        env = await db.query(language="sql", command="SELECT FROM PersonAsync")
        assert [row["name"] for row in env.result] == ["Grace"]
