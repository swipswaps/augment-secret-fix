#!/usr/bin/env python3
"""
🔄 AUGMENT VERSION MANAGER
Manages Augment extension versions, rollbacks, and locks
"""

import os
import sys
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


class AugmentVersionManager:
    def __init__(self):
        self.vscode_extensions = Path.home() / ".vscode" / "extensions"
        self.backup_dir = Path.home() / ".augment_backups"
        self.config_file = self.backup_dir / "version_config.json"
        self.log_file = "augment_version_manager.log"

        # Ensure backup directory exists
        self.backup_dir.mkdir(exist_ok=True)

    def log(self, message):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)

        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")

    def find_augment_extension(self):
        """Find the current Augment extension directory"""
        if not self.vscode_extensions.exists():
            self.log("❌ VSCode extensions directory not found")
            return None

        # Look for Augment extension patterns
        patterns = ["*augment*", "*Augment*", "*AUGMENT*"]

        for pattern in patterns:
            for ext_dir in self.vscode_extensions.glob(pattern):
                if ext_dir.is_dir():
                    self.log(f"✅ Found Augment extension: {ext_dir.name}")
                    return ext_dir

        self.log("❌ No Augment extension found")
        return None

    def get_extension_version(self, ext_dir):
        """Extract version from extension directory or package.json"""
        if not ext_dir or not ext_dir.exists():
            return "unknown"

        # Try to get version from directory name
        dir_name = ext_dir.name
        if "-" in dir_name:
            parts = dir_name.split("-")
            for part in parts:
                if part.replace(".", "").isdigit():
                    return part

        # Try to get version from package.json
        package_json = ext_dir / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r") as f:
                    data = json.load(f)
                    return data.get("version", "unknown")
            except Exception as e:
                self.log(f"⚠️ Error reading package.json: {e}")

        return "unknown"

    def backup_current_version(self):
        """Backup the current Augment extension"""
        current_ext = self.find_augment_extension()
        if not current_ext:
            return False

        version = self.get_extension_version(current_ext)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"augment_v{version}_{timestamp}"
        backup_path = self.backup_dir / backup_name

        self.log(f"💾 Backing up current version to: {backup_name}")

        try:
            shutil.copytree(current_ext, backup_path)
            self.log(f"✅ Backup completed: {backup_path}")

            # Update config
            self.update_config(
                "backup_created",
                {
                    "version": version,
                    "timestamp": timestamp,
                    "backup_path": str(backup_path),
                    "original_path": str(current_ext),
                },
            )

            return backup_path

        except Exception as e:
            self.log(f"❌ Backup failed: {e}")
            return False

    def list_backups(self):
        """List available backups"""
        self.log("📋 Available Augment backups:")

        backups = []
        for backup_dir in self.backup_dir.glob("augment_v*"):
            if backup_dir.is_dir():
                version = "unknown"
                timestamp = "unknown"

                # Parse backup directory name
                parts = backup_dir.name.split("_")
                if len(parts) >= 3:
                    version = parts[1].replace("v", "")
                    timestamp = f"{parts[2]}_{parts[3]}" if len(parts) > 3 else parts[2]

                backup_info = {
                    "path": backup_dir,
                    "name": backup_dir.name,
                    "version": version,
                    "timestamp": timestamp,
                    "size_mb": self.get_directory_size(backup_dir),
                }

                backups.append(backup_info)
                self.log(
                    f"  📦 {backup_dir.name} - Version: {version}, Size: {backup_info['size_mb']:.1f}MB"
                )

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

        return total_size / 1024 / 1024  # Convert to MB

    def rollback_to_version(self, backup_name_or_path):
        """Rollback to a specific backup version"""
        # Find backup
        if os.path.isabs(backup_name_or_path):
            backup_path = Path(backup_name_or_path)
        else:
            backup_path = self.backup_dir / backup_name_or_path

        if not backup_path.exists():
            self.log(f"❌ Backup not found: {backup_path}")
            return False

        # Find current extension
        current_ext = self.find_augment_extension()
        if not current_ext:
            self.log("❌ No current Augment extension found to replace")
            return False

        self.log(f"🔄 Rolling back to: {backup_path.name}")

        try:
            # Backup current version before rollback
            self.backup_current_version()

            # Remove current extension
            self.log(f"🗑️ Removing current extension: {current_ext.name}")
            shutil.rmtree(current_ext)

            # Restore backup
            self.log(f"📥 Restoring backup: {backup_path.name}")
            shutil.copytree(backup_path, current_ext)

            # Update config
            self.update_config(
                "rollback_completed",
                {
                    "backup_used": str(backup_path),
                    "restored_to": str(current_ext),
                    "timestamp": datetime.now().isoformat(),
                },
            )

            self.log("✅ Rollback completed successfully")
            return True

        except Exception as e:
            self.log(f"❌ Rollback failed: {e}")
            return False

    def lock_version(self):
        """Lock the current Augment version to prevent updates"""
        current_ext = self.find_augment_extension()
        if not current_ext:
            return False

        version = self.get_extension_version(current_ext)

        # Create lock file
        lock_file = current_ext / ".version_locked"
        lock_info = {
            "locked_at": datetime.now().isoformat(),
            "version": version,
            "locked_by": "augment_version_manager",
        }

        try:
            with open(lock_file, "w") as f:
                json.dump(lock_info, f, indent=2)

            # Make extension directory read-only
            os.chmod(current_ext, 0o555)

            self.log(f"🔒 Version locked: {version}")

            # Update config
            self.update_config(
                "version_locked",
                {
                    "version": version,
                    "timestamp": datetime.now().isoformat(),
                    "extension_path": str(current_ext),
                },
            )

            return True

        except Exception as e:
            self.log(f"❌ Failed to lock version: {e}")
            return False

    def unlock_version(self):
        """Unlock the current Augment version"""
        current_ext = self.find_augment_extension()
        if not current_ext:
            return False

        lock_file = current_ext / ".version_locked"

        try:
            # Restore write permissions
            os.chmod(current_ext, 0o755)

            # Remove lock file
            if lock_file.exists():
                lock_file.unlink()

            self.log("🔓 Version unlocked")

            # Update config
            self.update_config(
                "version_unlocked",
                {
                    "timestamp": datetime.now().isoformat(),
                    "extension_path": str(current_ext),
                },
            )

            return True

        except Exception as e:
            self.log(f"❌ Failed to unlock version: {e}")
            return False

    def update_config(self, action, data):
        """Update configuration file"""
        config = {}

        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
            except Exception:
                config = {}

        if "history" not in config:
            config["history"] = []

        config["history"].append(
            {"action": action, "timestamp": datetime.now().isoformat(), "data": data}
        )

        # Keep only last 50 entries
        config["history"] = config["history"][-50:]

        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.log(f"⚠️ Failed to update config: {e}")

    def show_status(self):
        """Show current Augment extension status"""
        self.log("📊 AUGMENT VERSION STATUS")
        self.log("=" * 40)

        current_ext = self.find_augment_extension()
        if current_ext:
            version = self.get_extension_version(current_ext)
            size_mb = self.get_directory_size(current_ext)
            lock_file = current_ext / ".version_locked"
            is_locked = lock_file.exists()

            self.log(f"📦 Extension: {current_ext.name}")
            self.log(f"🏷️ Version: {version}")
            self.log(f"📏 Size: {size_mb:.1f}MB")
            self.log(f"🔒 Locked: {'Yes' if is_locked else 'No'}")

            if is_locked:
                try:
                    with open(lock_file, "r") as f:
                        lock_info = json.load(f)
                        self.log(
                            f"🕐 Locked at: {lock_info.get('locked_at', 'Unknown')}"
                        )
                except Exception:
                    pass
        else:
            self.log("❌ No Augment extension found")

        # Show backup count
        backups = list(self.backup_dir.glob("augment_v*"))
        self.log(f"💾 Backups available: {len(backups)}")


def main():
    if len(sys.argv) < 2:
        print(
            """
🔄 AUGMENT VERSION MANAGER

Usage: python3 augment_version_manager.py <command> [options]

Commands:
    status          Show current extension status
    backup          Backup current version
    list            List available backups
    rollback <name> Rollback to specific backup
    lock            Lock current version
    unlock          Unlock current version

Examples:
    python3 augment_version_manager.py status
    python3 augment_version_manager.py backup
    python3 augment_version_manager.py rollback augment_v1.2.3_20250627_120000
        """
        )
        return

    manager = AugmentVersionManager()
    command = sys.argv[1].lower()

    try:
        if command == "status":
            manager.show_status()

        elif command == "backup":
            backup_path = manager.backup_current_version()
            if backup_path:
                print(f"✅ Backup created: {backup_path.name}")
            else:
                print("❌ Backup failed")

        elif command == "list":
            manager.list_backups()

        elif command == "rollback":
            if len(sys.argv) < 3:
                print("❌ Please specify backup name")
                return

            backup_name = sys.argv[2]
            if manager.rollback_to_version(backup_name):
                print("✅ Rollback completed")
            else:
                print("❌ Rollback failed")

        elif command == "lock":
            if manager.lock_version():
                print("✅ Version locked")
            else:
                print("❌ Lock failed")

        elif command == "unlock":
            if manager.unlock_version():
                print("✅ Version unlocked")
            else:
                print("❌ Unlock failed")

        else:
            print(f"❌ Unknown command: {command}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
