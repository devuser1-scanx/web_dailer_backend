import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


# App
APP_NAME = os.getenv("APP_NAME", "ScanX Web Dialer Backend")
APP_ENV = os.getenv("APP_ENV", "local")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")


# Security
API_SECRET = os.getenv("API_SECRET", "dev-secret")
ENABLE_IVR = os.getenv("ENABLE_IVR", "false").lower() == "true"


# Database
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "scanx_app")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")


# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_API_KEY_SID = os.getenv("TWILIO_API_KEY_SID")
TWILIO_API_KEY_SECRET = os.getenv("TWILIO_API_KEY_SECRET")
TWILIO_TWIML_APP_SID = os.getenv("TWILIO_TWIML_APP_SID")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")


# Current forwarding behavior
CLIENT_FORWARD_NUMBER = os.getenv("CLIENT_FORWARD_NUMBER")


# Google Chat
ENABLE_GCHAT_MISSED_CALL_ALERTS = (
    os.getenv("ENABLE_GCHAT_MISSED_CALL_ALERTS", "true").lower() == "true"
)
GCHAT_MISSED_CALL_WEBHOOK_URL = os.getenv("GCHAT_MISSED_CALL_WEBHOOK_URL")