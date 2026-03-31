import logging
import os
import sys
from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = [
    "ANTHROPIC_API_KEY",
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
]

missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing:
    print(f"Error: Missing required environment variables: {missing}")
    sys.exit(1)

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/bot.log"),
    ],
)

from scheduler import start

start()
