"""LLM client with OpenAI and Groq support with automatic fallback."""
from typing import Optional, Dict, Any, List
from openai import OpenAI
from groq import Groq
import json


class LLMClient:
    """Unified LLM client with OpenAI and Groq fallback support."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        groq_model: str = "meta-llama/llama-4-maverick-17b-128e-instruct",
        provider: str = "auto"
    ):
        """Initialize LLM client with fallback support."""
        self.openai_client = None
        self.groq_client = None
        self.groq_model = groq_model
        self.provider = provider
        self.current_provider = None
        
        # Initialize OpenAI client
        if openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=openai_api_key)
                print("✅ OpenAI client initialized")
            except Exception as e:
                print(f"⚠️  OpenAI initialization error: {e}, will use Groq as fallback")
                self.openai_client = None
        
        # Initialize Groq client
        if groq_api_key:
            try:
                self.groq_client = Groq(api_key=groq_api_key)
                if not self.current_provider:
                    self.current_provider = "groq"
                    print("✅ Using Groq as LLM provider")
            except Exception as e:
                print(f"⚠️  Groq initialization error: {e}")
        
        # Set provider based on preference
        if provider == "groq" and self.groq_client:
            self.current_provider = "groq"
            print("✅ Using Groq as LLM provider (manual selection)")
        elif provider == "openai" and self.openai_client:
            self.current_provider = "openai"
            print("✅ Using OpenAI as LLM provider (manual selection)")
        elif provider == "auto":
            # Auto-select: OpenAI first if available, else Groq
            # Will test OpenAI validity on first use
            if self.openai_client:
                self.current_provider = "openai"
                print("✅ Auto-selected OpenAI (will fallback to Groq if needed)")
            elif self.groq_client:
                self.current_provider = "groq"
                print("✅ Auto-selected Groq (OpenAI not available)")
    
    def _test_openai(self) -> bool:
        """Test if OpenAI API key is valid (lazy test - only when needed)."""
        if not self.openai_client:
            return False
        try:
            # Simple test call with minimal tokens
            test_response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception:
            return False
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        """Generate chat completion with automatic fallback."""
        
        # Try OpenAI first
        if self.current_provider == "openai" or (self.provider == "auto" and self.openai_client):
            try:
                openai_model = model or "gpt-4o-mini"
                response = self.openai_client.chat.completions.create(
                    model=openai_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream
                )
                
                if stream:
                    return self._handle_stream_response(response, "openai")
                else:
                    return response.choices[0].message.content.strip()
                    
            except Exception as e:
                print(f"⚠️  OpenAI error: {e}, falling back to Groq")
                # Fallback to Groq
                if self.groq_client:
                    self.current_provider = "groq"
                    return self._groq_completion(messages, temperature, max_tokens, stream)
                else:
                    raise Exception("Both OpenAI and Groq failed")
        
        # Use Groq
        elif self.current_provider == "groq" or self.groq_client:
            return self._groq_completion(messages, temperature, max_tokens, stream)
        
        else:
            raise Exception("No LLM provider available. Please configure OpenAI or Groq API keys.")
    
    def _groq_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        stream: bool
    ) -> str:
        """Generate completion using Groq."""
        if not self.groq_client:
            raise Exception("Groq client not initialized")
        
        try:
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,
                stream=stream,
                top_p=1,
                stop=None
            )
            
            if stream:
                return self._handle_stream_response(response, "groq")
            else:
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            raise Exception(f"Groq completion error: {e}")
    
    def _handle_stream_response(self, response, provider: str) -> str:
        """Handle streaming response."""
        full_content = ""
        for chunk in response:
            if provider == "openai":
                content = chunk.choices[0].delta.content or ""
            else:  # groq
                content = chunk.choices[0].delta.content or ""
            full_content += content
        return full_content.strip()
    
    def get_provider(self) -> str:
        """Get current LLM provider."""
        return self.current_provider or "none"

