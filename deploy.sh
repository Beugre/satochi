#!/bin/bash
# 🚀 SCRIPT DE DÉPLOIEMENT VPS - SATOCHI BOT
# Déploiement automatisé sur serveur Linux (Debian/Ubuntu)

set -e  # Arrêt en cas d'erreur

echo "🚀 DÉPLOIEMENT SATOCHI BOT - RSI SCALPING PRO"
echo "=============================================="

# Couleurs pour les     # Script de statut du bot
    tee /usr/local/bin/status-satochi-bot > /dev/null << 'EOF'
#!/bin/bash
echo "📊 Statut du bot Satochi..."
systemctl status satochi-tradebot
echo ""
echo "📊 Statut service binance-live..."
systemctl status satochi-binance-live
echo ""
echo "📝 Derniers logs bot:"
tail -20 /var/log/satochi-bot/bot.log
echo ""
echo "📝 Derniers logs binance-live:"
tail -10 /var/log/satochi-bot/binance-live.log
EOF033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BOT_USER="root"
BOT_DIR="/opt/satochi_bot"
LOG_DIR="/var/log/satochi-bot"
SERVICE_NAME="satochi-tradebot"
VPS_IP="213.199.41.168"

echo -e "${BLUE}📋 Configuration:${NC}"
echo "  • Utilisateur: $BOT_USER"
echo "  • Répertoire: $BOT_DIR"
echo "  • Logs: $LOG_DIR"
echo "  • Service: $SERVICE_NAME"
echo "  • VPS: $VPS_IP"
echo ""

# Fonction de log
log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérification des prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    # Vérification du système
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 n'est pas installé"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 n'est pas installé"
        exit 1
    fi
    
    log_info "Prérequis validés"
}

# Installation des dépendances système
install_system_dependencies() {
    log_info "Installation des dépendances système..."
    
    apt update
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        git \
        curl \
        wget \
        htop \
        nano \
        screen \
        nginx \
        certbot \
        python3-certbot-nginx
    
    log_info "Dépendances système installées"
}

# Création de l'utilisateur et des répertoires
setup_user_directories() {
    log_info "Configuration des répertoires..."
    
    # Création du répertoire principal dans /opt
    mkdir -p $BOT_DIR
    chmod 755 $BOT_DIR
    
    # Création du répertoire de logs
    mkdir -p $LOG_DIR
    chown $BOT_USER:$BOT_USER $LOG_DIR
    chmod 755 $LOG_DIR
    
    log_info "Répertoires configurés"
}

# Installation du bot
install_bot() {
    log_info "Installation du bot Satochi..."
    
    # Vérification que nous sommes dans le bon répertoire source
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Changement vers le répertoire /opt
    cd /opt
    
    # Si le répertoire existe déjà, sauvegarde
    if [ -d "satochi_bot" ]; then
        echo "Sauvegarde de l'ancienne installation..."
        mv satochi_bot satochi_bot_backup_$(date +%Y%m%d_%H%M%S)
    fi
    
    # Copie des fichiers du bot depuis le répertoire source
    cp -r "$SCRIPT_DIR" satochi_bot
    cd satochi_bot
    
    # Nettoyage des fichiers inutiles
    rm -f deploy.sh
    rm -rf .git
    
    # Création de l'environnement virtuel
    python3 -m venv venv
    source venv/bin/activate
    
    # Installation des dépendances Python
    pip install --upgrade pip
    
    # Installation depuis requirements_bot.txt (bot de trading)
    if [ -f "requirements_bot.txt" ]; then
        pip install -r requirements_bot.txt
        log_info "Dépendances bot installées depuis requirements_bot.txt"
    else
        # Fallback si le fichier n'existe pas
        pip install \
            ccxt \
            pandas \
            numpy \
            ta-lib \
            python-telegram-bot \
            firebase-admin \
            python-binance \
            requests \
            pytz \
            schedule \
            python-dotenv
        log_info "Dépendances bot installées (fallback)"
    fi \
        python-dotenv
    
    echo "Bot installé avec succès dans $BOT_DIR"
    
    log_info "Bot installé"
}

# Configuration du service binance-live
create_binance_live_service() {
    log_info "Configuration du service binance-live..."
    
    # Copier le fichier service depuis systemd/
    cp systemd/satochi-binance-live.service /etc/systemd/system/
    
    log_info "Service binance-live configuré"
}

# Configuration du service systemd
setup_systemd_service() {
    log_info "Configuration des services systemd..."
    
    # Service principal du bot (toujours nécessaire)
    cp systemd/satochi-tradebot.service /etc/systemd/system/
    
    # Service binance-live (nouveau)
    create_binance_live_service
    
    systemctl daemon-reload
    systemctl enable satochi-tradebot.service
    systemctl enable satochi-binance-live.service
    
    log_info "Services du bot et binance-live configurés"
    log_info "Note: Le service dashboard est commenté car vous utilisez Streamlit Cloud"
}

# Configuration de Nginx (optionnel - pour reverse proxy)
setup_nginx() {
    read -p "Voulez-vous installer Nginx pour reverse proxy? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Installation de Nginx..."
        
        apt update
        apt install -y nginx
        
        # Configuration basique
        tee /etc/nginx/sites-available/default > /dev/null << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    root /var/www/html;
    index index.html index.htm;
    
    server_name _;
    
    location / {
        try_files $uri $uri/ =404;
    }
}
EOF
        
        systemctl restart nginx
        systemctl enable nginx
        
        log_info "Nginx installé et configuré"
    else
        log_info "Nginx ignoré"
    fi
}

# Configuration des certificats SSL (optionnel)
setup_ssl() {
    read -p "Voulez-vous configurer SSL avec Let's Encrypt? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Entrez votre domaine (ex: bot.example.com): " domain
        if [ ! -z "$domain" ]; then
            log_info "Configuration SSL pour $domain..."
            certbot --nginx -d $domain
            log_info "SSL configuré"
        fi
    fi
}

# Configuration du firewall
setup_firewall() {
    log_info "Configuration du firewall..."
    
    ufw allow ssh
    ufw allow 'OpenSSH'
    ufw --force enable
    
    log_info "Firewall configuré (SSH autorisé)"
}

# Création des scripts de gestion
create_management_scripts() {
    log_info "Création des scripts de gestion..."
    
    # Script de démarrage du bot
    tee /usr/local/bin/start-satochi-bot > /dev/null << 'EOF'
#!/bin/bash
echo "🚀 Démarrage du bot Satochi..."
systemctl start satochi-tradebot
systemctl start satochi-binance-live
systemctl status satochi-tradebot
systemctl status satochi-binance-live
EOF
    
    # Script d'arrêt du bot
    tee /usr/local/bin/stop-satochi-bot > /dev/null << 'EOF'
#!/bin/bash
echo "⏹️ Arrêt du bot Satochi..."
systemctl stop satochi-tradebot
systemctl stop satochi-binance-live
systemctl status satochi-tradebot
systemctl status satochi-binance-live
EOF
    
    # Script de redémarrage du bot
    tee /usr/local/bin/restart-satochi-bot > /dev/null << 'EOF'
#!/bin/bash
echo "🔄 Redémarrage du bot Satochi..."
systemctl restart satochi-tradebot
systemctl restart satochi-binance-live
systemctl status satochi-tradebot
systemctl status satochi-binance-live
EOF
    
    # Script de statut du bot
    tee /usr/local/bin/status-satochi-bot > /dev/null << 'EOF'
#!/bin/bash
echo "📊 Statut du bot Satochi..."
systemctl status satochi-tradebot
echo ""
echo "� Statut service binance-live..."
systemctl status satochi-binance-live
echo ""
echo "�📝 Derniers logs bot:"
tail -20 /var/log/satochi-bot/bot.log
echo ""
echo "📝 Derniers logs binance-live:"
tail -10 /var/log/satochi-bot/binance-live.log
EOF
    
    # Script de démarrage du dashboard
    tee /usr/local/bin/start-satochi-dashboard > /dev/null << 'EOF'
#!/bin/bash
echo "📊 Démarrage du dashboard Satochi..."
cd /opt/satochi_bot
source venv/bin/activate
streamlit run streamlit_dashboard/app.py --server.port 8501 --server.address 0.0.0.0 &
echo "Dashboard démarré sur http://localhost:8501"
EOF
    
    # Permissions d'exécution
    chmod +x /usr/local/bin/start-satochi-bot
    chmod +x /usr/local/bin/stop-satochi-bot
    chmod +x /usr/local/bin/restart-satochi-bot
    chmod +x /usr/local/bin/status-satochi-bot
    chmod +x /usr/local/bin/start-satochi-dashboard
    
    log_info "Scripts de gestion créés"
}

# Configuration de la rotation des logs
setup_log_rotation() {
    log_info "Configuration de la rotation des logs..."
    
    tee /etc/logrotate.d/satochi-bot > /dev/null << 'EOF'
/var/log/satochi-bot/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload-or-restart satochi-tradebot
    endscript
}
EOF
    
    log_info "Rotation des logs configurée"
}

# Configuration de monitoring simple
setup_monitoring() {
    log_info "Configuration du monitoring..."
    
    # Script de monitoring
    sudo tee /usr/local/bin/monitor-satochi-bot > /dev/null << 'EOF'
#!/bin/bash
# Script de monitoring simple pour le bot Satochi

LOG_FILE="/var/log/satochi-bot/monitor.log"
BOT_SERVICE="satochi-tradebot"
BINANCE_SERVICE="satochi-binance-live"

# Fonction de log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Vérification du service principal
if ! systemctl is-active --quiet $BOT_SERVICE; then
    log "❌ Service $BOT_SERVICE arrêté - Redémarrage..."
    systemctl start $BOT_SERVICE
    sleep 10
    if systemctl is-active --quiet $BOT_SERVICE; then
        log "✅ Service $BOT_SERVICE redémarré avec succès"
    else
        log "🚨 ÉCHEC redémarrage du service $BOT_SERVICE"
    fi
else
    log "✅ Service $BOT_SERVICE actif"
fi

# Vérification du service binance-live
if ! systemctl is-active --quiet $BINANCE_SERVICE; then
    log "❌ Service $BINANCE_SERVICE arrêté - Redémarrage..."
    systemctl start $BINANCE_SERVICE
    sleep 10
    if systemctl is-active --quiet $BINANCE_SERVICE; then
        log "✅ Service $BINANCE_SERVICE redémarré avec succès"
    else
        log "🚨 ÉCHEC redémarrage du service $BINANCE_SERVICE"
    fi
else
    log "✅ Service $BINANCE_SERVICE actif"
fi

# Vérification de l'utilisation mémoire
MEM_USAGE=$(ps -o pid,ppid,cmd,%mem,%cpu --sort=-%mem -C python3 | grep main.py | awk '{print $4}' | head -1)
if [ ! -z "$MEM_USAGE" ] && [ $(echo "$MEM_USAGE > 80" | bc -l) -eq 1 ]; then
    log "⚠️ Utilisation mémoire élevée: ${MEM_USAGE}%"
fi
EOF
    
    sudo chmod +x /usr/local/bin/monitor-satochi-bot
    
    # Ajout au crontab pour monitoring automatique
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/monitor-satochi-bot") | crontab -
    
    log_info "Monitoring configuré"
}

# Affichage des informations de déploiement
display_deployment_info() {
    log_info "Déploiement terminé avec succès!"
    echo ""
    echo -e "${BLUE}📋 INFORMATIONS DE DÉPLOIEMENT${NC}"
    echo "=================================="
    echo "Bot installé dans: $BOT_DIR"
    echo "Logs disponibles dans: $LOG_DIR"
    echo "Services systemd: satochi-tradebot + satochi-binance-live"
    echo ""
    echo -e "${BLUE}� STRUCTURE DES FICHIERS:${NC}"
    echo "• Bot principal: /opt/satochi_bot/main.py"
    echo "• Service binance-live: /opt/satochi_bot/binance_live_service.py"
    echo "• Launcher service: /opt/satochi_bot/start_binance_live.py"
    echo "• Requirements bot: requirements_bot.txt"
    echo "• Requirements dashboard: requirements.txt"
    echo ""
    echo -e "${BLUE}�🔧 COMMANDES UTILES:${NC}"
    echo "• Démarrer les services: start-satochi-bot"
    echo "• Arrêter les services: stop-satochi-bot"
    echo "• Redémarrer les services: restart-satochi-bot"
    echo "• Statut des services: status-satochi-bot"
    echo "• Dashboard: start-satochi-dashboard"
    echo ""
    echo -e "${BLUE}📝 LOGS:${NC}"
    echo "• Bot principal: tail -f $LOG_DIR/bot.log"
    echo "• Service binance-live: tail -f $LOG_DIR/binance-live.log"
    echo "• Erreurs: tail -f $LOG_DIR/error.log"
    echo "• Monitoring: tail -f $LOG_DIR/monitor.log"
    echo "• Monitoring: tail -f $LOG_DIR/monitor.log"
    echo ""
    echo -e "${BLUE}🌐 ACCÈS:${NC}"
    echo "• Dashboard: http://$(curl -s ifconfig.me):80"
    echo "• SSH: ssh $BOT_USER@$(curl -s ifconfig.me)"
    echo ""
    echo -e "${GREEN}🚀 Le bot Satochi est prêt à être utilisé!${NC}"
}

# Fonction principale
main() {
    echo -e "${BLUE}Début du déploiement...${NC}"
    
    check_prerequisites
    install_system_dependencies
    setup_user_directories
    install_bot
    setup_systemd_service
    setup_nginx
    setup_ssl
    setup_firewall
    create_management_scripts
    setup_log_rotation
    setup_monitoring
    
    display_deployment_info
}

# Vérification des droits root (nécessaire pour VPS)
if [ "$EUID" -ne 0 ]; then
    log_error "Ce script doit être exécuté en tant que root sur le VPS."
    log_error "Utilisez: sudo ./deploy.sh"
    exit 1
fi

# Exécution
main "$@"
