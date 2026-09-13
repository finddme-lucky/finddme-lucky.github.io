"""수집 단계 오류. 셋 다 CLI에서 종료 코드 1로 이어진다."""


class SourceError(Exception):
    """응답이 기대한 형식이 아님 — 엔드포인트 변경 의심."""


class NetworkError(Exception):
    """재시도를 모두 소진한 네트워크 오류."""


class ValidationError(Exception):
    """수집한 값이 검증 규칙을 위반 — 저장하지 않는다."""
