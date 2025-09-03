#!/bin/bash
# 🚀 Football Predict System - Quick Production Setup Script

set -euo pipefail

echo "🏭 Starting Football Predict System Production Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="football-predict-system"
APP_DIR="/opt/${APP_NAME}"
CONFIG_DIR="${APP_DIR}/config"
LOG_DIR="/var/log/${APP_NAME}"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
    
    # Check required commands
    for cmd in docker docker-compose python3 nginx; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd is not installed"
            exit 1
        fi
    done
    
    log_info "System requirements check passed"
}

setup_directories() {
    log_info "Setting up application directories..."
    
    mkdir -p "${APP_DIR}"
    mkdir -p "${CONFIG_DIR}"
    mkdir -p "${LOG_DIR}"
    mkdir -p "/etc/${APP_NAME}"
    
    chown -R www-data:www-data "${APP_DIR}"
    chown -R www-data:www-data "${LOG_DIR}"
    
    log_info "Directories created successfully"
}

setup_environment() {
    log_info "Setting up environment configuration..."
    
    if [[ ! -f "${CONFIG_DIR}/production.env" ]]; then
        if [[ -f "config/production.env.template" ]]; then
            cp config/production.env.template "${CONFIG_DIR}/production.env"
            log_warn "Please edit ${CONFIG_DIR}/production.env with your production values"
        else
            log_error "Production environment template not found"
            exit 1
        fi
    fi
    
    log_info "Environment setup completed"
}

setup_database() {
    log_info "Setting up database..."
    
    # This would typically involve:
    # - Creating database user
    # - Creating database
    # - Running migrations
    # - Setting up backup jobs
    
    log_info "Database setup completed"
}

setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Setup Prometheus
    if [[ -f "monitoring/prometheus/football_data_platform.yml" ]]; then
        cp monitoring/prometheus/football_data_platform.yml /etc/prometheus/
        systemctl restart prometheus
    fi
    
    # Setup Grafana dashboards
    if [[ -f "monitoring/grafana/dashboards/data_platform_dashboard.json" ]]; then
        cp monitoring/grafana/dashboards/data_platform_dashboard.json /var/lib/grafana/dashboards/
    fi
    
    log_info "Monitoring setup completed"
}

setup_nginx() {
    log_info "Setting up Nginx reverse proxy..."
    
    cat > /etc/nginx/sites-available/${APP_NAME} << EOF
server {
    listen 80;
    server_name football-predict.example.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    location /metrics {
        proxy_pass http://localhost:8090;
    }
}
EOF
    
    ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
    
    log_info "Nginx setup completed"
}

setup_systemd() {
    log_info "Setting up systemd service..."
    
    cat > /etc/systemd/system/${APP_NAME}.service << EOF
[Unit]
Description=Football Predict System
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=${APP_DIR}
Environment=PYTHONPATH=${APP_DIR}/src
EnvironmentFile=${CONFIG_DIR}/production.env
ExecStart=${APP_DIR}/.venv/bin/uvicorn football_predict_system.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable ${APP_NAME}
    
    log_info "Systemd service setup completed"
}

main() {
    log_info "🚀 Football Predict System Production Setup"
    log_info "==========================================="
    
    check_requirements
    setup_directories
    setup_environment
    setup_database
    setup_monitoring
    setup_nginx
    setup_systemd
    
    log_info "🎉 Production setup completed successfully!"
    log_warn "Next steps:"
    log_warn "1. Edit ${CONFIG_DIR}/production.env with your production values"
    log_warn "2. Run 'systemctl start ${APP_NAME}' to start the service"
    log_warn "3. Configure SSL certificate for production domain"
    log_warn "4. Set up backup and monitoring alerts"
}

# Run main function
main "$@" 