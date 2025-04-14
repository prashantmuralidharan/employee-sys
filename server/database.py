"""
Configuration settings for the server application.
"""
"""
Database handling for the employee records.
"""
import logging
import aiomysql
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from mysql.connector import connect, Error
import pandas as pd
from server.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_POOL_SIZE
from .decorators import async_log_execution_time
from .models import Employee

# Setup logging
logger = logging.getLogger(__name__)


class Database:
    """Database handler for employee records."""

    async def init_db():
        # Your database initialization logic

        """Initialize the MySQL database and create the necessary tables."""
        try:
            conn = await aiomysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
            )
            async with conn.cursor() as cursor:
                # Create database if it doesn't exist
                await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
                await cursor.execute(f"USE {DB_NAME};")

                # Create employees table
                await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS employees (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            first_name VARCHAR(50) NOT NULL,
                            last_name VARCHAR(50) NOT NULL,
                            email VARCHAR(100) UNIQUE NOT NULL,
                            department VARCHAR(50),
                            salary DECIMAL(10,2),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)

            await conn.ensure_closed()
            logger.info("✅ Database initialized successfully.")

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
    def __init__(self):
        self.pool = None
        self.config = None

    def set_config(self, config):
        """Set the database configuration."""
        self.config = config
        logger.info(f"Database configuration set: {self.config}")

    async def create_pool(self):
        """Create a connection pool to the MySQL database."""
        try:
            if not self.config:
                # Use config from config module if no custom config is set
                self.config = {
                    "host": DB_HOST,
                    "port": DB_PORT,
                    "user": DB_USER,
                    "password": DB_PASSWORD,
                    "db": DB_NAME,  # FIXED key from 'database' to 'db'
                    "maxsize": DB_POOL_SIZE,
                    "autocommit": True
                }
            self.pool = await aiomysql.create_pool(
                host='localhost',
                port=3306,
                user='mdrkm',
                password='Akshara@93',  # Replace 'your_password' with the actual password
                db='employee_db',
                maxsize = self.config.get("maxsize", 10),
                autocommit = True
            )
            self.pool = await aiomysql.create_pool(
                host=self.config.get("host"),
                port=self.config.get("port", 3306),
                user=self.config.get("user"),
                password=self.config.get("password"),
                db=self.config.get("db"),  # FIXED
                maxsize=self.config.get("maxsize", 10),
                autocommit=True
            )
            logger.info(f"Database connection pool created successfully with max size {self.config.get('maxsize')}")
        except Exception as e:
            logger.error(f"Error creating database connection pool: {str(e)}")
            raise

    async def close(self):
        """Close the database connection pool."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Database connection pool closed")

    @async_log_execution_time
    async def insert_employees(self, employees: List[Employee]) -> Tuple[int, int]:
        """Insert multiple employee records into the database."""
        if not self.pool:
            await self.create_pool()

        success_count = 0
        error_count = 0

        # Convert Employee objects to tuples for database insertion
        values = [
            (
                emp.id, emp.employee_id, emp.name, emp.email, emp.department,
                emp.designation, emp.salary, emp.date_of_joining, emp.created_at, emp.updated_at
            )
            for emp in employees
        ]

        sql = """
        INSERT INTO employees (
            id, employee_id, name, email, department, designation, salary, 
            date_of_joining, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            name = VALUES(name),
            email = VALUES(email),
            department = VALUES(department),
            designation = VALUES(designation),
            salary = VALUES(salary),
            date_of_joining = VALUES(date_of_joining),
            updated_at = VALUES(updated_at)
        """

        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    for i in range(0, len(values), 100):  # Batch insert (100 at a time)
                        batch = values[i:i + 100]
                        await cursor.executemany(sql, batch)
                    await conn.commit()  # Ensure changes are saved

            success_count = len(values)
            logger.info(f"Successfully inserted/updated {success_count} employee records")
        except Exception as e:
            logger.error(f"Database Insert Error: {e}")
            error_count = len(values)
        print(f"Total records received: {len(employees)}")
        print(f"Total records successfully inserted: {success_count}")
        print(f"Total failed inserts: {error_count}")
        return success_count, error_count

    def create_tables(self):
        """Create the necessary database tables if they don't exist."""
        try:
            # Use configuration from self.config if available, otherwise fall back to imported constants
            host = self.config.get("host") if self.config else DB_HOST
            port = self.config.get("port", 3306) if self.config else DB_PORT
            user = self.config.get("user") if self.config else DB_USER
            password = self.config.get("password") if self.config else DB_PASSWORD
            db = self.config.get("database") if self.config else DB_NAME

            with connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=db
            ) as connection:
                with connection.cursor() as cursor:
                    # Create employees table
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS employees (
                        id VARCHAR(36) PRIMARY KEY,
                        employee_id VARCHAR(50) UNIQUE,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100) NOT NULL,
                        department VARCHAR(50) NOT NULL,
                        designation VARCHAR(50) NOT NULL,
                        salary DECIMAL(10, 2) NOT NULL,
                        date_of_joining DATE NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        INDEX idx_employee_id (employee_id),
                        INDEX idx_department (department),
                        INDEX idx_date_of_joining (date_of_joining)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """)
                    connection.commit()
                    logger.info("Database tables created successfully")
        except Error as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
if __name__ == "__main__":
    asyncio.run(init_db())
# ----------------------------------

