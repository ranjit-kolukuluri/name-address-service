# utils/config.py
"""
Configuration management for the validator app
"""

import os
import streamlit as st
import toml
from pathlib import Path
from typing import Tuple, Optional


def load_usps_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Load USPS credentials from streamlit.toml, secrets, or environment"""
    
    # Try .streamlit/streamlit.toml first
    try:
        streamlit_toml_path = Path('.streamlit/streamlit.toml')
        if streamlit_toml_path.exists():
            config = toml.load(streamlit_toml_path)
            client_id = config.get('USPS_CLIENT_ID', '')
            client_secret = config.get('USPS_CLIENT_SECRET', '')
            if client_id and client_secret:
                print("✅ USPS credentials loaded from .streamlit/streamlit.toml")
                return client_id, client_secret
    except Exception as e:
        print(f"⚠️ Failed to load from streamlit.toml: {str(e)}")
    
    # Try Streamlit secrets
    try:
        if hasattr(st, 'secrets'):
            client_id = st.secrets.get("USPS_CLIENT_ID", "")
            client_secret = st.secrets.get("USPS_CLIENT_SECRET", "")
            if client_id and client_secret:
                print("✅ USPS credentials loaded from Streamlit secrets")
                return client_id, client_secret
    except Exception as e:
        print(f"⚠️ Failed to load from Streamlit secrets: {str(e)}")
    
    # Try environment variables
    client_id = os.getenv('USPS_CLIENT_ID', '')
    client_secret = os.getenv('USPS_CLIENT_SECRET', '')
    
    if client_id and client_secret:
        print("✅ USPS credentials loaded from environment variables")
        return client_id, client_secret
    
    print("❌ USPS credentials not found")
    return None, None


class Config:
    """Application configuration"""
    
    # API Settings
    API_VERSION = "2.0.0"
    MAX_BATCH_RECORDS = 500
    VALIDATION_TIMEOUT = 30
    MAX_SUGGESTIONS = 5
    
    # UI Settings
    ENABLE_DEBUG_LOGGING = True
    PERFORMANCE_TRACKING = True
    
    # USPS Settings
    USPS_AUTH_URL = 'https://apis.usps.com/oauth2/v3/token'
    USPS_VALIDATE_URL = 'https://apis.usps.com/addresses/v3/address'
    
    # US States
    US_STATES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
    }