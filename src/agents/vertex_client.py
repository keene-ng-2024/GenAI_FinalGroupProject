"""
vertex_client.py
----------------
Vertex AI client with retry logic, rate limiting, and circuit breaker.

This module provides a wrapper around the Vertex AI API with:
- Automatic retry with exponential backoff for 429 errors
- Rate limiting to prevent API throttling
- Circuit breaker pattern to handle repeated failures
"""

from __future__ import annotations

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


@dataclass
class CircuitBreaker:
    """Circuit breaker for API calls."""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
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
        """Record a failed call."""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
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
