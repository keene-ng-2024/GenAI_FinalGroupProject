"""
vertex_client.py
----------------
<<<<<<< HEAD
Vertex AI client initialization and utilities for the AI Research Paper Critique Assistant.

This module provides:
- get_vertex_ai_client(): Get or create Vertex AI client
- generate_content(): Generate content with retry logic
- Rate limiting and circuit breaker support
=======
Vertex AI client with retry logic, rate limiting, and circuit breaker.

This module provides a wrapper around the Vertex AI API with:
- Automatic retry with exponential backoff for 429 errors
- Rate limiting to prevent API throttling
- Circuit breaker pattern to handle repeated failures
>>>>>>> vertexai
"""

from __future__ import annotations

<<<<<<< HEAD
import time
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from functools import wraps

from google.cloud import aiplatform
from google.cloud.aiplatform.gapic import PredictionServiceClient
from google.cloud.aiplatform_v1.types import (
    Content,
    GenerateContentRequest,
    Part,
    GenerationConfig,
)


# ── Configuration ──────────────────────────────────────────────────────────────

def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    import yaml
    with open(config_path) as f:
        return yaml.safe_load(f)


# ── Client management ────────────────────────────────────────────────────────

_client_cache: Dict[str, PredictionServiceClient] = {}


def get_vertex_ai_client(
    project: Optional[str] = None,
    location: Optional[str] = None,
    config: Optional[dict] = None,
) -> PredictionServiceClient:
    """
    Get or create a Vertex AI PredictionServiceClient.
    
    Args:
        project: GCP project ID (optional, uses config if not provided)
        location: GCP location (optional, uses config if not provided)
        config: Config dict with vertex_ai settings
        
    Returns:
        PredictionServiceClient instance
    """
    # Get config if not provided
    if config is None:
        config = load_config()
    
    # Get project and location from config or parameters
    vertex_config = config.get("vertex_ai", {})
    project_id = project or vertex_config.get("project", "your-project-id")
    loc = location or vertex_config.get("location", "us-central1")
    
    # Create cache key
    cache_key = f"{project_id}:{loc}"
    
    if cache_key not in _client_cache:
        # Initialize aiplatform
        aiplatform.init(project=project_id, location=loc)
        
        # Create client
        _client_cache[cache_key] = PredictionServiceClient(
            client_options={"api_endpoint": f"{loc}-aiplatform.googleapis.com"}
        )
    
    return _client_cache[cache_key]


# ── Content generation ───────────────────────────────────────────────────────

def generate_content(
    client: PredictionServiceClient,
    model: str,
    messages: List[Dict[str, str]],
    config: Optional[dict] = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> Dict[str, Any]:
    """
    Generate content using Vertex AI with retry logic.
    
    Args:
        client: PredictionServiceClient instance
        model: Model name (e.g., "gemini-1.5-flash")
        messages: List of message dicts with "role" and "content"
        config: Config dict with generation settings
        max_retries: Maximum number of retries
        base_delay: Base delay for exponential backoff
        
    Returns:
        Dict with "text" (response text) and "token_usage" (dict with input/output tokens)
        
    Raises:
        Exception: If all retries fail
    """
    if config is None:
        config = load_config()
    
    vertex_config = config.get("vertex_ai", {})
    max_tokens = config.get("max_tokens", 4096)
    temperature = config.get("temperature", 0.2)
    
    # Build content for Vertex AI
    contents = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        
        # Convert role to Vertex AI format
        vertex_role = "user" if role == "user" else "model"
        contents.append(Content(role=vertex_role, parts=[Part(text=content)]))
    
    generation_config = GenerationConfig(
        max_output_tokens=max_tokens,
        temperature=temperature,
    )
    
    request = GenerateContentRequest(
        model=model,
        contents=contents,
        generation_config=generation_config,
    )
    
    # Retry with exponential backoff
    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.generate_content(request=request)
            
            # Extract text from response
            text = ""
            if response.candidates and response.candidates[0].content.parts:
                text = response.candidates[0].content.parts[0].text
            
            # Extract token usage
            token_usage = {}
            if response.usage_metadata:
                token_usage = {
                    "input_tokens": response.usage_metadata.prompt_token_count,
                    "output_tokens": response.usage_metadata.candidates_token_count,
                }
            
            return {
                "text": text,
                "token_usage": token_usage,
            }
            
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"  [WARN] Vertex AI API call failed, retrying in {delay}s: {e}")
                time.sleep(delay)
            else:
                print(f"  [ERROR] Vertex AI API call failed after {max_retries} attempts: {e}")
                raise
    
    raise last_error


# ── Rate limiting and circuit breaker ────────────────────────────────────────

@dataclass
class RateLimiter:
    """Simple rate limiter for API calls."""
    max_calls: int
    window_seconds: float
    
    calls: List[float] = None
    
    def __post_init__(self):
        self.calls = []
    
    def is_allowed(self) -> bool:
        """Check if a call is allowed under the rate limit."""
        now = time.time()
        # Remove old calls outside the window
        self.calls = [t for t in self.calls if now - t < self.window_seconds]
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Record a call."""
        self.calls.append(time.time())
=======
import json
import time
import random
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

import yaml
from dotenv import load_dotenv

load_dotenv()


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered
>>>>>>> vertexai


@dataclass
class CircuitBreaker:
    """Circuit breaker for API calls."""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
<<<<<<< HEAD
    
    failures: int = 0
    last_failure_time: Optional[float] = None
    state: str = "closed"  # closed, open, half-open
    
    def is_allowed(self) -> bool:
        """Check if a call is allowed."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            # Check if recovery timeout has passed
            if self.last_failure_time and time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True
    
    def record_success(self):
        """Record a successful call."""
        self.failures = 0
        self.state = "closed"
    
    def record_failure(self):
=======
    half_open_max_calls: int = 3
    
    failures: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_time: Optional[float] = None
    half_open_calls: int = 0
    
    def record_success(self) -> None:
        """Record a successful call."""
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.half_open_calls = 0
    
    def record_failure(self) -> None:
>>>>>>> vertexai
        """Record a failed call."""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
<<<<<<< HEAD
            self.state = "open"


# ── Global instances ─────────────────────────────────────────────────────────

_rate_limiter: Optional[RateLimiter] = None
_circuit_breaker: Optional[CircuitBreaker] = None


def get_rate_limiter(config: Optional[dict] = None) -> RateLimiter:
    """Get or create rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        if config is None:
            config = load_config()
        vertex_config = config.get("vertex_ai", {})
        max_calls = vertex_config.get("rate_limit", {}).get("max_calls", 100)
        window_seconds = vertex_config.get("rate_limit", {}).get("window_seconds", 60)
        _rate_limiter = RateLimiter(max_calls=max_calls, window_seconds=window_seconds)
    return _rate_limiter


def get_circuit_breaker(config: Optional[dict] = None) -> CircuitBreaker:
    """Get or create circuit breaker."""
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker()
    return _circuit_breaker


def with_rate_limiting(func):
    """Decorator to add rate limiting to a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        limiter = get_rate_limiter()
        if not limiter.is_allowed():
            raise Exception("Rate limit exceeded")
        limiter.record_call()
        return func(*args, **kwargs)
    return wrapper


def with_circuit_breaker(func):
    """Decorator to add circuit breaker to a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        breaker = get_circuit_breaker()
        if not breaker.is_allowed():
            raise Exception("Circuit breaker is open")
        try:
            result = func(*args, **kwargs)
            breaker.record_success()
            return result
        except Exception as e:
            breaker.record_failure()
            raise
    return wrapper
=======
            self.state = CircuitState.OPEN
    
    def is_allowed(self) -> bool:
        """Check if a call is allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self.last_failure_time is None:
                return False
            
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        
        return False


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""
    
    def __init__(self, rate: float = 10.0, burst: int = 20):
        """
        Initialize rate limiter.
        
        Args:
            rate: Tokens per second (requests per second)
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self.lock = False
    
    def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        while True:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return
            
            # Wait a bit before checking again
            time.sleep(0.1)


class VertexAIClient:
    """Client for Vertex AI API with retry, rate limiting, and circuit breaker."""
    
    def __init__(self, project: str, location: str, config: dict):
        """
        Initialize Vertex AI client.
        
        Args:
            project: GCP project ID
            location: GCP location/region
            config: Configuration dictionary
        """
        self.project = project
        self.location = location
        self.config = config
        
        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.get("failure_threshold", 5),
            recovery_timeout=config.get("recovery_timeout", 30.0)
        )
        
        # Initialize rate limiter
        rate_limit = config.get("rate_limit", 10.0)
        burst = config.get("burst", 20)
        self.rate_limiter = RateLimiter(rate=rate_limit, burst=burst)
        
        # Model mappings
        self.model_map = config.get("models", {})
        
        # Initialize Vertex AI client
        self._client = None
        
        # Initialize Vertex AI with project
        try:
            import vertexai
            vertexai.init(project=self.project, location=self.location)
        except Exception as e:
            print(f"  [WARN] Could not initialize vertexai: {e}")
    
    def _get_client(self):
        """Get or create Vertex AI client."""
        if self._client is None:
            try:
                from vertexai.preview.generative_models import GenerativeModel
                self._client = GenerativeModel
            except ImportError:
                raise ImportError(
                    "vertexai package not installed. "
                    "Install with: pip install google-cloud-aiplatform"
                )
        return self._client
    
    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate content using Vertex AI model.
        
        Args:
            prompt: Input prompt for the model
            system_instruction: Optional system instruction
            model_name: Model name (uses default if not specified)
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            
        Returns:
            Dictionary with text, input_tokens, and output_tokens
        """
        # Check circuit breaker
        if not self.circuit_breaker.is_allowed():
            raise RuntimeError("Circuit breaker is open")
        
        # Apply rate limiting
        self.rate_limiter.acquire()
        
        # Get model name
        if model_name is None:
            model_name = self.model_map.get("default", "gemini-1.5-flash-002")
        
        # Build model name with full path
        full_model_name = f"projects/{self.project}/locations/{self.location}/publishers/google/models/{model_name}"
        
        try:
            # Generate content
            model = self._get_client()(model_name=full_model_name)
            
            # Build contents
            contents = []
            if system_instruction:
                contents.append({"role": "user", "parts": [{"text": system_instruction}]})
            contents.append({"role": "user", "parts": [{"text": prompt}]})
            
            response = model.generate_content(
                contents,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            
            # Record success
            self.circuit_breaker.record_success()
            
            return {
                "text": response.text,
                "input_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
            }
            
        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure()
            raise


def get_vertex_ai_client(config: dict) -> VertexAIClient:
    """
    Get or create a Vertex AI client instance.
    
    Args:
        config: Configuration dictionary with vertex_ai section
        
    Returns:
        VertexAIClient instance
    """
    vertex_config = config.get("vertex_ai", {})
    
    project = vertex_config.get("project", "genai-vertexai-492302")
    location = vertex_config.get("location", "asia-southeast1")
    
    # Create client
    return VertexAIClient(
        project=project,
        location=location,
        config=vertex_config
    )
>>>>>>> vertexai
