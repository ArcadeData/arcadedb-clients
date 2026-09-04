import arcadedb_driver


def test_package_reports_its_version() -> None:
    assert arcadedb_driver.__version__ == "0.1.0"
