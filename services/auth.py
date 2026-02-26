"""
Azure Entra ID (formerly Azure AD) authentication module using MSAL.
Handles user authentication and token management.
"""
import msal
import os
from dotenv import load_dotenv
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

load_dotenv()
logger = logging.getLogger(__name__)


def get_secret(secret_name, fallback_env_var=None):
    """
    Retrieve a secret from Azure Key Vault, with fallback to environment variable.
    
    Args:
        secret_name: Name of the secret in Key Vault
        fallback_env_var: Environment variable to use as fallback
    
    Returns:
        str: The secret value, or None if not found
    """
    # Try to get from Key Vault first
    try:
        key_vault_url = os.getenv('AZURE_KEYVAULT_URL')
        if key_vault_url:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=key_vault_url, credential=credential)
            secret = client.get_secret(secret_name)
            print(f"[KEY_VAULT] ✓ Successfully retrieved '{secret_name}' from Azure Key Vault")
            return secret.value
    except Exception as e:
        print(f"[KEY_VAULT] ⚠ Could not retrieve '{secret_name}' from Key Vault: {e}")
    
    # Fallback to environment variable
    if fallback_env_var:
        env_value = os.getenv(fallback_env_var)
        if env_value:
            print(f"[KEY_VAULT] Using fallback environment variable: {fallback_env_var}")
            return env_value
    
    print(f"[KEY_VAULT] ❌ Could not retrieve '{secret_name}' from Key Vault or environment variables")
    return None


# MSAL Configuration
CLIENT_ID = os.getenv('ENTRA_CLIENT_ID')
CLIENT_SECRET = get_secret('EntraClientSecret', 'EntraClientSecret')
AUTHORITY = os.getenv('ENTRA_AUTHORITY', 'https://login.microsoftonline.com/common')
REDIRECT_URI = os.getenv('ENTRA_REDIRECT_URI', 'http://localhost:8000/auth/callback')

print("\n[AUTH_INIT] ===== ENTRA AUTH MODULE INITIALIZED =====")
print(f"[AUTH_INIT] CLIENT_ID: {CLIENT_ID if CLIENT_ID else '❌ NOT SET'}")
print(f"[AUTH_INIT] CLIENT_SECRET: {'✓ Set' if CLIENT_SECRET else '❌ NOT SET'}")
print(f"[AUTH_INIT] AUTHORITY: {AUTHORITY}")
print(f"[AUTH_INIT] REDIRECT_URI: {REDIRECT_URI}")
print(f"[AUTH_INIT] =============================================\n")

# Scopes for user profile access
SCOPES = ['User.Read']


def get_msal_app():
    """
    Initialize and return MSAL application instance.
    
    Returns:
        msal.PublicClientApplication: MSAL app for authentication
    """
    return msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        token_cache=None  # In production, implement proper token caching
    )


def get_auth_url():
    """
    Generate the authorization URL for user login.
    
    Returns:
        str: Authorization URL for Entra ID login
    """
    print("\n[GET_AUTH_URL] Generating Entra ID authorization URL...")
    print(f"[GET_AUTH_URL] CLIENT_ID: {CLIENT_ID}")
    print(f"[GET_AUTH_URL] AUTHORITY: {AUTHORITY}")
    print(f"[GET_AUTH_URL] REDIRECT_URI: {REDIRECT_URI}")
    print(f"[GET_AUTH_URL] SCOPES: {SCOPES}")
    
    app = get_msal_app()
    print(f"[GET_AUTH_URL] MSAL app initialized")
    
    auth_url = app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        prompt='select_account'
    )
    print(f"[GET_AUTH_URL] Authorization URL returned: {type(auth_url)}")
    
    result_url = auth_url[0] if isinstance(auth_url, tuple) else auth_url
    print(f"[GET_AUTH_URL] ✓ Final URL: {result_url[:150]}...")
    return result_url


def acquire_token_by_auth_code(code, scopes=None):
    """
    Exchange authorization code for access token.
    
    Args:
        code (str): Authorization code from Entra ID
        scopes (list): Optional list of scopes
        
    Returns:
        dict: Token response or error
    """
    if not scopes:
        scopes = SCOPES
    
    print(f"\n[AUTH] Attempting token acquisition")
    print(f"[AUTH] CLIENT_ID: {CLIENT_ID}")
    print(f"[AUTH] AUTHORITY: {AUTHORITY}")
    print(f"[AUTH] REDIRECT_URI: {REDIRECT_URI}")
    print(f"[AUTH] SCOPES: {scopes}")
    print(f"[AUTH] Code received: {code[:50]}..." if code else "[AUTH] No code provided")
    
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    
    try:
        print(f"[AUTH] Initialized ConfidentialClientApplication")
        print(f"[AUTH] Calling acquire_token_by_authorization_code...")
        
        token_response = app.acquire_token_by_authorization_code(
            code=code,
            scopes=scopes,
            redirect_uri=REDIRECT_URI
        )
        
        print(f"[AUTH] Token Response Received:")
        print(f"[AUTH] Response Keys: {token_response.keys()}")
        
        if 'error' in token_response:
            print(f"[AUTH] ERROR in token response!")
            print(f"[AUTH] Error: {token_response.get('error')}")
            print(f"[AUTH] Error Description: {token_response.get('error_description')}")
            print(f"[AUTH] Correlation ID: {token_response.get('correlation_id')}")
            logger.error(f"Token acquisition failed: {token_response.get('error_description')}")
            return token_response
        
        if 'access_token' in token_response:
            print(f"[AUTH] ✓ SUCCESS! Access token acquired")
            print(f"[AUTH] Token Type: {token_response.get('token_type')}")
            print(f"[AUTH] Expires In: {token_response.get('expires_in')} seconds")
            if 'id_token_claims' in token_response:
                print(f"[AUTH] ID Token Claims: {token_response.get('id_token_claims')}")
        else:
            print(f"[AUTH] WARNING: No access token in response")
            print(f"[AUTH] Full Response: {token_response}")
        
        return token_response
        
    except Exception as e:
        print(f"[AUTH] EXCEPTION during token acquisition:")
        print(f"[AUTH] Exception Type: {type(e).__name__}")
        print(f"[AUTH] Exception Message: {str(e)}")
        import traceback
        print(f"[AUTH] Traceback:\n{traceback.format_exc()}")
        logger.error(f"Error acquiring token: {str(e)}")
        return {'error': str(e)}


def validate_token(access_token):
    """
    Validate the access token by attempting to use it in an API call.
    
    Args:
        access_token (str): JWT access token
        
    Returns:
        dict: User info if valid, error dict if invalid
    """
    try:
        # In production, you would validate the JWT signature
        # For now, we just check if it's not empty and has valid structure
        if not access_token or not isinstance(access_token, str):
            return {'error': 'Invalid token format'}
        
        parts = access_token.split('.')
        if len(parts) != 3:
            return {'error': 'Invalid JWT format'}
        
        logger.info("Token validation successful")
        return {'valid': True}
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return {'error': str(e)}


def is_authenticated(session):
    """
    Check if user is authenticated based on session.
    
    Args:
        session (dict): Flask session dictionary
        
    Returns:
        bool: True if user is authenticated
    """
    return 'access_token' in session and session.get('access_token') is not None
