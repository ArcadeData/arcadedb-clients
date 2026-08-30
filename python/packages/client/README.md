# arcadedb-client

A Python HTTP client for [ArcadeDB](https://arcadedb.com), generated from ArcadeDB's OpenAPI
contract.

**This package is not yet published to PyPI.** It is under active development; the generated
client, its public surface, and installation instructions land in later milestones. For now this
package exposes only `arcadedb_client.__version__`.

## Requirements

- Python `>=3.10`.

## Development

This package lives in a [uv](https://docs.astral.sh/uv/) workspace rooted at `python/`. From
`python/`:

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy
```
