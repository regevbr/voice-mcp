"""
Background loading state management for voice MCP components.

This module provides thread-safe coordination of background preloading
for TTS, STT, and hotkey components to enable fast server startup.
"""

import threading
import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum
from typing import Any, Optional

import structlog

from .config import config

logger = structlog.get_logger(__name__)


class ComponentStatus(Enum):
    """Status of a component's loading state."""

    NOT_STARTED = "not_started"
    LOADING = "loading"
    READY = "ready"
    FAILED = "failed"


class ComponentType(Enum):
    """Types of components that can be preloaded."""

    TTS = "tts"
    STT = "stt"
    HOTKEY = "hotkey"


class LoadingStateManager:
    """Thread-safe manager for background component loading."""

    _instance: Optional["LoadingStateManager"] = None
    _lock = threading.RLock()

    def __new__(cls) -> "LoadingStateManager":
        """Ensure singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        """Initialize the loading state manager (called only once due to singleton)."""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._status_lock = threading.RLock()
        self._component_status: dict[ComponentType, ComponentStatus] = {
            ComponentType.TTS: ComponentStatus.NOT_STARTED,
            ComponentType.STT: ComponentStatus.NOT_STARTED,
            ComponentType.HOTKEY: ComponentStatus.NOT_STARTED,
        }
        self._component_errors: dict[ComponentType, str] = {}
        self._loading_futures: dict[ComponentType, Future] = {}
        self._executor: ThreadPoolExecutor | None = None

        logger.info("LoadingStateManager initialized")

    def start_background_loading(self) -> None:
        """Start background loading of all enabled components."""
        with self._status_lock:
            if self._executor is not None:
                logger.debug("Background loading already started")
                return

            self._executor = ThreadPoolExecutor(
                max_workers=3, thread_name_prefix="voice-preload"
            )

            logger.info("Starting background preloading of voice components")

            # Start TTS preloading if enabled
            if config.tts_preload_enabled:
                self._start_component_loading(ComponentType.TTS, self._load_tts)

            # Start STT preloading if enabled
            if config.stt_enabled:
                self._start_component_loading(ComponentType.STT, self._load_stt)

            # Start hotkey preloading if enabled
            if config.enable_hotkey:
                self._start_component_loading(ComponentType.HOTKEY, self._load_hotkey)

    def _start_component_loading(
        self, component: ComponentType, loader_func: Callable
    ) -> None:
        """Start loading a specific component in background."""
        with self._status_lock:
            if self._component_status[component] != ComponentStatus.NOT_STARTED:
                return

            self._component_status[component] = ComponentStatus.LOADING
            logger.info(f"Starting background loading of {component.value}")

            if self._executor is None:
                logger.error("Executor not initialized")
                self._component_status[component] = ComponentStatus.FAILED
                self._component_errors[component] = "Executor not initialized"
                return

            future = self._executor.submit(
                self._load_component_safely, component, loader_func
            )
            self._loading_futures[component] = future

    def _load_component_safely(
        self, component: ComponentType, loader_func: Callable
    ) -> None:
        """Safely load a component with error handling."""
        try:
            start_time = time.time()
            logger.debug(f"Loading {component.value} component")

            success = loader_func()

            duration = time.time() - start_time
            with self._status_lock:
                if success:
                    self._component_status[component] = ComponentStatus.READY
                    logger.info(
                        f"{component.value} preloading completed successfully",
                        duration=duration,
                    )
                else:
                    self._component_status[component] = ComponentStatus.FAILED
                    error_msg = f"{component.value} preloading failed"
                    self._component_errors[component] = error_msg
                    logger.warning(error_msg, duration=duration)

        except Exception as e:
            duration = time.time() - start_time if "start_time" in locals() else 0
            error_msg = f"Error during {component.value} preloading: {str(e)}"
            with self._status_lock:
                self._component_status[component] = ComponentStatus.FAILED
                self._component_errors[component] = error_msg
            logger.error(error_msg, duration=duration, exc_info=True)

    def _load_tts(self) -> bool:
        """Load TTS component."""
        try:
            from .tools import get_tts_manager

            tts_manager = get_tts_manager()
            return tts_manager.is_available()
        except Exception as e:
            logger.error(f"TTS preloading failed: {e}")
            return False

    def _load_stt(self) -> bool:
        """Load STT component."""
        try:
            from .voice.stt import get_transcription_handler

            stt_handler = get_transcription_handler()
            return stt_handler.preload()
        except Exception as e:
            logger.error(f"STT preloading failed: {e}")
            return False

    def _load_hotkey(self) -> bool:
        """Load hotkey component."""
        try:
            from .tools import VoiceTools

            result = VoiceTools.start_hotkey_monitoring()
            # Check if result indicates success (contains ✅)
            return "✅" in result
        except Exception as e:
            logger.error(f"Hotkey preloading failed: {e}")
            return False

    def get_status(self, component: ComponentType) -> ComponentStatus:
        """Get current status of a component."""
        with self._status_lock:
            return self._component_status[component]

    def get_error(self, component: ComponentType) -> str | None:
        """Get error message for a component if it failed."""
        with self._status_lock:
            return self._component_errors.get(component)

    def is_ready(self, component: ComponentType) -> bool:
        """Check if a component is ready."""
        return self.get_status(component) == ComponentStatus.READY

    def is_loading(self, component: ComponentType) -> bool:
        """Check if a component is currently loading."""
        return self.get_status(component) == ComponentStatus.LOADING

    def wait_for_ready(self, component: ComponentType, timeout: float = 2.0) -> bool:
        """
        Wait for a component to be ready with timeout.

        Args:
            component: Component to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            True if component became ready, False if timeout or failed
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_status(component)
            if status == ComponentStatus.READY:
                return True
            elif status == ComponentStatus.FAILED:
                return False

            time.sleep(0.1)  # Check every 100ms

        return False

    def get_overall_status(self) -> dict[str, Any]:
        """Get comprehensive status of all components."""
        with self._status_lock:
            return {
                "tts": {
                    "status": self._component_status[ComponentType.TTS].value,
                    "error": self._component_errors.get(ComponentType.TTS),
                    "enabled": config.tts_preload_enabled,
                },
                "stt": {
                    "status": self._component_status[ComponentType.STT].value,
                    "error": self._component_errors.get(ComponentType.STT),
                    "enabled": config.stt_enabled,
                },
                "hotkey": {
                    "status": self._component_status[ComponentType.HOTKEY].value,
                    "error": self._component_errors.get(ComponentType.HOTKEY),
                    "enabled": config.enable_hotkey,
                },
            }

    def shutdown(self) -> None:
        """Shutdown the loading state manager and cleanup resources."""
        with self._status_lock:
            if self._executor is not None:
                logger.info("Shutting down background loading executor")

                # Cancel any pending futures
                for component, future in self._loading_futures.items():
                    if not future.done():
                        future.cancel()
                        logger.debug(f"Cancelled loading of {component.value}")

                # Shutdown executor
                self._executor.shutdown(wait=True)
                self._executor = None

                logger.info("Background loading executor shutdown complete")


# Global singleton instance
_loading_manager: LoadingStateManager | None = None


def get_loading_manager() -> LoadingStateManager:
    """Get the global loading state manager instance."""
    global _loading_manager
    if _loading_manager is None:
        _loading_manager = LoadingStateManager()
    return _loading_manager
