from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import json
from pathlib import Path
from app.core.config import settings
from app.models.models import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/admin/settings", tags=["Admin Settings"])


# ==================== SCHEMAS ====================

class APIKeysUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    xai_api_key: Optional[str] = None


class APIKeysResponse(BaseModel):
    openai_configured: bool
    anthropic_configured: bool
    xai_configured: bool
    openai_key_preview: str
    anthropic_key_preview: str
    xai_key_preview: str


class OpenHandsUpdate(BaseModel):
    url: Optional[str] = None
    api_key: Optional[str] = None


class OpenHandsResponse(BaseModel):
    url: str
    api_key_configured: bool
    api_key_preview: str


class GeneralSettingsUpdate(BaseModel):
    app_name: Optional[str] = None
    debug: Optional[bool] = None


class GeneralSettingsResponse(BaseModel):
    app_name: str
    debug: bool
    version: str


# ==================== HELPERS ====================

def mask_key(key: str) -> str:
    """Masque une clé API pour l'affichage."""
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


def load_env_file() -> dict:
    """Charge les variables d'environnement depuis le fichier .env."""
    env_path = Path(".env")
    env_vars = {}
    
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars


def save_env_file(env_vars: dict):
    """Sauvegarde les variables d'environnement dans le fichier .env."""
    env_path = Path(".env")
    
    # Lire le contenu existant
    lines = []
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()
    
    # Mettre à jour ou ajouter les variables
    updated_keys = set(env_vars.keys())
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            new_lines.append(line)
            continue
        
        if "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updated_keys:
                new_lines.append(f"{key}={env_vars[key]}\n")
                updated_keys.discard(key)
            else:
                new_lines.append(line)
    
    # Ajouter les nouvelles variables
    for key in updated_keys:
        if env_vars[key]:
            new_lines.append(f"{key}={env_vars[key]}\n")
    
    with open(env_path, "w") as f:
        f.writelines(new_lines)


# ==================== ROUTES ====================

@router.get("/overview", response_model=dict)
async def get_settings_overview(
    current_user: User = Depends(get_current_user)
):
    """Retourne un aperçu de tous les paramètres."""
    env_vars = load_env_file()
    
    return {
        "api_keys": {
            "openai_configured": bool(env_vars.get("OPENAI_API_KEY")),
            "anthropic_configured": bool(env_vars.get("ANTHROPIC_API_KEY")),
            "xai_configured": bool(env_vars.get("XAI_API_KEY")),
            "openai_key_preview": mask_key(env_vars.get("OPENAI_API_KEY", "")),
            "anthropic_key_preview": mask_key(env_vars.get("ANTHROPIC_API_KEY", "")),
            "xai_key_preview": mask_key(env_vars.get("XAI_API_KEY", "")),
        },
        "openhands": {
            "url": env_vars.get("OPENHANDS_URL", settings.OPENHANDS_URL),
            "api_key_configured": bool(env_vars.get("OPENHANDS_API_KEY")),
            "api_key_preview": mask_key(env_vars.get("OPENHANDS_API_KEY", "")),
        },
        "general": {
            "app_name": env_vars.get("APP_NAME", settings.APP_NAME),
            "debug": env_vars.get("DEBUG", "true").lower() == "true",
            "version": settings.APP_VERSION,
        },
        "env_file_exists": Path(".env").exists(),
    }


@router.get("/api-keys", response_model=APIKeysResponse)
async def get_api_keys(
    current_user: User = Depends(get_current_user)
):
    """Récupère le statut des API keys (sans les révéler)."""
    env_vars = load_env_file()
    
    return APIKeysResponse(
        openai_configured=bool(env_vars.get("OPENAI_API_KEY")),
        anthropic_configured=bool(env_vars.get("ANTHROPIC_API_KEY")),
        xai_configured=bool(env_vars.get("XAI_API_KEY")),
        openai_key_preview=mask_key(env_vars.get("OPENAI_API_KEY", "")),
        anthropic_key_preview=mask_key(env_vars.get("ANTHROPIC_API_KEY", "")),
        xai_key_preview=mask_key(env_vars.get("XAI_API_KEY", "")),
    )


@router.put("/api-keys", response_model=APIKeysResponse)
async def update_api_keys(
    keys: APIKeysUpdate,
    current_user: User = Depends(get_current_user)
):
    """Met à jour les API keys."""
    env_vars = load_env_file()
    
    # Mettre à jour les clés fournies
    if keys.openai_api_key is not None:
        env_vars["OPENAI_API_KEY"] = keys.openai_api_key
    
    if keys.anthropic_api_key is not None:
        env_vars["ANTHROPIC_API_KEY"] = keys.anthropic_api_key
    
    if keys.xai_api_key is not None:
        env_vars["XAI_API_KEY"] = keys.xai_api_key
    
    # Sauvegarder
    save_env_file(env_vars)
    
    return APIKeysResponse(
        openai_configured=bool(env_vars.get("OPENAI_API_KEY")),
        anthropic_configured=bool(env_vars.get("ANTHROPIC_API_KEY")),
        xai_configured=bool(env_vars.get("XAI_API_KEY")),
        openai_key_preview=mask_key(env_vars.get("OPENAI_API_KEY", "")),
        anthropic_key_preview=mask_key(env_vars.get("ANTHROPIC_API_KEY", "")),
        xai_key_preview=mask_key(env_vars.get("XAI_API_KEY", "")),
    )


@router.post("/api-keys/test")
async def test_api_key(
    provider: str,
    current_user: User = Depends(get_current_user)
):
    """Teste une API key."""
    env_vars = load_env_file()
    
    import time
    start = time.time()
    
    try:
        if provider == "openai":
            import httpx
            api_key = env_vars.get("OPENAI_API_KEY")
            if not api_key:
                return {"success": False, "error": "Clé non configurée"}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                
                if response.status_code == 200:
                    return {"success": True, "latency_ms": round((time.time() - start) * 1000)}
                else:
                    return {"success": False, "error": f"Erreur {response.status_code}"}
        
        elif provider == "anthropic":
            import httpx
            api_key = env_vars.get("ANTHROPIC_API_KEY")
            if not api_key:
                return {"success": False, "error": "Clé non configurée"}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={"x-api-key": api_key}
                )
                
                if response.status_code == 200:
                    return {"success": True, "latency_ms": round((time.time() - start) * 1000)}
                else:
                    return {"success": False, "error": f"Erreur {response.status_code}"}
        
        elif provider == "xai":
            import httpx
            api_key = env_vars.get("XAI_API_KEY")
            if not api_key:
                return {"success": False, "error": "Clé non configurée"}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/responses",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": "grok-2", "input": [{"role": "user", "content": "Hi"}]}
                )
                
                if response.status_code == 200:
                    return {"success": True, "latency_ms": round((time.time() - start) * 1000)}
                else:
                    return {"success": False, "error": f"Erreur {response.status_code}"}
        
        else:
            return {"success": False, "error": "Provider non supporté"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/openhands", response_model=OpenHandsResponse)
async def get_openhands_settings(
    current_user: User = Depends(get_current_user)
):
    """Récupère les paramètres OpenHands."""
    env_vars = load_env_file()
    
    return OpenHandsResponse(
        url=env_vars.get("OPENHANDS_URL", settings.OPENHANDS_URL),
        api_key_configured=bool(env_vars.get("OPENHANDS_API_KEY")),
        api_key_preview=mask_key(env_vars.get("OPENHANDS_API_KEY", "")),
    )


@router.put("/openhands", response_model=OpenHandsResponse)
async def update_openhands_settings(
    config: OpenHandsUpdate,
    current_user: User = Depends(get_current_user)
):
    """Met à jour les paramètres OpenHands."""
    env_vars = load_env_file()
    
    if config.url is not None:
        env_vars["OPENHANDS_URL"] = config.url
    
    if config.api_key is not None:
        env_vars["OPENHANDS_API_KEY"] = config.api_key
    
    save_env_file(env_vars)
    
    return OpenHandsResponse(
        url=env_vars.get("OPENHANDS_URL", settings.OPENHANDS_URL),
        api_key_configured=bool(env_vars.get("OPENHANDS_API_KEY")),
        api_key_preview=mask_key(env_vars.get("OPENHANDS_API_KEY", "")),
    )


@router.get("/general", response_model=GeneralSettingsResponse)
async def get_general_settings(
    current_user: User = Depends(get_current_user)
):
    """Récupère les paramètres généraux."""
    env_vars = load_env_file()
    
    return GeneralSettingsResponse(
        app_name=env_vars.get("APP_NAME", settings.APP_NAME),
        debug=env_vars.get("DEBUG", "true").lower() == "true",
        version=settings.APP_VERSION,
    )


@router.put("/general", response_model=GeneralSettingsResponse)
async def update_general_settings(
    config: GeneralSettingsUpdate,
    current_user: User = Depends(get_current_user)
):
    """Met à jour les paramètres généraux."""
    env_vars = load_env_file()
    
    if config.app_name is not None:
        env_vars["APP_NAME"] = config.app_name
    
    if config.debug is not None:
        env_vars["DEBUG"] = "true" if config.debug else "false"
    
    save_env_file(env_vars)
    
    return GeneralSettingsResponse(
        app_name=env_vars.get("APP_NAME", settings.APP_NAME),
        debug=env_vars.get("DEBUG", "true").lower() == "true",
        version=settings.APP_VERSION,
    )


@router.post("/reload")
async def reload_settings(
    current_user: User = Depends(get_current_user)
):
    """Demande le rechargement des settings (nécessite restart de l'app)."""
    return {
        "message": "Pour appliquer les changements, redémarrez l'application.",
        "note": "En production, un mécanisme de hot-reload peut être implémenté."
    }
