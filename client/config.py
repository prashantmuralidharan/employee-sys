
import os

# --- Server Connection Settings ---
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
# Modified to include http:// protocol in the URL
SERVER_URL = os.getenv("SERVER_URL", f"http://{SERVER_HOST}:{SERVER_PORT}/api/employees")
API_KEY = os.getenv("API_KEY", "1993")  # Secure API key, use a strong key in production
TRANSMISSION_MODE = os.getenv("TRANSMISSION_MODE", "http")  # Could be http, kafka, etc.
JWT_SECRET = os.getenv("JWT_SECRET", "051993")  # Change to a secure secret in production
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")  # JWT Algorithm, HS256 is a common choice

# --- Database Settings ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "employees")  # Use the existing database name
DB_USER = os.getenv("DB_USER", "employee_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "YES")
USE_MYSQL = os.getenv("USE_MYSQL", "False").lower() == "true"  # Set to True to use MySQL instead of SQLite
DB_PATH = os.getenv("DB_PATH", "client_data.db")  # SQLite database path (used if USE_MYSQL is False)
DB_HOST = "localhost"       # MySQL server host
DB_PORT = 3306              # MySQL default port
DB_USER = "mdrkm"           # Your MySQL username
DB_PASSWORD = "Akshara@93"  # Your MySQL password
DB_NAME = "employee_db"
# --- Client Settings ---
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))  # Number of records to send in each batch
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))  # Max number of retry attempts for failed requests
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))  # Delay between retries in seconds
CONCURRENCY_LIMIT = int(os.getenv("CONCURRENCY_LIMIT", "10"))  # Max concurrent requests for transmission

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # Can be DEBUG, INFO, WARN, ERROR
LOG_FILE = os.getenv("LOG_FILE", "client.log")  # Log file for client-side logs

# --- Keep for Backward Compatibility or Future Use ---
class Config:
    """Config class to store all configuration settings for easier access."""
    SERVER_HOST = SERVER_HOST
    SERVER_PORT = SERVER_PORT
    SERVER_URL = SERVER_URL
    API_KEY = API_KEY
    TRANSMISSION_MODE = TRANSMISSION_MODE
    JWT_SECRET = JWT_SECRET
    JWT_ALGORITHM = JWT_ALGORITHM
    BATCH_SIZE = BATCH_SIZE
    MAX_RETRIES = MAX_RETRIES
    RETRY_DELAY = RETRY_DELAY
    CONCURRENCY_LIMIT = CONCURRENCY_LIMIT
    LOG_LEVEL = LOG_LEVEL
    LOG_FILE = LOG_FILE
    # Add database settings
    DB_HOST = DB_HOST
    DB_PORT = DB_PORT
    DB_NAME = DB_NAME
    DB_USER = DB_USER
    DB_PASSWORD = DB_PASSWORD
    USE_MYSQL = USE_MYSQL
    DB_PATH = DB_PATH