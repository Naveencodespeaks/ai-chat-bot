from logging.config import fileConfig
import sys
from pathlib import Path

# ---------------------------------------------------------
# 1️⃣ Fix Python path FIRST
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]   # 🔥 IMPORTANT FIX
sys.path.append(str(BASE_DIR))

# ---------------------------------------------------------
# 2️⃣ Alembic Config
# ---------------------------------------------------------
from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------
# 3️⃣ Import Base + Settings
# ---------------------------------------------------------
from app.db.session import Base
from app.core.config import settings

# ---------------------------------------------------------
# 4️⃣ Import ALL models
# ---------------------------------------------------------
import app.models   # This loads all models from __init__.py

target_metadata = Base.metadata

# ---------------------------------------------------------
# 5️⃣ Use DATABASE_URL
# ---------------------------------------------------------
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


# ---------------------------------------------------------
# OFFLINE MIGRATIONS
# ---------------------------------------------------------
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

# ---------------------------------------------------------
# ONLINE MIGRATIONS
# ---------------------------------------------------------
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

# ---------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
