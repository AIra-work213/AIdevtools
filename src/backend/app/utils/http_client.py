"""HTTP client with retry logic and error handling"""

import asyncio
import time
from typing import Any, Dict, Optional, Callable
import httpx
from fastapi import HTTPException
import structlog

logger = structlog.get_logger(__name__)


async def make_request_with_retry(
    url: str,
    method: str = "POST",
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    timeout: float = 30.0,
    **kwargs
) -> Dict[str, Any]:
    """
    Make HTTP request with retry logic and exponential backoff.

    Args:
        url: Request URL
        method: HTTP method
        max_retries: Maximum number of retry attempts
        backoff_factor: Backoff factor for exponential delay
        timeout: Request timeout in seconds
        **kwargs: Additional arguments for httpx request

    Returns:
        Response JSON data

    Raises:
        HTTPException: If all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, url, **kwargs)

                # Raise exception for HTTP errors
                response.raise_for_status()

                return response.json()

        except httpx.HTTPStatusError as e:
            last_exception = e
            logger.warning(
                "HTTP error on attempt",
                attempt=attempt + 1,
                max_retries=max_retries + 1,
                status_code=e.response.status_code,
                url=str(e.request.url)
            )

            # Don't retry for client errors (4xx)
            if 400 <= e.response.status_code < 500:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Client error: {e.response.text}"
                )

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            last_exception = e
            logger.warning(
                "Network error on attempt",
                attempt=attempt + 1,
                max_retries=max_retries + 1,
                error=str(e),
                url=url
            )

        except Exception as e:
            last_exception = e
            logger.error(
                "Unexpected error on attempt",
                attempt=attempt + 1,
                max_retries=max_retries + 1,
                error=str(e),
                url=url
            )

        # Don't sleep after last attempt
        if attempt < max_retries:
            delay = backoff_factor * (2 ** attempt)
            logger.info(
                "Retrying request",
                attempt=attempt + 1,
                max_retries=max_retries + 1,
                delay=delay,
                url=url
            )
            await asyncio.sleep(delay)

    # All retries failed
    error_msg = "Failed after retries"
    if last_exception:
        if isinstance(last_exception, httpx.HTTPStatusError):
            raise HTTPException(
                status_code=last_exception.response.status_code,
                detail=f"{error_msg}: {last_exception.response.text}"
            )
        else:
            raise HTTPException(
                status_code=503,
                detail=f"{error_msg}: {str(last_exception)}"
            )

    raise HTTPException(status_code=503, detail=error_msg)


class RetryableHttpClient:
    """HTTP client with built-in retry logic"""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        timeout: float = 30.0,
        circuit_breaker: Optional['CircuitBreaker'] = None
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.circuit_breaker = circuit_breaker

    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make POST request with retry logic"""
        if self.circuit_breaker:
            return await self.circuit_breaker.call(
                lambda: make_request_with_retry(
                    url=url,
                    method="POST",
                    max_retries=self.max_retries,
                    backoff_factor=self.backoff_factor,
                    timeout=self.timeout,
                    **kwargs
                )
            )
        else:
            return await make_request_with_retry(
                url=url,
                method="POST",
                max_retries=self.max_retries,
                backoff_factor=self.backoff_factor,
                timeout=self.timeout,
                **kwargs
            )

    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make GET request with retry logic"""
        if self.circuit_breaker:
            return await self.circuit_breaker.call(
                lambda: make_request_with_retry(
                    url=url,
                    method="GET",
                    max_retries=self.max_retries,
                    backoff_factor=self.backoff_factor,
                    timeout=self.timeout,
                    **kwargs
                )
            )
        else:
            return await make_request_with_retry(
                url=url,
                method="GET",
                max_retries=self.max_retries,
                backoff_factor=self.backoff_factor,
                timeout=self.timeout,
                **kwargs
            )