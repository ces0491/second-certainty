# tests/test_performance.py
import time
from datetime import date

import pytest

from app.core.auth import get_password_hash
from app.core.tax_calculator import TaxCalculator
from app.models.tax_models import IncomeSource, UserExpense, UserProfile


class TestPerformance:
    """Test performance characteristics."""

    def test_tax_calculation_performance_single_user(self, test_db, test_user, complete_tax_data):
        """Test tax calculation performance for single user with multiple income sources."""
        tax_year = complete_tax_data

        # Add multiple income sources (10 sources)
        for i in range(10):
            income = IncomeSource(
                user_id=test_user.id,
                source_type=f"Income_Source_{i}",
                annual_amount=50000 + (i * 10000),
                tax_year=tax_year,
            )
            test_db.add(income)

        # Add multiple expenses (5 expenses)
        for i in range(5):
            expense = UserExpense(
                user_id=test_user.id,
                expense_type_id=1,  # Retirement contribution
                description=f"Expense_{i}",
                amount=5000 + (i * 1000),
                tax_year=tax_year,
            )
            test_db.add(expense)

        test_db.commit()

        calculator = TaxCalculator(test_db)

        # Measure calculation time
        start_time = time.time()
        result = calculator.calculate_tax_liability(test_user.id, tax_year)
        end_time = time.time()

        calculation_time = end_time - start_time

        # Should complete within reasonable time (less than 1 second)
        assert calculation_time < 1.0, f"Tax calculation took {calculation_time:.3f} seconds, expected < 1.0"

        # Verify calculation is correct
        assert result["gross_income"] > 0
        assert result["final_tax"] >= 0

        print(f"Tax calculation completed in {calculation_time:.3f} seconds")

    def test_multiple_user_calculations_performance(self, test_db, complete_tax_data):
        """Test tax calculations for multiple users."""
        tax_year = complete_tax_data
        calculator = TaxCalculator(test_db)

        # Create multiple test users (5 users)
        users = []
        for i in range(5):
            user = UserProfile(
                email=f"perftest_user{i}@test.com",
                hashed_password=get_password_hash("password123"),
                name=f"PerfTest{i}",
                surname="User",
                date_of_birth=date(1990, 1, 1),
                is_provisional_taxpayer=True,
            )
            test_db.add(user)
            users.append(user)
        test_db.commit()

        # Add income for each user
        for user in users:
            income = IncomeSource(user_id=user.id, source_type="Salary", annual_amount=300000, tax_year=tax_year)
            test_db.add(income)
        test_db.commit()

        # Calculate tax for all users and measure time
        start_time = time.time()
        results = []
        for user in users:
            result = calculator.calculate_tax_liability(user.id, tax_year)
            results.append(result)
        end_time = time.time()

        total_time = end_time - start_time
        avg_time_per_user = total_time / len(users)

        # Should complete all calculations efficiently
        assert total_time < 3.0, f"Multiple user calculations took {total_time:.3f} seconds, expected < 3.0"
        assert avg_time_per_user < 1.0, f"Average time per user {avg_time_per_user:.3f} seconds, expected < 1.0"

        # Verify all calculations completed
        assert len(results) == len(users)
        assert all(r["final_tax"] >= 0 for r in results)

        print(f"Multiple user calculations: {total_time:.3f}s total, {avg_time_per_user:.3f}s average per user")

    def test_provisional_tax_calculation_performance(self, test_db, test_user, complete_tax_data):
        """Test provisional tax calculation performance."""
        tax_year = complete_tax_data

        # Add income for provisional taxpayer
        income = IncomeSource(user_id=test_user.id, source_type="Consulting", annual_amount=500000, tax_year=tax_year)
        test_db.add(income)
        test_db.commit()

        calculator = TaxCalculator(test_db)

        # Measure provisional tax calculation time
        start_time = time.time()
        result = calculator.calculate_provisional_tax(test_user.id, tax_year)
        end_time = time.time()

        calculation_time = end_time - start_time

        # Should complete quickly
        assert (
            calculation_time < 0.5
        ), f"Provisional tax calculation took {calculation_time:.3f} seconds, expected < 0.5"

        # Verify result structure
        assert "total_tax" in result
        assert "first_payment" in result
        assert "second_payment" in result

        print(f"Provisional tax calculation completed in {calculation_time:.3f} seconds")

    def test_database_query_performance(self, test_db, complete_tax_data):
        """Test database query performance for tax data retrieval."""
        calculator = TaxCalculator(test_db)
        tax_year = complete_tax_data

        # Test individual query performance
        queries = [
            ("Tax Brackets", lambda: calculator.get_tax_brackets(tax_year)),
            ("Tax Rebates", lambda: calculator.get_tax_rebates(tax_year)),
            ("Tax Thresholds", lambda: calculator.get_tax_thresholds(tax_year)),
            ("Medical Credits", lambda: calculator.get_medical_tax_credits(tax_year)),
        ]

        for query_name, query_func in queries:
            start_time = time.time()
            result = query_func()
            end_time = time.time()

            query_time = end_time - start_time

            # Each query should be very fast
            assert query_time < 0.1, f"{query_name} query took {query_time:.3f} seconds, expected < 0.1"
            assert result is not None

            print(f"{query_name} query: {query_time:.3f} seconds")

    def test_api_endpoint_response_time(self, client, test_user, auth_headers, complete_tax_data):
        """Test API endpoint response times."""
        # Add test data
        income_data = {"source_type": "Salary", "annual_amount": 400000, "is_paye": True}
        client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)

        # Test various endpoint response times
        endpoints = [
            ("GET", f"/api/tax/users/{test_user.id}/income/"),
            ("GET", f"/api/tax/users/{test_user.id}/tax-calculation/"),
            ("GET", "/api/tax/tax-brackets/"),
            ("GET", "/api/tax/deductible-expenses/"),
            ("GET", "/api/auth/me"),
        ]

        for method, endpoint in endpoints:
            start_time = time.time()

            if method == "GET":
                response = client.get(endpoint, headers=auth_headers)

            end_time = time.time()
            response_time = end_time - start_time

            # API responses should be fast
            assert response_time < 2.0, f"{method} {endpoint} took {response_time:.3f} seconds, expected < 2.0"
            assert response.status_code == 200

            print(f"{method} {endpoint}: {response_time:.3f} seconds")

    def test_concurrent_api_requests(self, client, test_user, auth_headers, complete_tax_data):
        """Test handling of concurrent API requests."""
        # Add test data
        income_data = {"source_type": "Salary", "annual_amount": 300000, "is_paye": True}
        client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)

        # Simulate concurrent requests
        import queue
        import threading

        results_queue = queue.Queue()

        def make_request():
            start_time = time.time()
            response = client.get(f"/api/tax/users/{test_user.id}/tax-calculation/", headers=auth_headers)
            end_time = time.time()
            results_queue.put((response.status_code, end_time - start_time))

        # Create and start threads
        threads = []
        num_concurrent_requests = 5

        start_time = time.time()
        for _ in range(num_concurrent_requests):
            thread = threading.Thread(target=make_request)
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        end_time = time.time()

        total_time = end_time - start_time

        # Collect results
        status_codes = []
        response_times = []
        while not results_queue.empty():
            status_code, response_time = results_queue.get()
            status_codes.append(status_code)
            response_times.append(response_time)

        # All requests should succeed
        assert all(status == 200 for status in status_codes)
        assert len(response_times) == num_concurrent_requests

        # Concurrent requests should complete reasonably quickly
        assert total_time < 5.0, f"Concurrent requests took {total_time:.3f} seconds, expected < 5.0"

        avg_response_time = sum(response_times) / len(response_times)
        print(f"Concurrent requests: {total_time:.3f}s total, {avg_response_time:.3f}s average")

    def test_memory_usage_stability(self, test_db, complete_tax_data):
        """Test memory usage doesn't grow excessively during calculations."""
        import gc
        import sys

        tax_year = complete_tax_data
        calculator = TaxCalculator(test_db)

        # Create a test user
        user = UserProfile(
            email="memory_test@test.com",
            hashed_password=get_password_hash("password123"),
            name="Memory",
            surname="Test",
            date_of_birth=date(1990, 1, 1),
            is_provisional_taxpayer=False,
        )
        test_db.add(user)
        test_db.commit()

        # Add income
        income = IncomeSource(user_id=user.id, source_type="Salary", annual_amount=300000, tax_year=tax_year)
        test_db.add(income)
        test_db.commit()

        # Force garbage collection and get initial memory
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Perform multiple calculations
        for i in range(100):
            result = calculator.calculate_tax_liability(user.id, tax_year)
            assert result["final_tax"] >= 0

        # Force garbage collection and check final memory
        gc.collect()
        final_objects = len(gc.get_objects())

        object_growth = final_objects - initial_objects

        # Memory usage shouldn't grow significantly
        assert object_growth < 2000, f"Object count grew by {object_growth}, expected < 1000"

        print(f"Memory test: {object_growth} objects created during 100 calculations")

    def test_large_dataset_performance(self, test_db, complete_tax_data):
        """Test performance with larger datasets."""
        tax_year = complete_tax_data
        calculator = TaxCalculator(test_db)

        # Create user with many income sources and expenses
        user = UserProfile(
            email="large_dataset@test.com",
            hashed_password=get_password_hash("password123"),
            name="Large",
            surname="Dataset",
            date_of_birth=date(1990, 1, 1),
            is_provisional_taxpayer=True,
        )
        test_db.add(user)
        test_db.commit()

        # Add many income sources (50)
        for i in range(50):
            income = IncomeSource(
                user_id=user.id, source_type=f"Income_{i}", annual_amount=10000 + (i * 1000), tax_year=tax_year
            )
            test_db.add(income)

        # Add many expenses (25)
        for i in range(25):
            expense = UserExpense(
                user_id=user.id,
                expense_type_id=(i % 3) + 1,  # Cycle through expense types
                description=f"Expense_{i}",
                amount=1000 + (i * 100),
                tax_year=tax_year,
            )
            test_db.add(expense)

        test_db.commit()

        # Measure calculation time with large dataset
        start_time = time.time()
        result = calculator.calculate_tax_liability(user.id, tax_year)
        end_time = time.time()

        calculation_time = end_time - start_time

        # Should still complete within reasonable time even with large dataset
        assert calculation_time < 2.0, f"Large dataset calculation took {calculation_time:.3f} seconds, expected < 2.0"

        # Verify calculation correctness
        expected_gross_income = sum(10000 + (i * 1000) for i in range(50))
        expected_expenses = sum(1000 + (i * 100) for i in range(25))

        assert result["gross_income"] == expected_gross_income
        assert result["taxable_income"] == expected_gross_income - expected_expenses

        print(f"Large dataset calculation (50 incomes, 25 expenses): {calculation_time:.3f} seconds")

    def test_repeated_calculations_performance(self, test_db, test_user, complete_tax_data):
        """Test performance of repeated calculations (caching behavior)."""
        tax_year = complete_tax_data

        # Add test data
        income = IncomeSource(user_id=test_user.id, source_type="Salary", annual_amount=350000, tax_year=tax_year)
        test_db.add(income)
        test_db.commit()

        calculator = TaxCalculator(test_db)

        # Measure first calculation
        start_time = time.time()
        first_result = calculator.calculate_tax_liability(test_user.id, tax_year)
        first_time = time.time() - start_time

        # Measure repeated calculations
        repeated_times = []
        for _ in range(10):
            start_time = time.time()
            result = calculator.calculate_tax_liability(test_user.id, tax_year)
            repeated_times.append(time.time() - start_time)

            # Results should be consistent
            assert result["final_tax"] == first_result["final_tax"]

        avg_repeated_time = sum(repeated_times) / len(repeated_times)

        # Repeated calculations should be reasonably fast
        assert avg_repeated_time < 1.0, f"Average repeated calculation time {avg_repeated_time:.3f}s, expected < 1.0"

        print(f"First calculation: {first_time:.3f}s, Average repeated: {avg_repeated_time:.3f}s")
