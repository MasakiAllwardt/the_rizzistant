"""Configuration and environment variables"""
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from twilio.rest import Client

# Load environment variables from .env file
load_dotenv()

# Database configuration
DB_PATH = "date_summaries.db"

# API clients
def get_claude_client():
    """Get initialized Claude API client"""
    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def get_twilio_client():
    """Get initialized Twilio client"""
    return Client(
        os.environ.get("TWILIO_ACCOUNT_SID"),
        os.environ.get("TWILIO_AUTH_TOKEN")
    )

# Environment variables
def get_env_var(key: str, default=None):
    """Get environment variable with optional default"""
    return os.environ.get(key, default)

# OMI API configuration
OMI_APP_ID = os.environ.get("OMI_APP_ID")
OMI_API_KEY = os.environ.get("OMI_API_KEY")
OMI_BASE_URL = "https://api.omi.me/v2"

# Twilio configuration
PHONE_NUMBER = os.environ.get("PHONE_NUMBER")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

# Letta configuration
LETTA_API_KEY = os.environ.get("LETTA_API_KEY")
