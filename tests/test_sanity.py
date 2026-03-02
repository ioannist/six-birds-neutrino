import sbt_spt_audit


def test_version_exists() -> None:
    assert hasattr(sbt_spt_audit, "__version__")


def test_hello() -> None:
    assert sbt_spt_audit.hello.hello() == "sbt_spt_audit ok"
