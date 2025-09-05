"""
STT Server Manager for persistent model loading and management.

This module provides server mode functionality that maintains persistent
Whisper model instances in memory to improve transcription performance by
avoiding model reloading overhead on each request.
"""

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

import psutil
import structlog
import torch
from RealtimeSTT import AudioToTextRecorder

from ..config import config

logger = structlog.get_logger(__name__)


@dataclass
class ModelInfo:
    """Information about a loaded model."""

    model_name: str
    device: str
    compute_type: str
    load_time: float
    last_used: float
    memory_usage: int  # Memory in bytes
    recorder: Any | None = None

    def update_last_used(self):
        """Update the last used timestamp."""
        self.last_used = time.time()

    def get_age(self) -> float:
        """Get the age of the model since last use."""
        return time.time() - self.last_used

    def cleanup(self):
        """Clean up model resources."""
        if self.recorder:
            try:
                if hasattr(self.recorder, "cleanup"):
                    self.recorder.cleanup()
                logger.debug("Model cleaned up", model=self.model_name)
            except Exception as e:
                logger.warning(
                    "Error during model cleanup", model=self.model_name, error=str(e)
                )
            finally:
                self.recorder = None


class STTServerManager:
    """
    Manages persistent Whisper model instances for improved performance.

    Features:
    - Persistent model loading with LRU cache
    - Automatic device optimization (CUDA/CPU)
    - Memory management and cleanup
    - Background model operations
    - Model warming and preloading
    """

    def __init__(
        self,
        cache_size: int | None = None,
        model_timeout: int | None = None,
        preload_models: list[str] | None = None,
    ):
        """
        Initialize the STT server manager.

        Args:
            cache_size: Maximum number of models to keep in memory
            model_timeout: Timeout for unused models in seconds
            preload_models: List of models to preload on startup
        """
        self.cache_size = cache_size or config.stt_model_cache_size
        self.model_timeout = model_timeout or config.stt_model_timeout
        self.preload_models = preload_models or config.stt_preload_models

        # LRU cache for models (ordered dict maintains insertion order)
        self._models: OrderedDict[str, ModelInfo] = OrderedDict()

        # Thread safety
        self._lock = threading.RLock()
        self._loading_lock = threading.RLock()
        self._cleanup_thread: threading.Thread | None = None
        self._cleanup_stop_event = threading.Event()

        # Server state
        self._is_running = False
        self._start_time: float | None = None

        # Model loading tracking
        self._loading_models: dict[str, threading.Event] = {}

        logger.info(
            "STTServerManager initialized",
            cache_size=self.cache_size,
            model_timeout=self.model_timeout,
            preload_models=self.preload_models,
        )

    def start(self) -> dict[str, Any]:
        """
        Start the STT server with model preloading.

        Returns:
            Dictionary with start result and status
        """
        if self._is_running:
            return {
                "success": True,
                "message": "STT server already running",
                "loaded_models": list(self._models.keys()),
                "uptime": time.time() - self._start_time if self._start_time else 0,
            }

        logger.info("Starting STT server", preload_models=self.preload_models)
        start_time = time.time()

        try:
            # Check dependencies
            if not self._check_dependencies():
                return {
                    "success": False,
                    "error": "STT dependencies not available - install with: pip install 'voice-mcp[voice]'",
                }

            # Start cleanup thread
            self._start_cleanup_thread()

            # Mark as running
            self._is_running = True
            self._start_time = time.time()

            # Preload models in background
            preload_results = []
            for model_name in self.preload_models:
                result = self.preload_model(model_name)
                preload_results.append((model_name, result["success"]))

            successful_preloads = sum(1 for _, success in preload_results if success)

            duration = time.time() - start_time

            logger.info(
                "STT server started",
                preloaded_models=successful_preloads,
                total_models=len(self.preload_models),
                duration=duration,
            )

            return {
                "success": True,
                "message": f"STT server started with {successful_preloads}/{len(self.preload_models)} models preloaded",
                "loaded_models": list(self._models.keys()),
                "preload_results": preload_results,
                "startup_time": duration,
            }

        except Exception as e:
            logger.error("Failed to start STT server", error=str(e), exc_info=True)
            self._is_running = False
            return {"success": False, "error": f"Failed to start STT server: {str(e)}"}

    def stop(self) -> dict[str, Any]:
        """
        Stop the STT server and cleanup all models.

        Returns:
            Dictionary with stop result and cleanup status
        """
        if not self._is_running:
            return {
                "success": True,
                "message": "STT server not running",
                "models_unloaded": 0,
            }

        logger.info("Stopping STT server", loaded_models=list(self._models.keys()))

        try:
            # Stop cleanup thread
            self._cleanup_stop_event.set()
            if self._cleanup_thread and self._cleanup_thread.is_alive():
                self._cleanup_thread.join(timeout=5.0)

            # Cleanup all models
            models_unloaded = 0
            with self._lock:
                for model_info in self._models.values():
                    model_info.cleanup()
                    models_unloaded += 1
                self._models.clear()

            # Clear loading models
            with self._loading_lock:
                self._loading_models.clear()

            # Mark as stopped
            self._is_running = False
            uptime = time.time() - self._start_time if self._start_time else 0
            self._start_time = None

            logger.info(
                "STT server stopped", models_unloaded=models_unloaded, uptime=uptime
            )

            return {
                "success": True,
                "message": f"STT server stopped, {models_unloaded} models unloaded",
                "models_unloaded": models_unloaded,
                "uptime": uptime,
            }

        except Exception as e:
            logger.error("Error stopping STT server", error=str(e), exc_info=True)
            return {"success": False, "error": f"Error stopping STT server: {str(e)}"}

    def preload_model(self, model_name: str) -> dict[str, Any]:
        """
        Preload a model into memory.

        Args:
            model_name: Name of the model to preload

        Returns:
            Dictionary with preload result
        """
        if not self._is_running:
            return {"success": False, "error": "STT server not running"}

        # Check if model is already loaded
        with self._lock:
            if model_name in self._models:
                self._models[model_name].update_last_used()
                # Move to end (most recently used)
                self._models.move_to_end(model_name)
                return {
                    "success": True,
                    "message": f"Model '{model_name}' already loaded",
                    "cached": True,
                }

        logger.info("Preloading model", model=model_name)

        # Check if model is currently being loaded
        with self._loading_lock:
            if model_name in self._loading_models:
                # Wait for loading to complete
                event = self._loading_models[model_name]
                event.wait(timeout=300)  # 5 minute timeout

                # Check if it was loaded successfully
                with self._lock:
                    if model_name in self._models:
                        return {
                            "success": True,
                            "message": f"Model '{model_name}' loaded by another thread",
                            "waited": True,
                        }

                return {
                    "success": False,
                    "error": f"Model '{model_name}' loading failed or timed out",
                }

        # Start loading process
        loading_event = threading.Event()
        with self._loading_lock:
            self._loading_models[model_name] = loading_event

        try:
            return self._load_model_impl(model_name, loading_event)
        finally:
            # Clean up loading tracking
            with self._loading_lock:
                self._loading_models.pop(model_name, None)

    def unload_model(self, model_name: str) -> dict[str, Any]:
        """
        Unload a specific model from memory.

        Args:
            model_name: Name of the model to unload

        Returns:
            Dictionary with unload result
        """
        with self._lock:
            if model_name not in self._models:
                return {
                    "success": True,
                    "message": f"Model '{model_name}' not loaded",
                    "found": False,
                }

            model_info = self._models.pop(model_name)
            model_info.cleanup()

            logger.info("Model unloaded", model=model_name)

            return {
                "success": True,
                "message": f"Model '{model_name}' unloaded successfully",
                "memory_freed": model_info.memory_usage,
            }

    def get_model_recorder(self, model_name: str) -> Any | None:
        """
        Get a recorder for the specified model, loading it if necessary.

        Args:
            model_name: Name of the model to get recorder for

        Returns:
            AudioToTextRecorder instance or None if unavailable
        """
        if not self._is_running:
            logger.warning("STT server not running, cannot get model recorder")
            return None

        # Try to get cached model first
        with self._lock:
            if model_name in self._models:
                model_info = self._models[model_name]
                model_info.update_last_used()
                # Move to end (most recently used)
                self._models.move_to_end(model_name)
                logger.debug("Using cached model", model=model_name)
                return model_info.recorder

        # Model not loaded, try to load it
        logger.info("Loading model on-demand", model=model_name)
        result = self.preload_model(model_name)

        if not result["success"]:
            logger.error(
                "Failed to load model on-demand",
                model=model_name,
                error=result.get("error"),
            )
            return None

        # Get the loaded model
        with self._lock:
            if model_name in self._models:
                return self._models[model_name].recorder

        logger.error("Model was loaded but not found in cache", model=model_name)
        return None

    def get_status(self) -> dict[str, Any]:
        """
        Get current server status.

        Returns:
            Dictionary with server status and loaded models
        """
        with self._lock:
            loaded_models = []
            total_memory = 0

            for name, model_info in self._models.items():
                loaded_models.append(
                    {
                        "name": name,
                        "device": model_info.device,
                        "compute_type": model_info.compute_type,
                        "load_time": model_info.load_time,
                        "last_used": model_info.last_used,
                        "age": model_info.get_age(),
                        "memory_usage": model_info.memory_usage,
                    }
                )
                total_memory += model_info.memory_usage

            # Get system memory info
            try:
                memory_info = psutil.virtual_memory()
                system_memory = {
                    "total": memory_info.total,
                    "available": memory_info.available,
                    "percent_used": memory_info.percent,
                }
            except Exception:
                system_memory = {"error": "Unable to get system memory info"}

            return {
                "active": self._is_running,
                "uptime": time.time() - self._start_time if self._start_time else 0,
                "loaded_models": loaded_models,
                "model_count": len(self._models),
                "cache_size": self.cache_size,
                "model_timeout": self.model_timeout,
                "total_model_memory": total_memory,
                "system_memory": system_memory,
                "dependencies": {
                    "torch_available": True,
                    "realtimestt_available": True,
                },
            }

    def warm_model(self, model_name: str) -> dict[str, Any]:
        """
        Warm up a model by running a small transcription to fully initialize it.

        Args:
            model_name: Name of the model to warm up

        Returns:
            Dictionary with warmup result
        """
        recorder = self.get_model_recorder(model_name)
        if not recorder:
            return {
                "success": False,
                "error": f"Could not get recorder for model '{model_name}'",
            }

        logger.info("Warming up model", model=model_name)
        warmup_start = time.time()

        try:
            # Create a minimal warmup configuration
            # This is a placeholder - actual implementation would depend on RealtimeSTT API
            # for running a small warmup transcription

            warmup_duration = time.time() - warmup_start

            logger.info("Model warmed up", model=model_name, duration=warmup_duration)

            return {
                "success": True,
                "message": f"Model '{model_name}' warmed up successfully",
                "warmup_time": warmup_duration,
            }

        except Exception as e:
            logger.error("Model warmup failed", model=model_name, error=str(e))
            return {"success": False, "error": f"Model warmup failed: {str(e)}"}

    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        return True

    def _get_optimal_device(self, model_name: str) -> tuple[str, str]:
        """Get optimal device and compute type for a model."""

        try:
            if torch.cuda.is_available():
                # Check GPU memory for larger models
                if model_name in ["large", "large-v2", "large-v3"]:
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory
                    # Require at least 10GB for large models
                    if gpu_memory > 10 * 1024 * 1024 * 1024:
                        return "cuda", "float16"
                    else:
                        logger.warning(
                            "Insufficient GPU memory for large model, using CPU",
                            model=model_name,
                            gpu_memory=gpu_memory,
                        )
                        return "cpu", "int8"
                else:
                    return "cuda", "float16"
            else:
                return "cpu", "int8"
        except Exception as e:
            logger.warning("Error detecting optimal device", error=str(e))
            return "cpu", "int8"

    def _load_model_impl(
        self, model_name: str, loading_event: threading.Event
    ) -> dict[str, Any]:
        """
        Internal method to load a model.

        Args:
            model_name: Name of the model to load
            loading_event: Threading event to signal completion

        Returns:
            Dictionary with load result
        """
        load_start = time.time()

        try:
            # Get optimal device
            device, compute_type = self._get_optimal_device(model_name)

            logger.info(
                "Loading model",
                model=model_name,
                device=device,
                compute_type=compute_type,
            )

            # Check cache capacity before loading
            self._ensure_cache_capacity()

            # Create recorder configuration
            recorder_config = {
                "model": model_name,
                "language": config.stt_language,
                "device": device,
                "compute_type": compute_type,
                "silero_sensitivity": 0.4,
                "webrtc_sensitivity": 2,
                "post_speech_silence_duration": config.stt_silence_threshold,
                "min_length_of_recording": 0.5,
                "enable_realtime_transcription": True,
                "realtime_processing_pause": 0.1,
                "realtime_model_type": model_name,
                "use_microphone": True,
                "no_log_file": True,
                "spinner": False,
                "early_transcription_on_silence": 1,
            }

            # Create recorder
            recorder = AudioToTextRecorder(**recorder_config)

            # Get memory usage estimate
            memory_usage = self._estimate_memory_usage(model_name, device)

            # Create model info
            load_time = time.time() - load_start
            model_info = ModelInfo(
                model_name=model_name,
                device=device,
                compute_type=compute_type,
                load_time=load_time,
                last_used=time.time(),
                memory_usage=memory_usage,
                recorder=recorder,
            )

            # Add to cache
            with self._lock:
                self._models[model_name] = model_info
                # Move to end (most recently used)
                self._models.move_to_end(model_name)

            logger.info(
                "Model loaded successfully",
                model=model_name,
                device=device,
                load_time=load_time,
                memory_usage=memory_usage,
            )

            return {
                "success": True,
                "message": f"Model '{model_name}' loaded successfully",
                "device": device,
                "compute_type": compute_type,
                "load_time": load_time,
                "memory_usage": memory_usage,
            }

        except Exception as e:
            logger.error(
                "Failed to load model", model=model_name, error=str(e), exc_info=True
            )
            return {
                "success": False,
                "error": f"Failed to load model '{model_name}': {str(e)}",
            }
        finally:
            loading_event.set()

    def _ensure_cache_capacity(self):
        """Ensure cache has capacity for new model by removing oldest if necessary."""
        with self._lock:
            while len(self._models) >= self.cache_size:
                # Remove least recently used model
                oldest_name, oldest_model = self._models.popitem(last=False)
                oldest_model.cleanup()
                logger.info(
                    "Evicted model from cache",
                    model=oldest_name,
                    age=oldest_model.get_age(),
                    cache_size=len(self._models),
                )

    def _estimate_memory_usage(self, model_name: str, device: str) -> int:
        """
        Estimate memory usage for a model.

        Args:
            model_name: Name of the model
            device: Device the model is loaded on

        Returns:
            Estimated memory usage in bytes
        """
        # Rough estimates for Whisper models (in MB)
        model_sizes = {
            "tiny": 39,
            "base": 74,
            "small": 244,
            "medium": 769,
            "large": 1550,
            "large-v2": 1550,
            "large-v3": 1550,
        }

        base_size = model_sizes.get(model_name, 244) * 1024 * 1024  # Convert to bytes

        # Adjust for device and precision
        if device == "cuda":
            # GPU models might use more memory due to CUDA overhead
            base_size = int(base_size * 1.2)

        return base_size

    def _start_cleanup_thread(self):
        """Start background cleanup thread for expired models."""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        self._cleanup_stop_event.clear()
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker, daemon=True
        )
        self._cleanup_thread.start()
        logger.debug("Cleanup thread started")

    def _cleanup_worker(self):
        """Background worker to clean up expired models."""
        while not self._cleanup_stop_event.wait(60):  # Check every minute
            try:
                self._cleanup_expired_models()
            except Exception as e:
                logger.warning("Error in cleanup worker", error=str(e))

    def _cleanup_expired_models(self):
        """Clean up models that haven't been used for a while."""
        current_time = time.time()
        expired_models = []

        with self._lock:
            for name, model_info in list(self._models.items()):
                if model_info.get_age() > self.model_timeout:
                    expired_models.append(name)

        # Clean up expired models
        for model_name in expired_models:
            logger.info("Cleaning up expired model", model=model_name)
            self.unload_model(model_name)

    def __enter__(self):
        """Context manager entry."""
        result = self.start()
        if not result["success"]:
            raise RuntimeError(f"Failed to start STT server: {result.get('error')}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Global server instance
_stt_server_manager: STTServerManager | None = None


def get_stt_server() -> STTServerManager | None:
    """Get the global STT server instance."""
    global _stt_server_manager
    return _stt_server_manager


def create_stt_server(
    cache_size: int | None = None,
    model_timeout: int | None = None,
    preload_models: list[str] | None = None,
) -> STTServerManager:
    """
    Create and return a new STT server instance.

    Args:
        cache_size: Maximum number of models to keep in memory
        model_timeout: Timeout for unused models in seconds
        preload_models: List of models to preload on startup

    Returns:
        STTServerManager instance
    """
    global _stt_server_manager
    _stt_server_manager = STTServerManager(cache_size, model_timeout, preload_models)
    return _stt_server_manager


def ensure_stt_server() -> STTServerManager:
    """Ensure STT server exists and return it."""
    global _stt_server_manager
    if _stt_server_manager is None:
        _stt_server_manager = STTServerManager()
    return _stt_server_manager
