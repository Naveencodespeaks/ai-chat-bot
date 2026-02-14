"""
LLM Client Module

Provides abstractions for LLM interactions:
- Multi-provider support (OpenAI, Azure, Ollama)
- Prompt engineering and templates
- Response caching
- Token management
- Error handling and retries
- Streaming support
"""

import os
import json
import time
from typing import Dict, List, Optional, Generator, Tuple
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import hashlib

from app.core.logging import logger, log_performance
from app.core.config import settings


# -------------------------------------------------
# LLM CONFIGURATION
# -------------------------------------------------

class LLMConfig:
    """Configuration for LLM client."""
    
    def __init__(self):
        """Initialize LLM configuration."""
        self.provider = os.getenv("LLM_PROVIDER", "openai")
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.api_key = os.getenv("LLM_API_KEY")
        self.api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1024"))
        self.top_p = float(os.getenv("LLM_TOP_P", "0.9"))
        self.timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        
        logger.info(f"LLMConfig initialized - Provider: {self.provider}, Model: {self.model}")


# -------------------------------------------------
# RESPONSE CACHE
# -------------------------------------------------

class ResponseCache:
    """
    Simple in-memory cache for LLM responses.
    
    Uses SHA256 of prompt as key. Real production should use Redis.
    """
    
    def __init__(self, ttl_minutes: int = 60):
        """
        Initialize cache.
        
        Args:
            ttl_minutes: Time to live in minutes
        """
        self.cache: Dict = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        logger.info(f"ResponseCache initialized - TTL: {ttl_minutes}m")
    
    def _get_key(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[str]:
        """
        Retrieve cached response.
        
        Args:
            text: Prompt text
        
        Returns:
            Cached response or None
        """
        key = self._get_key(text)
        
        if key not in self.cache:
            return None
        
        cached_item = self.cache[key]
        
        # Check if expired
        if datetime.now() > cached_item["expires"]:
            del self.cache[key]
            return None
        
        logger.debug(f"Cache HIT for prompt: {text[:50]}...")
        return cached_item["response"]
    
    def set(self, text: str, response: str):
        """
        Cache response.
        
        Args:
            text: Prompt text
            response: LLM response
        """
        key = self._get_key(text)
        self.cache[key] = {
            "response": response,
            "expires": datetime.now() + self.ttl,
            "created": datetime.now(),
        }
        logger.debug(f"Cache SET for prompt: {text[:50]}...")
    
    def clear(self):
        """Clear all cache."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "memory_mb": len(json.dumps(self.cache)) / 1024 / 1024,
        }


# -------------------------------------------------
# BASE LLM CLIENT
# -------------------------------------------------

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, config: LLMConfig):
        """
        Initialize base LLM client.
        
        Args:
            config: LLM configuration
        """
        self.config = config
        self.cache = ResponseCache()
        logger.info(f"BaseLLMClient initialized")
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate response from LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            **kwargs: Additional parameters
        
        Returns:
            Generated response
        """
        pass
    
    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Generate streaming response.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            **kwargs: Additional parameters
        
        Yields:
            Response chunks
        """
        pass
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count.
        
        Args:
            text: Text to count
        
        Returns:
            Approximate token count
        """
        # Simple estimation: ~4 chars per token
        return len(text) // 4
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens
        
        Returns:
            Truncated text
        """
        max_chars = max_tokens * 4
        return text[:max_chars]


# -------------------------------------------------
# OPENAI CLIENT
# -------------------------------------------------

class OpenAIClient(BaseLLMClient):
    """OpenAI LLM client."""
    
    def __init__(self, config: LLMConfig):
        """Initialize OpenAI client."""
        super().__init__(config)
        
        try:
            import openai
            openai.api_key = config.api_key
            openai.api_base = config.api_base
            self.client = openai
            logger.info("OpenAI client initialized")
        except ImportError:
            logger.error("openai library not installed")
            raise
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_cache: bool = True,
        **kwargs
    ) -> str:
        """
        Generate response using OpenAI API.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            use_cache: Use response cache
            **kwargs: Additional parameters
        
        Returns:
            Generated response
        """
        try:
            # Check cache
            if use_cache:
                cached = self.cache.get(prompt)
                if cached:
                    return cached
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Call API
            start_time = time.time()
            
            response = self.client.ChatCompletion.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                timeout=self.config.timeout,
                **kwargs
            )
            
            duration = time.time() - start_time
            log_performance("OpenAI API call", duration)
            
            # Extract response
            result = response["choices"][0]["message"]["content"]
            
            # Cache result
            if use_cache:
                self.cache.set(prompt, result)
            
            logger.debug(f"OpenAI response generated in {duration:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Generate streaming response using OpenAI API.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            **kwargs: Additional parameters
        
        Yields:
            Response chunks
        """
        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Stream API call
            response = self.client.ChatCompletion.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                stream=True,
                **kwargs
            )
            
            for chunk in response:
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
        except Exception as e:
            logger.error(f"Error streaming from OpenAI: {str(e)}")
            raise


# -------------------------------------------------
# FALLBACK/MOCK CLIENT
# -------------------------------------------------

class MockLLMClient(BaseLLMClient):
    """
    Mock LLM client for testing and development.
    
    Returns templated responses based on keywords.
    """
    
    def __init__(self, config: LLMConfig):
        """Initialize mock client."""
        super().__init__(config)
        logger.warning("Using MockLLMClient - for development only!")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate mock response.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            **kwargs: Additional parameters
        
        Returns:
            Mock response
        """
        # Simple keyword-based responses
        lower_prompt = prompt.lower()
        
        if "help" in lower_prompt or "issue" in lower_prompt:
            return "I understand you need help. Please provide more details about your issue."
        elif "??" in prompt or "???" in prompt:
            return "I'm not sure I understand. Could you rephrase that?"
        elif "thank" in lower_prompt:
            return "You're welcome! Is there anything else I can help you with?"
        else:
            return f"I acknowledge your message: '{prompt[:50]}...'. How can I assist you further?"
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Generate streaming mock response.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            **kwargs: Additional parameters
        
        Yields:
            Response chunks
        """
        response = self.generate(prompt, system_prompt, **kwargs)
        
        # Yield word by word
        for word in response.split():
            yield word + " "
            time.sleep(0.05)  # Simulate streaming delay


# -------------------------------------------------
# LLM CLIENT FACTORY
# -------------------------------------------------

class LLMClientFactory:
    """Factory for creating LLM clients."""
    
    _clients = {
        "openai": OpenAIClient,
        "mock": MockLLMClient,
    }
    
    @classmethod
    def create(cls, config: LLMConfig = None) -> BaseLLMClient:
        """
        Create LLM client based on configuration.
        
        Args:
            config: LLM configuration
        
        Returns:
            LLM client instance
        """
        if config is None:
            config = LLMConfig()
        
        provider = config.provider.lower()
        
        if provider not in cls._clients:
            logger.warning(
                f"Unknown provider: {provider}, falling back to mock"
            )
            provider = "mock"
        
        client_class = cls._clients[provider]
        return client_class(config)
    
    @classmethod
    def register(cls, name: str, client_class: type):
        """
        Register custom LLM client.
        
        Args:
            name: Provider name
            client_class: Client class
        """
        cls._clients[name] = client_class
        logger.info(f"Registered LLM client: {name}")


# -------------------------------------------------
# PROMPT TEMPLATES
# -------------------------------------------------

class PromptTemplate:
    """Template for constructing prompts."""
    
    def __init__(self, template: str):
        """
        Initialize prompt template.
        
        Args:
            template: Template string with {variable} placeholders
        """
        self.template = template
    
    def format(self, **kwargs) -> str:
        """
        Format template with variables.
        
        Args:
            **kwargs: Variables to fill
        
        Returns:
            Formatted prompt
        """
        return self.template.format(**kwargs)


# -------------------------------------------------
# SYSTEM PROMPTS
# -------------------------------------------------

SYSTEM_PROMPTS = {
    "assistant": """You are a helpful AI assistant. 
    - Be concise and clear
    - Provide accurate information
    - Ask clarifying questions when needed
    - Maintain a professional tone""",
    
    "support": """You are a customer support AI assistant.
    - Empathize with customer issues
    - Provide clear solutions
    - Offer alternatives when needed
    - Escalate to human when necessary""",
    
    "technical": """You are a technical support AI assistant.
    - Provide technical solutions
    - Explain technical concepts clearly
    - Suggest troubleshooting steps
    - Provide code examples when relevant""",
    
    "sales": """You are a sales AI assistant.
    - Be helpful and informative
    - Highlight product benefits
    - Address customer concerns
    - Suggest relevant products""",
}


# -------------------------------------------------
# GLOBAL CLIENT INSTANCE
# -------------------------------------------------

_client = None

def get_llm_client() -> BaseLLMClient:
    """
    Get global LLM client instance.
    
    Returns:
        LLM client
    """
    global _client
    
    if _client is None:
        config = LLMConfig()
        _client = LLMClientFactory.create(config)
    
    return _client


# -------------------------------------------------
# CONVENIENCE FUNCTIONS
# -------------------------------------------------

def generate_response(
    prompt: str,
    system_prompt_name: str = "assistant",
    use_cache: bool = True,
    **kwargs
) -> str:
    """
    Generate LLM response.
    
    Args:
        prompt: User prompt
        system_prompt_name: Name of system prompt template
        use_cache: Use response cache
        **kwargs: Additional parameters
    
    Returns:
        Generated response
    """
    client = get_llm_client()
    system_prompt = SYSTEM_PROMPTS.get(system_prompt_name)
    
    try:
        response = client.generate(
            prompt,
            system_prompt=system_prompt,
            use_cache=use_cache,
            **kwargs
        )
        return response
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise


def generate_response_stream(
    prompt: str,
    system_prompt_name: str = "assistant",
    **kwargs
) -> Generator[str, None, None]:
    """
    Generate streaming LLM response.
    
    Args:
        prompt: User prompt
        system_prompt_name: Name of system prompt template
        **kwargs: Additional parameters
    
    Yields:
        Response chunks
    """
    client = get_llm_client()
    system_prompt = SYSTEM_PROMPTS.get(system_prompt_name)
    
    try:
        yield from client.generate_stream(
            prompt,
            system_prompt=system_prompt,
            **kwargs
        )
    except Exception as e:
        logger.error(f"Error streaming response: {str(e)}")
        raise


# -------------------------------------------------
# EXPORTS
# -------------------------------------------------

__all__ = [
    "LLMConfig",
    "ResponseCache",
    "BaseLLMClient",
    "OpenAIClient",
    "MockLLMClient",
    "LLMClientFactory",
    "PromptTemplate",
    "SYSTEM_PROMPTS",
    "get_llm_client",
    "generate_response",
    "generate_response_stream",
]
 
