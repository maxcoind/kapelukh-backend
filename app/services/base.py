from abc import ABC, abstractmethod
from typing import Optional, Dict
import httpx
from app.logger import get_logger

logger = get_logger("base_service")


class ExternalServiceError(Exception):
    """Base exception for external service errors."""

    pass


class ServiceConnectionError(ExternalServiceError):
    """Raised when connection to external service fails."""

    pass


class ServiceTimeoutError(ExternalServiceError):
    """Raised when external service request times out."""

    pass


class ServiceRateLimitError(ExternalServiceError):
    """Raised when external service rate limit is exceeded."""

    pass


class ServiceResponseError(ExternalServiceError):
    """Raised when external service returns unexpected response."""

    def __init__(
        self, status_code: int, message: str, response_body: Optional[str] = None
    ):
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(f"HTTP {status_code}: {message}")


class BaseExternalService(ABC):
    """Abstract base class for external service clients."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        verify_ssl: bool = True,
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(
            f"Initialized {self.__class__.__name__} with base_url={base_url}, "
            f"timeout={timeout}s, max_retries={max_retries}"
        )

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        """Establish connection to the service."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                verify=self.verify_ssl,
                base_url=self.base_url,
            )
            logger.debug(f"{self.__class__.__name__} connected to {self.base_url}")

    async def close(self):
        """Close the connection."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.debug(f"{self.__class__.__name__} connection closed")

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the httpx client, ensuring it's connected."""
        if self._client is None or self._client.is_closed:
            raise ServiceConnectionError(
                f"{self.__class__.__name__} is not connected. Use async context manager or call connect()."
            )
        return self._client

    def _get_headers(
        self, extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Get default headers with optional extra headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def _should_retry(self, exception: Exception) -> bool:
        """Determine if request should be retried based on exception."""
        if isinstance(exception, httpx.TimeoutException):
            return True
        if isinstance(exception, httpx.ConnectError):
            return True
        if isinstance(exception, httpx.NetworkError):
            return True
        if isinstance(exception, httpx.HTTPStatusError):
            return exception.response.status_code in {429, 502, 503, 504}
        return False

    def _handle_request_error(self, error: Exception) -> None:
        """Handle and classify request errors."""
        if isinstance(error, httpx.TimeoutException):
            logger.error(f"Request timeout: {error}")
            raise ServiceTimeoutError(
                f"Request timeout after {self.timeout}s"
            ) from error
        elif isinstance(error, httpx.ConnectError):
            logger.error(f"Connection error: {error}")
            raise ServiceConnectionError(
                f"Failed to connect to {self.base_url}"
            ) from error
        elif isinstance(error, httpx.HTTPStatusError):
            e = error
            status = e.response.status_code
            body = e.response.text[:500] if e.response.text else None
            logger.error(f"HTTP error {status}: {body}")

            if status == 429:
                raise ServiceRateLimitError("Rate limit exceeded") from error
            raise ServiceResponseError(status, f"HTTP {status}", body) from error
        else:
            logger.error(f"Unexpected error: {error}")
            raise ExternalServiceError(f"Unexpected error: {error}") from error

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is healthy and accessible."""
        pass
