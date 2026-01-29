"""
Application Configuration and API Clients
Contains configuration and API client implementations.
"""

import os
import requests
import hashlib
import hmac
from typing import Optional, Dict, Any
from datetime import datetime
import jwt


# BUG: Hardcoded API keys and secrets
API_KEY = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234"
SECRET_KEY = "super_secret_key_do_not_share_12345"
DATABASE_PASSWORD = "admin123!@#"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# BUG: Hardcoded JWT secret
JWT_SECRET = "my-jwt-secret-key-that-should-be-in-env"

# BUG: Hardcoded encryption key
ENCRYPTION_KEY = b"0123456789abcdef0123456789abcdef"


class Config:
    """Application configuration."""

    # BUG: Hardcoded credentials in class
    STRIPE_API_KEY = "sk_live_51ABC123DEF456GHI789JKL012MNO345PQR678STU901VWX"
    STRIPE_WEBHOOK_SECRET = "whsec_abc123def456ghi789"

    SENDGRID_API_KEY = "SG.abc123def456ghi789.jkl012mno345pqr678stu901vwx234yz"

    TWILIO_ACCOUNT_SID = "ACabcdef1234567890abcdef1234567890"
    TWILIO_AUTH_TOKEN = "abcdef1234567890abcdef1234567890"

    # BUG: Database connection string with credentials
    DATABASE_URL = "postgresql://admin:secretpassword123@localhost:5432/production_db"
    REDIS_URL = "redis://:redis_password_123@localhost:6379/0"

    # BUG: OAuth credentials hardcoded
    GOOGLE_CLIENT_ID = "123456789-abcdefghijklmnop.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET = "GOCSPX-abcdef123456-ghijkl789012"

    GITHUB_CLIENT_ID = "Iv1.abcdef1234567890"
    GITHUB_CLIENT_SECRET = "abcdef1234567890abcdef1234567890abcdef12"


class APIClient:
    """Generic API client with authentication."""

    def __init__(self):
        # BUG: Using hardcoded API key
        self.api_key = API_KEY
        self.base_url = "https://api.example.com/v1"

    def make_request(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """Make an authenticated API request."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/{endpoint}"

        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)

        return response.json()


class PaymentProcessor:
    """Handles payment processing."""

    def __init__(self):
        # BUG: Hardcoded Stripe key
        self.stripe_key = Config.STRIPE_API_KEY
        self.webhook_secret = Config.STRIPE_WEBHOOK_SECRET

    def create_charge(self, amount: int, currency: str, source: str) -> dict:
        """Create a payment charge."""
        # Using hardcoded API key
        headers = {
            "Authorization": f"Bearer {self.stripe_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "amount": amount,
            "currency": currency,
            "source": source
        }

        response = requests.post(
            "https://api.stripe.com/v1/charges",
            headers=headers,
            data=data
        )
        return response.json()

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature."""
        # BUG: Using hardcoded webhook secret
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)


class AuthManager:
    """Manages authentication and tokens."""

    def __init__(self):
        # BUG: Hardcoded JWT secret
        self.jwt_secret = JWT_SECRET
        # BUG: Weak/default admin password
        self.admin_password = "admin123"

    def create_token(self, user_id: str, role: str) -> str:
        """Create a JWT token."""
        payload = {
            "user_id": user_id,
            "role": role,
            "exp": datetime.utcnow().timestamp() + 3600
        }
        # Using hardcoded secret
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify a JWT token."""
        try:
            # Using hardcoded secret
            return jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return None

    def check_admin_password(self, password: str) -> bool:
        """Check if password matches admin password."""
        # BUG: Comparing against hardcoded password
        return password == self.admin_password


class DatabaseConnection:
    """Database connection manager."""

    def __init__(self):
        # BUG: Hardcoded database credentials
        self.host = "production-db.example.com"
        self.port = 5432
        self.user = "db_admin"
        self.password = "Pr0duct10n_P@ssw0rd!"
        self.database = "production"

    def get_connection_string(self) -> str:
        """Get the database connection string."""
        # BUG: Credentials in connection string
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class EmailService:
    """Email sending service."""

    def __init__(self):
        # BUG: Hardcoded SendGrid API key
        self.api_key = Config.SENDGRID_API_KEY

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": "noreply@example.com"},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}]
        }

        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers=headers,
            json=data
        )
        return response.status_code == 202


class SMSService:
    """SMS sending service."""

    def __init__(self):
        # BUG: Hardcoded Twilio credentials
        self.account_sid = Config.TWILIO_ACCOUNT_SID
        self.auth_token = Config.TWILIO_AUTH_TOKEN
        self.from_number = "+15551234567"

    def send_sms(self, to: str, message: str) -> bool:
        """Send an SMS message."""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

        response = requests.post(
            url,
            auth=(self.account_sid, self.auth_token),
            data={
                "To": to,
                "From": self.from_number,
                "Body": message
            }
        )
        return response.status_code == 201


def get_aws_client():
    """Get AWS client with credentials."""
    # BUG: Hardcoded AWS credentials
    return {
        "aws_access_key_id": AWS_ACCESS_KEY,
        "aws_secret_access_key": AWS_SECRET_KEY,
        "region_name": "us-east-1"
    }


def encrypt_data(data: str) -> bytes:
    """Encrypt sensitive data."""
    from cryptography.fernet import Fernet

    # BUG: Using hardcoded encryption key
    # Also: This isn't even a valid Fernet key format
    f = Fernet(ENCRYPTION_KEY)
    return f.encrypt(data.encode())


# BUG: Debug/test credentials left in code
DEBUG_USER = "test_user"
DEBUG_PASSWORD = "test_password_123"
TEST_API_KEY = "test_key_abc123"


def get_test_credentials() -> dict:
    """Get test credentials (should not be in production)."""
    return {
        "username": DEBUG_USER,
        "password": DEBUG_PASSWORD,
        "api_key": TEST_API_KEY
    }
