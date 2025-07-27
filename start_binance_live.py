#!/usr/bin/env python3
"""
🎬 LAUNCHER BINANCE LIVE SERVICE
Script de démarrage avec gestion d'erreurs et restart automatique
"""

import argparse
import asyncio
import logging
import os
import signal
import sys
import time
from pathlib import Path

# Ajouter le répertoire parent au PATH
sys.path.append(str(Path(__file__).parent.parent))

from binance_live_service import BinanceLiveService


class BinanceLiveManager:
    """Gestionnaire du service Binance Live avec restart automatique"""
    
    def __init__(self, max_retries: int = 5, retry_delay: int = 30):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.service = None
        self.should_restart = True
        self.setup_logging()
        
    def setup_logging(self):
        """Configuration du logging pour le manager"""
        possible_log_dirs = [
            '/opt/satochi_bot/logs',
            '/var/log/satochi-bot',
            'logs'
        ]
        
        log_dir = None
        for log_path in possible_log_dirs:
            try:
                os.makedirs(log_path, exist_ok=True)
                log_dir = log_path
                break
            except (OSError, PermissionError):
                continue
        
        handlers = [logging.StreamHandler()]
        if log_dir:
            handlers.append(logging.FileHandler(os.path.join(log_dir, 'binance_live_manager.log')))
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
        self.logger = logging.getLogger('BinanceLiveManager')
        
    def signal_handler(self, signum, frame):
        """Gestionnaire des signaux système"""
        self.logger.info(f"🛑 Signal {signum} reçu - Arrêt en cours")
        self.should_restart = False
        if self.service:
            self.service.stop_service()
            
    def setup_signal_handlers(self):
        """Configuration des gestionnaires de signaux"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    async def run_service_with_retry(self):
        """Exécute le service avec retry automatique"""
        retry_count = 0
        
        while self.should_restart and retry_count < self.max_retries:
            try:
                self.logger.info(f"🚀 Démarrage service (tentative {retry_count + 1}/{self.max_retries})")
                
                # Créer nouvelle instance
                self.service = BinanceLiveService()
                
                # Démarrer
                await self.service.start_service()
                
                self.logger.info("✅ Service arrêté proprement")
                break
                
            except Exception as e:
                retry_count += 1
                self.logger.error(f"❌ Erreur service (tentative {retry_count}): {e}")
                
                if retry_count < self.max_retries and self.should_restart:
                    self.logger.info(f"⏳ Retry dans {self.retry_delay} secondes...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logger.error("💀 Nombre maximum de tentatives atteint")
                    break
        
        self.logger.info("🔚 Manager arrêté")
        
    async def start(self):
        """Démarrage du gestionnaire"""
        self.setup_signal_handlers()
        self.logger.info("🎯 Manager Binance Live démarré")
        
        await self.run_service_with_retry()


def check_environment():
    """Vérification de l'environnement"""
    required_files = [
        'firebase-credentials.json'
    ]
    
    missing_files = []
    for filename in required_files:
        # Chercher dans plusieurs emplacements
        possible_paths = [
            f'/opt/satochi_bot/{filename}',
            filename,
            f'../{filename}'
        ]
        
        found = False
        for path in possible_paths:
            if os.path.exists(path):
                found = True
                break
        
        if not found:
            missing_files.append(filename)
    
    if missing_files:
        print("❌ Fichiers manquants:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ Environnement validé")
    return True


def create_systemd_service():
    """Génère le fichier de service systemd"""
    service_content = """[Unit]
Description=Satochi Bot - Binance Live Data Collector
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/satochi_bot
ExecStart=/usr/bin/python3 /opt/satochi_bot/scripts/start_binance_live.py --daemon
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/satochi_bot

# Limites de ressources
MemoryLimit=512M
CPUQuota=25%

# Logging
StandardOutput=append:/var/log/satochi-bot/binance-live.log
StandardError=append:/var/log/satochi-bot/binance-live-error.log

[Install]
WantedBy=multi-user.target
"""
    
    service_path = '/etc/systemd/system/satochi-binance-live.service'
    
    try:
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        print(f"✅ Service systemd créé: {service_path}")
        print("\n📋 Commandes pour activer:")
        print("   sudo systemctl daemon-reload")
        print("   sudo systemctl enable satochi-binance-live")
        print("   sudo systemctl start satochi-binance-live")
        print("   sudo systemctl status satochi-binance-live")
        
    except PermissionError:
        print("❌ Permissions insuffisantes - Exécutez avec sudo")


async def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Manager du service Binance Live')
    parser.add_argument('--daemon', action='store_true', help='Mode démon (systemd)')
    parser.add_argument('--check-env', action='store_true', help='Vérifier environnement')
    parser.add_argument('--create-service', action='store_true', help='Créer service systemd')
    parser.add_argument('--max-retries', type=int, default=5, help='Max tentatives')
    parser.add_argument('--retry-delay', type=int, default=30, help='Délai retry (sec)')
    
    args = parser.parse_args()
    
    # Vérification environnement
    if args.check_env:
        return 0 if check_environment() else 1
    
    # Création service systemd
    if args.create_service:
        create_systemd_service()
        return 0
    
    # Vérification avant démarrage
    if not check_environment():
        print("❌ Environnement non prêt")
        return 1
    
    # Démarrage du service
    try:
        manager = BinanceLiveManager(
            max_retries=args.max_retries,
            retry_delay=args.retry_delay
        )
        
        await manager.start()
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
        return 0
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
