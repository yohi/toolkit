"""LLM client implementation for AI-powered analysis."""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
import time

from ..cache import CacheManager, CacheKey
from ..patterns.observer import publish_event, EventType

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM configuration."""
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.1
    timeout_seconds: int = 30
    retry_attempts: int = 3
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    rate_limit_per_minute: int = 60


@dataclass
class LLMResponse:
    """LLM response structure."""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    response_time_ms: float = 0.0
    cached: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'content': self.content,
            'model': self.model,
            'usage': self.usage,
            'response_time_ms': self.response_time_ms,
            'cached': self.cached,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class LLMClient(ABC):
    """Abstract LLM client."""

    def __init__(self, config: LLMConfig, cache_manager: Optional[CacheManager] = None):
        """Initialize LLM client.

        Args:
            config: LLM configuration
            cache_manager: Optional cache manager
        """
        self.config = config
        self.cache_manager = cache_manager

        # Rate limiting
        self._request_times: List[float] = []

        # Statistics
        self.stats = {
            'requests_sent': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_tokens_used': 0,
            'total_response_time_ms': 0.0,
            'errors': 0
        }

    @abstractmethod
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response asynchronously.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            LLM response
        """
        pass

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response synchronously.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            LLM response
        """
        # Run async method in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.generate_async(prompt, system_prompt, **kwargs)
        )

    async def _check_cache(self, cache_key: str) -> Optional[LLMResponse]:
        """Check cache for response."""
        if not self.config.cache_enabled or not self.cache_manager:
            return None

        try:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                self.stats['cache_hits'] += 1

                # Convert to LLMResponse
                response = LLMResponse(
                    content=cached_data['content'],
                    model=cached_data['model'],
                    usage=cached_data.get('usage', {}),
                    response_time_ms=cached_data.get('response_time_ms', 0.0),
                    cached=True,
                    timestamp=datetime.fromisoformat(cached_data['timestamp']),
                    metadata=cached_data.get('metadata', {})
                )

                logger.debug(f"Cache hit for LLM request: {cache_key}")
                return response
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")

        self.stats['cache_misses'] += 1
        return None

    async def _store_cache(self, cache_key: str, response: LLMResponse) -> None:
        """Store response in cache."""
        if not self.config.cache_enabled or not self.cache_manager:
            return

        try:
            self.cache_manager.set(
                cache_key,
                response.to_dict(),
                ttl_seconds=self.config.cache_ttl_seconds
            )
            logger.debug(f"Cached LLM response: {cache_key}")
        except Exception as e:
            logger.warning(f"Cache store failed: {e}")

    def _generate_cache_key(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate cache key for request."""
        import hashlib

        key_data = {
            'model': self.config.model_name,
            'prompt': prompt,
            'system_prompt': system_prompt or '',
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens,
            **kwargs
        }

        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

        return f"llm_response:{self.config.model_name}:{key_hash}"

    async def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting."""
        current_time = time.time()

        # Remove requests older than 1 minute
        self._request_times = [
            t for t in self._request_times
            if current_time - t < 60
        ]

        # Check rate limit
        if len(self._request_times) >= self.config.rate_limit_per_minute:
            wait_time = 60 - (current_time - self._request_times[0])
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

        self._request_times.append(current_time)

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        stats = self.stats.copy()

        # Calculate additional metrics
        if stats['requests_sent'] > 0:
            stats['average_response_time_ms'] = stats['total_response_time_ms'] / stats['requests_sent']
            stats['cache_hit_rate'] = stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses'])
        else:
            stats['average_response_time_ms'] = 0.0
            stats['cache_hit_rate'] = 0.0

        stats['config'] = {
            'model_name': self.config.model_name,
            'max_tokens': self.config.max_tokens,
            'temperature': self.config.temperature,
            'cache_enabled': self.config.cache_enabled
        }

        return stats


class OpenAIClient(LLMClient):
    """OpenAI API client."""

    def __init__(self, config: LLMConfig, cache_manager: Optional[CacheManager] = None):
        """Initialize OpenAI client."""
        super().__init__(config, cache_manager)
        self._client: Optional[Any] = None

    async def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout_seconds
                )
            except ImportError:
                raise ImportError("OpenAI library not installed. Install with: pip install openai")

        return self._client

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using OpenAI API."""
        # Check cache
        cache_key = self._generate_cache_key(prompt, system_prompt, **kwargs)
        cached_response = await self._check_cache(cache_key)
        if cached_response:
            return cached_response

        # Enforce rate limiting
        await self._enforce_rate_limit()

        start_time = time.time()

        try:
            client = await self._get_client()

            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Make API call
            response = await client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                **kwargs
            )

            response_time_ms = (time.time() - start_time) * 1000

            # Create response object
            llm_response = LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                    'total_tokens': response.usage.total_tokens if response.usage else 0
                },
                response_time_ms=response_time_ms,
                cached=False
            )

            # Update statistics
            self.stats['requests_sent'] += 1
            self.stats['total_tokens_used'] += llm_response.usage.get('total_tokens', 0)
            self.stats['total_response_time_ms'] += response_time_ms

            # Cache response
            await self._store_cache(cache_key, llm_response)

            # Publish event
            publish_event(
                EventType.PROCESSING_COMPLETED,
                source="OpenAIClient",
                data={
                    'model': self.config.model_name,
                    'tokens_used': llm_response.usage.get('total_tokens', 0),
                    'response_time_ms': response_time_ms,
                    'cached': False
                }
            )

            logger.debug(f"OpenAI response generated in {response_time_ms:.1f}ms")
            return llm_response

        except Exception as e:
            self.stats['errors'] += 1

            # Publish error event
            publish_event(
                EventType.PROCESSING_FAILED,
                source="OpenAIClient",
                data={'error': str(e), 'model': self.config.model_name},
                severity="error"
            )

            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicClient(LLMClient):
    """Anthropic Claude API client."""

    def __init__(self, config: LLMConfig, cache_manager: Optional[CacheManager] = None):
        """Initialize Anthropic client."""
        super().__init__(config, cache_manager)
        self._client: Optional[Any] = None

    async def _get_client(self):
        """Get or create Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(
                    api_key=self.config.api_key,
                    timeout=self.config.timeout_seconds
                )
            except ImportError:
                raise ImportError("Anthropic library not installed. Install with: pip install anthropic")

        return self._client

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Anthropic API."""
        # Check cache
        cache_key = self._generate_cache_key(prompt, system_prompt, **kwargs)
        cached_response = await self._check_cache(cache_key)
        if cached_response:
            return cached_response

        # Enforce rate limiting
        await self._enforce_rate_limit()

        start_time = time.time()

        try:
            client = await self._get_client()

            # Prepare messages
            messages = [{"role": "user", "content": prompt}]

            # Make API call
            response = await client.messages.create(
                model=self.config.model_name,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_prompt or "",
                messages=messages,
                **kwargs
            )

            response_time_ms = (time.time() - start_time) * 1000

            # Create response object
            llm_response = LLMResponse(
                content=response.content[0].text if response.content else "",
                model=response.model,
                usage={
                    'input_tokens': response.usage.input_tokens if response.usage else 0,
                    'output_tokens': response.usage.output_tokens if response.usage else 0,
                    'total_tokens': (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
                },
                response_time_ms=response_time_ms,
                cached=False
            )

            # Update statistics
            self.stats['requests_sent'] += 1
            self.stats['total_tokens_used'] += llm_response.usage.get('total_tokens', 0)
            self.stats['total_response_time_ms'] += response_time_ms

            # Cache response
            await self._store_cache(cache_key, llm_response)

            logger.debug(f"Anthropic response generated in {response_time_ms:.1f}ms")
            return llm_response

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Anthropic API error: {e}")
            raise


class LocalLLMClient(LLMClient):
    """Local LLM client (for self-hosted models)."""

    def __init__(self, config: LLMConfig, cache_manager: Optional[CacheManager] = None):
        """Initialize local LLM client."""
        super().__init__(config, cache_manager)

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using local LLM."""
        # Check cache
        cache_key = self._generate_cache_key(prompt, system_prompt, **kwargs)
        cached_response = await self._check_cache(cache_key)
        if cached_response:
            return cached_response

        start_time = time.time()

        try:
            # For demonstration - replace with actual local LLM implementation
            # This could use transformers, llama.cpp, etc.

            full_prompt = ""
            if system_prompt:
                full_prompt += f"System: {system_prompt}\n\n"
            full_prompt += f"User: {prompt}\n\nAssistant:"

            # Placeholder response
            response_content = f"[LOCAL LLM RESPONSE] Analyzed prompt: {len(prompt)} characters"

            response_time_ms = (time.time() - start_time) * 1000

            llm_response = LLMResponse(
                content=response_content,
                model=self.config.model_name,
                usage={
                    'prompt_tokens': len(prompt.split()),
                    'completion_tokens': len(response_content.split()),
                    'total_tokens': len(prompt.split()) + len(response_content.split())
                },
                response_time_ms=response_time_ms,
                cached=False
            )

            # Update statistics
            self.stats['requests_sent'] += 1
            self.stats['total_tokens_used'] += llm_response.usage.get('total_tokens', 0)
            self.stats['total_response_time_ms'] += response_time_ms

            # Cache response
            await self._store_cache(cache_key, llm_response)

            logger.debug(f"Local LLM response generated in {response_time_ms:.1f}ms")
            return llm_response

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Local LLM error: {e}")
            raise


def create_llm_client(
    provider: str,
    model_name: str,
    api_key: Optional[str] = None,
    cache_manager: Optional[CacheManager] = None,
    **kwargs
) -> LLMClient:
    """Create LLM client based on provider.

    Args:
        provider: LLM provider ('openai', 'anthropic', 'local')
        model_name: Model name
        api_key: API key (if required)
        cache_manager: Optional cache manager
        **kwargs: Additional config parameters

    Returns:
        LLM client instance
    """
    config = LLMConfig(
        model_name=model_name,
        api_key=api_key,
        **kwargs
    )

    if provider.lower() == 'openai':
        return OpenAIClient(config, cache_manager)
    elif provider.lower() == 'anthropic':
        return AnthropicClient(config, cache_manager)
    elif provider.lower() == 'local':
        return LocalLLMClient(config, cache_manager)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


# Global LLM client instance
_global_llm_client: Optional[LLMClient] = None


def get_llm_client() -> Optional[LLMClient]:
    """Get global LLM client."""
    return _global_llm_client


def set_llm_client(client: LLMClient) -> None:
    """Set global LLM client."""
    global _global_llm_client
    _global_llm_client = client
    logger.info(f"Set global LLM client: {type(client).__name__}")


async def generate_llm_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    **kwargs
) -> Optional[LLMResponse]:
    """Generate LLM response using global client.

    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        **kwargs: Additional parameters

    Returns:
        LLM response or None if no global client
    """
    client = get_llm_client()
    if client:
        return await client.generate_async(prompt, system_prompt, **kwargs)
    return None
