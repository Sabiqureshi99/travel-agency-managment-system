import bcrypt
import secrets
import uuid
import base64
from cryptography.fernet import Fernet
from config.settings import settings

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verifies a password against its hash using bcrypt."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def generate_token(length: int = 32) -> str:
    """Generates a secure random hexadecimal token."""
    return secrets.token_hex(length // 2)

def generate_session_id() -> str:
    """Generates a UUID4 session ID."""
    return str(uuid.uuid4())

def get_app_key() -> bytes:
    """Derives a Fernet-compatible key from settings.security.secret_key."""
    secret = getattr(settings, 'security', type('Security', (), {'secret_key': 'default_secret_key'})).secret_key.encode('utf-8')
    if len(secret) < 32:
        secret = secret.ljust(32, b'*')
    elif len(secret) > 32:
        secret = secret[:32]
    return base64.urlsafe_b64encode(secret)

def encrypt_sensitive(data: str, key: str | None = None) -> str:
    """Encrypts sensitive data using Fernet symmetric encryption."""
    k = key.encode('utf-8') if key else get_app_key()
    f = Fernet(k)
    return f.encrypt(data.encode('utf-8')).decode('utf-8')

def decrypt_sensitive(token: str, key: str | None = None) -> str:
    """Decrypts sensitive token using Fernet symmetric encryption."""
    k = key.encode('utf-8') if key else get_app_key()
    f = Fernet(k)
    return f.decrypt(token.encode('utf-8')).decode('utf-8')

def generate_backup_password() -> str:
    """Generates a 12-char alphanumeric password."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(secrets.choice(alphabet) for _ in range(12))
