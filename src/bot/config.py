"""
Configuration management for the bot application.
"""
import os
import logging
from pathlib import Path
from typing import Final, Optional

# Configure logging
logger = logging.getLogger(__name__)


def _load_dotenv(path: Path) -> None:
    """Load environment variables from a .env file."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not load .env file: {e}")
        return
    
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip("'\"")
        
        if key and key not in os.environ:
            os.environ[key] = val


class Config:
    """Configuration class for the bot application."""
    
    def __init__(self, env_file_path: Optional[Path] = None):
        """Initialize configuration."""
        if env_file_path is None:
            env_file_path = Path(__file__).parent.parent.parent / ".env"
        
        # Load environment variables
        _load_dotenv(env_file_path)
        
        # Bot configuration
        self.TELEGRAM_BOT_TOKEN: Final = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.TELEGRAM_BOT_USERNAME: Final = os.environ.get("TELEGRAM_BOT_USERNAME")
        
        # OpenAI configuration
        self.OPENAI_API_KEY: Final = os.environ.get("OPENAI_API_KEY")
        
        # Database configuration
        self.PGHOST: Final = os.environ.get("PGHOST", "localhost")
        self.PGPORT: Final = os.environ.get("PGPORT", "5432")
        self.PGUSER: Final = os.environ.get("PGUSER")
        self.PGPASSWORD: Final = os.environ.get("PGPASSWORD")
        self.PGDATABASE: Final = os.environ.get("PGDATABASE")
        self.DATABASE_URL: Final = os.environ.get("DATABASE_URL")
    
    def validate(self) -> None:
        """Validate that required configuration is present."""
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("No TELEGRAM_BOT_TOKEN provided. Please set it in your .env file.")
        
        if not self.OPENAI_API_KEY:
            raise ValueError("No OPENAI_API_KEY provided. Please set it in your .env file.")
        
        # Check either DATABASE_URL or individual credentials
        has_db_url = bool(self.DATABASE_URL)
        has_db_creds = all([self.PGUSER, self.PGPASSWORD, self.PGDATABASE])
        
        if not (has_db_url or has_db_creds):
            raise ValueError(
                "Missing database configuration. Please set DATABASE_URL or (PGUSER, PGPASSWORD, and PGDATABASE) in your .env file"
            )