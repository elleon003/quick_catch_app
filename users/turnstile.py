import os
import requests
from django.conf import settings

def verify_turnstile(token: str, remote_ip: str = None) -> bool:
    """
    Verify Cloudflare Turnstile CAPTCHA token
    
    Args:
        token: The Turnstile token from the client
        remote_ip: The user's IP address (optional)
    
    Returns:
        bool: True if verification successful, False otherwise
    """
    secret_key = os.environ.get('TURNSTILE_SECRET_KEY')
    if not secret_key:
        return True  # Skip verification if not configured
    
    verify_url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
    
    data = {
        'secret': secret_key,
        'response': token,
    }
    
    if remote_ip:
        data['remoteip'] = remote_ip
    
    try:
        response = requests.post(verify_url, data=data, timeout=10)
        result = response.json()
        return result.get('success', False)
    except (requests.RequestException, ValueError):
        return False

def get_turnstile_site_key() -> str:
    """Get the Turnstile site key for frontend use"""
    return os.environ.get('TURNSTILE_SITE_KEY', '')

def is_turnstile_enabled() -> bool:
    """Check if Turnstile is properly configured"""
    return bool(get_turnstile_site_key() and os.environ.get('TURNSTILE_SECRET_KEY'))