"""Common source connector interface — TDD §13.1, ADR-002.

KLIBRA requires a unified contract across heterogeneous sources (World Bank,
ECB SDMX, FRED, IMF, Alpha Vantage, CoinGecko). Each connector implements six
lifecycle methods: discover, authenticate, extract, validate_response,
persist_raw, emit_metadata. The interface intentionally excludes any downstream
business logic; business rules live in Bronze/Silver/Gold layers.

Concrete connectors extend :class:`SourceConnectorBase` and must implement
``extract``; other methods are overridable with sensible defaults.
"""

from __future__ import annotations

import abc
import datetime as dt
import enum
import hashlib
import logging
import os
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "ConnectorCapability",
    "ExtractionResult",
    "HttpRequest",
    "HttpResponse",
    "REQUEST_TIMEOUT_SECONDS",
    "SourceConnectorBase",
    "SourceMetadata",
]

logger = logging.getLogger(__name__)

RawPayload = bytes

# Default HTTP request timeout for all source connectors (TDD §13.1).
# Override per-source if the provider is known to be slow.
REQUEST_TIMEOUT_SECONDS = float(os.environ.get("KLIBRA_CONNECTOR_TIMEOUT", "30.0"))

# Default User-Agent string identifying KLIBRA to upstream providers.
DEFAULT_USER_AGENT = "klibra-platform/0.1.0 (+https://github.com/echidev/klibra)"


class ConnectorCapability(enum.Enum):
    """Enumerates optional capabilities a connector may report."""

    DISCOVER = "discover"
    AUTH = "authenticate"
    PULLED_INCREMENTAL = "incremental"
    BACKFILL = "backfill"
    VERSIONED = "versioned"
    RATE_LIMIT = "rate_limit"


@dataclass(frozen=True, slots=True)
class HttpRequest:
    """HTTP request descriptor produced by a connector."""

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    body: bytes | None = None
    timeout_seconds: float = REQUEST_TIMEOUT_SECONDS


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """HTTP response wrapper returned by ``send_request``."""

    status_code: int
    headers: dict[str, str]
    body: bytes
    url: str


def send_request(
    request: HttpRequest,
    *,
    max_retries: int = 3,
    backoff_base_seconds: float = 1.0,
    backoff_factor: float = 2.0,
    backoff_jitter_seconds: float = 0.5,
) -> HttpResponse:
    """Send an HTTP request with retry, backoff, and jitter (TDD §73).

    Retries on transient errors: connection errors, timeouts, and HTTP 429/5xx.
    Respects ``Retry-After`` from the upstream if present.
    """
    import requests  # local import to keep the base module pure

    headers = dict(request.headers)
    headers.setdefault("User-Agent", DEFAULT_USER_AGENT)
    attempt = 0
    while True:
        attempt += 1
        try:
            response = requests.request(
                method=request.method,
                url=request.url,
                headers=headers,
                params=request.params,
                data=request.body,
                timeout=request.timeout_seconds,
            )
        except requests.RequestException as exc:
            if attempt > max_retries:
                logger.error(
                    "HTTP %s %s failed after %d attempts: %s",
                    request.method,
                    request.url,
                    attempt,
                    exc,
                )
                raise
            _sleep_with_jitter(
                attempt, backoff_base_seconds, backoff_factor, backoff_jitter_seconds, exc
            )
            continue

        if response.status_code in (429, 500, 502, 503, 504):
            if attempt > max_retries:
                response.raise_for_status()
                break
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    time.sleep(float(retry_after))
                except ValueError:
                    _sleep_with_jitter(
                        attempt,
                        backoff_base_seconds,
                        backoff_factor,
                        backoff_jitter_seconds,
                        response.status_code,
                    )
            else:
                _sleep_with_jitter(
                    attempt,
                    backoff_base_seconds,
                    backoff_factor,
                    backoff_jitter_seconds,
                    response.status_code,
                )
            continue

        if response.status_code >= 400:
            response.raise_for_status()

        return HttpResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=response.content,
            url=response.url,
        )


def _sleep_with_jitter(
    attempt: int,
    base: float,
    factor: float,
    jitter: float,
    reason: Any,
) -> None:
    delay = base * (factor ** (attempt - 1)) + random.uniform(0, jitter)
    logger.warning(
        "retrying after %.2fs (attempt %d) reason=%r",
        delay,
        attempt,
        reason,
    )
    time.sleep(delay)


@dataclass(frozen=True, slots=True)
class SourceMetadata:
    """Populated by :meth:`SourceConnectorBase.emit_metadata`.

    Mirrors TDD §7 (raw acquisition metadata) and TDD §14 (operational
    metadata). Emitted as a manifest entry alongside the payload.
    """

    source_id: str
    dataset_id: str
    retrieval_timestamp: dt.datetime
    source_url: str
    request_params: dict[str, Any]
    response_metadata: dict[str, Any]
    content_hash: str
    payload_format: str
    run_id: str
    connector_version: str
    source_publication_timestamp: dt.datetime | None = None
    source_version: str | None = None


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Payload bundle returned by :meth:`SourceConnectorBase.extract`."""

    payload: RawPayload
    source_url: str
    request_params: dict[str, Any] = field(default_factory=dict)
    response_metadata: dict[str, Any] = field(default_factory=dict)
    payload_format: str = "json"
    source_publication_timestamp: dt.datetime | None = None
    source_version: str | None = None


class SourceConnectorBase(abc.ABC):
    """Abstract base class for all KLIBRA source connectors.

    Every concrete implementation is initialized with the resolved
    :class:`SourceMetadata` seed and an operational ``run_id``. See
    TDD §13.1 and ``docs/architecture/decisions/ADR-002-*.md``.
    """

    source_id: str
    connector_version: str = "0.0.0"

    def __init__(
        self,
        source_id: str,
        dataset_id: str,
        run_id: str | None = None,
    ) -> None:
        if not source_id:
            msg = "source_id is required"
            raise ValueError(msg)
        if not dataset_id:
            msg = "dataset_id is required"
            raise ValueError(msg)
        self.source_id = source_id
        self.dataset_id = dataset_id
        self.run_id = run_id or str(uuid.uuid4())
        self._retrieval_timestamp: dt.datetime | None = None
        self._last_extraction: ExtractionResult | None = None

    def discover(self) -> list[str]:
        """Enumerate available dataset identifiers for the source.

        Returns an empty list by default; override if the provider exposes
        an enumeration endpoint.
        """
        return []

    def authenticate(self) -> dict[str, str]:
        """Return authentication headers or tokens.

        Raises
        ------
        NotImplementedError
            Auth-required connectors must override this method.
        """
        return {}

    def validate_response(self, payload: RawPayload) -> None:
        """Verify HTTP status, schema, content hash, and semantics.

        Raises
        ------
        ValueError
            When the payload is empty, malformed, or violates the contract.
        """
        if payload is None:
            msg = "empty response payload"
            raise ValueError(msg)
        if len(payload) == 0:
            msg = "response payload is zero bytes"
            raise ValueError(msg)

    def compute_hash(self, payload: RawPayload | str | bytes) -> str:
        """Content hash for :attr:`SourceMetadata.content_hash`."""

        if isinstance(payload, str):
            payload = payload.encode()
        return hashlib.sha256(payload).hexdigest()

    @abc.abstractmethod
    def extract(self, **kwargs: Any) -> ExtractionResult:
        """Retrieve bytes from the upstream provider.

        Implementations perform the actual HTTP call. The caller
        is responsible for surrounding retries and rate-limiting.
        """

    def persist_raw(self, result: ExtractionResult) -> str:
        """Persist the raw payload under the lakehouse layout.

        The actual storage backend is injected by the ingestion runner.
        This base method computes the blob key without writing; callers
        should route the payload to S3/MinIO.
        """
        date = dt.datetime.now(tz=dt.UTC).date().isoformat()
        return (
            f"raw/source={self.source_id}"
            f"/dataset={self.dataset_id}"
            f"/ingestion_date={date}"
            f"/run_id={self.run_id}/payload"
        )

    def emit_metadata(self, result: ExtractionResult) -> SourceMetadata:
        """Build :class:`SourceMetadata` from an extraction result."""

        content_hash = self.compute_hash(result.payload)
        return SourceMetadata(
            source_id=self.source_id,
            dataset_id=self.dataset_id,
            retrieval_timestamp=dt.datetime.now(tz=dt.UTC),
            source_url=result.source_url,
            request_params=dict(result.request_params),
            response_metadata=dict(result.response_metadata),
            content_hash=content_hash,
            payload_format=result.payload_format,
            run_id=self.run_id,
            connector_version=str(getattr(self, "connector_version", "0.0.0")),
            source_publication_timestamp=result.source_publication_timestamp,
            source_version=result.source_version,
        )
