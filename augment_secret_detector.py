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
from datetime import datetime
from pathlib import Path

class AugmentSecretDetector:
    def __init__(self):
        self.config_dir = Path.home() / ".vscode" / "extensions"
        self.augment_dirs = []
        self.cpu_threshold = 80.0  # CPU usage threshold
        self.monitoring_duration = 30  # seconds
        self.log_file = "augment_secret_detection.log"
        
    def log(self, message):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def find_augment_extensions(self):
        """Find all Augment extension directories"""
        self.log("🔍 Scanning for Augment extensions...")
        
        if not self.config_dir.exists():
            self.log("❌ VSCode extensions directory not found")
            return []
        
        augment_patterns = [
            "*augment*",
            "*Augment*",
            "*AUGMENT*"
        ]
        
        for pattern in augment_patterns:
            for ext_dir in self.config_dir.glob(pattern):
                if ext_dir.is_dir():
                    self.augment_dirs.append(ext_dir)
                    self.log(f"✅ Found Augment extension: {ext_dir.name}")
        
        return self.augment_dirs
    
    def monitor_cpu_usage(self):
        """Monitor CPU usage and detect spikes"""
        self.log(f"📊 Monitoring CPU usage for {self.monitoring_duration} seconds...")
        
        cpu_readings = []
        start_time = time.time()
        
        while time.time() - start_time < self.monitoring_duration:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_readings.append(cpu_percent)
            
            if cpu_percent > self.cpu_threshold:
                self.log(f"⚠️ High CPU usage detected: {cpu_percent:.1f}%")
                self.analyze_processes()
            
            time.sleep(1)
        
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
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                proc_info = proc.info
                proc_name = proc_info['name'].lower()
                
                # Check for Augment-related processes
                if any(keyword in proc_name for keyword in ['augment', 'vscode', 'code']):
                    cpu_usage = proc_info['cpu_percent']
                    memory_mb = proc_info['memory_info'].rss / 1024 / 1024
                    
                    process_data = {
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'cpu_percent': cpu_usage,
                        'memory_mb': memory_mb
                    }
                    
                    augment_processes.append(process_data)
                    
                    if cpu_usage > 50:  # High CPU usage process
                        self.log(f"🔥 High CPU process: {proc_info['name']} (PID: {proc_info['pid']}) - CPU: {cpu_usage:.1f}%, Memory: {memory_mb:.1f}MB")
            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return augment_processes
    
    def detect_secrets_activity(self):
        """Detect potential secrets causing resource contention"""
        self.log("🕵️ Detecting secrets activity...")
        
        secrets_indicators = []
        
        # Check for high I/O activity
        try:
            io_counters = psutil.disk_io_counters()
            if io_counters:
                read_mb = io_counters.read_bytes / 1024 / 1024
                write_mb = io_counters.write_bytes / 1024 / 1024
                
                self.log(f"💾 Disk I/O - Read: {read_mb:.1f}MB, Write: {write_mb:.1f}MB")
                
                if read_mb > 1000 or write_mb > 1000:  # High I/O threshold
                    secrets_indicators.append("high_disk_io")
                    self.log("⚠️ High disk I/O detected - possible secrets processing")
        
        except Exception as e:
            self.log(f"❌ Error checking disk I/O: {e}")
        
        # Check network activity
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                sent_mb = net_io.bytes_sent / 1024 / 1024
                recv_mb = net_io.bytes_recv / 1024 / 1024
                
                self.log(f"🌐 Network I/O - Sent: {sent_mb:.1f}MB, Received: {recv_mb:.1f}MB")
                
                if sent_mb > 100 or recv_mb > 100:  # High network threshold
                    secrets_indicators.append("high_network_io")
                    self.log("⚠️ High network activity detected - possible secrets transmission")
        
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
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
🔍 AUGMENT SECRET DETECTOR

Usage: python3 augment_secret_detector.py [options]

Options:
    --help          Show this help message
    --duration N    Set monitoring duration in seconds (default: 30)
    --threshold N   Set CPU threshold percentage (default: 80)

Examples:
    python3 augment_secret_detector.py
    python3 augment_secret_detector.py --duration 60 --threshold 70
        """)
        return
    
    detector = AugmentSecretDetector()
    
    # Parse command line arguments
    for i, arg in enumerate(sys.argv):
        if arg == "--duration" and i + 1 < len(sys.argv):
            detector.monitoring_duration = int(sys.argv[i + 1])
        elif arg == "--threshold" and i + 1 < len(sys.argv):
            detector.cpu_threshold = float(sys.argv[i + 1])
    
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
        print(f"❌ Error during detection: {e}")

if __name__ == "__main__":
    main()
