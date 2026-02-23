"""Unit tests for API client wrapper."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from anthropic import APIError, RateLimitError, APIConnectionError
import httpx

from src.api_client import APIClient


def create_mock_response(status_code=429):
    """Create a mock httpx.Response for testing."""
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.headers = {}
    return mock_response


def create_mock_request():
    """Create a mock httpx.Request for testing."""
    mock_request = Mock(spec=httpx.Request)
    mock_request.url = "https://api.anthropic.com/v1/messages"
    mock_request.method = "POST"
    return mock_request


class TestAPIClient:
    """Test suite for APIClient class."""
    
    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        client = APIClient(api_key="test-key-123")
        assert client.api_key == "test-key-123"
        assert client.max_retries == 3
    
    def test_init_with_env_var(self):
        """Test initialization with environment variable."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'env-key-456'}):
            client = APIClient()
            assert client.api_key == "env-key-456"
    
    def test_init_without_api_key_raises_error(self):
        """Test initialization without API key raises ValueError."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key must be provided"):
                APIClient()
    
    def test_successful_api_call(self):
        """Test successful API call returns response text."""
        client = APIClient(api_key="test-key")
        
        # Mock the Anthropic client
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        client.client.messages.create = Mock(return_value=mock_response)
        
        result = client.call_api("Test prompt")
        
        assert result == "Test response"
        client.client.messages.create.assert_called_once()
    
    def test_rate_limit_retry_with_exponential_backoff(self):
        """Test rate limit error triggers retry with exponential backoff."""
        client = APIClient(api_key="test-key", max_retries=3)
        
        # Mock to fail twice with rate limit, then succeed
        mock_response = Mock()
        mock_response.content = [Mock(text="Success after retries")]
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RateLimitError("Rate limited", response=create_mock_response(429), body=None)
            return mock_response
        
        client.client.messages.create = Mock(side_effect=side_effect)
        
        with patch('time.sleep') as mock_sleep:
            result = client.call_api("Test prompt")
        
        assert result == "Success after retries"
        assert call_count == 3
        # Check exponential backoff: 2^0=1, 2^1=2
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)
    
    def test_rate_limit_max_retries_exceeded(self):
        """Test rate limit error raises after max retries."""
        client = APIClient(api_key="test-key", max_retries=3)
        
        # Mock to always fail with rate limit
        client.client.messages.create = Mock(
            side_effect=RateLimitError("Rate limited", response=create_mock_response(429), body=None)
        )
        
        with patch('time.sleep'):
            with pytest.raises(RateLimitError):
                client.call_api("Test prompt")
        
        assert client.client.messages.create.call_count == 3
    
    def test_network_error_retry(self):
        """Test network error triggers retry."""
        client = APIClient(api_key="test-key", max_retries=3)
        
        # Mock to fail once with network error, then succeed
        mock_response = Mock()
        mock_response.content = [Mock(text="Success after network error")]
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise APIConnectionError(message="Network error", request=create_mock_request())
            return mock_response
        
        client.client.messages.create = Mock(side_effect=side_effect)
        
        with patch('time.sleep') as mock_sleep:
            result = client.call_api("Test prompt")
        
        assert result == "Success after network error"
        assert call_count == 2
        # Network errors use 1 second wait
        mock_sleep.assert_called_once_with(1)
    
    def test_network_error_max_retries_exceeded(self):
        """Test network error raises after max retries."""
        client = APIClient(api_key="test-key", max_retries=3)
        
        # Mock to always fail with network error
        client.client.messages.create = Mock(
            side_effect=APIConnectionError(message="Network error", request=create_mock_request())
        )
        
        with patch('time.sleep'):
            with pytest.raises(APIConnectionError):
                client.call_api("Test prompt")
        
        assert client.client.messages.create.call_count == 3
    
    def test_client_error_no_retry(self):
        """Test 4xx client errors (except 429) don't retry."""
        client = APIClient(api_key="test-key", max_retries=3)
        
        # Mock 400 error
        error = APIError("Bad request", body=None, request=create_mock_request())
        error.status_code = 400
        client.client.messages.create = Mock(side_effect=error)
        
        with pytest.raises(APIError):
            client.call_api("Test prompt")
        
        # Should only try once, no retries
        assert client.client.messages.create.call_count == 1
    
    def test_server_error_retry(self):
        """Test 5xx server errors trigger retry."""
        client = APIClient(api_key="test-key", max_retries=3)
        
        # Mock to fail once with 503, then succeed
        mock_response = Mock()
        mock_response.content = [Mock(text="Success after server error")]
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                error = APIError("Service unavailable", body=None, request=create_mock_request())
                error.status_code = 503
                raise error
            return mock_response
        
        client.client.messages.create = Mock(side_effect=side_effect)
        
        with patch('time.sleep') as mock_sleep:
            result = client.call_api("Test prompt")
        
        assert result == "Success after server error"
        assert call_count == 2
        mock_sleep.assert_called_once_with(1)
    
    def test_api_call_with_system_prompt(self):
        """Test API call with system prompt."""
        client = APIClient(api_key="test-key")
        
        mock_response = Mock()
        mock_response.content = [Mock(text="Response with system")]
        client.client.messages.create = Mock(return_value=mock_response)
        
        result = client.call_api("User prompt", system="System prompt")
        
        assert result == "Response with system"
        call_args = client.client.messages.create.call_args
        assert call_args[1]["system"] == "System prompt"
    
    def test_api_call_with_custom_parameters(self):
        """Test API call with custom model, tokens, and temperature."""
        client = APIClient(api_key="test-key")
        
        mock_response = Mock()
        mock_response.content = [Mock(text="Custom response")]
        client.client.messages.create = Mock(return_value=mock_response)
        
        result = client.call_api(
            "Test prompt",
            model="claude-3-opus-20240229",
            max_tokens=2048,
            temperature=0.5
        )
        
        assert result == "Custom response"
        call_args = client.client.messages.create.call_args
        assert call_args[1]["model"] == "claude-3-opus-20240229"
        assert call_args[1]["max_tokens"] == 2048
        assert call_args[1]["temperature"] == 0.5
    
    def test_logging_on_success(self, caplog):
        """Test that successful API calls are logged."""
        client = APIClient(api_key="test-key")
        
        mock_response = Mock()
        mock_response.content = [Mock(text="Success")]
        client.client.messages.create = Mock(return_value=mock_response)
        
        with caplog.at_level('INFO'):
            client.call_api("Test prompt")
        
        assert "API call successful" in caplog.text
    
    def test_logging_on_rate_limit(self, caplog):
        """Test that rate limit errors are logged."""
        client = APIClient(api_key="test-key", max_retries=2)
        
        client.client.messages.create = Mock(
            side_effect=RateLimitError("Rate limited", response=create_mock_response(429), body=None)
        )
        
        with caplog.at_level('WARNING'):
            with patch('time.sleep'):
                with pytest.raises(RateLimitError):
                    client.call_api("Test prompt")
        
        assert "Rate limit error" in caplog.text
        assert "Max retries reached" in caplog.text
    
    def test_logging_on_network_error(self, caplog):
        """Test that network errors are logged."""
        client = APIClient(api_key="test-key", max_retries=2)
        
        client.client.messages.create = Mock(
            side_effect=APIConnectionError(message="Network error", request=create_mock_request())
        )
        
        with caplog.at_level('WARNING'):
            with patch('time.sleep'):
                with pytest.raises(APIConnectionError):
                    client.call_api("Test prompt")
        
        assert "Network error" in caplog.text
        assert "Max retries reached" in caplog.text

class TestAPIClientQueueing:
    """Test suite for API client request queueing functionality."""
    
    def test_queue_initialization(self):
        """Test that queue is initialized empty."""
        client = APIClient(api_key="test-key")
        assert client.get_queue_size() == 0
        assert client.request_queue == []
        assert client.rate_limited == False
        assert client.rate_limit_reset_time is None
    
    def test_rate_limit_queues_request(self):
        """Test that rate limit error queues the request after all retries."""
        client = APIClient(api_key="test-key", max_retries=2)
        
        # Mock to always fail with rate limit
        client.client.messages.create = Mock(
            side_effect=RateLimitError("Rate limited", response=create_mock_response(429), body=None)
        )
        
        with patch('time.sleep'):
            with pytest.raises(RateLimitError):
                client.call_api("Test prompt")
        
        # Request should be queued after all retries exhausted
        assert client.get_queue_size() == 1
        assert client.rate_limited == True
    
    def test_queue_maintains_fifo_order(self):
        """Test that queue maintains FIFO order."""
        client = APIClient(api_key="test-key")
        
        # Manually enqueue requests
        client._enqueue_request({'prompt': 'First', 'model': 'test'})
        client._enqueue_request({'prompt': 'Second', 'model': 'test'})
        client._enqueue_request({'prompt': 'Third', 'model': 'test'})
        
        assert client.get_queue_size() == 3
        assert client.request_queue[0]['prompt'] == 'First'
        assert client.request_queue[1]['prompt'] == 'Second'
        assert client.request_queue[2]['prompt'] == 'Third'
    
    def test_process_queue_processes_in_order(self):
        """Test that process_queue processes requests in FIFO order."""
        client = APIClient(api_key="test-key")
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.content = [Mock(text="Success")]
        client.client.messages.create = Mock(return_value=mock_response)
        
        # Enqueue multiple requests
        client._enqueue_request({
            'prompt': 'First',
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 4096,
            'temperature': 1.0,
            'system': None
        })
        client._enqueue_request({
            'prompt': 'Second',
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 4096,
            'temperature': 1.0,
            'system': None
        })
        
        assert client.get_queue_size() == 2
        
        # Process queue
        client._process_queue()
        
        # Queue should be empty
        assert client.get_queue_size() == 0
        
        # Check that requests were made in order
        assert client.client.messages.create.call_count == 2
        calls = client.client.messages.create.call_args_list
        assert calls[0][1]['messages'][0]['content'] == 'First'
        assert calls[1][1]['messages'][0]['content'] == 'Second'
    
    def test_process_queue_stops_on_rate_limit(self):
        """Test that process_queue stops when hitting rate limit."""
        client = APIClient(api_key="test-key")
        
        # Mock to succeed once, then hit rate limit
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_response = Mock()
                mock_response.content = [Mock(text="Success")]
                return mock_response
            else:
                raise RateLimitError("Rate limited", response=create_mock_response(429), body=None)
        
        client.client.messages.create = Mock(side_effect=side_effect)
        
        # Enqueue three requests
        for i in range(3):
            client._enqueue_request({
                'prompt': f'Request {i}',
                'model': 'claude-3-5-sonnet-20241022',
                'max_tokens': 4096,
                'temperature': 1.0,
                'system': None
            })
        
        assert client.get_queue_size() == 3
        
        # Process queue
        client._process_queue()
        
        # First request should be processed, remaining two should stay in queue
        assert client.get_queue_size() == 2
        assert client.rate_limited == True
        assert client.rate_limit_reset_time is not None
    
    def test_process_queue_waits_for_rate_limit_reset(self):
        """Test that process_queue waits for rate limit to clear."""
        client = APIClient(api_key="test-key")
        
        # Set rate limit state
        client.rate_limited = True
        client.rate_limit_reset_time = time.time() + 0.1  # 100ms in future
        
        # Mock successful response
        mock_response = Mock()
        mock_response.content = [Mock(text="Success")]
        client.client.messages.create = Mock(return_value=mock_response)
        
        # Enqueue request
        client._enqueue_request({
            'prompt': 'Test',
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 4096,
            'temperature': 1.0,
            'system': None
        })
        
        with patch('time.sleep') as mock_sleep:
            client._process_queue()
        
        # Should have waited for rate limit to clear
        mock_sleep.assert_called_once()
        wait_time = mock_sleep.call_args[0][0]
        assert 0 < wait_time <= 0.2  # Should be around 100ms
        
        # Queue should be empty after processing
        assert client.get_queue_size() == 0
        assert client.rate_limited == False
    
    def test_clear_queue(self):
        """Test that clear_queue removes all requests."""
        client = APIClient(api_key="test-key")
        
        # Enqueue multiple requests
        for i in range(5):
            client._enqueue_request({'prompt': f'Request {i}'})
        
        assert client.get_queue_size() == 5
        
        client.clear_queue()
        
        assert client.get_queue_size() == 0
        assert client.request_queue == []
    
    def test_queue_processes_before_new_request(self):
        """Test that existing queue is processed before making new request."""
        client = APIClient(api_key="test-key")
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.content = [Mock(text="Success")]
        client.client.messages.create = Mock(return_value=mock_response)
        
        # Manually add a request to queue
        client._enqueue_request({
            'prompt': 'Queued',
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 4096,
            'temperature': 1.0,
            'system': None
        })
        
        # Make a new API call
        result = client.call_api("New request")
        
        # Both requests should have been processed
        assert result == "Success"
        assert client.get_queue_size() == 0
        assert client.client.messages.create.call_count == 2
    
    def test_rate_limit_with_retry_after_header(self):
        """Test that retry-after header is respected."""
        client = APIClient(api_key="test-key", max_retries=2)
        
        # Create mock response with retry-after header
        mock_response = create_mock_response(429)
        mock_response.headers = {'retry-after': '5'}
        
        client.client.messages.create = Mock(
            side_effect=RateLimitError("Rate limited", response=mock_response, body=None)
        )
        
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(RateLimitError):
                client.call_api("Test prompt")
        
        # Should wait for retry-after duration on first retry
        assert mock_sleep.call_count >= 1
        # First call should use retry-after value
        assert mock_sleep.call_args_list[0][0][0] == 5
        assert client.rate_limit_reset_time is not None
    
    def test_queue_removes_failed_requests(self):
        """Test that requests with non-rate-limit errors are removed from queue."""
        client = APIClient(api_key="test-key")
        
        # Mock to fail with non-rate-limit error
        client.client.messages.create = Mock(
            side_effect=APIError("Server error", body=None, request=create_mock_request())
        )
        
        # Enqueue requests
        for i in range(3):
            client._enqueue_request({
                'prompt': f'Request {i}',
                'model': 'claude-3-5-sonnet-20241022',
                'max_tokens': 4096,
                'temperature': 1.0,
                'system': None
            })
        
        assert client.get_queue_size() == 3
        
        # Process queue - all should fail and be removed
        client._process_queue()
        
        assert client.get_queue_size() == 0
    
    def test_enqueue_logs_queue_size(self, caplog):
        """Test that enqueuing logs the queue size."""
        client = APIClient(api_key="test-key")
        
        with caplog.at_level('INFO'):
            client._enqueue_request({'prompt': 'Test'})
        
        assert "Request queued" in caplog.text
        assert "Queue size: 1" in caplog.text
    
    def test_process_queue_logs_progress(self, caplog):
        """Test that processing queue logs progress."""
        client = APIClient(api_key="test-key")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.content = [Mock(text="Success")]
        client.client.messages.create = Mock(return_value=mock_response)
        
        # Enqueue request
        client._enqueue_request({
            'prompt': 'Test',
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 4096,
            'temperature': 1.0,
            'system': None
        })
        
        with caplog.at_level('INFO'):
            client._process_queue()
        
        assert "Processing 1 queued requests" in caplog.text
        assert "Queued request processed successfully" in caplog.text
