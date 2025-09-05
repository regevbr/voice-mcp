"""
Tests for STT server functionality.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock, call
from collections import OrderedDict

from voice_mcp.voice.stt_server import (
    STTServerManager, 
    ModelInfo, 
    create_stt_server, 
    get_stt_server,
    ensure_stt_server
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
            memory_usage=1024 * 1024 * 500  # 500MB
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
            memory_usage=1000
        )
        
        initial_time = model_info.last_used
        
        with patch('time.time', return_value=200.0):
            model_info.update_last_used()
            
        assert model_info.last_used == 200.0
        assert model_info.last_used > initial_time
    
    def test_get_age(self):
        """Test getting model age."""
        model_info = ModelInfo(
            model_name="base",
            device="cpu",
            compute_type="int8", 
            load_time=1.0,
            last_used=100.0,
            memory_usage=1000
        )
        
        with patch('time.time', return_value=150.0):
            age = model_info.get_age()
            
        assert age == 50.0
    
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
            recorder=mock_recorder
        )
        
        model_info.cleanup()
        
        mock_recorder.cleanup.assert_called_once()
        assert model_info.recorder is None
    
    def test_cleanup_with_exception(self):
        """Test cleanup when recorder cleanup raises exception."""
        mock_recorder = Mock()
        mock_recorder.cleanup.side_effect = Exception("Cleanup failed")
        
        model_info = ModelInfo(
            model_name="base",
            device="cpu", 
            compute_type="int8",
            load_time=1.0,
            last_used=100.0,
            memory_usage=1000,
            recorder=mock_recorder
        )
        
        # Should not raise exception
        model_info.cleanup()
        
        mock_recorder.cleanup.assert_called_once()
        assert model_info.recorder is None


class TestSTTServerManager:
    """Test suite for STTServerManager class."""
    
    @patch('voice_mcp.voice.stt_server.config')
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
            cache_size=5,
            model_timeout=900,
            preload_models=["large", "medium"]
        )
        
        assert manager.cache_size == 5
        assert manager.model_timeout == 900
        assert manager.preload_models == ["large", "medium"]
        assert not manager._is_running
    
    @patch('voice_mcp.voice.stt_server.TORCH_AVAILABLE', True)
    @patch('voice_mcp.voice.stt_server.REALTIMESTT_AVAILABLE', True)
    def test_check_dependencies_success(self):
        """Test dependency check when all dependencies available."""
        manager = STTServerManager()
        result = manager._check_dependencies()
        
        assert result is True
    
    @patch('voice_mcp.voice.stt_server.REALTIMESTT_AVAILABLE', False)
    def test_check_dependencies_missing_realtimestt(self):
        """Test dependency check when RealtimeSTT is missing."""
        manager = STTServerManager()
        result = manager._check_dependencies()
        
        assert result is False
    
    @patch('voice_mcp.voice.stt_server.TORCH_AVAILABLE', False)
    @patch('voice_mcp.voice.stt_server.REALTIMESTT_AVAILABLE', True)
    def test_check_dependencies_missing_torch(self):
        """Test dependency check when PyTorch is missing."""
        manager = STTServerManager()
        result = manager._check_dependencies()
        
        assert result is False
    
    @patch('voice_mcp.voice.stt_server.torch')
    def test_get_optimal_device_cuda_available(self, mock_torch):
        """Test device detection when CUDA is available."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_properties.return_value.total_memory = 12 * 1024**3  # 12GB
        
        manager = STTServerManager()
        
        # Test with small model
        device, compute_type = manager._get_optimal_device("base")
        assert device == "cuda"
        assert compute_type == "float16"
        
        # Test with large model (sufficient GPU memory)
        device, compute_type = manager._get_optimal_device("large")
        assert device == "cuda"
        assert compute_type == "float16"
    
    @patch('voice_mcp.voice.stt_server.torch')
    def test_get_optimal_device_cuda_insufficient_memory(self, mock_torch):
        """Test device detection when CUDA available but insufficient memory for large models."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_properties.return_value.total_memory = 4 * 1024**3  # 4GB
        
        manager = STTServerManager()
        
        # Test with large model (insufficient GPU memory)
        device, compute_type = manager._get_optimal_device("large")
        assert device == "cpu"
        assert compute_type == "int8"
    
    @patch('voice_mcp.voice.stt_server.torch')
    def test_get_optimal_device_cuda_unavailable(self, mock_torch):
        """Test device detection when CUDA is unavailable."""
        mock_torch.cuda.is_available.return_value = False
        
        manager = STTServerManager()
        device, compute_type = manager._get_optimal_device("base")
        
        assert device == "cpu"
        assert compute_type == "int8"
    
    @patch('voice_mcp.voice.stt_server.torch', None)
    def test_get_optimal_device_no_torch(self):
        """Test device detection when PyTorch is not available."""
        manager = STTServerManager()
        device, compute_type = manager._get_optimal_device("base")
        
        assert device == "cpu"
        assert compute_type == "int8"
    
    def test_estimate_memory_usage(self):
        """Test memory usage estimation for different models."""
        manager = STTServerManager()
        
        # Test known model sizes
        tiny_memory = manager._estimate_memory_usage("tiny", "cpu")
        base_memory = manager._estimate_memory_usage("base", "cpu")
        large_memory = manager._estimate_memory_usage("large", "cuda")
        
        assert tiny_memory > 0
        assert base_memory > tiny_memory
        assert large_memory > base_memory
        
        # CUDA models should have higher memory estimate
        cuda_memory = manager._estimate_memory_usage("base", "cuda")
        cpu_memory = manager._estimate_memory_usage("base", "cpu")
        assert cuda_memory > cpu_memory
    
    @patch('voice_mcp.voice.stt_server.TORCH_AVAILABLE', True)
    @patch('voice_mcp.voice.stt_server.REALTIMESTT_AVAILABLE', True)
    @patch('voice_mcp.voice.stt_server.AudioToTextRecorder')
    def test_start_server_success(self, mock_recorder_class):
        """Test successful server start with model preloading."""
        mock_recorder = Mock()
        mock_recorder_class.return_value = mock_recorder
        
        manager = STTServerManager(preload_models=["base"])
        
        with patch.object(manager, '_check_dependencies', return_value=True), \
             patch.object(manager, '_start_cleanup_thread'), \
             patch.object(manager, '_get_optimal_device', return_value=("cpu", "int8")), \
             patch('time.time', side_effect=[100.0, 101.0, 102.0, 103.0, 104.0, 105.0]):
            
            result = manager.start()
            
        assert result["success"] is True
        assert "STT server started" in result["message"]
        assert manager._is_running is True
        assert manager._start_time is not None
    
    @patch('voice_mcp.voice.stt_server.REALTIMESTT_AVAILABLE', False)
    def test_start_server_missing_dependencies(self):
        """Test server start when dependencies are missing."""
        manager = STTServerManager()
        result = manager.start()
        
        assert result["success"] is False
        assert "dependencies not available" in result["error"]
        assert manager._is_running is False
    
    def test_start_server_already_running(self):
        """Test starting server when it's already running."""
        manager = STTServerManager()
        manager._is_running = True
        manager._start_time = time.time()
        
        result = manager.start()
        
        assert result["success"] is True
        assert "already running" in result["message"]
    
    def test_stop_server_not_running(self):
        """Test stopping server when it's not running."""
        manager = STTServerManager()
        result = manager.stop()
        
        assert result["success"] is True
        assert "not running" in result["message"]
        assert result["models_unloaded"] == 0
    
    def test_stop_server_success(self):
        """Test successful server stop with model cleanup."""
        manager = STTServerManager()
        manager._is_running = True
        manager._start_time = time.time()
        
        # Add mock models
        mock_model1 = Mock(spec=ModelInfo)
        mock_model2 = Mock(spec=ModelInfo)
        manager._models["base"] = mock_model1
        manager._models["small"] = mock_model2
        
        # Mock cleanup thread
        mock_thread = Mock()
        manager._cleanup_thread = mock_thread
        mock_thread.is_alive.return_value = False
        
        result = manager.stop()
        
        assert result["success"] is True
        assert result["models_unloaded"] == 2
        assert manager._is_running is False
        assert manager._start_time is None
        assert len(manager._models) == 0
        
        # Verify model cleanup was called
        mock_model1.cleanup.assert_called_once()
        mock_model2.cleanup.assert_called_once()
    
    def test_preload_model_server_not_running(self):
        """Test preloading model when server is not running."""
        manager = STTServerManager()
        manager._is_running = False
        
        result = manager.preload_model("base")
        
        assert result["success"] is False
        assert "not running" in result["error"]
    
    def test_preload_model_already_loaded(self):
        """Test preloading model that's already loaded."""
        manager = STTServerManager()
        manager._is_running = True
        
        # Add mock model to cache
        mock_model = Mock(spec=ModelInfo)
        manager._models["base"] = mock_model
        
        result = manager.preload_model("base")
        
        assert result["success"] is True
        assert "already loaded" in result["message"]
        assert result["cached"] is True
        mock_model.update_last_used.assert_called_once()
    
    @patch('voice_mcp.voice.stt_server.AudioToTextRecorder')
    def test_preload_model_success(self, mock_recorder_class):
        """Test successful model preloading."""
        mock_recorder = Mock()
        mock_recorder_class.return_value = mock_recorder
        
        manager = STTServerManager(cache_size=3)
        manager._is_running = True
        
        with patch.object(manager, '_get_optimal_device', return_value=("cpu", "int8")), \
             patch.object(manager, '_estimate_memory_usage', return_value=1000000), \
             patch('time.time', side_effect=[100.0, 101.5, 102.0]):
            
            result = manager.preload_model("base")
            
        assert result["success"] is True
        assert "loaded successfully" in result["message"]
        assert "base" in manager._models
        assert manager._models["base"].model_name == "base"
        assert manager._models["base"].device == "cpu"
        assert manager._models["base"].compute_type == "int8"
        assert manager._models["base"].load_time == 1.5
    
    def test_preload_model_concurrent_loading(self):
        """Test concurrent model loading with threading synchronization."""
        manager = STTServerManager()
        manager._is_running = True
        
        # Simulate concurrent loading
        loading_event = threading.Event()
        manager._loading_models["base"] = loading_event
        
        # Start preload in background thread
        def delayed_set_event():
            time.sleep(0.1)
            # Add model to cache
            mock_model = Mock(spec=ModelInfo)
            manager._models["base"] = mock_model
            loading_event.set()
        
        thread = threading.Thread(target=delayed_set_event)
        thread.start()
        
        result = manager.preload_model("base")
        
        thread.join()
        
        assert result["success"] is True
        assert "loaded by another thread" in result["message"]
        assert result["waited"] is True
    
    def test_unload_model_not_loaded(self):
        """Test unloading model that's not loaded."""
        manager = STTServerManager()
        result = manager.unload_model("base")
        
        assert result["success"] is True
        assert "not loaded" in result["message"]
        assert result["found"] is False
    
    def test_unload_model_success(self):
        """Test successful model unloading."""
        manager = STTServerManager()
        
        # Add mock model
        mock_model = Mock(spec=ModelInfo)
        mock_model.memory_usage = 1000000
        manager._models["base"] = mock_model
        
        result = manager.unload_model("base")
        
        assert result["success"] is True
        assert "unloaded successfully" in result["message"]
        assert result["memory_freed"] == 1000000
        assert "base" not in manager._models
        mock_model.cleanup.assert_called_once()
    
    def test_get_model_recorder_server_not_running(self):
        """Test getting model recorder when server is not running."""
        manager = STTServerManager()
        manager._is_running = False
        
        recorder = manager.get_model_recorder("base")
        
        assert recorder is None
    
    def test_get_model_recorder_cached(self):
        """Test getting model recorder from cache."""
        manager = STTServerManager()
        manager._is_running = True
        
        # Add mock model to cache
        mock_recorder = Mock()
        mock_model = Mock(spec=ModelInfo)
        mock_model.recorder = mock_recorder
        manager._models["base"] = mock_model
        
        recorder = manager.get_model_recorder("base")
        
        assert recorder is mock_recorder
        mock_model.update_last_used.assert_called_once()
    
    def test_get_model_recorder_load_on_demand(self):
        """Test getting model recorder with on-demand loading."""
        manager = STTServerManager()
        manager._is_running = True
        
        mock_recorder = Mock()
        
        def mock_preload_side_effect(model_name):
            # Simulate successful preload by adding model to cache
            mock_model = Mock(spec=ModelInfo)
            mock_model.recorder = mock_recorder
            mock_model.update_last_used = Mock()
            manager._models[model_name] = mock_model
            return {"success": True}
        
        with patch.object(manager, 'preload_model', side_effect=mock_preload_side_effect) as mock_preload:
            recorder = manager.get_model_recorder("base")
            
        assert recorder is mock_recorder
        mock_preload.assert_called_once_with("base")
    
    @patch('voice_mcp.voice.stt_server.PSUTIL_AVAILABLE', True)
    @patch('voice_mcp.voice.stt_server.psutil')
    def test_get_status(self, mock_psutil):
        """Test getting server status."""
        # Mock system memory info
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3
        mock_memory.available = 8 * 1024**3
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        manager = STTServerManager()
        manager._is_running = True
        manager._start_time = time.time() - 3600  # 1 hour ago
        
        # Add mock models
        mock_model1 = Mock(spec=ModelInfo)
        mock_model1.model_name = "base"
        mock_model1.device = "cpu"
        mock_model1.compute_type = "int8" 
        mock_model1.load_time = 2.5
        mock_model1.last_used = time.time() - 300
        mock_model1.get_age.return_value = 300.0
        mock_model1.memory_usage = 1000000
        
        # Create a proper dict for the model with all required attributes
        mock_model1.configure_mock(**{
            'model_name': 'base',
            'device': 'cpu',
            'compute_type': 'int8',
            'load_time': 2.5,
            'last_used': time.time() - 300,
            'memory_usage': 1000000
        })
        
        manager._models["base"] = mock_model1
        
        with patch('time.time', return_value=time.time()):
            status = manager.get_status()
        
        assert status["active"] is True
        assert status["model_count"] == 1
        assert status["cache_size"] == manager.cache_size
        assert status["total_model_memory"] == 1000000
        assert len(status["loaded_models"]) == 1
        assert status["loaded_models"][0]["name"] == "base"
        assert status["system_memory"]["total"] == 16 * 1024**3
    
    def test_ensure_cache_capacity(self):
        """Test cache capacity management with LRU eviction."""
        manager = STTServerManager(cache_size=2)
        
        # Add models to fill cache
        mock_model1 = Mock(spec=ModelInfo)
        mock_model1.get_age.return_value = 100.0
        mock_model2 = Mock(spec=ModelInfo) 
        mock_model2.get_age.return_value = 50.0
        mock_model3 = Mock(spec=ModelInfo)
        mock_model3.get_age.return_value = 10.0
        
        manager._models["old"] = mock_model1
        manager._models["medium"] = mock_model2
        
        # This should trigger eviction of oldest model
        manager._ensure_cache_capacity()
        
        # Should evict "old" model (least recently used)
        assert "old" not in manager._models
        assert "medium" in manager._models
        mock_model1.cleanup.assert_called_once()
        mock_model2.cleanup.assert_not_called()
    
    def test_cleanup_expired_models(self):
        """Test cleanup of expired models."""
        manager = STTServerManager(model_timeout=300)  # 5 minutes
        
        # Add models with different ages
        mock_model_fresh = Mock(spec=ModelInfo)
        mock_model_fresh.get_age.return_value = 200.0  # 3 minutes - fresh
        mock_model_fresh.memory_usage = 1000000
        
        mock_model_expired = Mock(spec=ModelInfo)
        mock_model_expired.get_age.return_value = 400.0  # 6 minutes - expired
        mock_model_expired.memory_usage = 2000000
        
        manager._models["fresh"] = mock_model_fresh
        manager._models["expired"] = mock_model_expired
        
        manager._cleanup_expired_models()
        
        assert "fresh" in manager._models
        assert "expired" not in manager._models
        mock_model_expired.cleanup.assert_called_once()
        mock_model_fresh.cleanup.assert_not_called()
    
    def test_context_manager(self):
        """Test context manager functionality."""
        manager = STTServerManager()
        
        with patch.object(manager, 'start') as mock_start, \
             patch.object(manager, 'stop') as mock_stop:
            
            mock_start.return_value = {"success": True}
            
            with manager as ctx_manager:
                assert ctx_manager is manager
                mock_start.assert_called_once()
            
            mock_stop.assert_called_once()
    
    def test_context_manager_start_failure(self):
        """Test context manager when start fails."""
        manager = STTServerManager()
        
        with patch.object(manager, 'start') as mock_start:
            mock_start.return_value = {"success": False, "error": "Test error"}
            
            with pytest.raises(RuntimeError, match="Failed to start STT server"):
                with manager:
                    pass


class TestServerFunctions:
    """Test suite for server management functions."""
    
    def test_create_stt_server(self):
        """Test creating STT server instance."""
        server = create_stt_server(cache_size=3, model_timeout=600, preload_models=["base"])
        
        assert isinstance(server, STTServerManager)
        assert server.cache_size == 3
        assert server.model_timeout == 600
        assert server.preload_models == ["base"]
    
    def test_get_stt_server_none(self):
        """Test getting STT server when none exists."""
        # Reset global server
        import voice_mcp.voice.stt_server as stt_server_module
        stt_server_module._stt_server_manager = None
        
        server = get_stt_server()
        assert server is None
    
    def test_get_stt_server_existing(self):
        """Test getting existing STT server."""
        # Create server first
        created_server = create_stt_server()
        retrieved_server = get_stt_server()
        
        assert retrieved_server is created_server
    
    def test_ensure_stt_server_create_new(self):
        """Test ensuring STT server creates new one if none exists."""
        # Reset global server
        import voice_mcp.voice.stt_server as stt_server_module
        stt_server_module._stt_server_manager = None
        
        server = ensure_stt_server()
        
        assert isinstance(server, STTServerManager)
        assert get_stt_server() is server
    
    def test_ensure_stt_server_existing(self):
        """Test ensuring STT server returns existing one."""
        # Create server first
        created_server = create_stt_server()
        ensured_server = ensure_stt_server()
        
        assert ensured_server is created_server


class TestSTTServerIntegration:
    """Integration tests for STT server (with mocked dependencies)."""
    
    @patch('voice_mcp.voice.stt_server.TORCH_AVAILABLE', True)
    @patch('voice_mcp.voice.stt_server.REALTIMESTT_AVAILABLE', True)
    @patch('voice_mcp.voice.stt_server.AudioToTextRecorder')
    @patch('voice_mcp.voice.stt_server.torch')
    @patch('time.time')
    def test_full_server_workflow(self, mock_time, mock_torch, mock_recorder_class):
        """Test complete server workflow with model loading and management."""
        # Setup mocks
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_properties.return_value.total_memory = 12 * 1024**3
        # Use return_value instead of side_effect for simplicity in integration test
        mock_time.return_value = 100.0
        
        mock_recorder = Mock()
        mock_recorder_class.return_value = mock_recorder
        
        # Create and start server
        manager = STTServerManager(preload_models=["base"], cache_size=3)
        
        with patch.object(manager, '_start_cleanup_thread'):
            start_result = manager.start()
        
        assert start_result["success"] is True
        assert manager._is_running is True
        
        # Test getting model recorder
        recorder = manager.get_model_recorder("base")
        assert recorder is mock_recorder
        
        # Test preloading another model
        preload_result = manager.preload_model("small")
        assert preload_result["success"] is True
        
        # Test server status
        with patch('voice_mcp.voice.stt_server.PSUTIL_AVAILABLE', True), \
             patch('voice_mcp.voice.stt_server.psutil') as mock_psutil:
            mock_memory = Mock()
            mock_memory.total = 16 * 1024**3
            mock_memory.available = 8 * 1024**3
            mock_memory.percent = 50.0
            mock_psutil.virtual_memory.return_value = mock_memory
            
            status = manager.get_status()
            
        assert status["active"] is True
        assert status["model_count"] == 2  # base and small
        
        # Test stopping server
        stop_result = manager.stop()
        assert stop_result["success"] is True
        assert not manager._is_running
        assert len(manager._models) == 0
    
    @patch('voice_mcp.voice.stt_server.TORCH_AVAILABLE', False)
    @patch('voice_mcp.voice.stt_server.REALTIMESTT_AVAILABLE', False)
    def test_graceful_degradation_no_dependencies(self):
        """Test graceful behavior when dependencies are missing."""
        manager = STTServerManager()
        
        # Test start failure
        start_result = manager.start()
        assert start_result["success"] is False
        assert "dependencies not available" in start_result["error"]
        
        # Test preload failure
        preload_result = manager.preload_model("base")
        assert preload_result["success"] is False
        assert "not running" in preload_result["error"]
        
        # Test status
        status = manager.get_status()
        assert status["active"] is False
        assert status["dependencies"]["torch_available"] is False
        assert status["dependencies"]["realtimestt_available"] is False


class TestConcurrencyAndRaceConditions:
    """Test concurrent operations and race conditions."""
    
    @patch('voice_mcp.voice.stt_server.TORCH_AVAILABLE', True)
    @patch('voice_mcp.voice.stt_server.REALTIMESTT_AVAILABLE', True)
    @patch('voice_mcp.voice.stt_server.AudioToTextRecorder')
    def test_concurrent_model_loading(self, mock_recorder_class):
        """Test concurrent model loading doesn't cause race conditions."""
        mock_recorder = Mock()
        mock_recorder_class.return_value = mock_recorder
        
        manager = STTServerManager()
        manager._is_running = True
        
        results = []
        errors = []
        
        def load_model(model_name):
            try:
                with patch.object(manager, '_get_optimal_device', return_value=("cpu", "int8")), \
                     patch.object(manager, '_estimate_memory_usage', return_value=1000000):
                    result = manager.preload_model(model_name)
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads trying to load the same model
        threads = []
        for i in range(5):
            thread = threading.Thread(target=load_model, args=("base",))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have no errors
        assert len(errors) == 0
        
        # All results should be successful (either loaded or already loaded)
        assert len(results) == 5
        for result in results:
            assert result["success"] is True
        
        # Should only have one model in cache
        assert len(manager._models) == 1
        assert "base" in manager._models
    
    def test_cache_eviction_thread_safety(self):
        """Test cache eviction is thread-safe."""
        manager = STTServerManager(cache_size=2)
        
        # Add models to cache
        for i in range(5):
            mock_model = Mock(spec=ModelInfo)
            mock_model.get_age.return_value = i * 100  # Different ages
            manager._models[f"model_{i}"] = mock_model
        
        def evict_models():
            manager._ensure_cache_capacity()
        
        # Run eviction in multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=evict_models)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have cache_size or fewer models
        assert len(manager._models) <= manager.cache_size