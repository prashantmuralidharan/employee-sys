"""
Configuration settings for the server application.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ServerConfig:
    HOST = "127.0.0.1"
    PORT = 8080
    DEBUG = True
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "employee_db"
DB_USER = "root"
DB_PASSWORD = "password"
DB_POOL_SIZE = 10
JWT_SECRET = "051993"
JWT_ALGORITHM = "HS256"
SERVER_HOST = "127.0.0.1"  # Or your server's actual host
SERVER_NAME = "EmployeeRecordServer"
SERVER_PORT = 8080
class Config:
    """Centralized configuration class for server and database settings."""

    # Server settings
    SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8080"))
    API_KEY: str = os.getenv("API_KEY", "1993")
    AUTH_MODE: str = os.getenv("AUTH_MODE", "JWT")

    # JWT settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "051993")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # Database settings
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str = os.getenv("DB_NAME", "employee_db")
    DB_USER: str = os.getenv("DB_USER", "employee_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_HOST = "localhost"
    DB_PORT = 3306
    DB_NAME = "employee_db"
    DB_USER = "mdrkm"
    DB_PASSWORD = "Akshara@93"  # Ensure this is set correctly!
    DB_POOL_SIZE = 10
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "server.log")

# Example usage:
# To access any configuration value, use Config.<property>
# Example: Config.SERVER_HOST