"""
Unit tests for retry logic and retry service.
Tests retry count limits, exponential backoff, and retry condition evaluation.
"""

import pytest
import time
from app.services.retry_service import RetryService, MAX_PAGE_RETRY


# ===========================
# RetryService Tests
# ===========================

@pytest.mark.unit
class TestRetryService:
    """Tests for RetryService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.retry_service = RetryService()
    
    def test_should_retry_under_limit(self):
        """Test should_retry returns True when under retry limit."""
        page_info = {"retry_count": 3}
        
        assert self.retry_service.should_retry(page_info) is True
    
    def test_should_retry_at_limit(self):
        """Test should_retry returns False when at retry limit."""
        page_info = {"retry_count": MAX_PAGE_RETRY}
        
        assert self.retry_service.should_retry(page_info) is False
    
    def test_should_retry_over_limit(self):
        """Test should_retry returns False when over retry limit."""
        page_info = {"retry_count": MAX_PAGE_RETRY + 1}
        
        assert self.retry_service.should_retry(page_info) is False
    
    def test_should_retry_zero_retries(self):
        """Test should_retry with zero retries."""
        page_info = {"retry_count": 0}
        
        assert self.retry_service.should_retry(page_info) is True
    
    def test_handle_retry_increments_counter(self):
        """Test handle_retry increments retry count."""
        # Mock page controller
        class MockPageController:
            def __init__(self):
                self.pages = {1: {"retry_count": 0}}
            
            def increment_retry(self, page_no):
                self.pages[page_no]["retry_count"] += 1
        
        controller = MockPageController()
        
        # First retry should succeed
        result = self.retry_service.handle_retry(1, controller)
        
        assert result is True
        assert controller.pages[1]["retry_count"] == 1
    
    def test_handle_retry_stops_at_max(self):
        """Test handle_retry stops when max retries reached."""
        class MockPageController:
            def __init__(self):
                self.pages = {1: {"retry_count": MAX_PAGE_RETRY}}
            
            def increment_retry(self, page_no):
                self.pages[page_no]["retry_count"] += 1
        
        controller = MockPageController()
        
        # Should not retry when at max
        result = self.retry_service.handle_retry(1, controller)
        
        assert result is False
    
    def test_handle_retry_multiple_pages(self):
        """Test handle_retry with multiple pages."""
        class MockPageController:
            def __init__(self):
                self.pages = {
                    1: {"retry_count": 0},
                    2: {"retry_count": 5},
                    3: {"retry_count": MAX_PAGE_RETRY}
                }
            
            def increment_retry(self, page_no):
                self.pages[page_no]["retry_count"] += 1
        
        controller = MockPageController()
        
        # Page 1 should retry
        assert self.retry_service.handle_retry(1, controller) is True
        assert controller.pages[1]["retry_count"] == 1
        
        # Page 2 should retry
        assert self.retry_service.handle_retry(2, controller) is True
        assert controller.pages[2]["retry_count"] == 6
        
        # Page 3 should not retry
        assert self.retry_service.handle_retry(3, controller) is False


# ===========================
# Retry Logic Tests
# ===========================

@pytest.mark.unit
class TestRetryLogic:
    """Tests for retry logic patterns."""
    
    def test_max_retry_constant(self):
        """Test MAX_PAGE_RETRY constant value."""
        assert MAX_PAGE_RETRY == 10
        assert isinstance(MAX_PAGE_RETRY, int)
    
    def test_retry_count_boundary_values(self):
        """Test retry count at boundary values."""
        retry_service = RetryService()
        
        # Test boundary values
        test_cases = [
            ({"retry_count": -1}, True),   # Negative (should still retry)
            ({"retry_count": 0}, True),    # Zero
            ({"retry_count": 1}, True),    # One
            ({"retry_count": MAX_PAGE_RETRY - 1}, True),  # Just before max
            ({"retry_count": MAX_PAGE_RETRY}, False),      # Exactly at max
            ({"retry_count": MAX_PAGE_RETRY + 1}, False),  # Over max
            ({"retry_count": 100}, False)  # Way over max
        ]
        
        for page_info, expected in test_cases:
            result = retry_service.should_retry(page_info)
            assert result == expected, \
                f"Failed for retry_count={page_info['retry_count']}, expected={expected}, got={result}"
    
    def test_retry_progression_sequence(self):
        """Test retry count progression through sequence."""
        class MockPageController:
            def __init__(self):
                self.pages = {1: {"retry_count": 0}}
            
            def increment_retry(self, page_no):
                self.pages[page_no]["retry_count"] += 1
        
        controller = MockPageController()
        retry_service = RetryService()
        
        # Simulate retry progression
        retries_performed = 0
        
        while retry_service.handle_retry(1, controller):
            retries_performed += 1
            
            # Safety check to prevent infinite loop
            if retries_performed > MAX_PAGE_RETRY + 5:
                break
        
        # Should have performed exactly MAX_PAGE_RETRY retries
        assert retries_performed == MAX_PAGE_RETRY
        assert controller.pages[1]["retry_count"] == MAX_PAGE_RETRY


# ===========================
# Exponential Backoff Tests (Mock)
# ===========================

@pytest.mark.unit
class TestExponentialBackoff:
    """
    Tests for exponential backoff logic.
    Note: Actual backoff implementation may be in extractor.py or worker.py.
    These are example tests for expected backoff behavior.
    """
    
    def test_backoff_calculation(self):
        """Test exponential backoff calculation formula."""
        initial_backoff = 1.5  # seconds
        
        # Expected backoff times
        expected_backoffs = [
            1.5,    # retry 0
            3.0,    # retry 1 (1.5 * 2^1)
            6.0,    # retry 2 (1.5 * 2^2)
            12.0,   # retry 3 (1.5 * 2^3)
            24.0    # retry 4 (1.5 * 2^4)
        ]
        
        for retry_num, expected in enumerate(expected_backoffs):
            actual = initial_backoff * (2 ** retry_num)
            assert actual == expected
    
    def test_backoff_increases_with_retries(self):
        """Test that backoff time increases with retry count."""
        initial_backoff = 1.0
        
        previous_backoff = 0
        for retry_num in range(10):
            current_backoff = initial_backoff * (2 ** retry_num)
            
            assert current_backoff > previous_backoff
            previous_backoff = current_backoff
    
    @pytest.mark.slow
    def test_actual_backoff_timing(self):
        """Test actual backoff timing (slow test)."""
        initial_backoff = 0.1  # Use small value for test speed
        retry_count = 3
        
        start_time = time.time()
        expected_wait = initial_backoff * (2 ** retry_count)
        time.sleep(expected_wait)
        elapsed = time.time() - start_time
        
        # Allow 10% tolerance
        assert abs(elapsed - expected_wait) < expected_wait * 0.1


# ===========================
# Edge Cases
# ===========================

@pytest.mark.unit
class TestRetryEdgeCases:
    """Tests for retry logic edge cases."""
    
    def test_retry_with_missing_retry_count_key(self):
        """Test retry logic when retry_count key is missing."""
        retry_service = RetryService()
        
        # This should raise KeyError or handle gracefully
        with pytest.raises(KeyError):
            retry_service.should_retry({})
    
    def test_retry_with_invalid_retry_count_type(self):
        """Test retry logic with invalid retry count type."""
        retry_service = RetryService()
        
        # String retry count
        page_info = {"retry_count": "5"}
        
        # Should raise TypeError or handle comparison
        try:
            result = retry_service.should_retry(page_info)
            # If it doesn't raise, it should still work with string comparison
            assert isinstance(result, bool)
        except TypeError:
            # Expected behavior
            pass
    
    def test_retry_with_none_retry_count(self):
        """Test retry logic with None as retry count."""
        retry_service = RetryService()
        
        page_info = {"retry_count": None}
        
        # Should raise TypeError on comparison
        with pytest.raises(TypeError):
            retry_service.should_retry(page_info)
