import asyncio
from logging import getLogger
from logging.config import fileConfig

from sqlalchemy import engine_from_config, make_url, text
from sqlalchemy import pool

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from authentication.core import settings
from authentication.models import *

logger = getLogger(__name__)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
database_url = settings.database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def create_database():
    """Create the database if it does not exist."""
    url_obj = make_url(database_url)
    db_name = url_obj.database
    admin_url = url_obj.set(database="postgres")

    engine = create_async_engine(str(admin_url), isolation_level="AUTOCOMMIT", future=True)

    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname=:name"),
            {"name": db_name}
        )

        exists = result.scalar() is not None

        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
            logger.info(f"Database '{db_name}' created.")
        else:
            logger.info(f"Database '{db_name}' already exists. Skipping creation.")


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    await create_database()

    connectable = create_async_engine(
        database_url,
        echo=False,
        future=True
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
