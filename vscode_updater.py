#!/usr/bin/env python3
"""
🔄 VSCODE UPDATER WITH CHAT LOG PROTECTION
Updates VSCode while protecting current chat logs and offering recovery options
"""

import os
import sys
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

class VSCodeUpdater:
    def __init__(self):
        # Support both VSCode and VSCode Insiders
        self.vscode_configs = [
            Path.home() / ".config" / "Code" / "User",
            Path.home() / ".config" / "Code - Insiders" / "User"
        ]
        self.chat_logs_dir = Path.home() / ".augment_chat_logs"
        self.backup_dir = Path.home() / ".vscode_update_backups"
        self.log_file = "vscode_updater.log"

        # Ensure directories exist
        self.chat_logs_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
    def log(self, message):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def find_chat_logs(self):
        """Find all Augment chat logs"""
        chat_logs = []
        
        # Common chat log locations for both VSCode and Insiders
        search_paths = []

        # Add paths for all VSCode configurations
        for config in self.vscode_configs:
            if config.exists():
                search_paths.extend([
                    config / "globalStorage",
                    config / "workspaceStorage",
                    config.parent / "logs"
                ])

        # Add extension directories
        search_paths.extend([
            Path.home() / ".vscode" / "extensions",
            Path.home() / ".vscode-insiders" / "extensions"
        ])
        
        for search_path in search_paths:
            if search_path.exists():
                # Look for Augment-related files
                for pattern in ["*augment*", "*chat*", "*conversation*"]:
                    for file_path in search_path.rglob(pattern):
                        if file_path.is_file() and file_path.suffix in ['.json', '.log', '.txt', '.db']:
                            chat_logs.append(file_path)
                            self.log(f"📝 Found chat log: {file_path}")
        
        return chat_logs
    
    def backup_chat_logs(self):
        """Backup all chat logs before VSCode update"""
        self.log("💾 Backing up chat logs...")
        
        chat_logs = self.find_chat_logs()
        if not chat_logs:
            self.log("⚠️ No chat logs found")
            return []
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_session_dir = self.backup_dir / f"chat_backup_{timestamp}"
        backup_session_dir.mkdir(exist_ok=True)
        
        backed_up_files = []
        
        for log_file in chat_logs:
            try:
                # Create relative path structure in backup
                relative_path = log_file.relative_to(Path.home())
                backup_path = backup_session_dir / relative_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(log_file, backup_path)
                backed_up_files.append({
                    "original": str(log_file),
                    "backup": str(backup_path),
                    "size": log_file.stat().st_size
                })
                
                self.log(f"✅ Backed up: {log_file.name}")
            
            except Exception as e:
                self.log(f"❌ Failed to backup {log_file}: {e}")
        
        # Save backup manifest
        manifest = {
            "timestamp": timestamp,
            "backup_dir": str(backup_session_dir),
            "files": backed_up_files,
            "total_files": len(backed_up_files)
        }
        
        manifest_file = backup_session_dir / "backup_manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        self.log(f"📋 Backup manifest saved: {manifest_file}")
        self.log(f"✅ Backed up {len(backed_up_files)} chat log files")
        
        return backed_up_files
    
    def list_chat_backups(self):
        """List available chat log backups"""
        self.log("📋 Available chat log backups:")
        
        backups = []
        for backup_dir in self.backup_dir.glob("chat_backup_*"):
            if backup_dir.is_dir():
                manifest_file = backup_dir / "backup_manifest.json"
                
                if manifest_file.exists():
                    try:
                        with open(manifest_file, 'r') as f:
                            manifest = json.load(f)
                        
                        backup_info = {
                            "timestamp": manifest.get("timestamp", "unknown"),
                            "path": backup_dir,
                            "file_count": manifest.get("total_files", 0),
                            "size_mb": self.get_directory_size(backup_dir)
                        }
                        
                        backups.append(backup_info)
                        self.log(f"  📦 {backup_dir.name} - Files: {backup_info['file_count']}, Size: {backup_info['size_mb']:.1f}MB")
                    
                    except Exception as e:
                        self.log(f"⚠️ Error reading manifest for {backup_dir.name}: {e}")
        
        return backups
    
    def get_directory_size(self, path):
        """Get directory size in MB"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        
        return total_size / 1024 / 1024
    
    def restore_chat_logs(self, backup_timestamp=None):
        """Restore chat logs from backup"""
        if backup_timestamp:
            backup_dir = self.backup_dir / f"chat_backup_{backup_timestamp}"
        else:
            # Find most recent backup
            backups = sorted(self.backup_dir.glob("chat_backup_*"), reverse=True)
            if not backups:
                self.log("❌ No backups found")
                return False
            backup_dir = backups[0]
        
        if not backup_dir.exists():
            self.log(f"❌ Backup not found: {backup_dir}")
            return False
        
        manifest_file = backup_dir / "backup_manifest.json"
        if not manifest_file.exists():
            self.log(f"❌ Backup manifest not found: {manifest_file}")
            return False
        
        self.log(f"📥 Restoring chat logs from: {backup_dir.name}")
        
        try:
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            restored_count = 0
            for file_info in manifest.get("files", []):
                backup_path = Path(file_info["backup"])
                original_path = Path(file_info["original"])
                
                if backup_path.exists():
                    # Ensure parent directory exists
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Restore file
                    shutil.copy2(backup_path, original_path)
                    restored_count += 1
                    self.log(f"✅ Restored: {original_path.name}")
            
            self.log(f"✅ Restored {restored_count} chat log files")
            return True
        
        except Exception as e:
            self.log(f"❌ Restore failed: {e}")
            return False
    
    def update_vscode(self, method="auto"):
        """Update VSCode using specified method"""
        self.log(f"🔄 Starting VSCode update (method: {method})")
        
        # Backup chat logs first
        self.backup_chat_logs()
        
        try:
            if method == "snap":
                self.log("📦 Updating VSCode via snap...")
                result = subprocess.run(["sudo", "snap", "refresh", "code"], 
                                      capture_output=True, text=True, timeout=300)
            
            elif method == "apt":
                self.log("📦 Updating VSCode via apt...")
                subprocess.run(["sudo", "apt", "update"], check=True, timeout=60)
                result = subprocess.run(["sudo", "apt", "upgrade", "code"], 
                                      capture_output=True, text=True, timeout=300)
            
            elif method == "flatpak":
                self.log("📦 Updating VSCode via flatpak...")
                result = subprocess.run(["flatpak", "update", "com.visualstudio.code"], 
                                      capture_output=True, text=True, timeout=300)
            
            elif method == "download":
                self.log("📦 Downloading latest VSCode...")
                # This would implement direct download and install
                self.log("⚠️ Direct download method not implemented yet")
                return False
            
            else:  # auto method
                self.log("🔍 Auto-detecting VSCode installation method...")
                
                # Try snap first
                if shutil.which("snap"):
                    snap_result = subprocess.run(["snap", "list", "code"], 
                                               capture_output=True, text=True)
                    if snap_result.returncode == 0:
                        return self.update_vscode("snap")
                
                # Try apt
                if shutil.which("apt"):
                    return self.update_vscode("apt")
                
                # Try flatpak
                if shutil.which("flatpak"):
                    return self.update_vscode("flatpak")
                
                self.log("❌ No supported package manager found")
                return False
            
            if result.returncode == 0:
                self.log("✅ VSCode update completed successfully")
                self.log(f"📄 Output: {result.stdout}")
                return True
            else:
                self.log(f"❌ VSCode update failed: {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            self.log("⏰ VSCode update timed out")
            return False
        except Exception as e:
            self.log(f"❌ VSCode update error: {e}")
            return False
    
    def interactive_chat_restore(self):
        """Interactive menu for choosing chat logs to restore"""
        backups = self.list_chat_backups()
        
        if not backups:
            self.log("❌ No chat log backups available")
            return False
        
        print("\n🔄 CHAT LOG RESTORATION")
        print("=" * 40)
        print("Available backups:")
        
        for i, backup in enumerate(backups, 1):
            timestamp = backup["timestamp"]
            file_count = backup["file_count"]
            size_mb = backup["size_mb"]
            print(f"  {i}. {timestamp} - {file_count} files ({size_mb:.1f}MB)")
        
        print(f"  {len(backups) + 1}. Cancel")
        
        try:
            choice = input("\nSelect backup to restore (number): ").strip()
            choice_num = int(choice)
            
            if choice_num == len(backups) + 1:
                print("❌ Restoration cancelled")
                return False
            
            if 1 <= choice_num <= len(backups):
                selected_backup = backups[choice_num - 1]
                timestamp = selected_backup["timestamp"]
                
                confirm = input(f"Restore backup from {timestamp}? (y/N): ").strip().lower()
                if confirm == 'y':
                    return self.restore_chat_logs(timestamp)
                else:
                    print("❌ Restoration cancelled")
                    return False
            else:
                print("❌ Invalid selection")
                return False
        
        except (ValueError, KeyboardInterrupt):
            print("❌ Invalid input or cancelled")
            return False

def main():
    if len(sys.argv) < 2:
        print("""
🔄 VSCODE UPDATER WITH CHAT LOG PROTECTION

Usage: python3 vscode_updater.py <command> [options]

Commands:
    update [method]     Update VSCode (methods: auto, snap, apt, flatpak)
    backup-logs         Backup chat logs only
    list-backups        List available chat log backups
    restore-logs [timestamp]  Restore chat logs
    interactive-restore Interactive chat log restoration

Examples:
    python3 vscode_updater.py update
    python3 vscode_updater.py update snap
    python3 vscode_updater.py backup-logs
    python3 vscode_updater.py restore-logs 20250627_120000
    python3 vscode_updater.py interactive-restore
        """)
        return
    
    updater = VSCodeUpdater()
    command = sys.argv[1].lower()
    
    try:
        if command == "update":
            method = sys.argv[2] if len(sys.argv) > 2 else "auto"
            if updater.update_vscode(method):
                print("✅ VSCode update completed")
                
                # Offer to restore chat logs
                restore = input("Restore chat logs? (Y/n): ").strip().lower()
                if restore != 'n':
                    updater.restore_chat_logs()
            else:
                print("❌ VSCode update failed")
        
        elif command == "backup-logs":
            backed_up = updater.backup_chat_logs()
            print(f"✅ Backed up {len(backed_up)} files")
        
        elif command == "list-backups":
            updater.list_chat_backups()
        
        elif command == "restore-logs":
            timestamp = sys.argv[2] if len(sys.argv) > 2 else None
            if updater.restore_chat_logs(timestamp):
                print("✅ Chat logs restored")
            else:
                print("❌ Restore failed")
        
        elif command == "interactive-restore":
            if updater.interactive_chat_restore():
                print("✅ Chat logs restored")
            else:
                print("❌ Restore cancelled or failed")
        
        else:
            print(f"❌ Unknown command: {command}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
