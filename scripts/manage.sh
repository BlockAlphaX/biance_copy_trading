#!/usr/bin/env bash

# Binance Copy Trading Management Script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="${PROJECT_DIR}/venv"
PID_FILE="${PROJECT_DIR}/app.pid"

cd "$PROJECT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found. Run 'make setup' first."
        exit 1
    fi
}

activate_venv() {
    source "${VENV_DIR}/bin/activate"
}

start_app() {
    check_venv
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_warn "Application is already running (PID: $PID)"
            return 0
        fi
    fi
    
    log_info "Starting Binance Copy Trading..."
    activate_venv
    
    nohup python web_server.py > logs/app.log 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 2
    
    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        log_info "Application started successfully (PID: $(cat "$PID_FILE"))"
        log_info "Access dashboard at: http://localhost:8000"
    else
        log_error "Failed to start application"
        rm -f "$PID_FILE"
        exit 1
    fi
}

stop_app() {
    if [ ! -f "$PID_FILE" ]; then
        log_warn "Application is not running"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ! ps -p "$PID" > /dev/null 2>&1; then
        log_warn "Process not found, cleaning up PID file"
        rm -f "$PID_FILE"
        return 0
    fi
    
    log_info "Stopping application (PID: $PID)..."
    kill "$PID"
    
    # Wait for process to stop
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            log_info "Application stopped successfully"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    log_warn "Process did not stop gracefully, forcing..."
    kill -9 "$PID" 2>/dev/null || true
    rm -f "$PID_FILE"
    log_info "Application stopped"
}

restart_app() {
    log_info "Restarting application..."
    stop_app
    sleep 2
    start_app
}

status_app() {
    if [ ! -f "$PID_FILE" ]; then
        log_info "Application is ${RED}not running${NC}"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        log_info "Application is ${GREEN}running${NC} (PID: $PID)"
        
        # Show resource usage
        ps -p "$PID" -o pid,ppid,%cpu,%mem,etime,cmd
        return 0
    else
        log_info "Application is ${RED}not running${NC} (stale PID file)"
        rm -f "$PID_FILE"
        return 1
    fi
}

show_logs() {
    local lines="${1:-50}"
    
    if [ -f "logs/app.log" ]; then
        log_info "Showing last $lines lines of application log:"
        tail -n "$lines" logs/app.log
    else
        log_warn "Log file not found"
    fi
}

follow_logs() {
    if [ -f "logs/app.log" ]; then
        log_info "Following application log (Ctrl+C to stop):"
        tail -f logs/app.log
    else
        log_warn "Log file not found"
    fi
}

show_help() {
    cat <<EOF
Binance Copy Trading Management Script

Usage: $0 <command> [options]

Commands:
    start       Start the application
    stop        Stop the application
    restart     Restart the application
    status      Show application status
    logs        Show application logs (default: last 50 lines)
    logs <n>    Show last n lines of logs
    follow      Follow application logs in real-time
    help        Show this help message

Examples:
    $0 start
    $0 stop
    $0 restart
    $0 status
    $0 logs 100
    $0 follow

EOF
}

# Main
case "${1:-}" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        status_app
        ;;
    logs)
        show_logs "${2:-50}"
        ;;
    follow)
        follow_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: ${1:-}"
        echo ""
        show_help
        exit 1
        ;;
esac
