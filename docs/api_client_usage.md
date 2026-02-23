# API Client Usage Guide

## Overview

The `APIClient` class provides a robust wrapper around the Claude API with automatic retry logic, exponential backoff, request queueing, and comprehensive error handling.

## Features

✅ **Exponential backoff for retries** - Waits 1s, 2s, 4s between retries  
✅ **Rate limit handling (429)** - Automatically retries with backoff  
✅ **Request queueing** - Queues rate-limited requests for later processing  
✅ **FIFO queue processing** - Maintains request order  
✅ **Network error handling** - Retries on connection failures  
✅ **Comprehensive logging** - All API errors are logged  
✅ **Configurable retries** - Default 3 attempts, customizable  
✅ **Smart error handling** - Doesn't retry on client errors (4xx except 429)

## Basic Usage

```python
from src.api_client import APIClient

# Initialize with API key from environment
client = APIClient()

# Or provide API key explicitly
client = APIClient(api_key="your-api-key", max_retries=3)

# Make an API call
response = client.call_api(
    prompt="Your prompt here",
    model="claude-3-5-sonnet-20241022",  # default
    max_tokens=4096,  # default
    temperature=1.0,  # default
    system="Optional system prompt"  # optional
)
```

## Integration with Other Components

### Concept Extractor

```python
from src.api_client import APIClient

class ConceptExtractor:
    def __init__(self):
        self.api_client = APIClient(max_retries=3)
    
    def extract_concepts(self, text: str, source_file: str, topic: str):
        prompt = f"""Extract key concepts from this lecture text:

{text}

Source: {source_file}
Topic: {topic}

Return concepts in JSON format with: name, definition, context, keywords."""
        
        try:
            response = self.api_client.call_api(prompt)
            # Parse response and create Concept objects
            return self._parse_concepts(response)
        except Exception as e:
            logger.error(f"Failed to extract concepts: {e}")
            return []
```

### Question Generator

```python
from src.api_client import APIClient

class QuestionGenerator:
    def __init__(self):
        self.api_client = APIClient(max_retries=3)
    
    def generate_question(self, concept, related_concepts):
        prompt = f"""Generate a scenario-based exam question.

Concept: {concept.name}
Definition: {concept.definition}

Create a realistic scenario that tests understanding, not memorization.
Include a model answer."""
        
        try:
            response = self.api_client.call_api(
                prompt,
                system="You are an expert at creating exam questions."
            )
            return self._parse_question(response)
        except Exception as e:
            logger.error(f"Failed to generate question: {e}")
            return None
```

### Answer Evaluator

```python
from src.api_client import APIClient

class AnswerEvaluator:
    def __init__(self):
        self.api_client = APIClient(max_retries=3)
    
    def evaluate_answer(self, question, student_answer, concept):
        prompt = f"""Evaluate this student answer:

Question: {question.question_text}
Model Answer: {question.model_answer}
Student Answer: {student_answer}

Provide feedback in Korean including:
- Correctness score (0-100)
- What was correct
- What was missing
- Related concepts to review"""
        
        try:
            response = self.api_client.call_api(
                prompt,
                system="You are an expert educator providing feedback in Korean."
            )
            return self._parse_feedback(response)
        except Exception as e:
            logger.error(f"Failed to evaluate answer: {e}")
            return None
```

## Error Handling

The API client handles these error types automatically:

### Rate Limit Errors (429)
- Retries with exponential backoff: 1s, 2s, 4s
- Logs warnings for each retry
- After all retries exhausted, queues the request for later processing
- Raises `RateLimitError` after max retries
- Queued requests are processed automatically on next API call or manually via `_process_queue()`

### Network Errors
- Retries with 1 second wait
- Logs warnings for each retry
- Raises `APIConnectionError` after max retries

### Client Errors (4xx except 429)
- Does NOT retry (these are usually invalid requests)
- Raises `APIError` immediately
- Logs error details

### Server Errors (5xx)
- Retries with exponential backoff
- Logs warnings for each retry
- Raises `APIError` after max retries

## Request Queueing

When rate limits are encountered after all retries, requests are automatically queued:

```python
from src.api_client import APIClient

client = APIClient()

# If this hits rate limit after retries, it will be queued
try:
    response = client.call_api("First prompt")
except RateLimitError:
    print(f"Request queued. Queue size: {client.get_queue_size()}")

# Next API call will process queued requests first
response = client.call_api("Second prompt")

# Manually process queue
client._process_queue()

# Check queue size
print(f"Pending requests: {client.get_queue_size()}")

# Clear queue if needed
client.clear_queue()
```

### Queue Behavior

- **FIFO Order**: Requests are processed in the order they were queued
- **Automatic Processing**: Queue is processed before each new API call
- **Rate Limit Awareness**: Stops processing if rate limit is hit again
- **Retry-After Header**: Respects `retry-after` header from API responses
- **Error Handling**: Failed requests are removed from queue and logged

## Logging

All API operations are logged:

```
INFO: API call attempt 1/3
INFO: API call successful

WARNING: Rate limit error on attempt 1: Rate limited
INFO: Waiting 1 seconds before retry...
WARNING: Rate limit error on attempt 2: Rate limited
INFO: Waiting 2 seconds before retry...
ERROR: Max retries reached for rate limit error
INFO: Request queued. Queue size: 1

INFO: Processing 1 queued requests
INFO: Queued request processed successfully. Remaining: 0
```

## Testing

Comprehensive unit tests cover:
- Successful API calls
- Rate limit retry with exponential backoff
- Rate limit request queueing
- Queue FIFO order maintenance
- Queue processing with rate limit handling
- Queue clearing
- Network error retry
- Client error no-retry behavior
- Server error retry
- Custom parameters (model, tokens, temperature)
- System prompts
- Logging verification

Run tests:
```bash
python -m pytest tests/test_api_client.py -v
```

## Requirements Validation

This implementation satisfies:

**Requirement 8.4**: Handle API errors gracefully and retry when appropriate
✅ Implements exponential backoff for retries  
✅ Handles rate limit errors (429)  
✅ Handles network errors with retries  
✅ Logs all API errors  
✅ Graceful error handling without crashes

**Requirement 8.5**: Queue requests when rate limits are encountered
✅ Creates request queue for rate-limited requests  
✅ Processes queued requests when rate limit clears  
✅ Maintains request order (FIFO)  
✅ Automatic queue processing on next API call
