import pytest
import asyncio
import aiohttp
from client.client import EmployeeClient
from server.server import create_app
from server.database import Database


@pytest.mark.integration
@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for the full system."""

    async def test_end_to_end(self, sample_csv_file):
        """Test the full system flow from client to database."""
        # This test requires a running server and database
        # It's skipped by default and should be run manually in an environment with proper setup

        # Start the server
        app = await create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8000)
        await site.start()

        try:
            # Create client
            client = EmployeeClient(server_url="http://localhost:8000/api/employees")

            # Process file
            result = await client.process_file(sample_csv_file, batch_size=20)

            # Verify results
            assert result["total_records"] > 0
            assert result["success_count"] > 0

            # Verify records in database
            db = Database()
            await db.create_pool()

            # Count records in database
            async with db.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT COUNT(*) FROM employees")
                    count_result = await cursor.fetchone()
                    assert count_result[0] >= result["success_count"]

            await db.close()

        finally:
            # Cleanup
            await runner.cleanup()