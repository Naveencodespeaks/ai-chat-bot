import logging
from logging.config import fileConfig
import os
from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from app.db.session import Base

# Load environment variables
load_dotenv()

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Setup logging
logger = logging.getLogger('alembic.env')

# Set SQLAlchemy URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

# target_metadata for 'autogenerate' support
target_metadata = Base.metadata
