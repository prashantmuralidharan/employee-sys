import pytest
from datetime import datetime
from server.models import Employee


class TestEmployeeModel:
    """Test the Employee data class."""

    def test_employee_creation(self):
        """Test creating an Employee instance."""
        employee_data = {
            "employee_id": "EMP001",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "department": "Engineering",
            "designation": "Senior Developer",
            "salary": 85000.00,
            "date_of_joining": "2020-01-15"
        }

        employee = Employee.from_dict(employee_data)

        assert employee.employee_id == "EMP001"
        assert employee.name == "John Doe"
        assert employee.email == "john.doe@example.com"
        assert employee.department == "Engineering"
        assert employee.designation == "Senior Developer"
        assert employee.salary == 85000.00
        assert isinstance(employee.date_of_joining, datetime)
        assert employee.date_of_joining.strftime("%Y-%m-%d") == "2020-01-15"
        assert isinstance(employee.id, str)

    def test_employee_to_dict(self):
        """Test converting an Employee to a dictionary."""
        employee = Employee(
            employee_id="EMP002",
            name="Jane Smith",
            email="jane.smith@example.com",
            department="Marketing",
            designation="Manager",
            salary=95000.00,
            date_of_joining=datetime(2019, 5, 10),
            id="test-id",
            created_at=datetime(2022, 1, 1, 12, 0, 0),
            updated_at=datetime(2022, 1, 1, 12, 0, 0)
        )

        employee_dict = employee.to_dict()

        assert employee_dict["employee_id"] == "EMP002"
        assert employee_dict["name"] == "Jane Smith"
        assert employee_dict["salary"] == 95000.00
        assert "date_of_joining" in employee_dict
        assert "created_at" in employee_dict
        assert "updated_at" in employee_dict

    def test_employee_to_db_dict(self):
        """Test converting an Employee to a database-ready dictionary."""
        employee = Employee(
            employee_id="EMP003",
            name="Bob Johnson",
            email="bob.johnson@example.com",
            department="Finance",
            designation="Analyst",
            salary=75000.00,
            date_of_joining=datetime(2021, 3, 15),
            id="test-id-2",
            created_at=datetime(2022, 1, 1, 12, 0, 0),
            updated_at=datetime(2022, 1, 1, 12, 0, 0)
        )

        db_dict = employee.to_db_dict()

        assert db_dict["employee_id"] == "EMP003"
        assert db_dict["salary"] == 75000.00
        assert db_dict["date_of_joining"] == "2021-03-15"
        assert db_dict["created_at"] == "2022-01-01 12:00:00"
        assert db_dict["updated_at"] == "2022-01-01 12:00:00"
