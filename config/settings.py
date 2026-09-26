"""
config/settings.py
==================
Centralised application settings loaded from the .env file.

All settings are exposed as typed attributes on a singleton ``Settings``
instance (``settings``).  Import the singleton, never the class directly.

Usage::

    from config.settings import settings
    print(settings.DB_HOST)
"""
import os
import sys
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatabaseSettings:
    """PostgreSQL connection settings."""
    driver: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    name: str = "hamza_travels_db"
    user: str = "postgres"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False

    @property
    def url(self) -> str:
        """Full SQLAlchemy connection URL for PostgreSQL."""
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


@dataclass(frozen=True)
class SQLiteSettings:
    """SQLite fallback settings."""
    enabled: bool = False
    path: str = "data/hamza_travels.db"

    @property
    def url(self) -> str:
        """Full SQLAlchemy connection URL for SQLite."""
        if self.path == ":memory:":
            return "sqlite:///:memory:"
            
        # Get the user's AppData/Local directory
        if sys.platform == "win32":
            local_app_data = os.getenv('LOCALAPPDATA')
            if not local_app_data:
                local_app_data = str(Path.home() / "AppData" / "Local")
            app_data = Path(local_app_data) / "HamzaTravels"
        else:
            app_data = Path.home() / ".hamzatravels"
            
        # Ensure the directory exists
        app_data.mkdir(parents=True, exist_ok=True)
        
        db_path = app_data / "tams.db"
        return f"sqlite:///{db_path}"


@dataclass(frozen=True)
class SecuritySettings:
    """Security and auth settings."""
    secret_key: str = "change-this-secret"
    session_timeout_minutes: int = 30
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15


@dataclass(frozen=True)
class BackupSettings:
    """Backup configuration."""
    directory: str = "backups"
    auto_enabled: bool = True
    interval_hours: int = 24
    max_to_keep: int = 30


@dataclass(frozen=True)
class LoggingSettings:
    """Logging configuration."""
    directory: str = "logs"
    level: str = "INFO"
    max_bytes: int = 10_485_760  # 10 MB
    backup_count: int = 10


@dataclass(frozen=True)
class CompanySettings:
    """Company / report header information."""
    name: str = "Hamza Travels & Tours"
    address: str = "Your Office Address, City, Pakistan"
    phone: str = "+92-XXX-XXXXXXX"
    email: str = "info@hamzatravels.com"
    website: str = "www.hamzatravels.com"
    ntn: str = ""
    strn: str = ""


@dataclass(frozen=True)
class CurrencySettings:
    """Currency configuration."""
    default: str = "PKR"
    supported: List[str] = field(default_factory=lambda: ["PKR", "SAR", "USD"])
    symbols: dict = field(default_factory=lambda: {
        "PKR": "Rs.",
        "SAR": "SAR ",
        "USD": "$",
    })

    def symbol(self, currency: str) -> str:
        """Return the symbol for a given currency code."""
        return self.symbols.get(currency, currency)


@dataclass(frozen=True)
class UISettings:
    """UI and UX preferences."""
    default_theme: str = "dark"
    window_title: str = "Hamza Travels & Tours - Management System"


class Settings:
    """
    Singleton application settings.

    Reads all values from environment variables (populated by load_dotenv
    in main.py) and exposes them as strongly-typed nested dataclasses.
    """

    _instance: "Settings | None" = None

    def __new__(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """Load all settings from environment variables."""
        self.app_name: str = os.getenv("APP_NAME", "Hamza Travels & Tours")
        self.app_version: str = os.getenv("APP_VERSION", "1.0.0")
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.app_env: str = os.getenv("APP_ENV", "production")

        self.db = DatabaseSettings(
            driver=os.getenv("DB_DRIVER", "postgresql"),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            name=os.getenv("DB_NAME", "hamza_travels_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )

        self.sqlite = SQLiteSettings(
            enabled=os.getenv("USE_SQLITE_FALLBACK", "true").lower() == "true",
            path=os.getenv("SQLITE_PATH", "data/hamza_travels.db"),
        )

        self.security = SecuritySettings(
            secret_key=os.getenv("SECRET_KEY", "change-this-secret"),
            session_timeout_minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", "30")),
            password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
            max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
            lockout_duration_minutes=int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")),
        )

        self.backup = BackupSettings(
            directory=os.getenv("BACKUP_DIR", "backups"),
            auto_enabled=os.getenv("AUTO_BACKUP_ENABLED", "true").lower() == "true",
            interval_hours=int(os.getenv("AUTO_BACKUP_INTERVAL_HOURS", "24")),
            max_to_keep=int(os.getenv("MAX_BACKUPS_TO_KEEP", "30")),
        )

        self.logging = LoggingSettings(
            directory=os.getenv("LOG_DIR", "logs"),
            level=os.getenv("LOG_LEVEL", "INFO"),
            max_bytes=int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024))),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "10")),
        )

        self.company = CompanySettings(
            name=os.getenv("COMPANY_NAME", "Hamza Travels & Tours"),
            address=os.getenv("COMPANY_ADDRESS", "Your Office Address, City, Pakistan"),
            phone=os.getenv("COMPANY_PHONE", "+92-XXX-XXXXXXX"),
            email=os.getenv("COMPANY_EMAIL", "info@hamzatravels.com"),
            website=os.getenv("COMPANY_WEBSITE", "www.hamzatravels.com"),
            ntn=os.getenv("COMPANY_NTN", ""),
            strn=os.getenv("COMPANY_STRN", ""),
        )

        self.currency = CurrencySettings(
            default=os.getenv("DEFAULT_CURRENCY", "PKR"),
            supported=os.getenv("SUPPORTED_CURRENCIES", "PKR,SAR,USD").split(","),
            symbols={
                "PKR": os.getenv("PKR_SYMBOL", "Rs."),
                "SAR": os.getenv("SAR_SYMBOL", "SAR "),
                "USD": os.getenv("USD_SYMBOL", "$"),
            },
        )

        self.ui = UISettings(
            default_theme=os.getenv("DEFAULT_THEME", "dark"),
            window_title=os.getenv(
                "WINDOW_TITLE",
                "Hamza Travels & Tours - Management System",
            ),
        )

        # Paths
        self.documents_dir: str = os.getenv("DOCUMENTS_DIR", "documents")
        self.photos_dir: str = os.getenv("PHOTOS_DIR", "documents/photos")
        self.temp_dir: str = os.getenv("TEMP_DIR", "temp")
        self.reports_output_dir: str = os.getenv("REPORTS_OUTPUT_DIR", "reports/output")

        logger.debug("Settings loaded successfully. ENV=%s", self.app_env)

    @property
    def active_db_url(self) -> str:
        """Return the active database URL (PostgreSQL or SQLite fallback)."""
        if self.sqlite.enabled:
            logger.info("Using SQLite fallback database.")
            return self.sqlite.url
        return self.db.url

    @property
    def is_production(self) -> bool:
        """True if running in the production environment."""
        return self.app_env.lower() == "production"


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere
# ---------------------------------------------------------------------------
settings = Settings()
