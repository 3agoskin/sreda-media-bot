import os
import logging


logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TG_BOT_API_TOKEN")

BOT_VERSION = 0.1

BOT_DB_NAME = "sreda_media"

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = None

WEEK = 60 * 60 * 24 * 7
