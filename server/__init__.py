"""
Server-side initialization for Employee Record System
"""

import logging
import asyncio
from typing import Optional
from server.config import ServerConfig

# Configure server-side logging
logging.basicConfig(
    level=logging.INFO,
    format="[SERVER] %(asctime)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Server-side constants
SERVER_NAME = "EmployeeRecordServer"
SUPPORTED_AUTH_MODES = ["OAUTH", "JWT"]

async def initialize_server() -> None:
    from server.database import init_db  # ✅ Move import inside function
    conn = await init_db()
async def initialize_server() -> None:
    """
    Initialize server-side configurations and perform pre-flight checks.
    Raises an exception if initialization fails.
    """
    logger.info(f"Initializing {SERVER_NAME}")

    # Validate authentication mode
    if ServerConfig.AUTH_MODE not in SUPPORTED_AUTH_MODES:
        logger.critical(f"Unsupported authentication mode: {ServerConfig.AUTH_MODE}")
        raise ValueError(f"Unsupported authentication mode: {ServerConfig.AUTH_MODE}")

    try:
        # Initialize the database connection
        logger.info("Connecting to the database...")
        conn: Optional[Any] = await init_db()

        if conn is None:
            logger.critical("Database initialization failed. Please check your configuration.")
            raise ConnectionError("Database initialization failed.")

        logger.info("Server initialized successfully!")

        # Example server logic or additional setup here

        # Cleanup logic
        await conn.wait_closed()  # Gracefully close the database connection
        logger.info("Database connection closed successfully.")

    except Exception as e:
        logger.error(f"Server initialization failed: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(initialize_server())
    except Exception as main_error:
        logger.critical(f"Failed to start {SERVER_NAME}: {str(main_error)}")

# Perform initialization when module is imported

