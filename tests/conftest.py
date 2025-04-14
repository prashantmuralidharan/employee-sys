import os
import csv
import pytest
import asyncio
import tempfile
import aiomysql
import aiohttp
from datetime import datetime, timedelta
from aiohttp import web
import jwt
import shutil
from unittest.mock import MagicMock, patch

# Adjust these imports to match your actual project structure
from server.models import Employee
from server.database import Database
from server.server import create_app
from client.client import EmployeeClient
from server.config import JWT_SECRET, JWT_ALGORITHM


# Generate test data
@pytest.fixture
def sample_employee_data():
    """Generate a list of sample employee records."""
    return [
        {
            "employee_id": f"EMP{i:04d}",
            "name": f"Employee {i}",
            "email": f"employee{i}@example.com",
            "department": random.choice(["Engineering", "Marketing", "HR", "Finance"]),
            "designation": random.choice(["Manager", "Developer", "Analyst", "Director"]),
            "salary": round(random.uniform(50000, 150000), 2),
            "date_of_joining": (datetime.now() - timedelta(days=random.randint(0, 1000))).strftime("%Y-%m-%d")
        }
        for i in range(1, 101)  # Generate 100 records for testing
    ]


# Create a CSV file with test data
@pytest.fixture
def sample_csv_file(sample_employee_data):
    """Create a temporary CSV file with sample employee data."""
    temp_dir = tempfile.mkdtemp()
    csv_path = os.path.join(temp_dir, "test_employees.csv")

    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = sample_employee_data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for data in sample_employee_data:
            writer.writerow(data)

    yield csv_path

    # Cleanup
    shutil.rmtree(temp_dir)


# Mock JWT token
@pytest.fixture
def mock_jwt_token():
    """Generate a mock JWT token for testing."""
    payload = {
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "sub": "test_user"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# Mock database for server tests
@pytest.fixture
async def mock_db():
    """Create a mock database instance for testing."""
    db = MagicMock(spec=Database)
    db.insert_employees = MagicMock(return_value=(10, 0))
    db.create_pool = MagicMock()
    db.close = MagicMock()

    return db


# Test client for server API
@pytest.fixture
async def test_client(mock_db):
    """Create an aiohttp test client for the server API."""
    app = await create_app()

    # Replace the actual database with our mock
    app['db'] = mock_db

    client = aiohttp.test_client.TestClient(app)
    yield client

    # Cleanup
    await client.close()


# Mock aiohttp ClientSession for client tests
@pytest.fixture
def mock_client_session():
    """Create a mock aiohttp ClientSession for client tests."""
    session = MagicMock(spec=aiohttp.ClientSession)

    # Mock the response for post requests
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = MagicMock(return_value={"success_count": 10, "error_count": 0})

    # Make the __aenter__ and __aexit__ methods work as async context managers
    cm = MagicMock()
    cm.__aenter__ = MagicMock(return_value=mock_response)
    cm.__aexit__ = MagicMock(return_value=None)

    session.post = MagicMock(return_value=cm)

    return session


# Test database with real MySQL for integration tests
@pytest.fixture(scope="module")
async def test_db():
    """Create a test database for integration tests."""
    # Test database configuration
    DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
    DB_PORT = int(os.getenv("TEST_DB_PORT", "3306"))
    DB_USER = os.getenv("TEST_DB_USER", "root")
    DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "")
    TEST_DB_NAME = f"test_employee_db_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Create test database
    try:
        conn = await aiomysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        cursor = await conn.cursor()
        await cursor.execute(f"CREATE DATABASE {TEST_DB_NAME}")
        await cursor.close()
        conn.close()

        # Setup database instance for testing
        db = Database()
        db.config = {
            "host": DB_HOST,
            "port": DB_PORT,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "db": TEST_DB_NAME,
        }

        # Create tables
        db.create_tables()

        # Create connection pool
        await db.create_pool()

        yield db

        # Cleanup
        await db.close()

        # Drop test database
        conn = await aiomysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        cursor = await conn.cursor()
        await cursor.execute(f"DROP DATABASE {TEST_DB_NAME}")
        await cursor.close()
        conn.close()
    except Exception as e:
        pytest.skip(f"Could not connect to test database: {e}")
