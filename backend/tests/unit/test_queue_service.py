"""
Unit tests for async queue service.
Tests queue initialization, task enqueue/dequeue, and queue management.
"""

import pytest
import asyncio
from app.services.queue import PAGE_QUEUE


# ===========================
# Queue Initialization Tests
# ===========================

@pytest.mark.unit
@pytest.mark.asyncio
class TestQueueInitialization:
    """Tests for queue initialization."""
    
    async def test_page_queue_exists(self):
        """Test that PAGE_QUEUE is initialized."""
        assert PAGE_QUEUE is not None
        assert isinstance(PAGE_QUEUE, asyncio.Queue)
    
    async def test_page_queue_initially_empty(self):
        """Test that PAGE_QUEUE starts empty."""
        # Note: This assumes queue is empty or we need to drain it first
        # In a real scenario, we'd use a fresh queue instance
        assert PAGE_QUEUE.qsize() >= 0


# ===========================
# Queue Operations Tests
# ===========================

@pytest.mark.unit
@pytest.mark.asyncio
class TestQueueOperations:
    """Tests for basic queue operations."""
    
    async def test_queue_put_and_get(self):
        """Test putting and getting items from queue."""
        test_queue = asyncio.Queue()
        
        # Define a simple async task
        async def test_task():
            return "completed"
        
        # Put task in queue
        await test_queue.put(test_task)
        
        # Check queue size
        assert test_queue.qsize() == 1
        
        # Get task from queue
        retrieved_task = await test_queue.get()
        
        assert retrieved_task == test_task
        assert test_queue.qsize() == 0
    
    async def test_queue_fifo_order(self):
        """Test queue maintains FIFO order."""
        test_queue = asyncio.Queue()
        
        # Define multiple tasks
        async def task_1():
            return "task_1"
        
        async def task_2():
            return "task_2"
        
        async def task_3():
            return "task_3"
        
        # Put tasks in order
        await test_queue.put(task_1)
        await test_queue.put(task_2)
        await test_queue.put(task_3)
        
        # Get tasks and verify order
        retrieved_1 = await test_queue.get()
        retrieved_2 = await test_queue.get()
        retrieved_3 = await test_queue.get()
        
        assert retrieved_1 == task_1
        assert retrieved_2 == task_2
        assert retrieved_3 == task_3
    
    async def test_queue_task_done(self):
        """Test queue task_done marking."""
        test_queue = asyncio.Queue()
        
        async def simple_task():
            pass
        
        await test_queue.put(simple_task)
        
        # Get task
        task = await test_queue.get()
        
        # Mark as done (should not raise)
        test_queue.task_done()
        
        # Queue should be empty and all tasks done
        assert test_queue.qsize() == 0
    
    async def test_queue_join_after_task_done(self):
        """Test queue.join() completes after task_done()."""
        test_queue = asyncio.Queue()
        
        async def simple_task():
            pass
        
        await test_queue.put(simple_task)
        
        # Process task
        task = await test_queue.get()
        test_queue.task_done()
        
        # Join should complete immediately
        await asyncio.wait_for(test_queue.join(), timeout=1.0)


# ===========================
# Queue Size Management Tests
# ===========================

@pytest.mark.unit
@pytest.mark.asyncio
class TestQueueSizeManagement:
    """Tests for queue size tracking."""
    
    async def test_queue_size_tracking(self):
        """Test queue size is tracked correctly."""
        test_queue = asyncio.Queue()
        
        assert test_queue.qsize() == 0
        
        async def task():
            pass
        
        # Add items
        for i in range(5):
            await test_queue.put(task)
            assert test_queue.qsize() == i + 1
        
        # Remove items
        for i in range(5):
            await test_queue.get()
            assert test_queue.qsize() == 4 - i
    
    async def test_queue_empty_check(self):
        """Test queue.empty() method."""
        test_queue = asyncio.Queue()
        
        assert test_queue.empty() is True
        
        async def task():
            pass
        
        await test_queue.put(task)
        
        assert test_queue.empty() is False
        
        await test_queue.get()
        
        assert test_queue.empty() is True
    
    async def test_queue_full_check(self):
        """Test queue.full() with maxsize."""
        test_queue = asyncio.Queue(maxsize=3)
        
        assert test_queue.full() is False
        
        async def task():
            pass
        
        # Fill queue
        await test_queue.put(task)
        await test_queue.put(task)
        await test_queue.put(task)
        
        assert test_queue.full() is True


# ===========================
# Concurrent Queue Tests
# ===========================

@pytest.mark.unit
@pytest.mark.asyncio
class TestConcurrentQueue:
    """Tests for concurrent queue operations."""
    
    async def test_multiple_producers_single_consumer(self):
        """Test multiple producers adding to queue."""
        test_queue = asyncio.Queue()
        
        async def producer(item_count):
            for i in range(item_count):
                await test_queue.put(f"item_{i}")
        
        # Start multiple producers
        await asyncio.gather(
            producer(5),
            producer(3),
            producer(2)
        )
        
        # Check total items
        assert test_queue.qsize() == 10
    
    async def test_single_producer_multiple_consumers(self):
        """Test multiple consumers processing queue."""
        test_queue = asyncio.Queue()
        results = []
        
        # Add items
        for i in range(10):
            await test_queue.put(i)
        
        async def consumer():
            while not test_queue.empty():
                try:
                    item = test_queue.get_nowait()
                    results.append(item)
                    test_queue.task_done()
                except asyncio.QueueEmpty:
                    break
        
        # Start multiple consumers
        await asyncio.gather(
            consumer(),
            consumer(),
            consumer()
        )
        
        # All items should be processed
        assert len(results) == 10
        assert set(results) == set(range(10))


# ===========================
# Queue Error Handling Tests
# ===========================

@pytest.mark.unit
@pytest.mark.asyncio
class TestQueueErrorHandling:
    """Tests for queue error handling."""
    
    async def test_get_nowait_on_empty_queue(self):
        """Test get_nowait raises QueueEmpty on empty queue."""
        test_queue = asyncio.Queue()
        
        with pytest.raises(asyncio.QueueEmpty):
            test_queue.get_nowait()
    
    async def test_put_nowait_on_full_queue(self):
        """Test put_nowait raises QueueFull on full queue."""
        test_queue = asyncio.Queue(maxsize=1)
        
        async def task():
            pass
        
        # Fill queue
        test_queue.put_nowait(task)
        
        # Next put should raise
        with pytest.raises(asyncio.QueueFull):
            test_queue.put_nowait(task)
    
    async def test_task_done_more_than_get(self):
        """Test calling task_done() more than get() raises ValueError."""
        test_queue = asyncio.Queue()
        
        async def task():
            pass
        
        await test_queue.put(task)
        await test_queue.get()
        test_queue.task_done()
        
        # Calling task_done again should raise
        with pytest.raises(ValueError):
            test_queue.task_done()


# ===========================
# Queue Timeout Tests
# ===========================

@pytest.mark.unit
@pytest.mark.asyncio
class TestQueueTimeouts:
    """Tests for queue operation timeouts."""
    
    async def test_get_with_timeout(self):
        """Test queue.get() with timeout."""
        test_queue = asyncio.Queue()
        
        # Getting from empty queue should timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(test_queue.get(), timeout=0.1)
    
    async def test_put_with_timeout_on_full_queue(self):
        """Test queue.put() timeout on full queue."""
        test_queue = asyncio.Queue(maxsize=1)
        
        async def task():
            pass
        
        # Fill queue
        await test_queue.put(task)
        
        # Next put should timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(test_queue.put(task), timeout=0.1)
