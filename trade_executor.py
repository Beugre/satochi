#!/usr/bin/env python3
"""
💼 TRADE EXECUTOR - RSI SCALPING PRO
Gestionnaire d'exécution des trades avec gestion des risques
"""

import asyncio
import logging
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException
except ImportError:
    print("⚠️ Binance client non installé")
    Client = None


class TradeStatus(Enum):
    """Statuts des trades"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


class ExitReason(Enum):
    """Raisons de sortie"""
    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_LOSS = "STOP_LOSS"
    TIMEOUT = "TIMEOUT"
    EARLY_EXIT = "EARLY_EXIT"
    MANUAL = "MANUAL"
    ERROR = "ERROR"


@dataclass
class Trade:
    """Classe représentant un trade"""
    trade_id: str
    pair: str
    side: str  # BUY/SELL
    entry_price: float
    quantity: float
    capital_engaged: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    status: TradeStatus
    
    # Optionnels
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    exit_reason: Optional[ExitReason] = None
    pnl_amount: Optional[float] = None
    pnl_percent: Optional[float] = None
    fees: Optional[float] = None
    duration_seconds: Optional[int] = None
    
    # Données techniques
    rsi_value: Optional[float] = None
    entry_conditions: Optional[Dict[str, Any]] = None
    breakout_detected: Optional[bool] = None
    
    # Ordres Binance
    entry_order_id: Optional[str] = None
    stop_loss_order_id: Optional[str] = None
    take_profit_order_id: Optional[str] = None
    
    # Trailing Stop
    trailing_stop_order_id: Optional[str] = None
    trailing_stop_active: bool = False
    trailing_stop_pending: bool = False
    
    @property
    def duration_formatted(self) -> str:
        """Durée formatée du trade"""
        if self.duration_seconds is None:
            return "N/A"
        
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        
        if hours > 0:
            return f"{hours}h{minutes}m{seconds}s"
        elif minutes > 0:
            return f"{minutes}m{seconds}s"
        else:
            return f"{seconds}s"
    
    @property
    def current_pnl_percent(self) -> float:
        """P&L actuel en pourcentage"""
        if self.exit_price:
            return ((self.exit_price - self.entry_price) / self.entry_price) * 100
        return 0.0


class TradeExecutor:
    """Exécuteur de trades avec gestion complète du cycle de vie"""
    
    def __init__(self, data_fetcher, config, risk_config, firebase_logger=None, telegram_notifier=None):
        self.data_fetcher = data_fetcher
        self.config = config
        self.risk_config = risk_config
        self.firebase_logger = firebase_logger
        self.telegram_notifier = telegram_notifier
        self.logger = logging.getLogger(__name__)
        
        # Initialisation des indicateurs techniques pour stratégie RSI
        try:
            from indicators import TechnicalIndicators
            self.indicators = TechnicalIndicators(config=config)
            self.logger.info("📊 Indicateurs techniques RSI initialisés")
        except ImportError:
            self.indicators = None
            self.logger.warning("⚠️ Module indicators non trouvé - Stratégie RSI désactivée")
        
        # Gestion des trades
        self.active_trades: Dict[str, Trade] = {}
        self.trade_history: List[Trade] = []
        self.position_count = 0
        
        # Statistiques
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.last_trade_time = None
        self.trade_timestamps = []  # Pour anti-surtrading
        
        # État de pause
        self.is_paused = False
        self.pause_until = None
        
        self.logger.info("💼 Trade Executor initialisé")
    
    async def _format_quantity(self, symbol: str, quantity: float) -> float:
        """Formate la quantité selon les règles de précision de Binance"""
        try:
            symbol_info = await self.data_fetcher.get_symbol_info(symbol)
            if not symbol_info:
                self.logger.warning(f"⚠️ Informations symbole non trouvées pour {symbol}, utilisation précision par défaut")
                return round(quantity, 6)  # Précision par défaut
            
            # Récupération du filtre LOT_SIZE pour la précision de quantité
            step_size = None
            for filter_info in symbol_info.get('filters', []):
                if filter_info['filterType'] == 'LOT_SIZE':
                    step_size = float(filter_info['stepSize'])
                    break
            
            if step_size is None:
                # Fallback avec baseAssetPrecision si disponible
                precision = symbol_info.get('baseAssetPrecision', 6)
                return round(quantity, precision)
            
            # Calcul de la précision basée sur stepSize
            # stepSize = 0.001 → 3 décimales, stepSize = 0.01 → 2 décimales, etc.
            import math
            precision = max(0, int(-math.log10(step_size)))
            
            # Arrondi selon la règle stepSize (quantité doit être un multiple de stepSize)
            formatted_quantity = round(quantity / step_size) * step_size
            
            # Application de la précision pour éviter les erreurs de virgule flottante
            formatted_quantity = round(formatted_quantity, precision)
            
            self.logger.debug(f"📏 {symbol}: quantité {quantity:.8f} → {formatted_quantity:.8f} (stepSize: {step_size}, precision: {precision})")
            
            return formatted_quantity
            
        except Exception as e:
            self.logger.error(f"❌ Erreur formatage quantité {symbol}: {e}")
            return round(quantity, 6)  # Précision sécurisée par défaut
    
    async def _format_price(self, symbol: str, price: float) -> float:
        """Formate le prix selon les règles de précision de Binance"""
        try:
            symbol_info = await self.data_fetcher.get_symbol_info(symbol)
            if not symbol_info:
                self.logger.warning(f"⚠️ Informations symbole non trouvées pour {symbol}, utilisation précision prix par défaut")
                return round(price, 8)  # Précision par défaut
            
            # Récupération du filtre PRICE_FILTER pour la précision de prix
            tick_size = None
            for filter_info in symbol_info.get('filters', []):
                if filter_info['filterType'] == 'PRICE_FILTER':
                    tick_size = float(filter_info['tickSize'])
                    break
            
            if tick_size is None:
                # Fallback avec quotePrecision si disponible
                precision = symbol_info.get('quotePrecision', 8)
                return round(price, precision)
            
            # Calcul de la précision basée sur tickSize
            import math
            precision = max(0, int(-math.log10(tick_size)))
            
            # Arrondi selon la règle tickSize (prix doit être un multiple de tickSize)
            formatted_price = round(price / tick_size) * tick_size
            
            # Application de la précision pour éviter les erreurs de virgule flottante
            formatted_price = round(formatted_price, precision)
            
            self.logger.debug(f"💰 {symbol}: prix {price:.8f} → {formatted_price:.8f} (tickSize: {tick_size}, precision: {precision})")
            
            return formatted_price
            
        except Exception as e:
            self.logger.error(f"❌ Erreur formatage prix {symbol}: {e}")
            return round(price, 8)  # Précision sécurisée par défaut
    
    async def get_rsi_distribution_strategy(self, symbol: str) -> Tuple[float, float, str]:
        """
        Calcule le RSI et retourne la stratégie de répartition optimale
        Returns: (sl_percentage, tp_percentage, strategy_name)
        """
        try:
            # Vérifier que les indicateurs sont disponibles
            if not self.indicators:
                self.logger.warning(f"⚠️ Indicateurs non disponibles pour {symbol} - Stratégie équilibrée par défaut")
                return 50.0, 50.0, "Neutre (indicateurs non disponibles)"
            
            # Récupération des données historiques (100 bougies pour RSI fiable)
            klines = await self.data_fetcher.get_klines(symbol, "1h", 100)
            
            if not klines or len(klines) < 50:
                self.logger.warning(f"⚠️ Données insuffisantes pour RSI {symbol} - Stratégie équilibrée par défaut")
                return 50.0, 50.0, "Neutre (données insuffisantes)"
            
            # Extraction des prix de clôture
            closes = [float(kline[4]) for kline in klines]  # Index 4 = close price
            closes_series = pd.Series(closes)  # Convertir en Series pandas
            
            # Calcul du RSI
            rsi_values = self.indicators.calculate_rsi(closes_series, period=14)
            current_rsi = float(rsi_values.iloc[-1])  # Dernier RSI
            
            # Stratégie de répartition basée sur RSI
            if current_rsi > 70:
                # Marché SURACHETÉ → Privilégier les profits
                sl_pct, tp_pct = 30.0, 70.0
                strategy = f"Suracheté (RSI: {current_rsi:.1f})"
                self.logger.info(f"📈 {symbol} - Marché SURACHETÉ: RSI {current_rsi:.1f} → Privilégier profits (30% SL / 70% TP)")
            elif current_rsi < 30:
                # Marché SURVENDU → Protéger le capital
                sl_pct, tp_pct = 80.0, 20.0
                strategy = f"Survendu (RSI: {current_rsi:.1f})"
                self.logger.info(f"📉 {symbol} - Marché SURVENDU: RSI {current_rsi:.1f} → Protéger capital (80% SL / 20% TP)")
            else:
                # Marché NEUTRE → Approche équilibrée
                sl_pct, tp_pct = 50.0, 50.0
                strategy = f"Neutre (RSI: {current_rsi:.1f})"
                self.logger.info(f"⚖️ {symbol} - Marché NEUTRE: RSI {current_rsi:.1f} → Approche équilibrée (50% SL / 50% TP)")
            
            return sl_pct, tp_pct, strategy
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur calcul RSI pour {symbol}: {e} - Stratégie équilibrée par défaut")
            return 50.0, 50.0, "Neutre (erreur calcul RSI)"
    
    async def can_open_trade(self, pair: str) -> Tuple[bool, str]:
        """Vérifie si un nouveau trade peut être ouvert"""
        
        # Vérification pause
        if self.is_paused:
            if self.pause_until and datetime.now() > self.pause_until:
                self.is_paused = False
                self.pause_until = None
                self.logger.info("✅ Fin de pause - Trading réactivé")
            else:
                return False, "Bot en pause après pertes consécutives"
        
        # Vérification positions maximum
        if len(self.active_trades) >= self.config.MAX_OPEN_POSITIONS:
            return False, f"Maximum de {self.config.MAX_OPEN_POSITIONS} positions atteint"
        
        # Vérification paire déjà en position
        for trade in self.active_trades.values():
            if trade.pair == pair:
                return False, f"Position déjà ouverte sur {pair}"
        
        # Vérification capital minimum
        try:
            balance = await self.data_fetcher.get_account_balance()
            usdc_balance = float(balance.get('USDC', {}).get('free', 0))
            
            if usdc_balance < self.risk_config.MIN_CAPITAL_TO_TRADE:
                return False, f"Capital insuffisant: {usdc_balance:.2f} USDC"
                
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification balance: {e}")
            return False, "Erreur vérification balance"
        
        # Vérification anti-surtrading
        if not self._check_anti_surtrading(pair):
            return False, "Limite anti-surtrading atteinte"
        
        # Vérification limite quotidienne
        if self.daily_trades >= self.risk_config.MAX_DAILY_TRADES:
            return False, f"Limite quotidienne de {self.risk_config.MAX_DAILY_TRADES} trades atteinte"
        
        # Vérification stop loss quotidien
        if abs(self.daily_pnl) >= self.risk_config.MAX_DAILY_LOSS:
            return False, f"Stop loss quotidien atteint: {self.daily_pnl:.2f} USDC"
        
        return True, "OK"
    
    def _check_anti_surtrading(self, pair: str) -> bool:
        """Vérifie les règles anti-surtrading"""
        now = datetime.now()
        
        # Nettoyage des anciens timestamps (> 1 heure)
        hour_ago = now - timedelta(hours=1)
        self.trade_timestamps = [ts for ts in self.trade_timestamps if ts > hour_ago]
        
        # Vérification trades par heure globaux
        if len(self.trade_timestamps) >= self.config.MAX_TRADES_PER_HOUR:
            return False
        
        # Vérification temps minimum entre achats
        if self.last_trade_time:
            time_since_last = (now - self.last_trade_time).total_seconds()
            if time_since_last < self.config.MIN_TIME_BETWEEN_BUYS:
                return False
        
        # Vérification trades par paire (dernière heure)
        pair_trades_count = sum(
            1 for trade in self.trade_history
            if trade.pair == pair and trade.timestamp > hour_ago
        )
        
        if pair_trades_count >= self.config.MAX_TRADES_PER_PAIR_HOUR:
            return False
        
        return True
    
    async def open_trade(self, pair: str, analysis_data: Dict[str, Any]) -> Optional[Trade]:
        """Ouvre un nouveau trade basé sur l'analyse"""
        
        # Vérifications préalables
        can_trade, reason = await self.can_open_trade(pair)
        if not can_trade:
            self.logger.warning(f"⚠️ Trade {pair} refusé: {reason}")
            return None
        
        try:
            # Calcul de la taille de position
            position_size_usdc = await self._calculate_position_size()
            if position_size_usdc < self.config.MIN_POSITION_SIZE_USDC:
                self.logger.warning(f"⚠️ Position trop petite: {position_size_usdc:.2f} USDC")
                return None
            
            # Récupération du prix actuel
            ticker = await self.data_fetcher.get_ticker_price(pair)
            current_price = float(ticker['price'])
            
            # Calcul de la quantité
            quantity = position_size_usdc / current_price
            
            # 🔧 FORMATAGE DE LA QUANTITÉ selon les règles Binance
            quantity = await self._format_quantity(pair, quantity)
            
            # Calcul stop loss et take profit
            stop_loss_price = current_price * (1 - self.config.STOP_LOSS_PERCENT / 100)
            take_profit_price = current_price * (1 + self.config.TAKE_PROFIT_PERCENT / 100)
            
            # 🔧 FORMATAGE DES PRIX selon les règles Binance
            stop_loss_price = await self._format_price(pair, stop_loss_price)
            take_profit_price = await self._format_price(pair, take_profit_price)
            
            # Génération ID trade
            trade_id = f"{pair}_{int(time.time())}"
            
            # Création de l'objet trade
            trade = Trade(
                trade_id=trade_id,
                pair=pair,
                side="BUY",
                entry_price=current_price,
                quantity=quantity,
                capital_engaged=position_size_usdc,
                stop_loss=stop_loss_price,
                take_profit=take_profit_price,
                timestamp=datetime.now(),
                status=TradeStatus.PENDING,
                rsi_value=analysis_data.get('rsi_value', 0),
                entry_conditions=analysis_data.get('entry_conditions', {}),
                breakout_detected=analysis_data.get('breakout_detected', False)
            )
            
            # Exécution de l'ordre d'achat
            success = await self._execute_buy_order(trade)
            if not success:
                return None
            
            # Mise en place des ordres stop loss et take profit
            await self._setup_exit_orders(trade)
            
            # Mise à jour du statut
            trade.status = TradeStatus.OPEN
            self.active_trades[trade_id] = trade
            self.position_count += 1
            
            # Mise à jour des statistiques
            self.daily_trades += 1
            self.last_trade_time = datetime.now()
            self.trade_timestamps.append(datetime.now())
            
            # Logging
            await self._log_trade_open(trade)
            
            self.logger.info(f"✅ Trade ouvert: {pair} à {current_price:.6f} USDC")
            return trade
            
        except Exception as e:
            self.logger.error(f"❌ Erreur ouverture trade {pair}: {e}")
            await self._log_error("TRADE_EXECUTION", f"Erreur ouverture {pair}", str(e))
            return None
    
    async def _calculate_position_size(self) -> float:
        """Calcule la taille de position en USDC"""
        try:
            # Récupération du capital disponible
            balance = await self.data_fetcher.get_account_balance()
            usdc_balance = float(balance.get('USDC', {}).get('free', 0))
            
            # Taille de base
            base_size = usdc_balance * (self.config.POSITION_SIZE_PERCENT / 100)
            
            # Ajustement dynamique selon les pertes récentes
            if self.risk_config.DYNAMIC_SIZING and self.consecutive_losses > 0:
                reduction_factor = self.risk_config.SIZE_REDUCTION_FACTOR ** self.consecutive_losses
                base_size *= reduction_factor
                self.logger.info(f"📉 Taille réduite après {self.consecutive_losses} pertes: {reduction_factor:.2f}x")
            
            # Application des limites
            position_size = max(
                self.config.MIN_POSITION_SIZE_USDC,
                min(base_size, self.config.MAX_POSITION_SIZE_USDC)
            )
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul position: {e}")
            return self.config.MIN_POSITION_SIZE_USDC
    
    async def _execute_buy_order(self, trade: Trade) -> bool:
        """Exécute l'ordre d'achat"""
        try:
            # Ordre market buy
            order = await self.data_fetcher.place_order(
                symbol=trade.pair,
                side="BUY",
                order_type="MARKET",
                quantity=trade.quantity
            )
            
            trade.entry_order_id = order['orderId']
            
            # Mise à jour du prix d'entrée réel si différent
            if 'fills' in order and order['fills']:
                # Calcul du prix moyen pondéré
                total_cost = sum(float(fill['price']) * float(fill['qty']) for fill in order['fills'])
                total_qty = sum(float(fill['qty']) for fill in order['fills'])
                avg_price = total_cost / total_qty if total_qty > 0 else trade.entry_price
                trade.entry_price = avg_price
            
            self.logger.info(f"✅ Ordre d'achat exécuté: {trade.pair}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur ordre d'achat {trade.pair}: {e}")
            return False
    
    async def _setup_exit_orders(self, trade: Trade):
        """Met en place les ordres de sortie (SL/TP) automatiques dans Binance - VERSION ULTRA ROBUSTE avec répartition intelligente"""
        try:
            # Vérification des types d'ordres supportés
            symbol_info = await self.data_fetcher.get_symbol_info(trade.pair)
            supported_order_types = symbol_info.get('orderTypes', []) if symbol_info else []
            
            self.logger.info(f"📋 Types d'ordres supportés pour {trade.pair}: {supported_order_types}")
            
            # 🧠 STRATÉGIE INTELLIGENTE : Calcul de répartition optimale pour SL/TP
            # Estimation du prix SL pour calculer la valeur NOTIONAL minimale
            stop_loss_price_estimate = trade.stop_loss
            min_sl_quantity_for_notional = (6.0 / stop_loss_price_estimate) * 1.1  # +10% de marge pour 5 USDC min
            
            # Formatage robuste de la quantité avec vérifications multiples
            try:
                formatted_quantity = await self._format_quantity(trade.pair, trade.quantity)
                
                # Double vérification - si formatage donne 0, on essaie une approche différente
                if formatted_quantity <= 0:
                    try:
                        # Récupération manuelle des règles de formatage
                        if symbol_info and 'filters' in symbol_info:
                            lot_size_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
                            if lot_size_filter:
                                step_size = float(lot_size_filter['stepSize'])
                                # Arrondir à la step_size inférieure
                                formatted_quantity = (trade.quantity // step_size) * step_size
                                self.logger.info(f"🔧 Formatage manuel quantité {trade.pair}: {trade.quantity:.8f} → {formatted_quantity:.8f}")
                    except Exception as e:
                        self.logger.error(f"❌ Erreur formatage manuel {trade.pair}: {e}")
                
                if formatted_quantity <= 0:
                    self.logger.warning(f"⚠️ Impossible de formater quantité {trade.pair}: {trade.quantity:.8f} → passage en gestion manuelle")
                    return
                
                # 🚀 NOUVELLE STRATÉGIE ADAPTATIVE RSI : Répartition intelligente basée sur les conditions de marché
                # Calcul de la stratégie optimale selon le RSI
                sl_percentage, tp_percentage, strategy_name = await self.get_rsi_distribution_strategy(trade.pair)
                
                # Calcul des quantités optimales pour garantir SL avec valeur NOTIONAL suffisante
                
                # Estimation du prix SL pour calculer la valeur NOTIONAL minimale
                stop_loss_price_estimate = trade.stop_loss
                min_sl_quantity_for_notional = (6.0 / stop_loss_price_estimate) * 1.1  # +10% de marge pour 5 USDC min
                
                # 🎯 STRATÉGIE ADAPTATIVE RSI DE RÉPARTITION
                # Répartition basée sur les conditions de marché (RSI)
                if formatted_quantity > min_sl_quantity_for_notional * 1.5:  # Seuil plus bas pour permettre plus de répartitions
                    
                    # Calcul des quantités selon la stratégie RSI
                    sl_target_quantity = formatted_quantity * (sl_percentage / 100)
                    tp_target_quantity = formatted_quantity * (tp_percentage / 100)
                    
                    # S'assurer que la quantité SL respecte le minimum NOTIONAL
                    if sl_target_quantity < min_sl_quantity_for_notional:
                        sl_target_quantity = min_sl_quantity_for_notional
                        tp_target_quantity = formatted_quantity - sl_target_quantity
                    
                    # Formatage des quantités finales
                    reserved_sl_quantity = await self._format_quantity(trade.pair, sl_target_quantity)
                    tp_quantity = await self._format_quantity(trade.pair, tp_target_quantity)
                    
                    # Vérifier que les quantités formatées sont valides
                    if reserved_sl_quantity > 0 and tp_quantity > 0:
                        # Vérifier que la valeur NOTIONAL SL est suffisante
                        estimated_notional = reserved_sl_quantity * stop_loss_price_estimate
                        if estimated_notional >= 5.0:
                            self.logger.info(f"🧠 Stratégie RSI {strategy_name} pour {trade.pair}:")
                            self.logger.info(f"   📊 Total: {formatted_quantity:.8f}")
                            self.logger.info(f"   🎯 TP ({tp_percentage:.0f}%): {tp_quantity:.8f}")
                            self.logger.info(f"   🛡️ SL ({sl_percentage:.0f}%): {reserved_sl_quantity:.8f} (≈{estimated_notional:.2f} USDC)")
                            
                            # Utiliser les quantités calculées selon RSI
                            tp_order_quantity = tp_quantity
                            sl_reserved_quantity = reserved_sl_quantity
                        else:
                            # Quantité SL trop petite en valeur, mode standard
                            tp_order_quantity = formatted_quantity
                            sl_reserved_quantity = None
                            self.logger.info(f"⚠️ Quantité SL RSI {trade.pair} trop petite ({estimated_notional:.2f} USDC < 5 USDC) - Mode standard")
                    else:
                        # Formatage échoué, mode standard
                        tp_order_quantity = formatted_quantity
                        sl_reserved_quantity = None
                        self.logger.info(f"⚠️ Formatage quantités RSI {trade.pair} impossible - Mode standard")
                else:
                    # Si quantité insuffisante pour diviser selon RSI, utiliser toute la quantité pour TP
                    tp_order_quantity = formatted_quantity
                    sl_reserved_quantity = None
                    self.logger.info(f"⚠️ Quantité {trade.pair} insuffisante pour répartition RSI - Mode standard")
                    
            except Exception as e:
                self.logger.error(f"❌ Erreur formatage quantité {trade.pair}: {e}")
                tp_order_quantity = trade.quantity
                sl_reserved_quantity = None
                
        except Exception as e:
            self.logger.error(f"❌ Erreur formatage quantité {trade.pair}: {e}")
            self.logger.warning("⚠️ Passage en gestion manuelle des SL/TP")
            return
        
        # 1. Ordre Take Profit - Stratégie robuste avec fallbacks
        tp_order_placed = False
        
        # Essai TAKE_PROFIT_LIMIT d'abord (recommandé pour Spot)
        if 'TAKE_PROFIT_LIMIT' in supported_order_types and tp_order_quantity > 0:
            try:
                    tp_order = await self.data_fetcher.place_order(
                        symbol=trade.pair,
                        side="SELL",
                        order_type="TAKE_PROFIT_LIMIT",
                        quantity=tp_order_quantity,
                        price=trade.take_profit,
                        stopPrice=trade.take_profit,
                        timeInForce="GTC"
                    )
                    trade.take_profit_order_id = tp_order['orderId']
                    self.logger.info(f"✅ TP automatique (TAKE_PROFIT_LIMIT) placé: {trade.take_profit:.6f} USDC (ID: {tp_order['orderId']})")
                    tp_order_placed = True
            except Exception as e:
                    self.logger.error(f"❌ Erreur TAKE_PROFIT_LIMIT: {e}")
            
        # Fallback: TAKE_PROFIT (SANS timeInForce - pas supporté)
        if not tp_order_placed and 'TAKE_PROFIT' in supported_order_types and tp_order_quantity > 0:
            try:
                    tp_order = await self.data_fetcher.place_order(
                        symbol=trade.pair,
                        side="SELL",
                        order_type="TAKE_PROFIT",
                        quantity=tp_order_quantity,
                        stopPrice=trade.take_profit
                        # timeInForce pas supporté pour TAKE_PROFIT
                    )
                    trade.take_profit_order_id = tp_order['orderId']
                    self.logger.info(f"✅ TP automatique (TAKE_PROFIT) placé: {trade.take_profit:.6f} USDC (ID: {tp_order['orderId']})")
                    tp_order_placed = True
            except Exception as e:
                    self.logger.error(f"❌ Erreur TAKE_PROFIT: {e}")    
            
        # Fallback final: LIMIT classique
        if not tp_order_placed and 'LIMIT' in supported_order_types and tp_order_quantity > 0:
            try:
                tp_order = await self.data_fetcher.place_order(
                    symbol=trade.pair,
                    side="SELL",
                    order_type="LIMIT",
                    quantity=tp_order_quantity,
                    price=trade.take_profit,
                    timeInForce="GTC"
                )
                trade.take_profit_order_id = tp_order['orderId']
                self.logger.info(f"✅ TP automatique (LIMIT) placé: {trade.take_profit:.6f} USDC (ID: {tp_order['orderId']})")
                tp_order_placed = True
            except Exception as e:
                self.logger.error(f"❌ Erreur ordre TP LIMIT: {e}")
        
        if not tp_order_placed:
            self.logger.warning(f"⚠️ Impossible de placer TP automatique pour {trade.pair}")
        
        # 2. Ordre Stop Loss avec Trailing Stop - Version ultra robuste avec logique intelligente
        sl_order_placed = False
        
        # Conversion du pourcentage en BIPS pour trailing stop (ex: 0.3% -> 30 BIPS)
        trailing_delta_bips = int(self.config.TRAILING_STOP_DISTANCE * 100) if self.config.TRAILING_STOP_ENABLED else None
        
        # 🎯 NOUVELLE LOGIQUE: Utiliser la quantité réservée si disponible
        sl_quantity_to_use = sl_reserved_quantity if sl_reserved_quantity is not None else tp_order_quantity
        
        # Vérification de la valeur NOTIONAL minimale pour SL (éviter erreurs -1013)
        if sl_quantity_to_use > 0:
            notional_value = sl_quantity_to_use * trade.stop_loss
            if notional_value < 5.0:  # Valeur minimale généralement 5 USDC
                self.logger.warning(f"⚠️ Valeur SL {trade.pair} trop petite: {notional_value:.2f} USDC < 5 USDC - Skip SL automatique")
                sl_quantity_to_use = 0
            else:
                if sl_reserved_quantity is not None:
                    self.logger.info(f"✅ Utilisation quantité SL réservée: {sl_quantity_to_use:.8f} (≈{notional_value:.2f} USDC)")
                else:
                    self.logger.info(f"✅ Valeur SL {trade.pair} suffisante: {notional_value:.2f} USDC")
            
            # Essai STOP_LOSS_LIMIT avec trailing stop d'abord (recommandé pour Spot)
            if 'STOP_LOSS_LIMIT' in supported_order_types and sl_quantity_to_use > 0:
                try:
                    order_params = {
                        'symbol': trade.pair,
                        'side': "SELL",
                        'order_type': "STOP_LOSS_LIMIT",
                        'quantity': sl_quantity_to_use,
                        'price': trade.stop_loss,
                        'timeInForce': 'GTC'
                    }
                    
                    # Ajout du trailing stop si activé
                    if self.config.TRAILING_STOP_ENABLED and trailing_delta_bips:
                        order_params['trailingDelta'] = trailing_delta_bips
                        # Pour un trailing stop, stopPrice est optionnel - omis pour démarrage immédiat
                        self.logger.info(f"📈 Trailing Stop activé: {self.config.TRAILING_STOP_DISTANCE}% ({trailing_delta_bips} BIPS)")
                    else:
                        order_params['stopPrice'] = trade.stop_loss
                    
                    sl_order = await self.data_fetcher.place_order(**order_params)
                    trade.stop_loss_order_id = sl_order['orderId']
                    
                    if self.config.TRAILING_STOP_ENABLED and trailing_delta_bips:
                        trade.trailing_stop_active = True
                        self.logger.info(f"✅ SL automatique avec Trailing Stop (STOP_LOSS_LIMIT) placé: {self.config.TRAILING_STOP_DISTANCE}% trailing (ID: {sl_order['orderId']})")
                    else:
                        self.logger.info(f"✅ SL automatique (STOP_LOSS_LIMIT) placé: {trade.stop_loss:.6f} USDC (ID: {sl_order['orderId']})")
                    
                    sl_order_placed = True
                except Exception as e:
                    self.logger.error(f"❌ Erreur STOP_LOSS_LIMIT: {e}")
            
            # Fallback: Essai STOP_LOSS si STOP_LOSS_LIMIT échoue (SANS timeInForce)
            if not sl_order_placed and 'STOP_LOSS' in supported_order_types and sl_quantity_to_use > 0:
                try:
                    order_params = {
                        'symbol': trade.pair,
                        'side': "SELL",
                        'order_type': "STOP_LOSS",
                        'quantity': sl_quantity_to_use
                        # timeInForce pas supporté pour STOP_LOSS
                    }
                    
                    # Ajout du trailing stop si activé
                    if self.config.TRAILING_STOP_ENABLED and trailing_delta_bips:
                        order_params['trailingDelta'] = trailing_delta_bips
                        # Pour un trailing stop, stopPrice est optionnel
                        self.logger.info(f"📈 Trailing Stop activé: {self.config.TRAILING_STOP_DISTANCE}% ({trailing_delta_bips} BIPS)")
                    else:
                        order_params['stopPrice'] = trade.stop_loss
                    
                    sl_order = await self.data_fetcher.place_order(**order_params)
                    trade.stop_loss_order_id = sl_order['orderId']
                    
                    if self.config.TRAILING_STOP_ENABLED and trailing_delta_bips:
                        trade.trailing_stop_active = True
                        self.logger.info(f"✅ SL automatique avec Trailing Stop (STOP_LOSS) placé: {self.config.TRAILING_STOP_DISTANCE}% trailing (ID: {sl_order['orderId']})")
                    else:
                        self.logger.info(f"✅ SL automatique (STOP_LOSS) placé: {trade.stop_loss:.6f} USDC (ID: {sl_order['orderId']})")
                    
                    sl_order_placed = True
                except Exception as e:
                    self.logger.error(f"❌ Erreur STOP_LOSS: {e}")
            
            if not sl_order_placed:
                self.logger.warning(f"⚠️ Impossible de placer SL automatique pour {trade.pair} - Gestion manuelle activée")
            
            # 3. Logging des résultats
            if tp_order_placed and sl_order_placed:
                self.logger.info(f"📊 Ordres automatiques TP et SL configurés pour {trade.pair}")
            elif tp_order_placed:
                self.logger.info(f"📊 Ordre TP automatique configuré pour {trade.pair} - SL en gestion manuelle")
            elif sl_order_placed:
                self.logger.info(f"📊 Ordre SL automatique configuré pour {trade.pair} - TP en gestion manuelle")
            else:
                self.logger.warning(f"⚠️ Aucun ordre automatique pour {trade.pair} - Surveillance manuelle requise")
    
    async def monitor_positions(self):
        """Surveille les positions ouvertes"""
        for trade_id, trade in list(self.active_trades.items()):
            try:
                await self._check_exit_conditions(trade)
            except Exception as e:
                self.logger.error(f"❌ Erreur monitoring {trade.pair}: {e}")
    
    async def _check_exit_conditions(self, trade: Trade):
        """Vérifie les conditions de sortie pour un trade"""
        try:
            # Récupération du prix actuel
            ticker = await self.data_fetcher.get_ticker_price(trade.pair)
            current_price = float(ticker['price'])
            
            # Calcul P&L actuel
            current_pnl_percent = ((current_price - trade.entry_price) / trade.entry_price) * 100
            
            # 1. Vérification Take Profit
            if current_price >= trade.take_profit:
                await self._close_trade(trade, current_price, ExitReason.TAKE_PROFIT)
                return
            
            # 2. Vérification Stop Loss
            if current_price <= trade.stop_loss:
                await self._close_trade(trade, current_price, ExitReason.STOP_LOSS)
                return
            
            # 3. Vérification timeout adaptatif
            if self.config.TIMEOUT_ENABLED:
                duration = (datetime.now() - trade.timestamp).total_seconds() / 60  # en minutes
                if (duration >= self.config.TIMEOUT_MINUTES and
                    self.config.TIMEOUT_PNL_MIN <= current_pnl_percent <= self.config.TIMEOUT_PNL_MAX):
                    await self._close_trade(trade, current_price, ExitReason.TIMEOUT)
                    return
            
            # 4. Vérification sortie anticipée
            if self.config.EARLY_EXIT_ENABLED:
                duration_minutes = (datetime.now() - trade.timestamp).total_seconds() / 60
                
                if duration_minutes >= self.config.EARLY_EXIT_DURATION_MIN:
                    # Récupération des données pour analyse RSI/MACD
                    df = await self._get_recent_klines(trade.pair)
                    if df is not None and len(df) > 0:
                        from indicators import RSIScalpingIndicators
                        indicators = RSIScalpingIndicators(self.config)
                        exit_signals = indicators.get_exit_signals(df)
                        
                        if (exit_signals['rsi_weak'] or exit_signals['macd_negative']):
                            await self._close_trade(trade, current_price, ExitReason.EARLY_EXIT)
                            return
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification conditions sortie {trade.pair}: {e}")
    
    async def _close_trade(self, trade: Trade, exit_price: float, exit_reason: ExitReason):
        """Ferme un trade"""
        try:
            # Annuler les ordres SL/TP automatiques si ils existent
            if hasattr(trade, 'take_profit_order_id') and trade.take_profit_order_id:
                try:
                    await self.data_fetcher.cancel_order(trade.pair, trade.take_profit_order_id)
                    self.logger.info(f"✅ Take Profit {trade.take_profit_order_id} annulé pour {trade.pair}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Erreur annulation TP {trade.take_profit_order_id}: {e}")
            
            if hasattr(trade, 'stop_loss_order_id') and trade.stop_loss_order_id:
                try:
                    await self.data_fetcher.cancel_order(trade.pair, trade.stop_loss_order_id)
                    self.logger.info(f"✅ Stop Loss {trade.stop_loss_order_id} annulé pour {trade.pair}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Erreur annulation SL {trade.stop_loss_order_id}: {e}")
            
            # Exécution de l'ordre de vente
            order = await self.data_fetcher.place_order(
                symbol=trade.pair,
                side="SELL",
                order_type="MARKET",
                quantity=trade.quantity
            )
            
            # Mise à jour des données du trade
            trade.exit_price = exit_price
            trade.exit_timestamp = datetime.now()
            trade.exit_reason = exit_reason
            trade.status = TradeStatus.CLOSED
            
            # Calcul des performances
            trade.duration_seconds = int((trade.exit_timestamp - trade.timestamp).total_seconds())
            trade.pnl_amount = (exit_price - trade.entry_price) * trade.quantity
            trade.pnl_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100
            
            # Estimation des fees (0.1% par trade)
            trade.fees = trade.capital_engaged * 0.002  # 0.1% buy + 0.1% sell
            net_pnl = trade.pnl_amount - trade.fees
            
            # Mise à jour des statistiques
            self.daily_pnl += net_pnl
            
            # Gestion des pertes consécutives
            if net_pnl < 0:
                self.consecutive_losses += 1
                
                # Pause si trop de pertes consécutives
                if self.consecutive_losses >= self.config.MAX_LOSS_STREAK:
                    self.is_paused = True
                    self.pause_until = datetime.now() + timedelta(minutes=self.config.LOSS_PAUSE_MINUTES)
                    
                    self.logger.warning(f"⏸️ Bot en pause pour {self.config.LOSS_PAUSE_MINUTES} min après {self.consecutive_losses} pertes")
                    
                    if self.telegram_notifier:
                        await self.telegram_notifier.send_warning_notification({
                            'message': f"Bot en pause {self.config.LOSS_PAUSE_MINUTES}min après {self.consecutive_losses} pertes consécutives"
                        })
            else:
                self.consecutive_losses = 0  # Reset si trade gagnant
            
            # Suppression des positions actives
            if trade.trade_id in self.active_trades:
                del self.active_trades[trade.trade_id]
            
            self.position_count = len(self.active_trades)
            
            # Ajout à l'historique
            self.trade_history.append(trade)
            
            # Logging
            await self._log_trade_close(trade)
            
            self.logger.info(f"✅ Trade fermé: {trade.pair} | {exit_reason.value} | P&L: {net_pnl:+.2f} USDC")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur fermeture trade {trade.pair}: {e}")
            trade.status = TradeStatus.ERROR
    
    async def _get_recent_klines(self, pair: str, limit: int = 50):
        """Récupère les dernières bougies pour analyse"""
        try:
            klines = await self.data_fetcher.get_klines(pair, self.config.TIMEFRAME, limit)
            
            if not klines:
                return None
                
            # Conversion en DataFrame
            import pandas as pd
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'count', 'taker_buy_volume',
                'taker_buy_quote_volume', 'ignore'
            ])
            
            # Conversion des types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération klines {pair}: {e}")
            return None
    
    async def force_close_all_positions(self, reason: str = "MANUAL"):
        """Force la fermeture de toutes les positions"""
        self.logger.warning(f"⚠️ Fermeture forcée de toutes les positions: {reason}")
        
        for trade in list(self.active_trades.values()):
            try:
                ticker = await self.data_fetcher.get_ticker_price(trade.pair)
                current_price = float(ticker['price'])
                await self._close_trade(trade, current_price, ExitReason.MANUAL)
            except Exception as e:
                self.logger.error(f"❌ Erreur fermeture forcée {trade.pair}: {e}")
    
    async def get_position_status(self) -> Dict[str, Any]:
        """Retourne le statut des positions"""
        try:
            positions = []
            
            for trade in self.active_trades.values():
                # Prix actuel
                ticker = await self.data_fetcher.get_ticker_price(trade.pair)
                current_price = float(ticker['price'])
                
                # P&L actuel
                current_pnl_amount = (current_price - trade.entry_price) * trade.quantity
                current_pnl_percent = ((current_price - trade.entry_price) / trade.entry_price) * 100
                
                positions.append({
                    'pair': trade.pair,
                    'entry_price': trade.entry_price,
                    'current_price': current_price,
                    'quantity': trade.quantity,
                    'pnl_amount': current_pnl_amount,
                    'pnl_percent': current_pnl_percent,
                    'stop_loss': trade.stop_loss,
                    'take_profit': trade.take_profit,
                    'duration': trade.duration_formatted
                })
            
            return {
                'active_positions': positions,
                'position_count': len(positions),
                'daily_pnl': self.daily_pnl,
                'daily_trades': self.daily_trades,
                'consecutive_losses': self.consecutive_losses,
                'is_paused': self.is_paused,
                'pause_until': self.pause_until.isoformat() if self.pause_until else None
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération statut positions: {e}")
            return {}
    
    def reset_daily_stats(self):
        """Remet à zéro les statistiques quotidiennes"""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.trade_timestamps = []
        self.logger.info("🔄 Statistiques quotidiennes remises à zéro")
    
    async def _log_trade_open(self, trade: Trade):
        """Log l'ouverture d'un trade"""
        try:
            # Firebase
            if self.firebase_logger:
                await self.firebase_logger.log_trade_open(
                    pair=trade.pair,
                    entry_price=trade.entry_price,
                    quantity=trade.quantity,
                    take_profit=trade.take_profit,
                    stop_loss=trade.stop_loss,
                    analysis_data={}  # TODO: Passer les données d'analyse
                )
            
            # Telegram
            if self.telegram_notifier:
                await self.telegram_notifier.send_trade_open_notification(asdict(trade))
                
        except Exception as e:
            self.logger.error(f"❌ Erreur log ouverture trade: {e}")
    
    async def _log_trade_close(self, trade: Trade):
        """Log la fermeture d'un trade"""
        try:
            # Firebase
            if self.firebase_logger:
                await self.firebase_logger.log_trade_close(trade.trade_id, asdict(trade))
            
            # Telegram
            if self.telegram_notifier:
                trade_data = asdict(trade)
                trade_data.update({
                    'daily_pnl': self.daily_pnl,
                    'total_capital': await self._get_total_capital()
                })
                await self.telegram_notifier.send_trade_close_notification(trade_data)
                
        except Exception as e:
            self.logger.error(f"❌ Erreur log fermeture trade: {e}")
    
    async def _log_error(self, component: str, message: str, details: str):
        """Log une erreur"""
        try:
            if self.firebase_logger:
                await self.firebase_logger.log_error({
                    'component': component,
                    'message': message,
                    'details': details,
                    'level': 'ERROR'
                })
            
            if self.telegram_notifier:
                await self.telegram_notifier.send_error_notification({
                    'component': component,
                    'message': message
                })
                
        except Exception as e:
            self.logger.error(f"❌ Erreur log erreur: {e}")
    
    async def _get_total_capital(self) -> float:
        """Récupère le capital total"""
        try:
            balance = await self.data_fetcher.get_account_balance()
            return float(balance.get('USDC', {}).get('free', 0))
        except:
            return 0.0


# Test du trade executor
if __name__ == "__main__":
    print("🧪 Trade Executor - Tests unitaires")
    print("Utilisation dans le contexte du bot principal")
