"""
Groq LLM Client
Fast inference using Groq API
"""

from groq import Groq
from typing import Optional, Dict, Any
from loguru import logger
import os


class GroqLLMClient:
    """Client for Groq API"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """
        Initialize Groq client
        
        Args:
            api_key: Groq API key (or use GROQ_API_KEY env var)
            model: Model name (llama-3.1-70b-versatile, mixtral-8x7b-32768, etc.)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        logger.info(f"Initialized Groq client with model: {model}")
        
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text completion
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional Groq API parameters
            
        Returns:
            Generated text
        """
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs
            )
            
            result = response.choices[0].message.content
            logger.debug(f"Generated {len(result)} characters")
            
            return result
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
            
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate JSON response
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            Parsed JSON dict
        """
        import json
        
        if system_prompt:
            system_prompt += "\n\nRespond with valid JSON only."
        else:
            system_prompt = "Respond with valid JSON only."
            
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # Try to extract JSON from response
        try:
            # Find JSON in response (between { and })
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Response: {response}")
            raise
            
    def chat(
        self,
        messages: list[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Multi-turn chat
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq chat error: {e}")
            raise


# Convenience function
def create_llm_client() -> GroqLLMClient:
    """Create LLM client from environment variables"""
    return GroqLLMClient(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=float(os.getenv("GROQ_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("GROQ_MAX_TOKENS", "2048")),
    )


if __name__ == "__main__":
    # Test the client
    from dotenv import load_dotenv
    load_dotenv()
    
    client = create_llm_client()
    
    # Test simple generation
    response = client.generate(
        prompt="What is OSINT? Answer in 2 sentences.",
        system_prompt="You are an intelligence analyst."
    )
    
    print("Response:", response)
