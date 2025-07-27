#!/usr/bin/env python3
"""
🔄 SERVICE BINANCE LIVE - SATOCHI BOT
Collecte en temps réel les données Binance et les stocke dans Firebase
Synchronisation avec le bot de trading principal
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# Imports directs depuis la racine
from binance.client import Client
from binance.exceptions import BinanceAPIException
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.exceptions import FirebaseError

from config import APIConfig, TradingConfig


class BinanceLiveService:
    """Service de collecte des données Binance en temps réel"""
    
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.setup_binance_client()
        self.setup_firebase()
        self.monitored_pairs = []
        self.running = False
        self.cycle_count = 0
        
    def setup_logging(self):
        """Configuration du logging"""
        # Déterminer le répertoire de logs
        possible_log_dirs = [
            '/opt/satochi_bot/logs',        # VPS
            'logs',                         # Local
            '/var/log/satochi-bot'          # System
        ]
        
        log_dir = None
        for log_path in possible_log_dirs:
            try:
                os.makedirs(log_path, exist_ok=True)
                log_dir = log_path
                break
            except (OSError, PermissionError):
                continue
        
        # Configuration des handlers
        handlers = [logging.StreamHandler()]
        
        if log_dir:
            log_file = os.path.join(log_dir, 'binance_live.log')
            try:
                handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
            except (OSError, PermissionError):
                pass
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
        self.logger = logging.getLogger('BinanceLive')
        
        if log_dir:
            self.logger.info(f"[LOG] Logging configuré - Répertoire: {log_dir}")
        else:
            self.logger.info("[LOG] Logging configuré - Console seulement")
    
    def load_config(self):
        """Chargement de la configuration"""
        try:
            # Charger variables d'environnement depuis différents emplacements
            possible_env_paths = [
                '/opt/satochi_bot/.env',
                '.env',
                '../.env'
            ]
            
            env_loaded = False
            for env_path in possible_env_paths:
                if os.path.exists(env_path):
                    from dotenv import load_dotenv
                    load_dotenv(env_path)
                    self.logger.info(f"[CONFIG] Fichier .env chargé: {env_path}")
                    env_loaded = True
                    break
            
            if not env_loaded:
                self.logger.warning("[CONFIG] Aucun .env trouvé, utilisation variables système")
            
            # Initialiser les configs
            self.api_config = APIConfig()
            self.trading_config = TradingConfig()
            
            self.logger.info("[CONFIG] Configuration chargée avec succès")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur chargement config: {e}")
            raise
    
    def setup_binance_client(self):
        """Configuration du client Binance"""
        try:
            if not self.api_config.BINANCE_API_KEY or not self.api_config.BINANCE_SECRET_KEY:
                raise ValueError("Clés API Binance manquantes")
                
            self.binance_client = Client(
                api_key=self.api_config.BINANCE_API_KEY,
                api_secret=self.api_config.BINANCE_SECRET_KEY,
                testnet=self.api_config.BINANCE_TESTNET
            )
            
            # Test de connexion
            account = self.binance_client.get_account()
            env_type = "TESTNET" if self.api_config.BINANCE_TESTNET else "MAINNET"
            self.logger.info(f"[BINANCE] Connecté ({env_type}) - Type: {account.get('accountType', 'UNKNOWN')}")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur connexion Binance: {e}")
            raise
    
    def setup_firebase(self):
        """Configuration Firebase"""
        try:
            # Vérifier si une app existe déjà
            try:
                app = firebase_admin.get_app()
                self.firebase_db = firestore.client(app)
                self.logger.info("[FIREBASE] App réutilisée")
            except ValueError:
                # Initialiser nouvelle app
                cred_paths = [
                    '/opt/satochi_bot/firebase-credentials.json',
                    'firebase-credentials.json',
                    '../firebase-credentials.json'
                ]
                
                cred_path = None
                for path in cred_paths:
                    if os.path.exists(path):
                        cred_path = path
                        break
                
                if not cred_path:
                    raise FileNotFoundError("Fichier Firebase credentials introuvable")
                
                cred = credentials.Certificate(cred_path)
                app = firebase_admin.initialize_app(cred)
                self.firebase_db = firestore.client(app)
                self.logger.info(f"[FIREBASE] Initialisé avec: {cred_path}")
                
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur Firebase: {e}")
            raise
    
    def discover_active_pairs(self) -> List[str]:
        """Découvre les paires actives avec les critères du bot + historique trades"""
        try:
            # 1. Récupérer les paires de l'historique des trades
            traded_pairs = self.get_historically_traded_pairs()
            
            # 2. Récupérer les informations d'exchange
            exchange_info = self.binance_client.get_exchange_info()
            usdc_pairs = []
            
            for symbol_info in exchange_info['symbols']:
                symbol = symbol_info['symbol']
                if (symbol.endswith('USDC') and 
                    symbol_info['status'] == 'TRADING' and
                    symbol_info['quoteAsset'] == 'USDC' and
                    symbol not in self.trading_config.BLACKLISTED_PAIRS):
                    usdc_pairs.append(symbol)
            
            # 3. Combiner: paires tradées + prioritaires + autres actives
            all_pairs = set()
            
            # Ajouter toutes les paires déjà tradées (priorité absolue)
            all_pairs.update([p for p in traded_pairs if p in usdc_pairs])
            
            # Ajouter les paires prioritaires
            all_pairs.update([p for p in self.trading_config.PRIORITY_PAIRS if p in usdc_pairs])
            
            # Compléter avec d'autres paires actives si besoin
            remaining_slots = max(0, 30 - len(all_pairs))  # Max 30 paires total
            other_pairs = [p for p in usdc_pairs if p not in all_pairs]
            all_pairs.update(other_pairs[:remaining_slots])
            
            final_pairs = list(all_pairs)
            
            self.logger.info(f"[DISCOVERY] {len(final_pairs)} paires détectées (historique: {len(traded_pairs)}, prioritaires: {len(self.trading_config.PRIORITY_PAIRS)})")
            return final_pairs
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur découverte paires: {e}")
            return self.trading_config.PRIORITY_PAIRS[:5]  # Fallback
    
    def get_historically_traded_pairs(self) -> List[str]:
        """Récupère toutes les paires déjà tradées dans l'historique"""
        try:
            # Récupérer les trades des 30 derniers jours
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)
            
            traded_pairs = set()
            
            # Récupérer l'historique des trades de tous les symbols
            try:
                # Méthode 1: Récupérer via l'historique des ordres
                orders = self.binance_client.get_all_orders(limit=1000)
                for order in orders:
                    if order['symbol'].endswith('USDC'):
                        traded_pairs.add(order['symbol'])
                        
            except Exception as e:
                self.logger.warning(f"[TRADES] Erreur récupération ordres: {e}")
                
            # Méthode 2: Récupérer via l'historique des trades
            try:
                # Pour chaque paire USDC connue, vérifier s'il y a eu des trades
                exchange_info = self.binance_client.get_exchange_info()
                usdc_symbols = [s['symbol'] for s in exchange_info['symbols'] 
                              if s['symbol'].endswith('USDC') and s['status'] == 'TRADING']
                
                # Échantillonner quelques paires pour éviter le rate limit
                for symbol in usdc_symbols[:50]:  # Limiter à 50 pour éviter timeout
                    try:
                        trades = self.binance_client.get_my_trades(symbol=symbol, limit=1)
                        if trades:  # Si des trades existent
                            traded_pairs.add(symbol)
                    except:
                        continue  # Passer si pas de trades sur cette paire
                        
            except Exception as e:
                self.logger.warning(f"[TRADES] Erreur scan historique: {e}")
            
            traded_list = list(traded_pairs)
            self.logger.info(f"[HISTORY] {len(traded_list)} paires historiquement tradées trouvées")
            return traded_list
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur récupération historique: {e}")
            return []
    
    async def collect_account_info(self):
        """Collecte les informations de compte"""
        try:
            account = self.binance_client.get_account()
            
            # Filtrer les balances > 0
            balances = []
            total_value_usdc = 0
            
            for balance in account['balances']:
                free_balance = float(balance['free'])
                locked_balance = float(balance['locked'])
                total_balance = free_balance + locked_balance
                
                if total_balance > 0:
                    balance_data = {
                        'asset': balance['asset'],
                        'free': free_balance,
                        'locked': locked_balance,
                        'total': total_balance
                    }
                    balances.append(balance_data)
                    
                    # Calcul approximatif de la valeur en USDC
                    if balance['asset'] == 'USDC':
                        total_value_usdc += total_balance
            
            account_data = {
                'timestamp': datetime.now().isoformat(),
                'balances': balances,
                'total_balances_count': len(balances),
                'total_value_usdc_approx': total_value_usdc,
                'canTrade': account.get('canTrade', False),
                'canWithdraw': account.get('canWithdraw', False),
                'accountType': account.get('accountType', 'UNKNOWN'),
                'permissions': account.get('permissions', []),
                'collected_at': firestore.SERVER_TIMESTAMP,
                'service_version': 'satochi_bot_v1'
            }
            
            # Stockage Firebase
            self.firebase_db.collection('binance_live').document('account_info').set(account_data)
            self.logger.info(f"[ACCOUNT] Mis à jour - {len(balances)} balances, ~{total_value_usdc:.2f} USDC")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur collecte account: {e}")
    
    async def collect_recent_trades(self, hours_back: int = 24):
        """Collecte les trades récents"""
        try:
            if not self.monitored_pairs:
                self.monitored_pairs = self.discover_active_pairs()
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            all_trades = []
            
            for symbol in self.monitored_pairs:
                try:
                    trades = self.binance_client.get_my_trades(
                        symbol=symbol,
                        startTime=int(start_time.timestamp() * 1000),
                        endTime=int(end_time.timestamp() * 1000)
                    )
                    
                    for trade in trades:
                        trade_data = {
                            'symbol': trade['symbol'],
                            'id': trade['id'],
                            'orderId': trade['orderId'],
                            'price': float(trade['price']),
                            'qty': float(trade['qty']),
                            'quoteQty': float(trade['quoteQty']),
                            'commission': float(trade['commission']),
                            'commissionAsset': trade['commissionAsset'],
                            'time': datetime.fromtimestamp(trade['time'] / 1000).isoformat(),
                            'isBuyer': trade['isBuyer'],
                            'isMaker': trade['isMaker'],
                            'isBestMatch': trade['isBestMatch']
                        }
                        all_trades.append(trade_data)
                    
                    # Petite pause pour éviter rate limits
                    await asyncio.sleep(0.1)
                    
                except BinanceAPIException as e:
                    if "Invalid symbol" not in str(e):
                        self.logger.warning(f"[TRADES] Erreur {symbol}: {e}")
                    continue
            
            trades_data = {
                'timestamp': datetime.now().isoformat(),
                'period_hours': hours_back,
                'trades': all_trades,
                'pairs_monitored': self.monitored_pairs,
                'total_trades': len(all_trades),
                'collected_at': firestore.SERVER_TIMESTAMP,
                'service_version': 'satochi_bot_v1'
            }
            
            # Stockage Firebase
            self.firebase_db.collection('binance_live').document('recent_trades').set(trades_data)
            self.logger.info(f"[TRADES] {len(all_trades)} trades collectés sur {len(self.monitored_pairs)} paires")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur collecte trades: {e}")
    
    async def collect_open_orders(self):
        """Collecte les ordres ouverts"""
        try:
            if not self.monitored_pairs:
                self.monitored_pairs = self.discover_active_pairs()
            
            all_orders = []
            
            for symbol in self.monitored_pairs:
                try:
                    orders = self.binance_client.get_open_orders(symbol=symbol)
                    
                    for order in orders:
                        order_data = {
                            'symbol': order['symbol'],
                            'orderId': order['orderId'],
                            'clientOrderId': order['clientOrderId'],
                            'price': float(order['price']),
                            'origQty': float(order['origQty']),
                            'executedQty': float(order['executedQty']),
                            'cummulativeQuoteQty': float(order['cummulativeQuoteQty']),
                            'status': order['status'],
                            'type': order['type'],
                            'side': order['side'],
                            'stopPrice': float(order.get('stopPrice', 0)),
                            'time': datetime.fromtimestamp(order['time'] / 1000).isoformat(),
                            'updateTime': datetime.fromtimestamp(order['updateTime'] / 1000).isoformat(),
                            'isWorking': order['isWorking']
                        }
                        all_orders.append(order_data)
                    
                    await asyncio.sleep(0.1)  # Rate limit protection
                    
                except BinanceAPIException as e:
                    if "Invalid symbol" not in str(e):
                        self.logger.warning(f"[ORDERS] Erreur {symbol}: {e}")
                    continue
            
            orders_data = {
                'timestamp': datetime.now().isoformat(),
                'orders': all_orders,
                'pairs_monitored': self.monitored_pairs,
                'total_orders': len(all_orders),
                'collected_at': firestore.SERVER_TIMESTAMP,
                'service_version': 'satochi_bot_v1'
            }
            
            # Stockage Firebase
            self.firebase_db.collection('binance_live').document('open_orders').set(orders_data)
            self.logger.info(f"[ORDERS] {len(all_orders)} ordres ouverts collectés")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur collecte ordres: {e}")
    
    async def health_check(self):
        """Vérification de l'état du service"""
        try:
            # Test Binance
            server_time = self.binance_client.get_server_time()
            
            # Test Firebase
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'status': 'healthy',
                'service': 'binance_live_satochi',
                'binance_server_time': datetime.fromtimestamp(server_time['serverTime'] / 1000).isoformat(),
                'cycle_count': self.cycle_count,
                'monitored_pairs_count': len(self.monitored_pairs),
                'last_health_check': firestore.SERVER_TIMESTAMP
            }
            
            self.firebase_db.collection('binance_live').document('health').set(health_data)
            self.logger.info(f"[HEALTH] OK - Cycle #{self.cycle_count}")
            
        except Exception as e:
            self.logger.error(f"[HEALTH] FAILED: {e}")
    
    async def run_collection_cycle(self):
        """Cycle complet de collecte"""
        try:
            self.cycle_count += 1
            self.logger.info(f"[CYCLE] Début cycle #{self.cycle_count}")
            
            # Collecte parallèle des données
            await asyncio.gather(
                self.collect_account_info(),
                self.collect_recent_trades(hours_back=6),  # 6h de trades
                self.collect_open_orders(),
                return_exceptions=True
            )
            
            self.logger.info(f"[CYCLE] Terminé #{self.cycle_count}")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur cycle #{self.cycle_count}: {e}")
    
    async def start_service(self):
        """Démarrage du service principal"""
        self.logger.info("🚀 [START] Service Binance Live démarré")
        self.running = True
        
        # Health check initial
        await self.health_check()
        
        # Découverte initiale des paires
        self.monitored_pairs = self.discover_active_pairs()
        
        try:
            while self.running:
                # Cycle de collecte principal (toutes les 2 minutes)
                await self.run_collection_cycle()
                
                # Health check périodique (toutes les 10 cycles = 20 minutes)
                if self.cycle_count % 10 == 0:
                    await self.health_check()
                
                # Redécouverte des paires (toutes les 30 cycles = 1 heure)
                if self.cycle_count % 30 == 0:
                    self.monitored_pairs = self.discover_active_pairs()
                
                # Attendre 2 minutes avant le prochain cycle
                await asyncio.sleep(120)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 [STOP] Arrêt demandé par l'utilisateur")
        except Exception as e:
            self.logger.error(f"[ERROR] Erreur critique: {e}")
        finally:
            self.running = False
            self.logger.info("🔚 [STOP] Service Binance Live arrêté")
    
    def stop_service(self):
        """Arrêt du service"""
        self.logger.info("🛑 [STOP] Demande d'arrêt du service")
        self.running = False


async def main():
    """Point d'entrée principal"""
    service = BinanceLiveService()
    
    try:
        await service.start_service()
    except Exception as e:
        logging.error(f"[ERROR] Erreur fatale: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
