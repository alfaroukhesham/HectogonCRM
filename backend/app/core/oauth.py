from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.user import OAuthProvider
import httpx
from urllib.parse import urlencode


class OAuthProviderConfig:
    """OAuth provider configuration."""
    
    def __init__(self, client_id: str, client_secret: str, authorize_url: str, 
                 token_url: str, user_info_url: str, scopes: list):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.user_info_url = user_info_url
        self.scopes = scopes


# OAuth provider configurations
OAUTH_PROVIDERS = {
    OAuthProvider.GOOGLE: OAuthProviderConfig(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        user_info_url="https://www.googleapis.com/oauth2/v2/userinfo",
        scopes=["openid", "email", "profile"]
    ),
    OAuthProvider.FACEBOOK: OAuthProviderConfig(
        client_id=settings.FACEBOOK_CLIENT_ID,
        client_secret=settings.FACEBOOK_CLIENT_SECRET,
        authorize_url=f"https://www.facebook.com/{settings.FACEBOOK_API_VERSION}/dialog/oauth",
        token_url=f"https://graph.facebook.com/{settings.FACEBOOK_API_VERSION}/oauth/access_token",
        user_info_url=f"https://graph.facebook.com/{settings.FACEBOOK_API_VERSION}/me",
        scopes=["email", "public_profile"]
    ),
    OAuthProvider.TWITTER: OAuthProviderConfig(
        client_id=settings.TWITTER_CLIENT_ID,
        client_secret=settings.TWITTER_CLIENT_SECRET,
        authorize_url="https://twitter.com/i/oauth2/authorize",
        token_url="https://api.twitter.com/2/oauth2/token",
        user_info_url="https://api.twitter.com/2/users/me",
        scopes=["tweet.read", "users.read"]
    )
}


def get_oauth_provider(provider: OAuthProvider) -> OAuthProviderConfig:
    """Get OAuth provider configuration."""
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    
    config = OAUTH_PROVIDERS[provider]
    if not config.client_id or not config.client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth provider {provider} is not configured"
        )
    
    return config


def get_authorization_url(provider: OAuthProvider, state: str, redirect_uri: str) -> str:
    """Generate OAuth authorization URL."""
    config = get_oauth_provider(provider)
    
    params = {
        "client_id": config.client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(config.scopes),
        "state": state,
        "response_type": "code"
    }
    
    # Add provider-specific parameters
    if provider == OAuthProvider.GOOGLE:
        params["access_type"] = "offline"
        params["prompt"] = "consent"
    elif provider == OAuthProvider.TWITTER:
        params["code_challenge"] = "challenge"
        params["code_challenge_method"] = "plain"
    
    return f"{config.authorize_url}?{urlencode(params)}"


async def exchange_code_for_token(provider: OAuthProvider, code: str, redirect_uri: str) -> Dict[str, Any]:
    """Exchange authorization code for access token."""
    config = get_oauth_provider(provider)
    
    async with httpx.AsyncClient() as client:
        data = {
            "grant_type": "authorization_code",
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        }
        
        response = await client.post(config.token_url, data=data)
        
        if response.status_code != 200:
            error_detail = response.text
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange code for token: {error_detail}"
            )
        
        return response.json()


async def get_user_info(provider: OAuthProvider, access_token: str) -> Dict[str, Any]:
    """Get user information from OAuth provider."""
    config = get_oauth_provider(provider)
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Special handling for different providers
        if provider == OAuthProvider.FACEBOOK:
            # Facebook requires fields parameter
            params = {"fields": "id,name,email,picture"}
            response = await client.get(config.user_info_url, headers=headers, params=params)
        elif provider == OAuthProvider.TWITTER:
            # Twitter v2 API requires specific fields
            params = {"user.fields": "id,name,username,profile_image_url"}
            response = await client.get(config.user_info_url, headers=headers, params=params)
        else:
            # Google and others
            response = await client.get(config.user_info_url, headers=headers)
        
        if response.status_code != 200:
            error_detail = response.text
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get user information: {error_detail}"
            )
        
        return response.json()


def normalize_user_info(provider: OAuthProvider, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize user information from different providers."""
    if provider == OAuthProvider.GOOGLE:
        return {
            "oauth_id": user_data.get("id"),
            "email": user_data.get("email"),
            "full_name": user_data.get("name"),
            "avatar_url": user_data.get("picture"),
            "is_verified": user_data.get("verified_email", False)
        }
    
    elif provider == OAuthProvider.FACEBOOK:
        picture_data = user_data.get("picture", {}).get("data", {})
        return {
            "oauth_id": user_data.get("id"),
            "email": user_data.get("email"),
            "full_name": user_data.get("name"),
            "avatar_url": picture_data.get("url"),
            "is_verified": True  # Facebook emails are generally verified
        }
    
    elif provider == OAuthProvider.TWITTER:
        # Twitter v2 API response structure
        user_info = user_data.get("data", {})
        return {
            "oauth_id": user_info.get("id"),
            "email": user_info.get("email"),  # May be None if not provided
            "full_name": user_info.get("name"),
            "avatar_url": user_info.get("profile_image_url"),
            "is_verified": False  # Twitter doesn't provide email verification status
        }
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}"
        )


async def complete_oauth_flow(provider: OAuthProvider, code: str, redirect_uri: str) -> Dict[str, Any]:
    """Complete OAuth flow and return normalized user information."""
    # Exchange code for token
    token_data = await exchange_code_for_token(provider, code, redirect_uri)
    access_token = token_data.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No access token received"
        )
    
    # Get user information
    user_data = await get_user_info(provider, access_token)
    
    # Normalize user information
    normalized_data = normalize_user_info(provider, user_data)
    normalized_data["provider"] = provider
    
    return normalized_data 
 
 
 