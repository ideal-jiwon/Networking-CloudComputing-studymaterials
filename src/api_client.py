"""API client wrapper with retry logic and error handling for Claude API."""

import os
import time
import logging
from typing import Optional, Dict, Any
from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIClient:
    """Wrapper for Claude API with retry logic, error handling, and request queueing."""

    def __init__(self, api_key: Optional[str] = None, max_retries: int = 3):
        """
        Initialize API client.

        Args:
            api_key: Claude API key (defaults to ANTHROPIC_API_KEY env var)
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in ANTHROPIC_API_KEY environment variable")

        self.client = Anthropic(api_key=self.api_key)
        self.max_retries = max_retries
        self.request_queue = []
        self.rate_limited = False
        self.rate_limit_reset_time = None

    def _enqueue_request(self, request_params: Dict[str, Any]) -> None:
        """
        Add a request to the queue.

        Args:
            request_params: Dictionary containing all parameters for the API call
        """
        self.request_queue.append(request_params)
        logger.info(f"Request queued. Queue size: {len(self.request_queue)}")

    def _process_queue(self) -> None:
        """
        Process all queued requests in FIFO order.

        Processes requests one at a time until queue is empty or rate limit is hit again.
        """
        if not self.request_queue:
            return

        logger.info(f"Processing {len(self.request_queue)} queued requests")

        while self.request_queue:
            # Check if we need to wait for rate limit to clear
            if self.rate_limited and self.rate_limit_reset_time:
                wait_time = self.rate_limit_reset_time - time.time()
                if wait_time > 0:
                    logger.info(f"Waiting {wait_time:.1f} seconds for rate limit to clear")
                    time.sleep(wait_time)
                self.rate_limited = False
                self.rate_limit_reset_time = None

            # Get next request from queue (FIFO)
            request_params = self.request_queue[0]

            try:
                # Try to execute the request
                result = self._execute_request(**request_params)
                # Success - remove from queue and store result
                self.request_queue.pop(0)
                request_params['_result'] = result
                logger.info(f"Queued request processed successfully. Remaining: {len(self.request_queue)}")
            except RateLimitError as e:
                # Hit rate limit again - stop processing queue
                logger.warning("Hit rate limit while processing queue")
                self.rate_limited = True
                # Set reset time based on retry-after header if available
                if hasattr(e, 'response') and e.response and 'retry-after' in e.response.headers:
                    retry_after = int(e.response.headers['retry-after'])
                    self.rate_limit_reset_time = time.time() + retry_after
                else:
                    # Default wait time if no retry-after header
                    self.rate_limit_reset_time = time.time() + 60
                break
            except Exception as e:
                # Other errors - remove from queue and log
                logger.error(f"Error processing queued request: {e}")
                self.request_queue.pop(0)

    def _execute_request(
        self,
        prompt: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        system: Optional[str] = None
    ) -> str:
        """
        Execute a single API request without retry logic.

        Args:
            prompt: The user prompt to send to Claude
            model: The Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            system: Optional system prompt

        Returns:
            The API response text

        Raises:
            APIError: If the request fails
        """
        # Build message
        message_params = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }

        if system:
            message_params["system"] = system

        # Make API call
        response = self.client.messages.create(**message_params)

        # Extract text from response
        return response.content[0].text

    def call_api(
        self,
        prompt: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        system: Optional[str] = None
    ) -> str:
        """
        Call Claude API with retry logic, error handling, and request queueing.

        Implements exponential backoff for retries and handles:
        - Rate limit errors (429) - queues request for later processing
        - Network errors
        - Other API errors

        Args:
            prompt: The user prompt to send to Claude
            model: The Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            system: Optional system prompt

        Returns:
            The API response text

        Raises:
            APIError: If all retry attempts fail
        """
        # First, try to process any queued requests
        if self.request_queue:
            self._process_queue()

        for attempt in range(self.max_retries):
            try:
                logger.info(f"API call attempt {attempt + 1}/{self.max_retries}")

                result = self._execute_request(prompt, model, max_tokens, temperature, system)
                logger.info("API call successful")
                return result

            except RateLimitError as e:
                logger.warning(f"Rate limit error on attempt {attempt + 1}: {e}")

                # Set reset time based on retry-after header if available
                if hasattr(e, 'response') and e.response and 'retry-after' in e.response.headers:
                    retry_after = int(e.response.headers['retry-after'])
                    self.rate_limit_reset_time = time.time() + retry_after
                    wait_time = retry_after
                else:
                    # Exponential backoff if no retry-after header
                    wait_time = 2 ** attempt
                    self.rate_limit_reset_time = time.time() + wait_time

                if attempt < self.max_retries - 1:
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    self.rate_limited = False
                    self.rate_limit_reset_time = None
                else:
                    # On final retry failure, queue the request
                    logger.error("Max retries reached for rate limit error")
                    request_params = {
                        'prompt': prompt,
                        'model': model,
                        'max_tokens': max_tokens,
                        'temperature': temperature,
                        'system': system
                    }
                    self._enqueue_request(request_params)
                    self.rate_limited = True
                    raise

            except APIConnectionError as e:
                logger.warning(f"Network error on attempt {attempt + 1}: {e}")

                if attempt < self.max_retries - 1:
                    # Shorter wait for network errors
                    wait_time = 1
                    logger.info(f"Waiting {wait_time} second before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries reached for network error")
                    raise

            except APIError as e:
                logger.error(f"API error on attempt {attempt + 1}: {e}")

                # Don't retry on client errors (4xx except 429)
                if hasattr(e, 'status_code') and 400 <= e.status_code < 500 and e.status_code != 429:
                    logger.error(f"Client error {e.status_code}, not retrying")
                    raise

                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries reached for API error")
                    raise

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                raise

        # Should not reach here, but just in case
        raise APIError("Failed to complete API call after all retries")

    def get_queue_size(self) -> int:
        """
        Get the current size of the request queue.

        Returns:
            Number of requests in the queue
        """
        return len(self.request_queue)

    def clear_queue(self) -> None:
        """Clear all queued requests."""
        self.request_queue.clear()
        logger.info("Request queue cleared")
