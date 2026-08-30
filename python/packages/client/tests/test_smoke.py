import arcadedb_client


def test_package_reports_its_version() -> None:
    assert arcadedb_client.__version__ == "0.1.0"
