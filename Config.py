import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Discord ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", ";")

GUILD_ID = os.getenv("GUILD_ID")

# --- Paths ---
# BASE_DIR is the project root (the folder this file lives in).
# Every data path in the project is built from this, so the bot works
BASE_DIR = Path(__file__).resolve().parent

GAMEMODES_DIR = BASE_DIR / "gamemodes"
UNITS_DIR = BASE_DIR / "units"
MECHANICS_DIR = BASE_DIR / "mechanics"
MISC_DIR = BASE_DIR / "misc"
ASSETS_DIR = BASE_DIR / "assets"

# --- Startup checks ---
def validate() -> None:
    """Fail fast with a clear error instead of a confusing crash later."""
    if not DISCORD_TOKEN or DISCORD_TOKEN == "your_bot_token_here":
        raise RuntimeError(
            "DISCORD_TOKEN is not set. Copy .env.example to .env and fill "
            "in your bot's token before running."
        )