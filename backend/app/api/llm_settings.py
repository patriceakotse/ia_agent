from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.llm_factory import (
    llm_service, LLMProvider, LLM_MODELS, LLM_PRICING
)
from app.services.xai_service import XAI_MODELS, XAI_PRICING
from app.core.config import settings
from app.models.models import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/llm", tags=["LLM Settings"])


# ==================== SCHEMAS ====================

class LLMProviderInfo(BaseModel):
    id: str
    name: str
    has_api_key: bool


class LLMModelInfo(BaseModel):
    id: str
    name: str
    description: str
    has_pricing: bool = True


class LLMConfigResponse(BaseModel):
    provider: str
    model: str
    temperature: float
    has_api_key: bool


class LLMConfigUpdate(BaseModel):
    provider: str
    model: Optional[str] = None
    temperature: Optional[float] = None


class LLMTestRequest(BaseModel):
    provider: str
    model: Optional[str] = None
    message: str = "Dis-moi 'OK' si tu me lis correctement."


class LLMTestResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    latency_ms: Optional[float] = None


# ==================== ROUTES ====================

@router.get("/providers", response_model=List[LLMProviderInfo])
async def list_providers(
    current_user: User = Depends(get_current_user)
):
    """Liste les providers LLM disponibles."""
    return [
        {
            "id": "openai",
            "name": "OpenAI",
            "has_api_key": bool(settings.OPENAI_API_KEY),
        },
        {
            "id": "anthropic",
            "name": "Anthropic (Claude)",
            "has_api_key": bool(settings.ANTHROPIC_API_KEY),
        },
        {
            "id": "xai",
            "name": "xAI (Grok)",
            "has_api_key": bool(settings.XAI_API_KEY),
        },
    ]


@router.get("/models")
async def list_models(
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Liste les modèles disponibles par provider."""
    if provider:
        provider = provider.lower()
        if provider == "openai":
            return {
                "provider": "openai",
                "models": LLM_MODELS[LLMProvider.OPENAI],
                "pricing": LLM_PRICING.get(LLMProvider.OPENAI, {}),
            }
        elif provider == "anthropic":
            return {
                "provider": "anthropic",
                "models": LLM_MODELS[LLMProvider.ANTHROPIC],
                "pricing": LLM_PRICING.get(LLMProvider.ANTHROPIC, {}),
            }
        elif provider == "xai":
            return {
                "provider": "xai",
                "models": XAI_MODELS,
                "pricing": XAI_PRICING,
            }
        else:
            raise HTTPException(status_code=400, detail="Provider non supporté")
    
    # Retourner tous les providers
    return {
        "openai": {
            "models": LLM_MODELS[LLMProvider.OPENAI],
            "pricing": LLM_PRICING.get(LLMProvider.OPENAI, {}),
            "has_api_key": bool(settings.OPENAI_API_KEY),
        },
        "anthropic": {
            "models": LLM_MODELS[LLMProvider.ANTHROPIC],
            "pricing": LLM_PRICING.get(LLMProvider.ANTHROPIC, {}),
            "has_api_key": bool(settings.ANTHROPIC_API_KEY),
        },
        "xai": {
            "models": XAI_MODELS,
            "pricing": XAI_PRICING,
            "has_api_key": bool(settings.XAI_API_KEY),
        },
    }


@router.get("/config", response_model=LLMConfigResponse)
async def get_config(
    current_user: User = Depends(get_current_user)
):
    """Récupère la configuration LLM actuelle."""
    config = llm_service.current_config
    
    return {
        "provider": config.provider.value,
        "model": config.model,
        "temperature": config.temperature,
        "has_api_key": bool(config.api_key),
    }


@router.put("/config", response_model=LLMConfigResponse)
async def update_config(
    config_data: LLMConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    """Met à jour la configuration LLM."""
    try:
        llm_service.set_provider(
            provider=config_data.provider,
            model=config_data.model,
        )
        
        if config_data.temperature is not None:
            llm_service.current_config.temperature = config_data.temperature
        
        config = llm_service.current_config
        
        return {
            "provider": config.provider.value,
            "model": config.model,
            "temperature": config.temperature,
            "has_api_key": bool(config.api_key),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/test", response_model=LLMTestResponse)
async def test_llm(
    test_data: LLMTestRequest,
    current_user: User = Depends(get_current_user)
):
    """Teste la connexion à un provider LLM."""
    import time
    
    # Sauvegarder la config actuelle
    original_config = llm_service.current_config
    
    try:
        # Configurer le provider de test
        llm_service.set_provider(test_data.provider, test_data.model)
        
        # Tester la génération
        start = time.time()
        response = await llm_service.generate([
            {"role": "user", "content": test_data.message}
        ])
        latency = (time.time() - start) * 1000
        
        return {
            "success": True,
            "response": response,
            "latency_ms": round(latency, 2),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        # Restaurer la config originale
        llm_service.set_provider(
            original_config.provider.value,
            original_config.model,
            original_config.api_key,
        )
