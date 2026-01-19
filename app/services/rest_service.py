from typing import Optional, Dict, Any, Union
from httpx import Response
from app.services.base import BaseExternalService
from app.logger import get_logger

logger = get_logger("rest_service")


class RESTService(BaseExternalService):
    """Abstract REST API client with common CRUD operations."""

    @staticmethod
    def _log_request(method: str, url: str, **kwargs):
        """Log outgoing request."""
        logger.debug(f"REST {method} {url} - {kwargs}")

    @staticmethod
    def _log_response(method: str, url: str, response: Response, duration_ms: float):
        """Log response."""
        logger.debug(
            f"REST {method} {url} - Status: {response.status_code} "
            f"({duration_ms:.0f}ms)"
        )

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Response:
        """
        Make an HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint path (will be joined with base_url)
            **kwargs: Arguments to pass to httpx client request method

        Returns:
            httpx.Response object

        Raises:
            ServiceConnectionError: Connection failures
            ServiceTimeoutError: Request timeouts
            ServiceRateLimitError: Rate limit exceeded
            ServiceResponseError: HTTP errors (4xx, 5xx)
        """
        import time

        url = (
            f"{self.endpoint_base}{endpoint}"
            if hasattr(self, "endpoint_base")
            else endpoint
        )

        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                start_time = time.time()
                self._log_request(method, url, **kwargs)

                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()

                duration_ms = (time.time() - start_time) * 1000
                self._log_response(method, url, response, duration_ms)

                return response

            except Exception as error:
                last_exception = error
                if attempt < self.max_retries and self._should_retry(error):
                    wait_time = min(2**attempt, 10)
                    logger.warning(
                        f"Request failed (attempt {attempt}/{self.max_retries}), "
                        f"retrying in {wait_time}s: {error}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self._handle_request_error(error)

        raise (
            last_exception
            if last_exception
            else ServiceConnectionError("Max retries exceeded")
        )

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            headers: Additional headers

        Returns:
            httpx.Response object
        """
        return await self._make_request(
            "GET",
            endpoint,
            params=params,
            headers=self._get_headers(headers),
        )

    async def post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Make a POST request.

        Args:
            endpoint: API endpoint path
            json: JSON body
            data: Form data or raw data
            headers: Additional headers

        Returns:
            httpx.Response object
        """
        return await self._make_request(
            "POST",
            endpoint,
            json=json,
            data=data,
            headers=self._get_headers(headers),
        )

    async def put(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Make a PUT request.

        Args:
            endpoint: API endpoint path
            json: JSON body
            data: Form data or raw data
            headers: Additional headers

        Returns:
            httpx.Response object
        """
        return await self._make_request(
            "PUT",
            endpoint,
            json=json,
            data=data,
            headers=self._get_headers(headers),
        )

    async def patch(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Make a PATCH request.

        Args:
            endpoint: API endpoint path
            json: JSON body
            data: Form data or raw data
            headers: Additional headers

        Returns:
            httpx.Response object
        """
        return await self._make_request(
            "PATCH",
            endpoint,
            json=json,
            data=data,
            headers=self._get_headers(headers),
        )

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Make a DELETE request.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            headers: Additional headers

        Returns:
            httpx.Response object
        """
        return await self._make_request(
            "DELETE",
            endpoint,
            params=params,
            headers=self._get_headers(headers),
        )

    async def get_json(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a GET request and return JSON response.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            headers: Additional headers

        Returns:
            Parsed JSON response as dictionary
        """
        response = await self.get(endpoint, params=params, headers=headers)
        return response.json()

    async def post_json(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a POST request and return JSON response.

        Args:
            endpoint: API endpoint path
            json: JSON body
            headers: Additional headers

        Returns:
            Parsed JSON response as dictionary
        """
        response = await self.post(endpoint, json=json, headers=headers)
        return response.json()

    async def health_check(self) -> bool:
        """
        Check if the REST service is healthy.

        Default implementation tries to GET the health endpoint.
        Override this method for custom health checks.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


import asyncio
