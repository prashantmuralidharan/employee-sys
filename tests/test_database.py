import pytest
import asyncio
from server.database import Database
from server.models import Employee
from datetime import datetime


@pytest.mark.asyncio
class TestDatabase:
    """Test database operations."""

    async def test_insert_employees(self, test_db):
        """Test inserting employee records into the database."""
        if not test_db:
            pytest.skip("Database connection not available")

        # Create test employees
        employees = [
            Employee(
                employee_id=f"TEST{i}",
                name=f"Test Employee {i}",
                email=f"test{i}@example.com",
                department="Testing",
                designation="Tester",
                salary=70000.00,
                date_of_joining=datetime(2022, 1, 1),
                id=f"test-uuid-{i}",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            for i in range(1, 6)  # Create 5 test employees
        ]

        # Insert employees
        success_count, error_count = await test_db.insert_employees(employees)

        # Verify results
        assert success_count == 5
        assert error_count == 0

        # Verify employees in database
        async with test_db.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT COUNT(*) FROM employees WHERE department = 'Testing'")
                result = await cursor.fetchone()
                assert result[0] == 5

    async def test_duplicate_employee_id(self, test_db):
        """Test handling of duplicate employee IDs."""
        if not test_db:
            pytest.skip("Database connection not available")

        # Create employees with the same employee_id but different data
        employees = [
            Employee(
                employee_id="DUPE001",
                name="Original Employee",
                email="original@example.com",
                department="Original",
                designation="Original",
                salary=70000.00,
                date_of_joining=datetime(2022, 1, 1),
                id="dupe-uuid-1",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Employee(
                employee_id="DUPE001",  # Same employee_id
                name="Updated Employee",
                email="updated@example.com",
                department="Updated",
                designation="Updated",
                salary=80000.00,
                date_of_joining=datetime(2022, 2, 1),
                id="dupe-uuid-2",  # Different uuid
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]

        # Insert first employee
        await test_db.insert_employees([employees[0]])

        # Insert duplicate (should update)
        success_count, error_count = await test_db.insert_employees([employees[1]])

        # Verify results
        assert success_count > 0
        assert error_count == 0

        # Verify the employee was updated
        async with test_db.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT name, email FROM employees WHERE employee_id = 'DUPE001'")
                result = await cursor.fetchone()
                assert result[0] == "Updated Employee"
                assert result[1] == "updated@example.com"
