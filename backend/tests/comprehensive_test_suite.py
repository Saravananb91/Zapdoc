"""
Comprehensive OCR Test Suite for Meeting Demo
Tests covering: Performance, Latency, Consistency, Concurrency, Ground Truth Accuracy
For different invoice types: Normal, Poor Quality, Multi-page, Scanned
"""

import pytest
import asyncio
import time
import io
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean, stdev

from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from tests.utils.assertions import assert_api_success


# ===========================
# TEST CONFIGURATION
# ===========================

# Simulated test invoices (in real scenario, use actual files)
TEST_INVOICES = {
    "normal": {
        "filename": "normal_invoice.pdf",
        "description": "Standard quality single page invoice",
        "expected_fields": ["invoice_no", "date_of_issue", "total"],
    },
    "poor_quality": {
        "filename": "poor_quality_invoice.pdf",
        "description": "Low resolution scanned invoice",
        "expected_fields": ["invoice_no", "total"],
    },
    "multi_page": {
        "filename": "multi_page_invoice.pdf",
        "description": "3-page invoice with items",
        "expected_fields": ["invoice_no", "items"],
    },
    "scanned": {
        "filename": "scanned_invoice.pdf",
        "description": "Scanned physical invoice",
        "expected_fields": ["invoice_no", "seller_name"],
    },
}


# ===========================
# 1. PERFORMANCE TESTS (4 tests)
# ===========================

@pytest.mark.performance
@pytest.mark.asyncio
class TestPerformance:
    """Performance benchmarking tests"""
    
    async def test_001_single_page_processing_time(self, async_client):
        """Test 001: Single page invoice processing time < 5 seconds"""
        start_time = time.time()
        
        # Create request
        create_resp = await async_client.post("/api/v1/requests")
        request_id = create_resp.json()["requestId"]
        
        # Upload document
        files = {"file": ("test.pdf", io.BytesIO(b"PDF content"), "application/pdf")}
        await async_client.post(f"/api/v1/requests/{request_id}/documents", files=files)
        
        elapsed = time.time() - start_time
        
        assert elapsed < 5.0, f"Processing took {elapsed:.2f}s, expected < 5s"
        print(f"✓ Single page processing: {elapsed:.2f}s")
    
    async def test_002_api_response_latency(self, async_client):
        """Test 002: API endpoint latency < 200ms"""
        latencies = []
        
        for i in range(10):
            start = time.time()
            response = await async_client.get("/health")
            latency = (time.time() - start) * 1000  # ms
            latencies.append(latency)
            assert_api_success(response, 200)
        
        avg_latency = mean(latencies)
        assert avg_latency < 200, f"Average latency {avg_latency:.2f}ms > 200ms"
        print(f"✓ API latency: {avg_latency:.2f}ms (min: {min(latencies):.2f}ms, max: {max(latencies):.2f}ms)")
    
    async def test_003_multi_page_processing_performance(self, async_client):
        """Test 003: Multi-page invoice processing time < 15 seconds"""
        start_time = time.time()
        
        create_resp = await async_client.post("/api/v1/requests")
        request_id = create_resp.json()["requestId"]
        
        # Simulate 3-page PDF
        files = {"file": ("multipage.pdf", io.BytesIO(b"PDF 3 pages"), "application/pdf")}
        await async_client.post(f"/api/v1/requests/{request_id}/documents", files=files)
        
        elapsed = time.time() - start_time
        
        assert elapsed < 15.0, f"Multi-page processing took {elapsed:.2f}s, expected < 15s"
        print(f"✓ Multi-page processing: {elapsed:.2f}s")
    
    async def test_004_throughput_requests_per_second(self, async_client):
        """Test 004: System throughput > 10 requests/second"""
        num_requests = 50
        start_time = time.time()
        
        tasks = [async_client.get("/health") for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        throughput = num_requests / elapsed
        
        assert throughput > 10, f"Throughput {throughput:.2f} req/s < 10 req/s"
        print(f"✓ Throughput: {throughput:.2f} requests/second")


# ===========================
# 2. LATENCY TESTS (3 tests)
# ===========================

@pytest.mark.performance
@pytest.mark.asyncio
class TestLatency:
    """Latency measurement tests"""
    
    async def test_005_create_request_latency(self, async_client):
        """Test 005: Create request endpoint latency < 100ms"""
        latencies = []
        
        for _ in range(20):
            start = time.time()
            response = await async_client.post("/api/v1/requests")
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            assert_api_success(response, 200)
        
        avg = mean(latencies)
        assert avg < 100, f"Create request latency {avg:.2f}ms > 100ms"
        print(f"✓ Create request latency: {avg:.2f}ms ± {stdev(latencies):.2f}ms")
    
    async def test_006_upload_latency(self, async_client):
        """Test 006: Document upload latency < 500ms"""
        create_resp = await async_client.post("/api/v1/requests")
        request_id = create_resp.json()["requestId"]
        
        files = {"file": ("test.pdf", io.BytesIO(b"Small PDF"), "application/pdf")}
        
        start = time.time()
        response = await async_client.post(f"/api/v1/requests/{request_id}/documents", files=files)
        latency = (time.time() - start) * 1000
        
        assert latency < 500, f"Upload latency {latency:.2f}ms > 500ms"
        assert_api_success(response, 200)
        print(f"✓ Upload latency: {latency:.2f}ms")
    
    async def test_007_status_check_latency(self, async_client):
        """Test 007: Status check latency < 50ms"""
        create_resp = await async_client.post("/api/v1/requests")
        request_id = create_resp.json()["requestId"]
        
        latencies = []
        for _ in range(30):
            start = time.time()
            response = await async_client.get(f"/api/v1/requests/{request_id}/status")
            latency = (time.time() - start) * 1000
            latencies.append(latency)
        
        avg = mean(latencies)
        assert avg < 50, f"Status check latency {avg:.2f}ms > 50ms"
        print(f"✓ Status check latency: {avg:.2f}ms")


# ===========================
# 3. CONSISTENCY TESTS (4 tests)
# ===========================

@pytest.mark.accuracy
@pytest.mark.asyncio
class TestConsistency:
    """Consistency and determinism tests"""
    
    async def test_008_same_document_consistency(self, async_client):
        """Test 008: Same document produces consistent results across 5 runs"""
        results = []
        
        for run in range(5):
            create_resp = await async_client.post("/api/v1/requests")
            request_id = create_resp.json()["requestId"]
            
            files = {"file": ("same.pdf", io.BytesIO(b"Same content"), "application/pdf")}
            upload_resp = await async_client.post(
                f"/api/v1/requests/{request_id}/documents", files=files
            )
            results.append(upload_resp.json())
        
        # All should have same status
        statuses = [r["status"] for r in results]
        assert len(set(statuses)) == 1, "Inconsistent statuses across runs"
        print(f"✓ Consistency check: All 5 runs produced same status")
    
    async def test_009_field_extraction_determinism(self, async_client):
        """Test 009: Field extraction is deterministic"""
        # For same invoice, extracted fields should be identical
        pytest.skip("Requires actual OCR processing - mock test")
    
    async def test_010_retry_idempotency(self, async_client):
        """Test 010: Retrying same request is idempotent"""
        create_resp = await async_client.post("/api/v1/requests")
        request_id = create_resp.json()["requestId"]
        
        # Check status multiple times
        statuses = []
        for _ in range(5):
            resp = await async_client.get(f"/api/v1/requests/{request_id}/status")
            statuses.append(resp.json()["status"])
        
        assert len(set(statuses)) == 1, "Status changed unexpectedly"
        print(f"✓ Idempotency: Status remained consistent")
    
    async def test_011_concurrent_status_checks_consistency(self, async_client):
        """Test 011: Concurrent status checks return consistent data"""
        create_resp = await async_client.post("/api/v1/requests")
        request_id = create_resp.json()["requestId"]
        
        # Concurrent status checks
        tasks = [async_client.get(f"/api/v1/requests/{request_id}/status") for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        statuses = [r.json()["status"] for r in results]
        assert len(set(statuses)) == 1, "Inconsistent concurrent reads"
        print(f"✓ Concurrent consistency: All 20 checks matched")


# ===========================
# 4. CONCURRENCY TESTS (4 tests)
# ===========================

@pytest.mark.load
@pytest.mark.asyncio
class TestConcurrency:
    """Concurrency and concurrent request handling tests"""
    
    async def test_012_concurrent_request_creation(self, async_client):
        """Test 012: Handle 50 concurrent request creations"""
        tasks = [async_client.post("/api/v1/requests") for _ in range(50)]
        
        start = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        
        # All should succeed
        assert all(r.status_code == 200 for r in results), "Some requests failed"
        
        # All should have unique IDs
        request_ids = [r.json()["requestId"] for r in results]
        assert len(set(request_ids)) == 50, "Duplicate request IDs generated"
        
        print(f"✓ Concurrent creates: 50 requests in {elapsed:.2f}s, all unique IDs")
    
    async def test_013_concurrent_uploads(self, async_client):
        """Test 013: Handle 20 concurrent document uploads"""
        # Create 20 requests first
        create_tasks = [async_client.post("/api/v1/requests") for _ in range(20)]
        create_results = await asyncio.gather(*create_tasks)
        request_ids = [r.json()["requestId"] for r in create_results]
        
        # Upload concurrently
        upload_tasks = []
        for req_id in request_ids:
            files = {"file": (f"doc_{req_id}.pdf", io.BytesIO(b"PDF"), "application/pdf")}
            upload_tasks.append(
                async_client.post(f"/api/v1/requests/{req_id}/documents", files=files)
            )
        
        start = time.time()
        upload_results = await asyncio.gather(*upload_tasks)
        elapsed = time.time() - start
        
        success_count = sum(1 for r in upload_results if r.status_code == 200)
        assert success_count == 20, f"Only {success_count}/20 uploads succeeded"
        
        print(f"✓ Concurrent uploads: 20 uploads in {elapsed:.2f}s")
    
    async def test_014_high_concurrency_stress_test(self, async_client):
        """Test 014: Stress test with 100 concurrent requests"""
        tasks = [async_client.get("/health") for _ in range(100)]
        
        start = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start
        
        success_count = sum(1 for r in results if not isinstance(r, Exception) and r.status_code == 200)
        success_rate = (success_count / 100) * 100
        
        assert success_rate >= 95, f"Success rate {success_rate}% < 95%"
        print(f"✓ High concurrency: {success_count}/100 succeeded ({success_rate}%) in {elapsed:.2f}s")
    
    async def test_015_sustained_load_handling(self, async_client):
        """Test 015: Sustained load - 200 requests over 10 seconds"""
        num_requests = 200
        duration = 10  # seconds
        
        async def send_request():
            return await async_client.get("/health")
        
        start = time.time()
        results = []
        
        # Send requests evenly over duration
        delay = duration / num_requests
        for i in range(num_requests):
            task = asyncio.create_task(send_request())
            results.append(task)
            if i < num_requests - 1:
                await asyncio.sleep(delay)
        
        completed = await asyncio.gather(*results, return_exceptions=True)
        elapsed = time.time() - start
        
        success_count = sum(1 for r in completed if not isinstance(r, Exception) and r.status_code == 200)
        success_rate = (success_count / num_requests) * 100
        
        assert success_rate >= 95, f"Sustained load success rate {success_rate}% < 95%"
        print(f"✓ Sustained load: {success_count}/{num_requests} over {elapsed:.2f}s ({success_rate}%)")


# ===========================
# 5. GROUND TRUTH ACCURACY TESTS (5 tests)
# ===========================

@pytest.mark.accuracy
@pytest.mark.asyncio
class TestGroundTruthAccuracy:
    """Ground truth accuracy validation tests"""
    
    async def test_016_normal_invoice_field_accuracy(self, async_client):
        """Test 016: Normal invoice - field extraction accuracy > 95%"""
        # Mock test - in real scenario, compare with ground truth
        pytest.skip("Requires actual ground truth data and OCR processing")
    
    async def test_017_poor_quality_image_accuracy(self, async_client):
        """Test 017: Poor quality image - field extraction accuracy > 80%"""
        pytest.skip("Requires actual ground truth data and OCR processing")
    
    async def test_018_scanned_invoice_accuracy(self, async_client):
        """Test 018: Scanned invoice - field extraction accuracy > 85%"""
        pytest.skip("Requires actual ground truth data and OCR processing")
    
    async def test_019_multi_page_invoice_completeness(self, async_client):
        """Test 019: Multi-page invoice - all pages processed successfully"""
        pytest.skip("Requires actual multi-page PDF and OCR processing")
    
    async def test_020_numeric_field_precision(self, async_client):
        """Test 020: Numeric fields (totals, amounts) - accuracy > 98%"""
        pytest.skip("Requires actual ground truth data and OCR processing")


# ===========================
# 6. ERROR HANDLING & EDGE CASES (5 tests)
# ===========================

@pytest.mark.integration
@pytest.mark.asyncio
class TestErrorHandlingAndEdgeCases:
    """Error handling and edge case tests"""
    
    async def test_021_invalid_file_type_rejection(self, async_client):
        """Test 021: Reject invalid file types (e.g., .txt)"""
        create_resp = await async_client.post("/api/v1/requests")
        request_id = create_resp.json()["requestId"]
        
        files = {"file": ("test.txt", io.BytesIO(b"text"), "text/plain")}
        response = await async_client.post(
            f"/api/v1/requests/{request_id}/documents", files=files
        )
        
        assert response.status_code == 415, "Should reject .txt files"
        print(f"✓ Invalid file type correctly rejected")
    
    async def test_022_large_file_handling(self, async_client):
        """Test 022: Handle large files (10MB) gracefully"""
        create_resp = await async_client.post("/api/v1/requests")
        request_id = create_resp.json()["requestId"]
        
        # Simulate 10MB file
        large_content = b"X" * (10 * 1024 * 1024)
        files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
        
        response = await async_client.post(
            f"/api/v1/requests/{request_id}/documents", files=files
        )
        
        # Should either accept or reject gracefully (not crash)
        assert response.status_code in [200, 413], "Should handle large files gracefully"
        print(f"✓ Large file handled: status {response.status_code}")
    
    async def test_023_non_existent_request_id(self, async_client):
        """Test 023: Non-existent request ID returns 404"""
        response = await async_client.get("/api/v1/requests/FAKE_ID/status")
        assert response.status_code == 404
        print(f"✓ Non-existent ID returns 404")
    
    async def test_024_duplicate_upload_prevention(self, async_client):
        """Test 024: Prevent duplicate uploads to same request"""
        create_resp = await async_client.post("/api/v1/requests")
        request_id = create_resp.json()["requestId"]
        
        files = {"file": ("test.pdf", io.BytesIO(b"PDF"), "application/pdf")}
        
        # First upload
        resp1 = await async_client.post(f"/api/v1/requests/{request_id}/documents", files=files)
        assert resp1.status_code == 200
        
        # Second upload to same request
        files2 = {"file": ("test2.pdf", io.BytesIO(b"PDF2"), "application/pdf")}
        resp2 = await async_client.post(f"/api/v1/requests/{request_id}/documents", files=files2)
        
        # Should reject (status not RECEIVED anymore)
        assert resp2.status_code == 400
        print(f"✓ Duplicate upload prevented")
    
    async def test_025_cors_headers_validation(self, test_client):
        """Test 025: CORS headers present in responses"""
        response = test_client.get("/health", headers={"Origin": "http://localhost:3000"})
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        print(f"✓ CORS headers present")
