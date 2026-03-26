"""
Locust load testing configuration for OCR API.
Simulates concurrent users uploading documents and triggering extraction.
"""

from locust import HttpUser, task, between, events
import io
import time
import random


# ===========================
# User Behavior Definition
# ===========================

class OCRUser(HttpUser):
    """
    Simulates a user interacting with the OCR API.
    Performs the complete workflow: create request -> upload -> extract -> check status.
    """
    
    # Wait time between tasks (1-3 seconds)
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a simulated user starts."""
        self.request_id = None
        self.test_file_content = b"Test PDF content for load testing"
    
    @task(3)
    def create_and_upload_workflow(self):
        """
        Complete workflow: create request and upload document.
        Weight: 3 (most common task)
        """
        # Step 1: Create request
        with self.client.post(
            "/api/v1/requests",
            catch_response=True,
            name="Create Request"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.request_id = data.get("requestId")
                response.success()
            else:
                response.failure(f"Failed to create request: {response.status_code}")
                return
        
        # Step 2: Upload document
        if self.request_id:
            files = {
                "file": ("test_invoice.pdf", io.BytesIO(self.test_file_content), "application/pdf")
            }
            
            with self.client.post(
                f"/api/v1/requests/{self.request_id}/documents",
                files=files,
                catch_response=True,
                name="Upload Document"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed to upload: {response.status_code}")
    
    @task(2)
    def trigger_extraction(self):
        """
        Trigger extraction on uploaded document.
        Weight: 2
        """
        if not self.request_id:
            return
        
        with self.client.post(
            f"/api/v1/requests/{self.request_id}/extract",
            catch_response=True,
            name="Trigger Extraction"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to extract: {response.status_code}")
    
    @task(5)
    def check_status(self):
        """
        Check extraction status.
        Weight: 5 (users check status frequently)
        """
        if not self.request_id:
            # Create a request first
            response = self.client.post("/api/v1/requests")
            if response.status_code == 200:
                self.request_id = response.json().get("requestId")
        
        if self.request_id:
            with self.client.get(
                f"/api/v1/requests/{self.request_id}/status",
                catch_response=True,
                name="Check Status"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed to check status: {response.status_code}")
    
    @task(1)
    def download_result(self):
        """
        Attempt to download extraction result.
        Weight: 1 (less common, only when processing is done)
        """
        if not self.request_id:
            return
        
        with self.client.get(
            f"/api/v1/requests/{self.request_id}/extracted-data/download",
            catch_response=True,
            name="Download Result"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Not ready yet, mark as success (expected)
                response.success()
            else:
                response.failure(f"Unexpected response: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """
        Periodic health check.
        Weight: 1
        """
        with self.client.get(
            "/health",
            catch_response=True,
            name="Health Check"
        ) as response:
            if response.status_code == 200 and response.json().get("status") == "ok":
                response.success()
            else:
                response.failure("Health check failed")


# ===========================
# Complete End-to-End User
# ===========================

class EndToEndOCRUser(HttpUser):
    """
    User that performs complete end-to-end OCR workflow in sequence.
    """
    
    wait_time = between(2, 5)
    
    @task
    def complete_ocr_workflow(self):
        """Execute complete OCR workflow from start to finish."""
        
        # 1. Create request
        response = self.client.post("/api/v1/requests", name="E2E: Create")
        if response.status_code != 200:
            return
        
        request_id = response.json().get("requestId")
        
        # 2. Upload document
        files = {
            "file": ("invoice.pdf", io.BytesIO(b"Test content"), "application/pdf")
        }
        response = self.client.post(
            f"/api/v1/requests/{request_id}/documents",
            files=files,
            name="E2E: Upload"
        )
        if response.status_code != 200:
            return
        
        # 3. Trigger extraction
        response = self.client.post(
            f"/api/v1/requests/{request_id}/extract",
            name="E2E: Extract"
        )
        if response.status_code != 200:
            return
        
        # 4. Poll status until completed (max 10 times)
        for i in range(10):
            time.sleep(1)
            response = self.client.get(
                f"/api/v1/requests/{request_id}/status",
                name="E2E: Status Poll"
            )
            
            if response.status_code == 200:
                status = response.json().get("status")
                if status in ["COMPLETED", "FAILED"]:
                    break
        
        # 5. Download result
        self.client.get(
            f"/api/v1/requests/{request_id}/extracted-data/download",
            name="E2E: Download"
        )


# ===========================
# Stress Test User
# ===========================

class StressTestUser(HttpUser):
    """
    Aggressive user pattern for stress testing.
    Creates many concurrent requests rapidly.
    """
    
    wait_time = between(0.1, 0.5)  # Very short wait time
    
    @task
    def rapid_request_creation(self):
        """Rapidly create requests."""
        self.client.post("/api/v1/requests", name="Stress: Create")
    
    @task
    def rapid_status_checks(self):
        """Rapidly check status of random request IDs."""
        request_id = f"req_stress_{random.randint(1, 1000)}"
        self.client.get(
            f"/api/v1/requests/{request_id}/status",
            name="Stress: Status"
        )


# ===========================
# Event Hooks for Custom Metrics
# ===========================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("\n=== OCR Load Test Started ===")
    print(f"Target host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*40 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("\n=== OCR Load Test Completed ===")
    stats = environment.stats
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Avg Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    print("="*40 + "\n")


# ===========================
# Usage Instructions
# ===========================

"""
How to run these load tests:

1. Basic load test (web UI):
   locust -f locustfile.py --host=http://localhost:8000

2. Headless mode (no web UI):
   locust -f locustfile.py --host=http://localhost:8000 --users=50 --spawn-rate=5 --run-time=60s --headless

3. Specific user class:
   locust -f locustfile.py --host=http://localhost:8000 --users=10 OCRUser

4. End-to-end workflow test:
   locust -f locustfile.py --host=http://localhost:8000 --users=5 EndToEndOCRUser --run-time=120s --headless

5. Stress test:
   locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10 StressTestUser --headless

6. View results:
   - Web UI: http://localhost:8089
   - CSV export: locust ... --csv=results
   - HTML report: locust ... --html=report.html

7. Recommended test scenarios:
   - Light load: 10 users, 2/sec spawn rate, 5 min duration
   - Medium load: 50 users, 5/sec spawn rate, 10 min duration
   - Heavy load: 100 users, 10/sec spawn rate, 15 min duration
   - Stress test: 200+ users, 20/sec spawn rate, 5 min duration
"""
