#!/usr/bin/env python3
"""
🧪 UNIT TESTS FOR AUGMENT SECRET DETECTOR
Basic tests to verify core functionality and catch regressions
"""

import unittest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import os

# Add the current directory to the path so we can import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from augment_secret_detector import AugmentSecretDetector


class TestAugmentSecretDetector(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.detector = AugmentSecretDetector(
            cpu_threshold=80.0,
            monitoring_duration=1,  # Short duration for tests
            disk_threshold=50.0,
            network_threshold=10.0
        )
    
    def test_initialization(self):
        """Test detector initializes with correct parameters"""
        detector = AugmentSecretDetector(
            cpu_threshold=90.0,
            monitoring_duration=60,
            disk_threshold=100.0,
            network_threshold=20.0
        )
        
        self.assertEqual(detector.cpu_threshold, 90.0)
        self.assertEqual(detector.monitoring_duration, 60)
        self.assertEqual(detector.disk_threshold, 100.0)
        self.assertEqual(detector.network_threshold, 20.0)
    
    def test_custom_extensions_directory(self):
        """Test custom extensions directory is properly set"""
        custom_dir = "/custom/extensions"
        detector = AugmentSecretDetector(extensions_dir=custom_dir)
        
        self.assertIn(Path(custom_dir), detector.config_dirs)
        self.assertEqual(detector.config_dirs[0], Path(custom_dir))
    
    @patch('augment_secret_detector.psutil.process_iter')
    def test_analyze_processes_high_cpu(self, mock_process_iter):
        """Test that high CPU processes are detected and reported"""
        # Mock a high CPU process
        mock_proc = Mock()
        mock_proc.name.return_value = "code-insiders"
        mock_proc.pid = 12345
        mock_proc.cpu_percent.return_value = 85.0  # High CPU
        mock_proc.memory_info.return_value = Mock(rss=256 * 1024 * 1024)  # 256MB
        
        # Mock a normal CPU process
        mock_proc_normal = Mock()
        mock_proc_normal.name.return_value = "firefox"
        mock_proc_normal.pid = 67890
        mock_proc_normal.cpu_percent.return_value = 5.0  # Normal CPU
        mock_proc_normal.memory_info.return_value = Mock(rss=128 * 1024 * 1024)  # 128MB
        
        mock_process_iter.return_value = [mock_proc, mock_proc_normal]
        
        # Run analysis
        processes = self.detector.analyze_processes()
        
        # Should find the code-insiders process
        self.assertEqual(len(processes), 1)
        self.assertEqual(processes[0]['name'], 'code-insiders')
        self.assertEqual(processes[0]['pid'], 12345)
        self.assertEqual(processes[0]['cpu_percent'], 85.0)
    
    @patch('augment_secret_detector.psutil.disk_io_counters')
    @patch('augment_secret_detector.time.sleep')
    def test_detect_secrets_activity_high_disk_io(self, mock_sleep, mock_disk_io):
        """Test detection of high disk I/O activity"""
        # Mock disk I/O counters showing high activity
        mock_start = Mock(read_bytes=0, write_bytes=0)
        mock_end = Mock(read_bytes=100 * 1024 * 1024, write_bytes=50 * 1024 * 1024)  # 100MB read, 50MB write
        
        mock_disk_io.side_effect = [mock_start, mock_end, mock_start, mock_end]
        
        indicators = self.detector.detect_secrets_activity()
        
        # Should detect high disk I/O
        self.assertIn("high_disk_io", indicators)
    
    @patch('augment_secret_detector.psutil.net_io_counters')
    @patch('augment_secret_detector.time.sleep')
    def test_detect_secrets_activity_high_network_io(self, mock_sleep, mock_net_io):
        """Test detection of high network I/O activity"""
        # Mock network I/O counters showing high activity
        mock_start = Mock(bytes_sent=0, bytes_recv=0)
        mock_end = Mock(bytes_sent=20 * 1024 * 1024, bytes_recv=15 * 1024 * 1024)  # 20MB sent, 15MB received
        
        mock_net_io.side_effect = [mock_start, mock_end]
        
        indicators = self.detector.detect_secrets_activity()
        
        # Should detect high network I/O
        self.assertIn("high_network_io", indicators)
    
    def test_find_augment_extensions_no_directories(self):
        """Test extension finding when no directories exist"""
        # Create detector with non-existent directories only
        with patch.dict(os.environ, {}, clear=True):  # Clear environment variables
            detector = AugmentSecretDetector(extensions_dir="/nonexistent/path")
            # Override config_dirs to only include non-existent path
            detector.config_dirs = [Path("/nonexistent/path")]

            extensions = detector.find_augment_extensions()

            # Should return empty list when no directories exist
            self.assertEqual(len(extensions), 0)
    
    def test_generate_report_structure(self):
        """Test that generated reports have correct structure"""
        # Mock data
        cpu_analysis = {
            "average_cpu": 75.0,
            "peak_cpu": 90.0,
            "readings": [70, 80, 90, 85, 75],
            "high_usage_detected": True
        }
        processes = [
            {"pid": 12345, "name": "code-insiders", "cpu_percent": 85.0, "memory_mb": 256.0}
        ]
        secrets_indicators = ["high_disk_io"]
        
        report = self.detector.generate_report(cpu_analysis, processes, secrets_indicators)
        
        # Verify report structure
        self.assertIn("timestamp", report)
        self.assertIn("cpu_analysis", report)
        self.assertIn("augment_processes", report)
        self.assertIn("secrets_indicators", report)
        self.assertIn("recommendations", report)
        
        # Verify recommendations are generated for high CPU
        self.assertTrue(len(report["recommendations"]) > 0)
        self.assertTrue(any("High CPU usage detected" in rec for rec in report["recommendations"]))
    
    @patch('augment_secret_detector.psutil.cpu_percent')
    def test_monitor_cpu_usage_threshold_detection(self, mock_cpu_percent):
        """Test CPU monitoring detects threshold violations"""
        # Mock CPU readings that exceed threshold - need enough for the duration
        mock_cpu_percent.side_effect = [85.0, 90.0, 75.0, 80.0, 85.0]  # Enough readings for test
        
        # Use very short monitoring duration for test
        self.detector.monitoring_duration = 3
        
        with patch.object(self.detector, 'analyze_processes') as mock_analyze:
            cpu_analysis = self.detector.monitor_cpu_usage()
        
        # Should detect high usage
        self.assertTrue(cpu_analysis["high_usage_detected"])
        self.assertEqual(cpu_analysis["peak_cpu"], 90.0)
        
        # Should have called analyze_processes for high CPU readings
        self.assertTrue(mock_analyze.called)


class TestCLIArguments(unittest.TestCase):
    """Test command line argument parsing"""
    
    @patch('augment_secret_detector.AugmentSecretDetector')
    @patch('sys.argv', ['augment_secret_detector.py', '--cpu-threshold', '90', '--duration', '60'])
    def test_cli_argument_parsing(self, mock_detector_class):
        """Test that CLI arguments are properly parsed"""
        from augment_secret_detector import main
        
        # Mock os.getuid to avoid root check
        with patch('os.getuid', return_value=1000):
            main()
        
        # Verify detector was created with correct arguments
        mock_detector_class.assert_called_once_with(
            cpu_threshold=90.0,
            monitoring_duration=60,
            disk_threshold=50.0,  # default
            network_threshold=10.0,  # default
            extensions_dir=None  # default
        )


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
