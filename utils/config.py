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
    """Load USPS credentials from various sources"""
    
    # Try .streamlit/secrets.toml first (your current file)
    try:
        secrets_toml_path = Path('.streamlit/secrets.toml')
        if secrets_toml_path.exists():
            config = toml.load(secrets_toml_path)
            client_id = config.get('USPS_CLIENT_ID', '')
            client_secret = config.get('USPS_CLIENT_SECRET', '')
            if client_id and client_secret:
                print("✅ USPS credentials loaded from .streamlit/secrets.toml")
                return client_id, client_secret
    except Exception as e:
        print(f"⚠️ Failed to load from .streamlit/secrets.toml: {str(e)}")
    
    # Try .streamlit/streamlit.toml as backup
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
    
    # Try .env file
    try:
        env_path = Path('.env')
        if env_path.exists():
            env_vars = {}
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip('"').strip("'")
            
            client_id = env_vars.get('USPS_CLIENT_ID', '')
            client_secret = env_vars.get('USPS_CLIENT_SECRET', '')
            if client_id and client_secret:
                print("✅ USPS credentials loaded from .env file")
                return client_id, client_secret
    except Exception as e:
        print(f"⚠️ Failed to load from .env file: {str(e)}")
    
    # Try Streamlit secrets (when running through Streamlit)
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
    
    print("❌ USPS credentials not found in any location")
    print("💡 Checked: .streamlit/secrets.toml, .streamlit/streamlit.toml, .env, environment variables")
    return None, None


class Config:
    """Application configuration"""
    
    # API Settings
    API_VERSION = "2.0.0"
    MAX_BATCH_RECORDS = 1000  # ← Increase for multiple CSV support
    MAX_FILES_PER_UPLOAD = 10  # ← Add limit for multiple files
    VALIDATION_TIMEOUT = 60  # ← Increase timeout for batch processing
    MAX_SUGGESTIONS = 5
    
    # File Upload Settings
    MAX_FILE_SIZE_MB = 50  # ← Add file size limit
    SUPPORTED_CSV_ENCODINGS = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']  # ← Support various encodings
    
    # UI Settings
    ENABLE_DEBUG_LOGGING = True
    PERFORMANCE_TRACKING = True
    
    # USPS Settings
    USPS_AUTH_URL = 'https://apis.usps.com/oauth2/v3/token'
    USPS_VALIDATE_URL = 'https://apis.usps.com/addresses/v3/address'
    
    # US States (same as before)
    US_STATES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
    }
    