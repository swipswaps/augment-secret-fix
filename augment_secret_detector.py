#!/usr/bin/env python3
"""
🔍 AUGMENT SECRET DETECTOR
Detects and manages Augment secrets causing CPU resource contention
"""

import os
import sys
import json
import time
import psutil
import subprocess
import logging
import traceback
import argparse
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

class AugmentSecretDetector:
    def __init__(self, cpu_threshold=80.0, monitoring_duration=30, disk_threshold=50, network_threshold=10, extensions_dir=None):
        # Support both VSCode and VSCode Insiders extension directories
        self.config_dirs = [
            Path.home() / ".vscode" / "extensions",
            Path.home() / ".vscode-insiders" / "extensions"
        ]

        # Check for custom extensions directory
        if extensions_dir:
            self.config_dirs.insert(0, Path(extensions_dir))
        elif os.getenv('VSC_EXT_DIR'):
            self.config_dirs.insert(0, Path(os.getenv('VSC_EXT_DIR')))

        self.augment_dirs = []
        self.cpu_threshold = cpu_threshold
        self.monitoring_duration = monitoring_duration
        self.disk_threshold = disk_threshold  # MB per 2 seconds
        self.network_threshold = network_threshold  # MB per 1 second
        self.log_file = "augment_secret_detection.log"

        # Setup rotating log handler
        self.setup_logging()

    def setup_logging(self):
        """Setup rotating file handler for logs"""
        self.logger = logging.getLogger('augment_secret_detector')
        self.logger.setLevel(logging.INFO)

        # Create rotating file handler (5MB max, keep 3 backups)
        handler = RotatingFileHandler(
            self.log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )

        formatter = logging.Formatter('[%(asctime)s] %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # Also log to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def log(self, message):
        """Log messages with timestamp"""
        self.logger.info(message)
    
    def find_augment_extensions(self):
        """Find all Augment extension directories"""
        self.log("🔍 Scanning for Augment extensions...")

        augment_patterns = [
            "*augment*",
            "*Augment*",
            "*AUGMENT*"
        ]

        for config_dir in self.config_dirs:
            if not config_dir.exists():
                self.log(f"⚠️ Extensions directory not found: {config_dir}")
                continue

            self.log(f"📁 Scanning directory: {config_dir}")

            for pattern in augment_patterns:
                for ext_dir in config_dir.glob(pattern):
                    if ext_dir.is_dir():
                        self.augment_dirs.append(ext_dir)
                        self.log(f"✅ Found Augment extension: {ext_dir.name} in {config_dir.name}")

        if not self.augment_dirs:
            self.log("❌ No Augment extensions found in any directory")

        return self.augment_dirs
    
    def monitor_cpu_usage(self):
        """Monitor CPU usage and detect spikes"""
        self.log(f"📊 Monitoring CPU usage for {self.monitoring_duration} seconds...")
        
        cpu_readings = []
        start_time = time.time()
        
        while time.time() - start_time < self.monitoring_duration:
            cpu_percent = psutil.cpu_percent(interval=1)  # Already blocks for 1 second
            cpu_readings.append(cpu_percent)

            if cpu_percent > self.cpu_threshold:
                self.log(f"⚠️ High CPU usage detected: {cpu_percent:.1f}%")
                self.analyze_processes()

            # No additional sleep needed - psutil.cpu_percent(interval=1) already waited
        
        avg_cpu = sum(cpu_readings) / len(cpu_readings)
        max_cpu = max(cpu_readings)
        
        self.log(f"📈 CPU Analysis - Average: {avg_cpu:.1f}%, Peak: {max_cpu:.1f}%")
        
        return {
            "average_cpu": avg_cpu,
            "peak_cpu": max_cpu,
            "readings": cpu_readings,
            "high_usage_detected": max_cpu > self.cpu_threshold
        }
    
    def analyze_processes(self):
        """Analyze running processes for Augment-related activity"""
        self.log("🔍 Analyzing running processes...")

        augment_processes = []

        # First pass: Prime CPU monitoring for all processes
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                proc.cpu_percent()  # Prime the CPU monitoring
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Wait for CPU measurement interval
        time.sleep(0.1)

        # Second pass: Get actual CPU usage
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                proc_name = proc.name().lower()

                # Check for Augment-related processes
                if any(keyword in proc_name for keyword in ['augment', 'vscode', 'code']):
                    cpu_usage = proc.cpu_percent()  # Get current CPU usage
                    memory_mb = proc.memory_info().rss / 1024 / 1024
                    
                    process_data = {
                        'pid': proc.pid,
                        'name': proc.name(),
                        'cpu_percent': cpu_usage,
                        'memory_mb': memory_mb
                    }
                    
                    augment_processes.append(process_data)
                    
                    # Normalize CPU usage for multi-core systems
                    cpu_cores = psutil.cpu_count()
                    normalized_threshold = 80 / cpu_cores  # Adjust threshold based on core count

                    if cpu_usage > normalized_threshold:  # High CPU usage process (normalized)
                        self.log(f"🔥 High CPU process: {proc.name()} (PID: {proc.pid}) - CPU: {cpu_usage:.1f}%, Memory: {memory_mb:.1f}MB (Threshold: {normalized_threshold:.1f}%)")
            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return augment_processes
    
    def detect_secrets_activity(self):
        """Detect potential secrets causing resource contention"""
        self.log("🕵️ Detecting secrets activity...")

        secrets_indicators = []

        # Check for high I/O activity using delta measurement
        try:
            # Take initial snapshot
            io_start = psutil.disk_io_counters()
            time.sleep(2)  # Sample interval for delta calculation
            io_end = psutil.disk_io_counters()

            if io_start and io_end:
                read_delta_mb = (io_end.read_bytes - io_start.read_bytes) / 1024 / 1024
                write_delta_mb = (io_end.write_bytes - io_start.write_bytes) / 1024 / 1024

                self.log(f"💾 Disk I/O Delta (2s) - Read: {read_delta_mb:.1f}MB, Write: {write_delta_mb:.1f}MB")

                # Configurable threshold for high activity
                if read_delta_mb > self.disk_threshold or write_delta_mb > self.disk_threshold:
                    secrets_indicators.append("high_disk_io")
                    self.log("⚠️ High disk I/O delta detected - possible secrets processing")

        except Exception as e:
            self.log(f"❌ Error checking disk I/O: {e}")

        # Check network activity using delta measurement
        try:
            # Take initial snapshot
            net_start = psutil.net_io_counters()
            time.sleep(1)  # Sample interval for delta calculation
            net_end = psutil.net_io_counters()

            if net_start and net_end:
                sent_delta_mb = (net_end.bytes_sent - net_start.bytes_sent) / 1024 / 1024
                recv_delta_mb = (net_end.bytes_recv - net_start.bytes_recv) / 1024 / 1024

                self.log(f"🌐 Network I/O Delta (1s) - Sent: {sent_delta_mb:.1f}MB, Received: {recv_delta_mb:.1f}MB")

                # Configurable threshold for high activity
                if sent_delta_mb > self.network_threshold or recv_delta_mb > self.network_threshold:
                    secrets_indicators.append("high_network_io")
                    self.log("⚠️ High network activity delta detected - possible secrets transmission")

        except Exception as e:
            self.log(f"❌ Error checking network I/O: {e}")

        return secrets_indicators
    
    def generate_report(self, cpu_analysis, processes, secrets_indicators):
        """Generate comprehensive detection report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "cpu_analysis": cpu_analysis,
            "augment_processes": processes,
            "secrets_indicators": secrets_indicators,
            "augment_extensions": [str(d) for d in self.augment_dirs],
            "recommendations": []
        }
        
        # Generate recommendations
        if cpu_analysis["high_usage_detected"]:
            report["recommendations"].append("High CPU usage detected - consider Augment version rollback")
        
        if "high_disk_io" in secrets_indicators:
            report["recommendations"].append("High disk I/O detected - check for secrets processing")
        
        if "high_network_io" in secrets_indicators:
            report["recommendations"].append("High network activity detected - monitor secrets transmission")
        
        if len(processes) > 5:
            report["recommendations"].append("Multiple Augment processes detected - consider process cleanup")
        
        # Save report
        report_file = f"augment_secret_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"📊 Report saved to: {report_file}")
        return report
    
    def run_detection(self):
        """Run complete detection process"""
        self.log("🚀 Starting Augment Secret Detection")
        self.log("=" * 50)
        
        # Find Augment extensions
        self.find_augment_extensions()
        
        # Monitor CPU usage
        cpu_analysis = self.monitor_cpu_usage()
        
        # Analyze processes
        processes = self.analyze_processes()
        
        # Detect secrets activity
        secrets_indicators = self.detect_secrets_activity()
        
        # Generate report
        report = self.generate_report(cpu_analysis, processes, secrets_indicators)
        
        self.log("✅ Detection complete")
        self.log("=" * 50)
        
        return report

def main():
    # Security check: Don't run as root
    if os.getuid() == 0:
        print("❌ ERROR: This script should not be run as root for security reasons.")
        print("   Running as root exposes process information and broadens attack surface.")
        print("   Please run as a regular user.")
        sys.exit(1)

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='🔍 AUGMENT SECRET DETECTOR - Monitor CPU and detect secrets activity',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 augment_secret_detector.py
    python3 augment_secret_detector.py --duration 60 --cpu-threshold 70
    python3 augment_secret_detector.py --disk-threshold 100 --network-threshold 20
    python3 augment_secret_detector.py --extensions-dir /custom/vscode/extensions

Environment Variables:
    VSC_EXT_DIR     Override VSCode extensions directory (if --extensions-dir not specified)
        """
    )

    parser.add_argument('--duration', type=int, default=30,
                       help='Monitoring duration in seconds (default: 30)')
    parser.add_argument('--cpu-threshold', type=float, default=80.0,
                       help='CPU threshold percentage (default: 80.0)')
    parser.add_argument('--disk-threshold', type=float, default=50.0,
                       help='Disk I/O threshold in MB per 2 seconds (default: 50.0)')
    parser.add_argument('--network-threshold', type=float, default=10.0,
                       help='Network I/O threshold in MB per 1 second (default: 10.0)')
    parser.add_argument('--extensions-dir', type=str,
                       help='Custom VSCode extensions directory path')

    args = parser.parse_args()

    detector = AugmentSecretDetector(
        cpu_threshold=args.cpu_threshold,
        monitoring_duration=args.duration,
        disk_threshold=args.disk_threshold,
        network_threshold=args.network_threshold,
        extensions_dir=args.extensions_dir
    )
    
    try:
        report = detector.run_detection()
        
        # Print summary
        print("\n🎯 DETECTION SUMMARY:")
        print(f"CPU Peak: {report['cpu_analysis']['peak_cpu']:.1f}%")
        print(f"Augment Processes: {len(report['augment_processes'])}")
        print(f"Secrets Indicators: {len(report['secrets_indicators'])}")
        print(f"Recommendations: {len(report['recommendations'])}")
        
        if report['recommendations']:
            print("\n💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
    
    except KeyboardInterrupt:
        print("\n⚠️ Detection interrupted by user")
    except Exception as e:
        # Redact sensitive paths from error messages
        error_msg = str(e).replace(str(Path.home()), "~")
        print(f"❌ Error during detection: {error_msg}")

        # Log full traceback to file (but not console for security)
        detector.logger.error(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
