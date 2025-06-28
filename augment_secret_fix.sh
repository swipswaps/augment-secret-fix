#!/bin/bash

# 🛠️ AUGMENT SECRET FIX - Master Control Script
# Comprehensive solution for Augment secrets, CPU contention, version management, and VSCode updates

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="augment_secret_fix.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Check dependencies
check_dependencies() {
    log "🔍 Checking dependencies..."
    
    local missing_deps=()
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Check required Python modules
    if ! python3 -c "import psutil" 2>/dev/null; then
        missing_deps+=("python3-psutil")
    fi
    
    if ! python3 -c "import json" 2>/dev/null; then
        warning "JSON module not available (should be built-in)"
    fi
    
    # Check system tools
    for tool in "ps" "top" "kill" "chmod"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_deps+=("$tool")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        error "Missing dependencies: ${missing_deps[*]}"
        info "Install with: sudo apt install ${missing_deps[*]} (Ubuntu/Debian)"
        info "Or: sudo dnf install ${missing_deps[*]} (Fedora)"
        return 1
    fi
    
    log "✅ All dependencies satisfied"
    return 0
}

# Main menu
show_menu() {
    echo
    echo -e "${CYAN}🛠️ AUGMENT SECRET FIX - MAIN MENU${NC}"
    echo "=" * 50
    echo "1. 🔍 Detect Secrets & CPU Issues"
    echo "2. 📊 Monitor System Resources"
    echo "3. 🔄 Manage Augment Versions"
    echo "4. 🔒 Lock/Unlock Augment Version"
    echo "5. 🔄 Update VSCode (with chat protection)"
    echo "6. 💾 Backup Chat Logs"
    echo "7. 📥 Restore Chat Logs"
    echo "8. 🧹 Emergency Cleanup"
    echo "9. 📋 Show System Status"
    echo "10. ⚙️ Configuration"
    echo "11. 📖 Help & Documentation"
    echo "0. 🚪 Exit"
    echo
}

# Detect secrets and CPU issues
detect_secrets() {
    log "🔍 Starting secrets detection..."
    
    if [ -f "$SCRIPT_DIR/augment_secret_detector.py" ]; then
        python3 "$SCRIPT_DIR/augment_secret_detector.py"
    else
        error "Secret detector script not found"
        return 1
    fi
}

# Monitor system resources
monitor_resources() {
    log "📊 Starting resource monitoring..."
    
    duration=${1:-60}
    info "Monitoring for $duration seconds..."
    
    if [ -f "$SCRIPT_DIR/augment_secret_detector.py" ]; then
        python3 "$SCRIPT_DIR/augment_secret_detector.py" --duration "$duration"
    else
        error "Resource monitor script not found"
        return 1
    fi
}

# Manage Augment versions
manage_versions() {
    log "🔄 Opening version management..."
    
    if [ -f "$SCRIPT_DIR/augment_version_manager.py" ]; then
        echo "Version Management Options:"
        echo "1. Show status"
        echo "2. Create backup"
        echo "3. List backups"
        echo "4. Rollback to version"
        echo "5. Return to main menu"
        
        read -p "Select option (1-5): " choice
        
        case $choice in
            1) python3 "$SCRIPT_DIR/augment_version_manager.py" status ;;
            2) python3 "$SCRIPT_DIR/augment_version_manager.py" backup ;;
            3) python3 "$SCRIPT_DIR/augment_version_manager.py" list ;;
            4) 
                python3 "$SCRIPT_DIR/augment_version_manager.py" list
                read -p "Enter backup name to rollback to: " backup_name
                if [ -n "$backup_name" ]; then
                    python3 "$SCRIPT_DIR/augment_version_manager.py" rollback "$backup_name"
                fi
                ;;
            5) return 0 ;;
            *) error "Invalid option" ;;
        esac
    else
        error "Version manager script not found"
        return 1
    fi
}

# Lock/unlock version
toggle_version_lock() {
    log "🔒 Version lock management..."
    
    if [ -f "$SCRIPT_DIR/augment_version_manager.py" ]; then
        echo "Lock Management Options:"
        echo "1. Lock current version"
        echo "2. Unlock current version"
        echo "3. Check lock status"
        echo "4. Return to main menu"
        
        read -p "Select option (1-4): " choice
        
        case $choice in
            1) python3 "$SCRIPT_DIR/augment_version_manager.py" lock ;;
            2) python3 "$SCRIPT_DIR/augment_version_manager.py" unlock ;;
            3) python3 "$SCRIPT_DIR/augment_version_manager.py" status ;;
            4) return 0 ;;
            *) error "Invalid option" ;;
        esac
    else
        error "Version manager script not found"
        return 1
    fi
}

# Update VSCode
update_vscode() {
    log "🔄 Starting VSCode update with chat protection..."
    
    if [ -f "$SCRIPT_DIR/vscode_updater.py" ]; then
        echo "VSCode Update Options:"
        echo "1. Auto-detect and update"
        echo "2. Update via snap"
        echo "3. Update via apt"
        echo "4. Update via flatpak"
        echo "5. Backup logs only"
        echo "6. Return to main menu"
        
        read -p "Select option (1-6): " choice
        
        case $choice in
            1) python3 "$SCRIPT_DIR/vscode_updater.py" update auto ;;
            2) python3 "$SCRIPT_DIR/vscode_updater.py" update snap ;;
            3) python3 "$SCRIPT_DIR/vscode_updater.py" update apt ;;
            4) python3 "$SCRIPT_DIR/vscode_updater.py" update flatpak ;;
            5) python3 "$SCRIPT_DIR/vscode_updater.py" backup-logs ;;
            6) return 0 ;;
            *) error "Invalid option" ;;
        esac
    else
        error "VSCode updater script not found"
        return 1
    fi
}

# Backup chat logs
backup_chat_logs() {
    log "💾 Backing up chat logs..."
    
    if [ -f "$SCRIPT_DIR/vscode_updater.py" ]; then
        python3 "$SCRIPT_DIR/vscode_updater.py" backup-logs
    else
        error "VSCode updater script not found"
        return 1
    fi
}

# Restore chat logs
restore_chat_logs() {
    log "📥 Restoring chat logs..."
    
    if [ -f "$SCRIPT_DIR/vscode_updater.py" ]; then
        echo "Restore Options:"
        echo "1. Interactive restore (choose from backups)"
        echo "2. Restore latest backup"
        echo "3. List available backups"
        echo "4. Return to main menu"
        
        read -p "Select option (1-4): " choice
        
        case $choice in
            1) python3 "$SCRIPT_DIR/vscode_updater.py" interactive-restore ;;
            2) python3 "$SCRIPT_DIR/vscode_updater.py" restore-logs ;;
            3) python3 "$SCRIPT_DIR/vscode_updater.py" list-backups ;;
            4) return 0 ;;
            *) error "Invalid option" ;;
        esac
    else
        error "VSCode updater script not found"
        return 1
    fi
}

# Emergency cleanup
emergency_cleanup() {
    log "🧹 Starting emergency cleanup..."
    
    warning "This will attempt to resolve high CPU usage and resource contention"
    read -p "Continue with emergency cleanup? (y/N): " confirm
    
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        # Kill high CPU VSCode processes
        log "🔥 Killing high CPU VSCode processes..."
        pkill -f "code.*--type=renderer" 2>/dev/null || true
        pkill -f "code.*--type=gpu-process" 2>/dev/null || true
        
        # Clear temporary files
        log "🗑️ Clearing temporary files..."
        rm -rf /tmp/vscode-* 2>/dev/null || true
        rm -rf ~/.cache/vscode-* 2>/dev/null || true
        
        # Restart VSCode if it was running
        if pgrep -f "code" > /dev/null; then
            log "🔄 Restarting VSCode..."
            pkill -f "code" 2>/dev/null || true
            sleep 3
            nohup code > /dev/null 2>&1 &
        fi
        
        log "✅ Emergency cleanup completed"
    else
        log "❌ Emergency cleanup cancelled"
    fi
}

# Show system status
show_status() {
    log "📋 System Status Report"
    echo "=" * 40
    
    # CPU usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo "💻 CPU Usage: ${cpu_usage}%"
    
    # Memory usage
    memory_info=$(free -h | grep "Mem:")
    echo "🧠 Memory: $memory_info"
    
    # VSCode processes
    vscode_count=$(pgrep -f "code" | wc -l)
    echo "📝 VSCode Processes: $vscode_count"
    
    # Augment extension status
    if [ -f "$SCRIPT_DIR/augment_version_manager.py" ]; then
        echo
        python3 "$SCRIPT_DIR/augment_version_manager.py" status
    fi
}

# Configuration
configure() {
    log "⚙️ Configuration options..."
    
    echo "Configuration Options:"
    echo "1. Set CPU monitoring threshold"
    echo "2. Set monitoring duration"
    echo "3. View current configuration"
    echo "4. Reset to defaults"
    echo "5. Return to main menu"
    
    read -p "Select option (1-5): " choice
    
    case $choice in
        1) 
            read -p "Enter CPU threshold (default 80%): " threshold
            if [[ "$threshold" =~ ^[0-9]+$ ]]; then
                echo "CPU_THRESHOLD=$threshold" > ~/.augment_secret_fix.conf
                log "✅ CPU threshold set to $threshold%"
            else
                error "Invalid threshold value"
            fi
            ;;
        2)
            read -p "Enter monitoring duration in seconds (default 30): " duration
            if [[ "$duration" =~ ^[0-9]+$ ]]; then
                echo "MONITORING_DURATION=$duration" >> ~/.augment_secret_fix.conf
                log "✅ Monitoring duration set to $duration seconds"
            else
                error "Invalid duration value"
            fi
            ;;
        3)
            if [ -f ~/.augment_secret_fix.conf ]; then
                echo "Current configuration:"
                cat ~/.augment_secret_fix.conf
            else
                echo "No configuration file found (using defaults)"
            fi
            ;;
        4)
            rm -f ~/.augment_secret_fix.conf
            log "✅ Configuration reset to defaults"
            ;;
        5) return 0 ;;
        *) error "Invalid option" ;;
    esac
}

# Help and documentation
show_help() {
    echo -e "${CYAN}📖 AUGMENT SECRET FIX - HELP & DOCUMENTATION${NC}"
    echo "=" * 60
    echo
    echo "🎯 PURPOSE:"
    echo "This tool helps resolve Augment extension issues including:"
    echo "  • CPU resource contention from secrets processing"
    echo "  • Version management and rollbacks"
    echo "  • VSCode updates with chat log protection"
    echo "  • System monitoring and cleanup"
    echo
    echo "🔧 MAIN FEATURES:"
    echo "  1. Secret Detection - Monitors CPU and detects secrets activity"
    echo "  2. Version Management - Backup, rollback, and lock Augment versions"
    echo "  3. VSCode Updates - Safe updates with automatic chat log protection"
    echo "  4. Emergency Cleanup - Quick resolution of resource issues"
    echo
    echo "📋 TYPICAL WORKFLOW:"
    echo "  1. Run detection to identify issues"
    echo "  2. Backup current Augment version"
    echo "  3. Lock version to prevent auto-updates"
    echo "  4. Update VSCode safely with chat protection"
    echo "  5. Monitor system for improvements"
    echo
    echo "🆘 EMERGENCY PROCEDURES:"
    echo "  • High CPU: Use Emergency Cleanup (option 8)"
    echo "  • Version issues: Rollback to previous version"
    echo "  • Lost chats: Use Interactive Restore"
    echo
    echo "📁 FILES CREATED:"
    echo "  • ~/.augment_backups/ - Version backups"
    echo "  • ~/.augment_chat_logs/ - Chat log backups"
    echo "  • ~/.vscode_update_backups/ - VSCode update backups"
    echo "  • Various .log files for troubleshooting"
    echo
}

# Main execution
main() {
    log "🛠️ Starting Augment Secret Fix"
    
    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi
    
    # Main loop
    while true; do
        show_menu
        read -p "Select option (0-11): " choice
        
        case $choice in
            1) detect_secrets ;;
            2) 
                read -p "Monitoring duration in seconds (default 60): " duration
                monitor_resources "${duration:-60}"
                ;;
            3) manage_versions ;;
            4) toggle_version_lock ;;
            5) update_vscode ;;
            6) backup_chat_logs ;;
            7) restore_chat_logs ;;
            8) emergency_cleanup ;;
            9) show_status ;;
            10) configure ;;
            11) show_help ;;
            0) 
                log "👋 Goodbye!"
                exit 0
                ;;
            *) error "Invalid option. Please try again." ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
    done
}

# Handle script interruption
trap 'echo -e "\n⚠️ Script interrupted"; exit 1' INT TERM

# Run main function
main "$@"
