"""
Service factory unifié pour les LLMs (OpenAI, Anthropic, xAI)
Permet de basculer facilement entre les différents providers.
"""

from typing import List, Dict, Optional, Any, Literal
from enum import Enum
from app.core.config import settings
from app.services.xai_service import xai_client, XAI_MODELS, XAI_PRICING


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    XAI = "xai"


class LLMConfig:
    """Configuration pour un provider LLM."""
    
    def __init__(
        self,
        provider: LLMProvider,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature


class LLMService:
    """
    Service unifié pour tous les LLMs.
    Permet de changer de provider facilement.
    """
    
    def __init__(self):
        self.current_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model=settings.LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )
        
        # Registry des providers disponibles
        self._providers = {
            LLMProvider.OPENAI: self._call_openai,
            LLMProvider.ANTHROPIC: self._call_anthropic,
            LLMProvider.XAI: self._call_xai,
        }
    
    def set_provider(
        self,
        provider: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Configure le provider LLM à utiliser.
        
        Args:
            provider: "openai", "anthropic" ou "xai"
            model: Modèle spécifique (optionnel)
            api_key: Clé API (optionnel)
        """
        provider = provider.lower()
        
        if provider == "openai":
            self.current_config.provider = LLMProvider.OPENAI
            self.current_config.model = model or "gpt-4"
            self.current_config.api_key = api_key or settings.OPENAI_API_KEY
        elif provider == "anthropic":
            self.current_config.provider = LLMProvider.ANTHROPIC
            self.current_config.model = model or "claude-3-5-sonnet-20241022"
            self.current_config.api_key = api_key or settings.ANTHROPIC_API_KEY
        elif provider == "xai":
            self.current_config.provider = LLMProvider.XAI
            self.current_config.model = model or "grok-4.3"
            self.current_config.api_key = api_key or settings.XAI_API_KEY
        else:
            raise ValueError(f"Provider '{provider}' non supporté")
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Génère une réponse en utilisant le provider configuré.
        
        Args:
            messages: Liste des messages
            temperature: Température (optionnel)
            max_tokens: Tokens max (optionnel)
            
        Returns:
            Texte généré
        """
        provider_func = self._providers[self.current_config.provider]
        
        return await provider_func(
            messages=messages,
            model=self.current_config.model,
            temperature=temperature or self.current_config.temperature,
            max_tokens=max_tokens,
            api_key=self.current_config.api_key,
        )
    
    async def generate_document(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        Génère un document via le provider configuré.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.generate(messages)
    
    # ==================== PROVIDER IMPLEMENTATIONS ====================
    
    async def _call_openai(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        api_key: str,
    ) -> str:
        """Appel OpenAI via httpx."""
        import httpx
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY n'est pas configuré")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["message"]["content"]
    
    async def _call_anthropic(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        api_key: str,
    ) -> str:
        """Appel Anthropic via httpx."""
        import httpx
        
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY n'est pas configuré")
        
        # Convertir le format OpenAI vers Anthropic
        system_msg = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }
        
        if system_msg:
            payload["system"] = system_msg
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return data["content"][0]["text"]
    
    async def _call_xai(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        api_key: str,
    ) -> str:
        """Appel x.ai via le client xai."""
        if not api_key:
            raise ValueError("XAI_API_KEY n'est pas configuré")
        
        # Utiliser le client xai
        client = xai_client.__class__(api_key=api_key)
        
        result = await client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Parser la réponse x.ai
        if "output" in result and len(result["output"]) > 0:
            for item in result["output"]:
                if isinstance(item, dict) and "content" in item:
                    for content in item["content"]:
                        if isinstance(content, dict) and "text" in content:
                            return content["text"]
        
        return str(result)


# Modèles disponibles par provider
LLM_MODELS = {
    LLMProvider.OPENAI: [
        {"id": "gpt-4o", "name": "GPT-4o", "description": "Le plus récent et polyvalent"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "Rapide et puissant"},
        {"id": "gpt-4", "name": "GPT-4", "description": "Très intelligent"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Rapide et économique"},
    ],
    LLMProvider.ANTHROPIC: [
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "description": "Excellent équilibre"},
        {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "description": "Rapide et économique"},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "description": "Le plus puissant"},
        {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "description": "Polyvalent"},
    ],
    LLMProvider.XAI: XAI_MODELS,
}

# Prix par 1M tokens (approximatifs)
LLM_PRICING = {
    LLMProvider.OPENAI: {
        "gpt-4o": {"input": 5.0, "output": 15.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    },
    LLMProvider.ANTHROPIC: {
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-5-haiku-20241022": {"input": 0.8, "output": 4.0},
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
    },
    LLMProvider.XAI: XAI_PRICING,
}


# Instance singleton
llm_service = LLMService()
