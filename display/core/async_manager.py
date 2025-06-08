"""
Asynchronous operations management for the display system.
"""
import asyncio
import logging
import time
import traceback
import weakref
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Coroutine

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class AsyncWorkerError(Exception):
    """Custom exception for async worker errors."""
    pass


class AsyncWorker(QObject):
    """Handles asynchronous operations using the shared event loop."""
    
    finished = pyqtSignal(object)
    error = pyqtSignal(dict)
    
    def __init__(self, coro: Coroutine, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._coro = coro
        self._task = None
        
    def start(self) -> None:
        """Start the coroutine using the shared event loop."""
        try:
            # Get the current event loop (should be the qasync loop)
            loop = asyncio.get_event_loop()
            
            # Create a task and add done callback
            self._task = loop.create_task(self._execute())
        except Exception as e:
            self.error.emit({
                'error': str(e),
                'traceback': traceback.format_exc(),
                'context': {'coroutine': str(self._coro)}
            })
    
    async def _execute(self):
        """Execute the coroutine and handle result/errors."""
        try:
            result = await self._coro
            self.finished.emit(result)
        except asyncio.CancelledError:
            self.error.emit({
                'error': 'Operation cancelled',
                'context': {'coroutine': str(self._coro)}
            })
        except Exception as e:
            self.error.emit({
                'error': str(e),
                'traceback': traceback.format_exc(),
                'context': {'coroutine': str(self._coro)}
            })
    
    def cancel(self):
        """Cancel the task if it's running."""
        if self._task and not self._task.done():
            self._task.cancel()


class AsyncHelper:
    """Manages asynchronous operations using qasync."""

    def __init__(self, parent: QObject):
        self.parent = parent
        self._workers = []
        self._shutdown = False
        self._task_timeout = 300  # 5 minutes default timeout for tasks

    def run_coroutine(self, coro: Coroutine, callback: Optional[Callable] = None) -> None:
        """Run a coroutine using the shared event loop."""
        if self._shutdown:
            logger.warning("AsyncHelper is shutting down, rejecting new coroutine")
            return
            
        # Create worker without timeout wrapper to avoid reentrancy
        worker = AsyncWorker(coro, self.parent)
        
        # Connect signals
        if callback:
            worker.finished.connect(callback)
        worker.error.connect(self._handle_worker_error)
        
        # Track worker and start it
        self._workers.append(worker)
        worker.finished.connect(lambda _: self._cleanup_worker(worker))
        worker.error.connect(lambda _: self._cleanup_worker(worker))
        
        # Start the worker
        worker.start()

    def _handle_worker_error(self, error_info: Dict[str, Any]) -> None:
        """Handle worker errors."""
        self.parent._handle_error(
            "Async execution error",
            {"error": error_info, "source": "async_helper"}
        )
    
    def _cleanup_worker(self, worker: AsyncWorker) -> None:
        """Remove finished worker from tracking."""
        if worker in self._workers:
            self._workers.remove(worker)

    def stop_all(self) -> None:
        """Stop all running workers and wait for completion."""
        logger.info(f"AsyncHelper stopping {len(self._workers)} workers")
        self._shutdown = True
        
        # Create a copy of workers to avoid modification during iteration
        workers = self._workers.copy()
        
        # Cancel all workers
        for worker in workers:
            try:
                worker.cancel()
            except Exception as e:
                logger.warning(f"Error cancelling worker: {e}")
        
        # Wait for all workers to complete (with timeout)
        start_time = datetime.now()
        timeout = timedelta(seconds=5)
        
        while self._workers and datetime.now() - start_time < timeout:
            try:
                QApplication.processEvents()  # Allow Qt events to process
                time.sleep(0.05)  # Shorter sleep for better responsiveness
            except Exception as e:
                logger.warning(f"Error during worker shutdown processing: {e}")
                break
        
        # Force clear any remaining workers
        if self._workers:
            logger.warning(f"Forced clearing of {len(self._workers)} workers that didn't stop cleanly")
            # Try to disconnect signals to prevent issues
            for worker in self._workers:
                try:
                    worker.finished.disconnect()
                    worker.error.disconnect()
                except Exception:
                    pass  # Ignore disconnect errors
            self._workers.clear()
        
        logger.info("AsyncHelper shutdown complete")