from lucky.errors import NetworkError, SourceError, ValidationError


def test_errors_are_distinct_exceptions():
    for cls in (SourceError, NetworkError, ValidationError):
        assert issubclass(cls, Exception)
    assert len({SourceError, NetworkError, ValidationError}) == 3
