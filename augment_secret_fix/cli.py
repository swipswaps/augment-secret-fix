#!/usr/bin/env python3
"""
🎯 AUGMENT SECRET FIX - UNIFIED CLI
Single entry point for all Augment secret fix functionality
"""

import argparse
import sys
import os
from pathlib import Path

# Import our modules
from .detector import AugmentSecretDetector
from .version_manager import AugmentVersionManager
from .updater import VSCodeUpdater


def create_parser():
    """Create the main argument parser with subcommands"""
    parser = argparse.ArgumentParser(
        prog="augment-fix",
        description="🛠️ Comprehensive solution for Augment extension issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Detect secrets and CPU issues
    augment-fix detect --duration 60 --cpu-threshold 70
    
    # Manage Augment versions
    augment-fix version status
    augment-fix version backup
    augment-fix version rollback augment_v0.467.1_20250627_120000
    augment-fix version lock
    
    # Update VSCode safely
    augment-fix vscode update
    augment-fix vscode backup-logs
    augment-fix vscode restore-logs
    
    # Show overall status
    augment-fix status
        """
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="%(prog)s 0.2.1"
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND"
    )
    
    # Detection subcommand
    detect_parser = subparsers.add_parser(
        "detect",
        help="Detect secrets and CPU issues",
        description="Monitor CPU usage and detect Augment secrets activity"
    )
    detect_parser.add_argument(
        "--duration", 
        type=int, 
        default=30,
        help="Monitoring duration in seconds (default: 30)"
    )
    detect_parser.add_argument(
        "--cpu-threshold", 
        type=float, 
        default=80.0,
        help="CPU threshold percentage (default: 80.0)"
    )
    detect_parser.add_argument(
        "--disk-threshold", 
        type=float, 
        default=50.0,
        help="Disk I/O threshold in MB per 2 seconds (default: 50.0)"
    )
    detect_parser.add_argument(
        "--network-threshold", 
        type=float, 
        default=10.0,
        help="Network I/O threshold in MB per 1 second (default: 10.0)"
    )
    detect_parser.add_argument(
        "--extensions-dir", 
        type=str,
        help="Custom VSCode extensions directory path"
    )
    
    # Version management subcommand
    version_parser = subparsers.add_parser(
        "version",
        help="Manage Augment versions",
        description="Backup, rollback, and lock Augment extension versions"
    )
    version_subparsers = version_parser.add_subparsers(
        dest="version_action",
        help="Version management actions"
    )
    
    version_subparsers.add_parser("status", help="Show current version status")
    version_subparsers.add_parser("backup", help="Backup current version")
    version_subparsers.add_parser("list", help="List available backups")
    
    rollback_parser = version_subparsers.add_parser("rollback", help="Rollback to specific version")
    rollback_parser.add_argument("backup_name", help="Backup name to rollback to")
    
    version_subparsers.add_parser("lock", help="Lock current version")
    version_subparsers.add_parser("unlock", help="Unlock current version")
    
    # VSCode update subcommand
    vscode_parser = subparsers.add_parser(
        "vscode",
        help="Update VSCode safely",
        description="Update VSCode with chat log protection"
    )
    vscode_subparsers = vscode_parser.add_subparsers(
        dest="vscode_action",
        help="VSCode update actions"
    )
    
    update_parser = vscode_subparsers.add_parser("update", help="Update VSCode")
    update_parser.add_argument(
        "--method", 
        choices=["auto", "snap", "apt", "flatpak"], 
        default="auto",
        help="Update method (default: auto)"
    )
    
    vscode_subparsers.add_parser("backup-logs", help="Backup chat logs")
    vscode_subparsers.add_parser("list-backups", help="List chat log backups")
    
    restore_parser = vscode_subparsers.add_parser("restore-logs", help="Restore chat logs")
    restore_parser.add_argument(
        "timestamp", 
        nargs="?", 
        help="Specific backup timestamp to restore"
    )
    
    vscode_subparsers.add_parser("interactive-restore", help="Interactive chat log restoration")
    
    # Status subcommand
    subparsers.add_parser(
        "status",
        help="Show overall system status",
        description="Display Augment extension status, CPU usage, and backup information"
    )
    
    return parser


def handle_detect(args):
    """Handle detection subcommand"""
    # Security check: Don't run as root
    if os.getuid() == 0:
        print("❌ ERROR: This script should not be run as root for security reasons.")
        print("   Running as root exposes process information and broadens attack surface.")
        print("   Please run as a regular user.")
        return 1
    
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
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Detection interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error during detection: {e}")
        return 1


def handle_version(args):
    """Handle version management subcommand"""
    manager = AugmentVersionManager()
    
    if args.version_action == "status":
        manager.show_status()
    elif args.version_action == "backup":
        backup_path = manager.backup_current_version()
        if backup_path:
            print(f"✅ Backup created: {backup_path.name}")
        else:
            print("❌ Backup failed")
            return 1
    elif args.version_action == "list":
        manager.list_backups()
    elif args.version_action == "rollback":
        if manager.rollback_to_version(args.backup_name):
            print("✅ Rollback completed")
        else:
            print("❌ Rollback failed")
            return 1
    elif args.version_action == "lock":
        if manager.lock_version():
            print("✅ Version locked")
        else:
            print("❌ Lock failed")
            return 1
    elif args.version_action == "unlock":
        if manager.unlock_version():
            print("✅ Version unlocked")
        else:
            print("❌ Unlock failed")
            return 1
    else:
        print("❌ No version action specified. Use --help for options.")
        return 1
    
    return 0


def handle_vscode(args):
    """Handle VSCode update subcommand"""
    updater = VSCodeUpdater()
    
    if args.vscode_action == "update":
        if updater.update_vscode(args.method):
            print("✅ VSCode update completed")
            
            # Offer to restore chat logs
            try:
                restore = input("Restore chat logs? (Y/n): ").strip().lower()
                if restore != 'n':
                    updater.restore_chat_logs()
            except KeyboardInterrupt:
                print("\n⚠️ Skipping chat log restoration")
        else:
            print("❌ VSCode update failed")
            return 1
    elif args.vscode_action == "backup-logs":
        backed_up = updater.backup_chat_logs()
        print(f"✅ Backed up {len(backed_up)} files")
    elif args.vscode_action == "list-backups":
        updater.list_chat_backups()
    elif args.vscode_action == "restore-logs":
        if updater.restore_chat_logs(args.timestamp):
            print("✅ Chat logs restored")
        else:
            print("❌ Restore failed")
            return 1
    elif args.vscode_action == "interactive-restore":
        if updater.interactive_chat_restore():
            print("✅ Chat logs restored")
        else:
            print("❌ Restore cancelled or failed")
    else:
        print("❌ No VSCode action specified. Use --help for options.")
        return 1
    
    return 0


def handle_status(args):
    """Handle status subcommand"""
    try:
        from colorama import Fore, Style, init as colorama_init
        colorama_init(autoreset=True)

        def colored_status(status, text):
            if status == "good":
                return f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}"
            elif status == "warning":
                return f"{Fore.YELLOW}⚠️ {text}{Style.RESET_ALL}"
            elif status == "error":
                return f"{Fore.RED}❌ {text}{Style.RESET_ALL}"
            else:
                return f"ℹ️ {text}"
    except ImportError:
        def colored_status(status, text):
            if status == "good":
                return f"✅ {text}"
            elif status == "warning":
                return f"⚠️ {text}"
            elif status == "error":
                return f"❌ {text}"
            else:
                return f"ℹ️ {text}"

    print("📊 AUGMENT SECRET FIX - COMPREHENSIVE STATUS")
    print("=" * 60)

    # System Resources
    import psutil
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    print(f"\n💻 SYSTEM RESOURCES:")

    # CPU Status
    if cpu_usage < 70:
        print(colored_status("good", f"CPU Usage: {cpu_usage:.1f}% (Normal)"))
    elif cpu_usage < 90:
        print(colored_status("warning", f"CPU Usage: {cpu_usage:.1f}% (High)"))
    else:
        print(colored_status("error", f"CPU Usage: {cpu_usage:.1f}% (Critical)"))

    # Memory Status
    if memory.percent < 80:
        print(colored_status("good", f"Memory: {memory.percent:.1f}% ({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)"))
    elif memory.percent < 95:
        print(colored_status("warning", f"Memory: {memory.percent:.1f}% ({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)"))
    else:
        print(colored_status("error", f"Memory: {memory.percent:.1f}% ({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)"))

    # Disk Status
    if disk.percent < 85:
        print(colored_status("good", f"Disk: {disk.percent:.1f}% ({disk.used // 1024 // 1024 // 1024}GB / {disk.total // 1024 // 1024 // 1024}GB)"))
    elif disk.percent < 95:
        print(colored_status("warning", f"Disk: {disk.percent:.1f}% ({disk.used // 1024 // 1024 // 1024}GB / {disk.total // 1024 // 1024 // 1024}GB)"))
    else:
        print(colored_status("error", f"Disk: {disk.percent:.1f}% ({disk.used // 1024 // 1024 // 1024}GB / {disk.total // 1024 // 1024 // 1024}GB)"))

    # Augment Extension Status
    print(f"\n🔧 AUGMENT EXTENSION:")
    manager = AugmentVersionManager()
    current_ext = manager.find_augment_extension()

    if current_ext:
        version = manager.get_extension_version(current_ext)
        lock_file = current_ext / ".version_locked"
        is_locked = lock_file.exists()

        print(colored_status("good", f"Extension Found: {current_ext.name}"))
        print(colored_status("good", f"Version: {version}"))

        if version == "0.467.1":
            print(colored_status("good", "Version Status: SAFE (Recommended stable version)"))
        elif version in ["0.487.x", "0.490.0", "0.491.0"]:
            print(colored_status("error", f"Version Status: PROBLEMATIC (Known issues with {version})"))
        else:
            print(colored_status("warning", f"Version Status: UNKNOWN (Version {version} not in database)"))

        if is_locked:
            print(colored_status("good", "Lock Status: LOCKED (Protected from auto-updates)"))
        else:
            print(colored_status("warning", "Lock Status: UNLOCKED (May auto-update to problematic version)"))
    else:
        print(colored_status("error", "Extension: NOT FOUND"))

    # Process Status
    print(f"\n🔍 PROCESS ANALYSIS:")
    augment_processes = []
    vscode_processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            proc_name = proc.name().lower()
            if 'augment' in proc_name:
                augment_processes.append(proc)
            elif any(keyword in proc_name for keyword in ['vscode', 'code']):
                vscode_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    print(colored_status("info", f"Augment Processes: {len(augment_processes)}"))
    print(colored_status("info", f"VSCode Processes: {len(vscode_processes)}"))

    # High CPU processes
    high_cpu_procs = []
    for proc in augment_processes + vscode_processes:
        try:
            cpu = proc.cpu_percent()
            if cpu > 20:  # High CPU threshold
                high_cpu_procs.append((proc.name(), proc.pid, cpu))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if high_cpu_procs:
        print(colored_status("warning", f"High CPU Processes: {len(high_cpu_procs)}"))
        for name, pid, cpu in high_cpu_procs[:3]:  # Show top 3
            print(f"    • {name} (PID: {pid}): {cpu:.1f}% CPU")
    else:
        print(colored_status("good", "High CPU Processes: None"))

    # Backup Status
    print(f"\n💾 BACKUP STATUS:")
    updater = VSCodeUpdater()
    backups = updater.list_chat_backups()

    if len(backups) > 0:
        print(colored_status("good", f"Chat Log Backups: {len(backups)} available"))
        if len(backups) > 10:
            print(colored_status("warning", f"Many backups found - consider cleanup"))
    else:
        print(colored_status("warning", "Chat Log Backups: None found"))

    # Version backups
    version_backups = list(manager.backup_dir.glob("augment_v*"))
    if len(version_backups) > 0:
        print(colored_status("good", f"Version Backups: {len(version_backups)} available"))
    else:
        print(colored_status("warning", "Version Backups: None found"))

    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    recommendations = []

    if cpu_usage > 80:
        recommendations.append("High CPU detected - run 'augment-fix detect' for detailed analysis")

    if current_ext and not is_locked:
        recommendations.append("Extension not locked - run 'augment-fix version lock' to prevent auto-updates")

    if current_ext and version != "0.467.1":
        recommendations.append("Consider rolling back to stable version 0.467.1")

    if len(backups) == 0:
        recommendations.append("No chat log backups - run 'augment-fix vscode backup-logs'")

    if len(version_backups) == 0:
        recommendations.append("No version backups - run 'augment-fix version backup'")

    if not recommendations:
        print(colored_status("good", "System appears healthy - no immediate actions needed"))
    else:
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

    print(f"\n📋 For detailed analysis, run: augment-fix detect")
    print(f"📖 For help with any command, add --help")

    return 0


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate handler
    if args.command == "detect":
        return handle_detect(args)
    elif args.command == "version":
        return handle_version(args)
    elif args.command == "vscode":
        return handle_vscode(args)
    elif args.command == "status":
        return handle_status(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
