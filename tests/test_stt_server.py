"""
Tests for STT server functionality.
"""

import threading
import time
from unittest.mock import Mock, patch

from voice_mcp.voice.stt_server import (
    ModelInfo,
    STTServerManager,
    create_stt_server,
    ensure_stt_server,
    get_stt_server,
)


class TestModelInfo:
    """Test suite for ModelInfo class."""

    def test_model_info_creation(self):
        """Test ModelInfo creation with basic properties."""
        load_time = time.time()
        model_info = ModelInfo(
            model_name="base",
            device="cuda",
            compute_type="float16",
            load_time=2.5,
            last_used=load_time,
            memory_usage=1024 * 1024 * 500,  # 500MB
        )

        assert model_info.model_name == "base"
        assert model_info.device == "cuda"
        assert model_info.compute_type == "float16"
        assert model_info.load_time == 2.5
        assert model_info.memory_usage == 1024 * 1024 * 500

    def test_update_last_used(self):
        """Test updating last used timestamp."""
        model_info = ModelInfo(
            model_name="base",
            device="cpu",
            compute_type="int8",
            load_time=1.0,
            last_used=100.0,
            memory_usage=1000,
        )

        original_time = model_info.last_used
        time.sleep(0.001)  # Small delay to ensure time difference

        model_info.update_last_used()

        assert model_info.last_used > original_time

    def test_get_age(self):
        """Test getting model age."""
        current_time = time.time()
        model_info = ModelInfo(
            model_name="base",
            device="cpu",
            compute_type="int8",
            load_time=1.0,
            last_used=current_time - 10.0,
            memory_usage=1000,
        )

        age = model_info.get_age()

        assert age >= 10.0
        assert age < 11.0  # Should be close to 10 seconds

    def test_cleanup(self):
        """Test model cleanup."""
        mock_recorder = Mock()
        mock_recorder.cleanup = Mock()

        model_info = ModelInfo(
            model_name="base",
            device="cpu",
            compute_type="int8",
            load_time=1.0,
            last_used=100.0,
            memory_usage=1000,
            recorder=mock_recorder,
        )

        # Should not raise exception
        model_info.cleanup()

        mock_recorder.cleanup.assert_called_once()
        assert model_info.recorder is None


class TestSTTServerManager:
    """Test suite for STTServerManager class."""

    @patch("voice_mcp.voice.stt_server.config")
    def test_initialization_default(self, mock_config):
        """Test STTServerManager initialization with defaults."""
        mock_config.stt_model_cache_size = 3
        mock_config.stt_model_timeout = 600
        mock_config.stt_preload_models = ["base", "small"]

        manager = STTServerManager()

        assert manager.cache_size == 3
        assert manager.model_timeout == 600
        assert manager.preload_models == ["base", "small"]
        assert not manager._is_running
        assert len(manager._models) == 0

    def test_initialization_custom(self):
        """Test STTServerManager initialization with custom values."""
        manager = STTServerManager(
            cache_size=5, model_timeout=900, preload_models=["large", "medium"]
        )

        assert manager.cache_size == 5
        assert manager.model_timeout == 900
        assert manager.preload_models == ["large", "medium"]
        assert not manager._is_running

    def test_start_server(self):
        """Test server start functionality."""
        manager = STTServerManager()

        with (
            patch.object(manager, "_check_dependencies", return_value=True),
            patch.object(manager, "_start_cleanup_thread"),
        ):

            result = manager.start()

            assert result["success"] is True
            assert manager._is_running is True

    def test_start_server_missing_dependencies(self):
        """Test server start with missing dependencies."""
        manager = STTServerManager()

        with patch.object(manager, "_check_dependencies", return_value=False):
            result = manager.start()

            assert result["success"] is False
            assert "dependencies" in result["error"]
            assert not manager._is_running

    def test_get_status(self):
        """Test status retrieval."""
        manager = STTServerManager()
        manager._is_running = True

        status = manager.get_status()

        assert isinstance(status, dict)
        assert "active" in status
        assert status["active"] is True


class TestSTTServerIntegration:
    """Integration tests for STT server functionality."""

    def test_create_stt_server(self):
        """Test STT server creation."""
        server = create_stt_server()
        assert isinstance(server, STTServerManager)

    def test_get_stt_server_exists(self):
        """Test getting STT server when it exists."""
        # The server is automatically created when accessed
        result = get_stt_server()
        assert result is not None
        assert isinstance(result, STTServerManager)

    def test_ensure_stt_server(self):
        """Test ensuring STT server exists."""
        server = ensure_stt_server()
        assert isinstance(server, STTServerManager)


class TestSTTServerConcurrency:
    """Test concurrent operations on STT server."""

    def test_concurrent_status_requests(self):
        """Test concurrent status requests don't cause issues."""
        manager = STTServerManager()
        results = []

        def get_status_worker():
            try:
                status = manager.get_status()
                results.append(status)
            except Exception as e:
                results.append(f"Error: {e}")

        threads = [threading.Thread(target=get_status_worker) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All requests should succeed
        assert len(results) == 5
        for result in results:
            assert isinstance(result, dict)
