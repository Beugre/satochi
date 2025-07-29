#!/usr/bin/env python3
"""
🚀 RSI SCALPING PRO BOT - MAIN
Bot de trading automatisé avec stratégie RSI Scalping
Objectif: +0.8% à +1% net/jour en moyenne

Conditions d'entrée (BUY):
- RSI 14 < 28 (zone de survente profonde)
- EMA(9) > EMA(21) (reprise haussière)
- MACD > Signal (confirmation momentum)
- Prix proche/cassure Bollinger inférieur
- Volume > moyenne mobile volume (20)
- Cassure +0.07% du dernier haut local (5 bougies)
- Minimum 4 conditions sur 5 validées

Conditions de sortie (SELL):
- TP automatique: +0.9%
- SL automatique: -0.4%
- Timeout adaptatif si stagne dans [-0.1%, +0.2%]
- Sortie anticipée si momentum faible

Gestion de position:
- Taille: 20-25% du capital USDC
- Max 2 positions ouvertes simultanées
- Anti-surtrading: max 2 trades/heure, 300s entre BUY
"""

import asyncio
import logging
import os
import sys
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

# Imports locaux
from config import TradingConfig, APIConfig, LoggingConfig
from data_fetcher import DataFetcher
from indicators import TechnicalIndicators
from firebase_logger import FirebaseLogger
from telegram_notifier import TelegramNotifier, NotificationConfig
from trade_executor import TradeExecutor


class RSIScalpingBot:
    """Bot de trading RSI Scalping Pro"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.config = TradingConfig()
        self.api_config = APIConfig()
        
        # État du bot
        self.is_running = False
        self.last_trade_time = {}  # Dernier trade par paire
        self.consecutive_losses = 0
        self.loss_streak_pause_until = None
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.trades_this_hour = 0
        self.last_hour_reset = datetime.now().hour
        
        # Positions ouvertes
        self.open_positions = {}
        
        # Initialisation des modules
        self.data_fetcher = None
        self.indicators = None
        self.firebase_logger = None
        self.telegram_notifier = None
        self.trade_executor = None
        
        self.logger.info("🚀 RSI Scalping Pro Bot initialisé")
    
    def setup_logging(self):
        """Configuration du système de logging"""
        logging_config = LoggingConfig()
        
        # Créer le dossier logs s'il n'existe pas
        os.makedirs("logs", exist_ok=True)
        
        # Configuration du logging
        logging.basicConfig(
            level=getattr(logging, logging_config.CONSOLE_LEVEL),
            format=logging_config.FORMAT,
            handlers=[
                logging.FileHandler(logging_config.FILE_PATH, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    async def initialize_modules(self):
        """Initialisation de tous les modules"""
        try:
            self.logger.info("🔧 Initialisation des modules...")
            
            # Data Fetcher
            self.data_fetcher = DataFetcher(
                api_key=self.api_config.BINANCE_API_KEY,
                secret_key=self.api_config.BINANCE_SECRET_KEY,
                testnet=self.api_config.BINANCE_TESTNET
            )
            
            # Test de connexion Binance
            await self.data_fetcher.test_connection()
            
            # Indicateurs techniques
            self.indicators = TechnicalIndicators(self.config)
            
            # Firebase Logger
            if self.api_config.FIREBASE_CREDENTIALS:
                self.firebase_logger = FirebaseLogger(self.api_config.FIREBASE_CREDENTIALS)
                await self.firebase_logger.initialize()
            
            # Telegram Notifier
            notification_config = NotificationConfig(
                send_start=True,
                send_trade_open=True,
                send_trade_close=True,
                send_daily_summary=True,
                send_errors=True,
                send_signals=False  # Éviter le spam
            )
            
            self.telegram_notifier = TelegramNotifier(
                bot_token=self.api_config.TELEGRAM_BOT_TOKEN,
                chat_id=self.api_config.TELEGRAM_CHAT_ID,
                config=notification_config,
                trading_config=self.config
            )
            
            # Test Telegram
            if self.telegram_notifier.bot:
                await self.telegram_notifier.test_connection()
            
            # Trade Executor
            self.trade_executor = TradeExecutor(
                data_fetcher=self.data_fetcher,
                config=self.config,
                firebase_logger=self.firebase_logger,
                telegram_notifier=self.telegram_notifier
            )
            
            self.logger.info("✅ Tous les modules initialisés avec succès")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation modules: {e}")
            raise
    
    async def check_trading_conditions(self) -> bool:
        """Vérifie si les conditions de trading sont remplies"""
        
        # Vérification des horaires de trading
        if not self.is_trading_hours():
            return False
        
        # Vérification pause après pertes consécutives
        if self.loss_streak_pause_until and datetime.now() < self.loss_streak_pause_until:
            return False
        
        # Vérification stop loss quotidien
        current_capital = await self.get_current_capital()
        daily_loss_limit = current_capital * (self.config.DAILY_STOP_LOSS_PERCENT / 100)
        if self.daily_pnl <= -daily_loss_limit:
            self.logger.warning(f"🛑 Stop loss quotidien atteint: {self.daily_pnl:.2f} USDC")
            return False
        
        # Vérification objectif quotidien atteint
        daily_target = current_capital * (self.config.DAILY_TARGET_PERCENT / 100)
        if self.daily_pnl >= daily_target:
            self.logger.info(f"🎯 Objectif quotidien atteint: {self.daily_pnl:.2f} USDC")
            return False
        
        # Vérification nombre maximum de positions
        if len(self.open_positions) >= self.config.MAX_OPEN_POSITIONS:
            return False
        
        # Vérification anti-surtrading
        if not self.check_anti_surtrading():
            return False
        
        return True
    
    def is_trading_hours(self) -> bool:
        """Vérifie si on est dans les heures de trading"""
        if not self.config.TRADING_HOURS_ENABLED:
            return True
        
        now = datetime.now()
        current_hour = now.hour
        
        # Horaires de base (9h-23h)
        if not (self.config.TRADING_START_HOUR <= current_hour < self.config.TRADING_END_HOUR):
            return False
        
        # Week-end
        if now.weekday() >= 5:  # Samedi (5) et Dimanche (6)
            if not self.config.WEEKEND_TRADING_ENABLED:
                return False
        
        return True
    
    def check_anti_surtrading(self) -> bool:
        """Vérifie les règles anti-surtrading"""
        now = datetime.now()
        
        # Reset compteur horaire
        if now.hour != self.last_hour_reset:
            self.trades_this_hour = 0
            self.last_hour_reset = now.hour
        
        # Max 2 trades par heure
        if self.trades_this_hour >= 2:
            return False
        
        return True
    
    async def get_current_capital(self) -> float:
        """Récupère le capital USDC actuel"""
        try:
            balance = await self.data_fetcher.get_account_balance()
            usdc_balance = 0.0
            
            # balance est un dictionnaire avec les assets comme clés
            if 'USDC' in balance:
                usdc_balance = float(balance['USDC']['free'])
            
            return usdc_balance
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération capital: {e}")
            return 0.0
    
    async def get_daily_stats_from_firebase(self) -> dict:
        """Calcule les statistiques quotidiennes depuis Firebase"""
        try:
            if not self.firebase_logger or not self.firebase_logger.db:
                return {
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'total_trades': self.trades_today,
                    'daily_pnl': self.daily_pnl,
                    'uptime_hours': 0
                }
            
            # Date d'aujourd'hui
            today = datetime.now().date()
            today_str = today.isoformat()
            
            # Récupérer les trades du jour depuis Firebase
            trades_ref = self.firebase_logger.db.collection('trades')
            today_trades = trades_ref.where('date', '==', today_str).stream()
            
            winning_trades = 0
            losing_trades = 0
            total_pnl = 0.0
            
            for trade_doc in today_trades:
                trade_data = trade_doc.to_dict()
                pnl = float(trade_data.get('pnl_amount', 0))
                
                if pnl > 0:
                    winning_trades += 1
                elif pnl < 0:
                    losing_trades += 1
                
                total_pnl += pnl
            
            # Calculer l'uptime depuis Firebase health
            uptime_hours = 0
            try:
                health_doc = self.firebase_logger.db.collection('binance_live').document('health').get()
                if health_doc.exists:
                    health_data = health_doc.to_dict()
                    if 'timestamp' in health_data:
                        start_time = datetime.fromisoformat(health_data['timestamp'].replace('Z', '+00:00'))
                        uptime_seconds = (datetime.now() - start_time).total_seconds()
                        uptime_hours = round(uptime_seconds / 3600, 1)
            except:
                pass
            
            return {
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'total_trades': winning_trades + losing_trades,
                'daily_pnl': total_pnl if total_pnl != 0 else self.daily_pnl,
                'uptime_hours': uptime_hours
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul stats Firebase: {e}")
            return {
                'winning_trades': 0,
                'losing_trades': 0,
                'total_trades': self.trades_today,
                'daily_pnl': self.daily_pnl,
                'uptime_hours': 0
            }
    
    async def scan_pairs(self) -> List[str]:
        """Scan et sélection des paires à analyser"""
        try:
            # Récupération de toutes les paires USDC
            all_pairs = await self.data_fetcher.get_all_pairs()
            usdc_pairs = [pair for pair in all_pairs if pair.endswith('USDC')]
            
            # Filtrage par volume et critères
            valid_pairs = []
            rejected_count = 0
            
            for pair in usdc_pairs:
                # Vérification blacklist
                symbol = pair.replace('USDC', '')
                if symbol in self.config.BLACKLISTED_SYMBOLS:
                    if self.firebase_logger:
                        await self.firebase_logger.log_pair_rejected_detailed(
                            pair, "symbole en blacklist", {'symbol': symbol}
                        )
                    rejected_count += 1
                    continue
                
                # Vérification volume et spread
                ticker = await self.data_fetcher.get_ticker(pair)
                if not ticker:
                    if self.firebase_logger:
                        await self.firebase_logger.log_pair_rejected_detailed(
                            pair, "données ticker indisponibles"
                        )
                    rejected_count += 1
                    continue
                
                volume_usdc = float(ticker.get('quoteVolume', 0))
                if volume_usdc < self.config.MIN_VOLUME_USDC:
                    if self.firebase_logger:
                        await self.firebase_logger.log_pair_rejected_detailed(
                            pair, f"volume trop faible ({volume_usdc:.0f} USDC)", 
                            volume=volume_usdc
                        )
                    rejected_count += 1
                    continue
                
                # Calcul du spread
                bid = float(ticker.get('bidPrice', 0))
                ask = float(ticker.get('askPrice', 0))
                if bid > 0:
                    spread = (ask - bid) / bid * 100
                    if spread > self.config.MAX_SPREAD_PERCENT:
                        if self.firebase_logger:
                            await self.firebase_logger.log_pair_rejected_detailed(
                                pair, f"spread trop élevé ({spread:.2f}%)", 
                                spread=spread, volume=volume_usdc
                            )
                        rejected_count += 1
                        continue
                
                # Vérification volatilité
                price_change_percent = abs(float(ticker.get('priceChangePercent', 0)))
                if price_change_percent < self.config.MIN_VOLATILITY_PERCENT:
                    if self.firebase_logger:
                        await self.firebase_logger.log_pair_rejected_detailed(
                            pair, f"volatilité trop faible ({price_change_percent:.1f}%)", 
                            volatility=price_change_percent, volume=volume_usdc
                        )
                    rejected_count += 1
                    continue
                
                valid_pairs.append(pair)
                
                # Limite à 7 paires par scan
                if len(valid_pairs) >= 7:
                    break
            
            message = f"📊 {len(valid_pairs)} paires sélectionnées pour analyse ({rejected_count} rejetées)"
            self.logger.info(message)
            
            # Log console mirror
            if self.firebase_logger:
                await self.firebase_logger.log_console_mirror('INFO', message, 'pair_scanner')
            
            return valid_pairs
            
        except Exception as e:
            self.logger.error(f"❌ Erreur scan des paires: {e}")
            return []
    
    def _get_latest_value(self, data):
        """Helper pour récupérer la dernière valeur, que ce soit un float ou une Series"""
        if hasattr(data, 'iloc'):
            return data.iloc[-1]
        elif hasattr(data, '__len__') and len(data) > 0:
            return data[-1]
        else:
            return data
    
    async def analyze_pair(self, pair: str) -> Tuple[bool, Dict]:
        """Analyse une paire selon la stratégie RSI Scalping"""
        try:
            # Récupération des données 1m
            klines = await self.data_fetcher.get_klines(pair, "1m", limit=100)
            if not klines or len(klines) < 50:
                return False, {}
            
            # Conversion en DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                'taker_buy_quote_volume', 'ignore'
            ])
            
            # Conversion des types
            for col in ['open', 'high', 'low', 'close', 'volume', 'quote_volume']:
                df[col] = pd.to_numeric(df[col])
            
            # Analyse des conditions
            conditions_met = []
            
            # 1. RSI 14 < 28 (zone de survente profonde)
            rsi = self.indicators.calculate_rsi(df['close'], period=14)
            current_rsi = self._get_latest_value(rsi)
            if current_rsi < 28:
                conditions_met.append(f"RSI < 28 ({current_rsi:.1f})")
            
            # 2. EMA(9) > EMA(21) (reprise haussière)
            ema9 = self.indicators.calculate_ema(df['close'], period=9)
            ema21 = self.indicators.calculate_ema(df['close'], period=21)
            ema9_value = self._get_latest_value(ema9)
            ema21_value = self._get_latest_value(ema21)
            if ema9_value > ema21_value:
                conditions_met.append(f"EMA9 > EMA21 ({ema9_value:.4f} > {ema21_value:.4f})")
            
            # 3. MACD > Signal (confirmation momentum)
            macd_data = self.indicators.calculate_macd(df['close'])
            macd_value = self._get_latest_value(macd_data['macd'])
            signal_value = self._get_latest_value(macd_data['signal'])
            if macd_value > signal_value:
                conditions_met.append("MACD > Signal")
            
            # 4. Prix proche/cassure Bollinger inférieur
            bb_data = self.indicators.calculate_bollinger_bands(df['close'])
            current_price = df['close'].iloc[-1]
            bb_lower = self._get_latest_value(bb_data['lower'])
            distance_to_lower = abs(current_price - bb_lower) / bb_lower
            if distance_to_lower <= 0.005:  # 0.5% de marge
                conditions_met.append(f"Prix proche BB inf. (distance: {distance_to_lower*100:.2f}%)")
            
            # 5. Volume > moyenne mobile volume (20)
            volume_ma = self.indicators.calculate_volume_sma(df['volume'], period=20)
            current_volume = df['volume'].iloc[-1]
            volume_ma_value = self._get_latest_value(volume_ma)
            if current_volume > volume_ma_value:
                conditions_met.append(f"Volume élevé ({current_volume/volume_ma_value:.1f}x)")
            
            # 6. Cassure +0.07% du dernier haut local (5 bougies)
            recent_highs = df['high'].iloc[-5:].max()
            breakout_level = recent_highs * 1.0007
            if current_price > breakout_level:
                conditions_met.append(f"Cassure haut local (+{((current_price/recent_highs-1)*100):.2f}%)")
            
            # Vérification: minimum 4 conditions sur 5
            signal_strength = len(conditions_met)
            is_valid_signal = signal_strength >= 4
            
            analysis_data = {
                'pair': pair,
                'current_price': current_price,
                'rsi': current_rsi,
                'ema9': ema9_value,
                'ema21': ema21_value,
                'macd': macd_value,
                'signal': signal_value,
                'bb_lower': bb_lower,
                'volume_ratio': current_volume / volume_ma_value,
                'breakout_level': breakout_level,
                'conditions_met': conditions_met,
                'signal_strength': signal_strength,
                'is_valid': is_valid_signal
            }
            
            if is_valid_signal:
                message = f"✅ Signal valide détecté pour {pair}: {signal_strength}/6 conditions"
                self.logger.info(message)
                for condition in conditions_met:
                    self.logger.info(f"  ✓ {condition}")
                
                # Log signal détecté dans Firebase
                if self.firebase_logger:
                    await self.firebase_logger.log_signal_detected(
                        pair, analysis_data, True, signal_strength, "BUY_ATTEMPT"
                    )
            else:
                # Log signal ignoré
                reason = f"force insuffisante ({signal_strength}/6)"
                if self.firebase_logger:
                    await self.firebase_logger.log_signal_detected(
                        pair, analysis_data, False, signal_strength, reason
                    )
            
            return is_valid_signal, analysis_data
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse {pair}: {e}")
            return False, {}
    
    async def execute_buy_order(self, pair: str, analysis_data: Dict):
        """Exécute un ordre d'achat"""
        try:
            # Vérification dernier trade sur cette paire (1 trade/paire/heure)
            now = datetime.now()
            if pair in self.last_trade_time:
                time_since_last = (now - self.last_trade_time[pair]).total_seconds()
                if time_since_last < 3600:  # 1 heure
                    self.logger.info(f"⏳ Attente cooldown pour {pair}: {3600-time_since_last:.0f}s")
                    return False
            
            # Vérification délai entre trades (300s minimum)
            if self.last_trade_time:
                last_trade = max(self.last_trade_time.values())
                time_since_any_trade = (now - last_trade).total_seconds()
                if time_since_any_trade < 300:
                    self.logger.info(f"⏳ Attente délai anti-surtrading: {300-time_since_any_trade:.0f}s")
                    return False
            
            # Calcul de la taille de position
            current_capital = await self.get_current_capital()
            position_size_percent = np.random.uniform(20, 25)  # Entre 20-25%
            position_value = current_capital * (position_size_percent / 100)
            
            # Vérification taille min/max
            if position_value < self.config.MIN_POSITION_SIZE_USDC:
                self.logger.warning(f"⚠️ Position trop petite: {position_value:.2f} < {self.config.MIN_POSITION_SIZE_USDC}")
                return False
            
            if position_value > self.config.MAX_POSITION_SIZE_USDC:
                position_value = self.config.MAX_POSITION_SIZE_USDC
            
            # Calcul de la quantité
            current_price = analysis_data['current_price']
            quantity = position_value / current_price
            
            # Calcul des niveaux TP/SL
            take_profit_price = current_price * (1 + self.config.TAKE_PROFIT_PERCENT / 100)
            stop_loss_price = current_price * (1 - self.config.STOP_LOSS_PERCENT / 100)
            
            # Exécution de l'ordre via open_trade
            trade_result = await self.trade_executor.open_trade(
                pair=pair,
                analysis_data=analysis_data
            )
            
            if trade_result is not None:
                # Enregistrement de la position UNIQUEMENT (pas de re-logging)
                self.open_positions[pair] = {
                    'entry_price': trade_result.entry_price,
                    'quantity': trade_result.quantity,
                    'take_profit': trade_result.take_profit_price,
                    'stop_loss': trade_result.stop_loss_price,
                    'entry_time': trade_result.entry_time,
                    'position_value': trade_result.capital_engaged,
                    'analysis_data': analysis_data
                }
                
                # Mise à jour des compteurs
                self.last_trade_time[pair] = now
                self.trades_today += 1
                self.trades_this_hour += 1
                
                # Log simple dans main.py
                self.logger.info(f"✅ Trade {pair} enregistré dans les positions ouvertes")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erreur exécution BUY {pair}: {e}")
            return False
    
    async def monitor_positions(self):
        """Surveillance des positions ouvertes"""
        try:
            positions_to_close = []
            
            for pair, position in self.open_positions.items():
                # Récupération du prix actuel
                ticker = await self.data_fetcher.get_ticker(pair)
                if not ticker:
                    continue
                
                current_price = float(ticker['price'])
                entry_price = position['entry_price']
                pnl_percent = (current_price - entry_price) / entry_price * 100
                
                # Vérification timeout adaptatif
                time_in_position = (datetime.now() - position['entry_time']).total_seconds() / 60
                should_close = False
                close_reason = ""
                
                # Timeout si stagne dans [-0.1%, +0.2%]
                if time_in_position > 3 and -0.1 <= pnl_percent <= 0.2:
                    should_close = True
                    close_reason = "Timeout stagnation"
                
                # Sortie anticipée si momentum faible
                elif time_in_position > 3:
                    # Récupération données pour vérifier momentum
                    klines = await self.data_fetcher.get_klines(pair, "1m", limit=20)
                    if klines:
                        df = pd.DataFrame(klines, columns=[
                            'timestamp', 'open', 'high', 'low', 'close', 'volume',
                            'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                            'taker_buy_quote_volume', 'ignore'
                        ])
                        df['close'] = pd.to_numeric(df['close'])
                        
                        # Vérification RSI et MACD
                        rsi = self.indicators.calculate_rsi(df['close'], period=14)
                        macd_data = self.indicators.calculate_macd(df['close'])
                        
                        if (rsi.iloc[-1] < 35 or 
                            macd_data['macd'].iloc[-1] < macd_data['signal'].iloc[-1]):
                            should_close = True
                            close_reason = "Momentum faible"
                
                if should_close:
                    positions_to_close.append((pair, close_reason))
            
            # Fermeture des positions identifiées
            for pair, reason in positions_to_close:
                await self.close_position(pair, reason)
                
        except Exception as e:
            self.logger.error(f"❌ Erreur surveillance positions: {e}")
    
    async def close_position(self, pair: str, reason: str = "Manuel"):
        """Ferme une position"""
        try:
            if pair not in self.open_positions:
                return
            
            position = self.open_positions[pair]
            
            # Exécution de l'ordre de vente via trade_executor
            result = await self.trade_executor.execute_sell_order(pair, position['quantity'])
            
            if result['success']:
                # Calcul du P&L
                exit_price = result['price']
                entry_price = position['entry_price']
                pnl_amount = (exit_price - entry_price) * position['quantity']
                pnl_percent = (exit_price - entry_price) / entry_price * 100
                
                # Mise à jour du P&L quotidien
                self.daily_pnl += pnl_amount
                
                # Gestion des pertes consécutives
                if pnl_amount < 0:
                    self.consecutive_losses += 1
                    if self.consecutive_losses >= self.config.MAX_LOSS_STREAK:
                        self.loss_streak_pause_until = datetime.now() + timedelta(minutes=60)
                        self.logger.warning(f"🛑 Pause 60min après {self.consecutive_losses} pertes consécutives")
                else:
                    self.consecutive_losses = 0
                
                # Suppression de la position
                del self.open_positions[pair]
                
                # Log simple dans main.py
                self.logger.info(f"✅ Position {pair} fermée | P&L: {pnl_amount:+.2f} USDC ({pnl_percent:+.2f}%) | Raison: {reason}")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur fermeture position {pair}: {e}")
    
    async def main_loop(self):
        """Boucle principale du bot"""
        self.logger.info("🚀 Démarrage de la boucle principale")
        
        # Notification de démarrage
        if self.telegram_notifier:
            capital = await self.get_current_capital()
            await self.telegram_notifier.send_start_notification(capital)
        
        while self.is_running:
            try:
                # Vérification des conditions de trading
                if not await self.check_trading_conditions():
                    await asyncio.sleep(40)  # Scan toutes les 40 secondes
                    continue
                
                # Surveillance des positions ouvertes
                await self.monitor_positions()
                
                # Scan des nouvelles opportunités
                if len(self.open_positions) < self.config.MAX_OPEN_POSITIONS:
                    pairs_to_analyze = await self.scan_pairs()
                    
                    for pair in pairs_to_analyze:
                        # Éviter les paires déjà en position
                        if pair in self.open_positions:
                            continue
                        
                        # Analyse de la paire
                        is_signal, analysis_data = await self.analyze_pair(pair)
                        
                        if is_signal:
                            # Tentative d'achat
                            success = await self.execute_buy_order(pair, analysis_data)
                            if success:
                                # Attendre un peu avant le prochain trade
                                await asyncio.sleep(10)
                                break
                
                # Attente avant le prochain cycle
                await asyncio.sleep(40)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Arrêt demandé par l'utilisateur")
                break
            except Exception as e:
                self.logger.error(f"❌ Erreur dans la boucle principale: {e}")
                self.logger.error(traceback.format_exc())
                
                # Notification d'erreur
                try:
                    if self.telegram_notifier:
                        await self.telegram_notifier.send_error_notification(str(e), "Boucle principale")
                except:
                    self.logger.error("❌ Impossible d'envoyer la notification d'erreur")
                
                # Réinitialisation des connexions en cas d'erreur réseau
                try:
                    if "timeout" in str(e).lower() or "connection" in str(e).lower():
                        self.logger.warning("🔄 Reconnexion après erreur réseau...")
                        await self.data_fetcher.test_connection()
                except:
                    self.logger.error("❌ Échec de la reconnexion")
                
                # Attendre avant de continuer
                await asyncio.sleep(60)
    
    async def shutdown(self):
        """Arrêt propre du bot"""
        self.logger.info("🛑 Arrêt du bot en cours...")
        self.is_running = False
        
        # Fermeture de toutes les positions ouvertes
        for pair in list(self.open_positions.keys()):
            await self.close_position(pair, "Arrêt du bot")
        
        # Notification de fin
        if self.telegram_notifier:
            # Récupérer les vraies statistiques depuis Firebase
            daily_stats = await self.get_daily_stats_from_firebase()
            
            summary_data = {
                'daily_pnl': daily_stats['daily_pnl'],
                'total_trades': daily_stats['total_trades'],
                'winning_trades': daily_stats['winning_trades'],
                'losing_trades': daily_stats['losing_trades'],
                'total_capital': await self.get_current_capital(),
                'uptime_hours': daily_stats['uptime_hours']
            }
            await self.telegram_notifier.send_daily_summary(summary_data)
        
        # Fermeture des connexions
        if self.data_fetcher and hasattr(self.data_fetcher, 'close'):
            await self.data_fetcher.close()
        
        self.logger.info("✅ Bot arrêté proprement")
    
    async def run(self):
        """Point d'entrée principal"""
        try:
            self.is_running = True
            await self.initialize_modules()
            await self.main_loop()
        except Exception as e:
            self.logger.error(f"❌ Erreur critique: {e}")
            self.logger.error(traceback.format_exc())
        finally:
            await self.shutdown()


async def main():
    """Point d'entrée du programme"""
    bot = RSIScalpingBot()
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
    finally:
        if bot.is_running:
            await bot.shutdown()


if __name__ == "__main__":
    # Configuration pour Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Programme interrompu")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
