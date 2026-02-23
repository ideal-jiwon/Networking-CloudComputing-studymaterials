"""Example usage of the API client wrapper."""

import os
from src.api_client import APIClient


def main():
    """Demonstrate API client usage."""
    # Initialize client (will use ANTHROPIC_API_KEY from environment)
    client = APIClient(max_retries=3)
    
    # Example 1: Simple API call
    print("Example 1: Simple API call")
    try:
        response = client.call_api(
            prompt="What is cloud computing in one sentence?",
            max_tokens=100
        )
        print(f"Response: {response}\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Example 2: API call with system prompt
    print("Example 2: API call with system prompt")
    try:
        response = client.call_api(
            prompt="Explain TCP vs UDP",
            system="You are a networking expert. Provide concise technical explanations.",
            max_tokens=200
        )
        print(f"Response: {response}\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Example 3: The client automatically handles retries
    print("Example 3: Automatic retry handling")
    print("The client will automatically retry on rate limits and network errors")
    print("with exponential backoff (1s, 2s, 4s, etc.)")
    print("All errors are logged for debugging.\n")


if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it before running this example:")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
    else:
        main()
