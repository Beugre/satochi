#!/usr/bin/env python3
"""
💼 TRADE EXECUTOR - RSI SCALPING PRO
Gestionnaire d'exécution des trades avec gestion des risques
"""

import asyncio
import logging
import time
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
    take_profit: float
    stop_loss: float
    timestamp: datetime
    
    # Données de signal (ajout pour compatibilité)
    rsi_value: Optional[float] = None
    signal_data: Optional[dict] = None
    
    # Ordres
    entry_order_id: Optional[str] = None
    take_profit_order_id: Optional[str] = None
    stop_loss_order_id: Optional[str] = None
    trailing_stop_order_id: Optional[str] = None
    oco_order_id: Optional[str] = None  # ID du groupe OCO
    
    # Statut
    status: TradeStatus = TradeStatus.PENDING
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    exit_reason: Optional[ExitReason] = None
    
    # Performance
    pnl_amount: Optional[float] = None
    pnl_percent: Optional[float] = None
    duration_seconds: Optional[int] = None
    fees: Optional[float] = None
    
    # Trailing stop
    trailing_stop_active: bool = False
    trailing_stop_pending: bool = False
    highest_price: Optional[float] = None
    
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
        
        # Indicateurs techniques
        from indicators import TechnicalIndicators
        self.indicators = TechnicalIndicators(config)
        
        self.logger.info("� Indicateurs techniques RSI initialisés")
        self.logger.info("�💼 Trade Executor initialisé")
    
    async def sync_positions_with_binance(self):
        """Synchronise les positions actives avec l'état réel de Binance"""
        try:
            if not self.active_trades:
                return
            
            # Récupérer les balances actuels depuis Binance
            account_info = await self.data_fetcher.get_account_balance()
            
            positions_to_remove = []
            
            for trade_id, trade in self.active_trades.items():
                symbol_without_usdc = trade.pair.replace('USDC', '')
                
                # Vérifier si on a encore du balance de cette crypto
                has_balance = False
                if symbol_without_usdc in account_info:
                    balance = float(account_info[symbol_without_usdc]['free'])
                    locked = float(account_info[symbol_without_usdc]['locked'])
                    total_balance = balance + locked
                    
                    # Si le balance est très proche de la quantité de la position
                    if abs(total_balance - trade.quantity) < 0.001:
                        has_balance = True
                
                # Si plus de balance, la position a été fermée automatiquement
                if not has_balance:
                    self.logger.info(f"🔄 Trade {trade.pair} fermé automatiquement par TP/SL - Suppression de active_trades")
                    positions_to_remove.append(trade_id)
            
            # Supprimer les positions fermées
            for trade_id in positions_to_remove:
                if trade_id in self.active_trades:
                    del self.active_trades[trade_id]
            
            # Mettre à jour le compteur
            self.position_count = len(self.active_trades)
            
            if positions_to_remove:
                self.logger.info(f"🗑️ {len(positions_to_remove)} position(s) supprimée(s) de active_trades. Positions restantes: {len(self.active_trades)}")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur synchronisation positions: {e}")
    
    async def can_open_trade(self, pair: str) -> Tuple[bool, str]:
        """Vérifie si un nouveau trade peut être ouvert"""
        
        # SYNCHRONISATION D'ABORD avec Binance
        await self.sync_positions_with_binance()
        
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
            
            # Récupérer les informations du symbole pour l'arrondi
            symbol_info = await self.data_fetcher.get_symbol_info(pair)
            if not symbol_info:
                raise Exception(f"Impossible de récupérer les infos du symbole {pair}")
            
            # Calcul de la quantité
            quantity = position_size_usdc / current_price
            rounded_quantity = self.data_fetcher.round_quantity(symbol_info, quantity)
            
            # Calcul stop loss et take profit
            stop_loss_price = current_price * (1 - self.config.STOP_LOSS_PERCENT / 100)
            take_profit_price = current_price * (1 + self.config.TAKE_PROFIT_PERCENT / 100)
            
            # Arrondir les prix selon les règles Binance
            rounded_stop_loss = self.data_fetcher.round_price(symbol_info, stop_loss_price)
            rounded_take_profit = self.data_fetcher.round_price(symbol_info, take_profit_price)
            
            self.logger.info(f"💰 Prix calculés - Entry: {current_price:.8f}, SL: {rounded_stop_loss:.8f}, TP: {rounded_take_profit:.8f}")
            
            # Génération ID trade
            trade_id = f"{pair}_{int(time.time())}"
            
            # Création de l'objet trade
            trade = Trade(
                trade_id=trade_id,
                pair=pair,
                side="BUY",
                entry_price=current_price,
                quantity=rounded_quantity,
                capital_engaged=position_size_usdc,
                stop_loss=rounded_stop_loss,
                take_profit=rounded_take_profit,
                timestamp=datetime.now(),
                status=TradeStatus.PENDING,
                rsi_value=analysis_data.get('rsi_value', 0),
                signal_data=analysis_data
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
        """Met en place les ordres de sortie avec OCO (One-Cancels-Other)"""
        try:
            # Configuration OCO pour Take Profit + Trailing Stop
            
            # Récupérer les informations du symbole pour l'arrondi des prix
            symbol_info = await self.data_fetcher.get_symbol_info(trade.pair)
            if not symbol_info:
                raise Exception(f"Impossible de récupérer les infos du symbole {trade.pair}")
            
            # Arrondir les prix selon les règles Binance
            rounded_tp = self.data_fetcher.round_price(symbol_info, trade.take_profit)
            rounded_sl = self.data_fetcher.round_price(symbol_info, trade.stop_loss)
            rounded_qty = self.data_fetcher.round_quantity(symbol_info, trade.quantity)
            
            self.logger.info(f"📏 Prix arrondis - TP: {trade.take_profit:.8f} -> {rounded_tp:.8f}, SL: {trade.stop_loss:.8f} -> {rounded_sl:.8f}")
            
            # Configuration OCO : Take Profit + Trailing Stop en UN SEUL ordre
            self.logger.info(f"🔄 Configuration OCO : TP={rounded_tp:.6f} + Trailing Stop={self.config.TRAILING_STOP_DISTANCE}%")
            
            try:
                # Essayer l'ordre OCO avec trailing stop
                oco_order = await self.data_fetcher.place_oco_order(
                    symbol=trade.pair,
                    side="SELL",
                    quantity=rounded_qty,
                    
                    # Take Profit (ordre limite)
                    price=rounded_tp,
                    
                    # Stop Loss avec trailing
                    stopPrice=rounded_sl,
                    stopLimitPrice=rounded_sl * 0.995,  # Prix limite -0.5% du stop
                )
                
                # Enregistrer les IDs des ordres OCO
                if 'orderListId' in oco_order:
                    trade.oco_order_id = oco_order['orderListId']
                    orders = oco_order.get('orders', [])
                    if len(orders) >= 2:
                        trade.take_profit_order_id = orders[0].get('orderId')  # Premier ordre = TP
                        trade.trailing_stop_order_id = orders[1].get('orderId')  # Deuxième ordre = Stop
                        trade.trailing_stop_active = True
                        
                        self.logger.info(f"✅ OCO créé avec succès!")
                        self.logger.info(f"   📈 Take Profit: {rounded_tp:.6f} USDC (ID: {trade.take_profit_order_id})")
                        self.logger.info(f"   🛡️ Stop Loss: {rounded_sl:.6f} USDC (ID: {trade.trailing_stop_order_id})")
                        self.logger.info(f"   🔗 OCO Group: {trade.oco_order_id}")
                        return
                
            except Exception as oco_error:
                self.logger.warning(f"⚠️ OCO échoué: {oco_error}")
                # Fallback: ordres séparés
                await self._setup_fallback_orders(trade, rounded_tp, rounded_sl, rounded_qty)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur setup ordres de sortie: {e}")
            # Fallback: gestion manuelle si ordres automatiques échouent
            self.logger.warning("⚠️ Passage en gestion manuelle des SL/TP")
    
    async def _setup_fallback_orders(self, trade: Trade, rounded_tp: float, rounded_sl: float, rounded_qty: float):
        """Fallback : ordres séparés si OCO échoue"""
        try:
            self.logger.info("🔄 Fallback: création d'ordres séparés...")
            
            # 1. Ordre Take Profit (LIMIT)
            tp_order = await self.data_fetcher.place_order(
                symbol=trade.pair,
                side="SELL",
                order_type="LIMIT",
                quantity=rounded_qty,
                price=rounded_tp,
                timeInForce="GTC"
            )
            trade.take_profit_order_id = tp_order['orderId']
            self.logger.info(f"✅ TP automatique placé: {rounded_tp:.6f} USDC (ID: {tp_order['orderId']})")
            
            # 2. Ordre Stop Loss/Trailing Stop
            if self.config.TRAILING_STOP_ENABLED:
                try:
                    # Essayer TRAILING_STOP_MARKET
                    trailing_order = await self.data_fetcher.place_order(
                        symbol=trade.pair,
                        side="SELL",
                        order_type="TRAILING_STOP_MARKET",
                        quantity=rounded_qty,
                        callbackRate=self.config.TRAILING_STOP_DISTANCE
                    )
                    trade.trailing_stop_order_id = trailing_order['orderId']
                    trade.trailing_stop_active = True
                    self.logger.info(f"✅ Trailing Stop placé: {self.config.TRAILING_STOP_DISTANCE}% (ID: {trailing_order['orderId']})")
                    
                except Exception as trailing_error:
                    self.logger.warning(f"⚠️ TRAILING_STOP_MARKET échoué: {trailing_error}")
                    # Fallback final: STOP_LOSS_LIMIT
                    sl_order = await self.data_fetcher.place_order(
                        symbol=trade.pair,
                        side="SELL",
                        order_type="STOP_LOSS_LIMIT",
                        quantity=rounded_qty,
                        price=rounded_sl * 0.995,
                        stopPrice=rounded_sl,
                        timeInForce="GTC"
                    )
                    trade.stop_loss_order_id = sl_order['orderId']
                    self.logger.info(f"✅ Stop Loss Limit placé: {rounded_sl:.6f} USDC (ID: {sl_order['orderId']})")
            else:
                # Stop Loss fixe seulement
                sl_order = await self.data_fetcher.place_order(
                    symbol=trade.pair,
                    side="SELL",
                    order_type="STOP_LOSS_LIMIT",
                    quantity=rounded_qty,
                    price=rounded_sl * 0.995,
                    stopPrice=rounded_sl,
                    timeInForce="GTC"
                )
                trade.stop_loss_order_id = sl_order['orderId']
                self.logger.info(f"✅ Stop Loss fixe placé: {rounded_sl:.6f} USDC (ID: {sl_order['orderId']})")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur fallback orders: {e}")
            self.logger.warning("⚠️ Pas d'ordres automatiques - surveillance manuelle requise")
    
    async def monitor_positions(self):
        """Surveille les positions ouvertes (OCO gère automatiquement les sorties)"""
        for trade_id, trade in list(self.active_trades.items()):
            try:
                # Avec OCO, la sortie est automatique, on vérifie juste le statut
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
            
            # 5. Trailing Stop (si activé)
            if self.risk_config.TRAILING_STOP_ENABLED:
                await self._update_trailing_stop(trade, current_price, current_pnl_percent)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification conditions sortie {trade.pair}: {e}")
    
    async def _update_trailing_stop(self, trade: Trade, current_price: float, current_pnl_percent: float):
        """Met à jour le trailing stop"""
        try:
            # Démarrage du trailing stop si profit >= seuil
            if current_pnl_percent >= self.risk_config.TRAILING_START_PERCENT:
                
                # Calcul du nouveau stop loss
                trailing_distance = self.risk_config.TRAILING_STEP_PERCENT / 100
                new_stop_loss = current_price * (1 - trailing_distance)
                
                # Mise à jour seulement si le nouveau SL est plus élevé
                if new_stop_loss > trade.stop_loss:
                    old_stop_loss = trade.stop_loss
                    trade.stop_loss = new_stop_loss
                    
                    self.logger.info(f"🔄 Trailing stop mis à jour {trade.pair}: {old_stop_loss:.6f} -> {new_stop_loss:.6f}")
                    
                    # Notification Telegram
                    if self.telegram_notifier:
                        await self.telegram_notifier.send_position_update({
                            'pair': trade.pair,
                            'current_pnl': current_pnl_percent,
                            'trailing_stop': new_stop_loss
                        })
                        
        except Exception as e:
            self.logger.error(f"❌ Erreur trailing stop {trade.pair}: {e}")
    
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
    
    async def cancel_open_orders_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """Annule tous les ordres ouverts pour un symbole et retourne les infos"""
        try:
            self.logger.info(f"🗑️ Annulation des ordres ouverts pour {symbol}")
            
            # Récupérer les ordres ouverts
            open_orders = await self.data_fetcher.get_open_orders(symbol)
            
            if not open_orders:
                self.logger.info(f"📋 Aucun ordre ouvert pour {symbol}")
                return {
                    'success': True,
                    'cancelled_count': 0,
                    'orders_before': [],
                    'errors': []
                }
            
            self.logger.info(f"📋 {len(open_orders)} ordres trouvés pour {symbol}")
            for order in open_orders:
                self.logger.info(f"  • Ordre {order['orderId']}: {order['type']} {order['side']} {order['origQty']} @ {order['price']}")
            
            # Annuler tous les ordres
            result = await self.data_fetcher.cancel_all_orders(symbol)
            
            success = len(result['errors']) == 0
            cancelled_count = result['count']
            
            if success and cancelled_count > 0:
                self.logger.info(f"✅ {cancelled_count} ordres annulés avec succès pour {symbol}")
                # Attendre un peu pour que Binance libère la balance
                await asyncio.sleep(2)
            elif result['errors']:
                self.logger.error(f"❌ Erreurs lors de l'annulation pour {symbol}: {result['errors']}")
            
            return {
                'success': success,
                'cancelled_count': cancelled_count,
                'orders_before': open_orders,
                'cancelled_orders': result['cancelled'],
                'errors': result['errors']
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur annulation ordres {symbol}: {e}")
            return {
                'success': False,
                'cancelled_count': 0,
                'orders_before': [],
                'errors': [str(e)]
            }
    
    async def execute_sell_order(self, pair: str, quantity: float) -> Dict[str, Any]:
        """Exécute un ordre de vente pour fermer une position"""
        try:
            # Chercher le trade correspondant
            trade = self.active_trades.get(pair)
            
            # Si pas de trade dans active_trades, créer un trade temporaire pour la fermeture
            if not trade:
                self.logger.warning(f"⚠️ Trade {pair} pas trouvé dans active_trades, fermeture directe via Binance")
                
                # ÉTAPE 1: Vérifier et annuler les ordres ouverts qui peuvent locker la balance
                cancel_result = await self.cancel_open_orders_for_symbol(pair)
                if cancel_result['cancelled_count'] > 0:
                    self.logger.info(f"🗑️ {cancel_result['cancelled_count']} ordres annulés pour libérer la balance")
                
                # ÉTAPE 2: Récupérer le prix actuel
                ticker = await self.data_fetcher.get_ticker_price(pair)
                current_price = float(ticker['price'])
                
                # ÉTAPE 3: Vérifier le balance APRÈS annulation des ordres
                try:
                    base_asset = pair.replace('USDC', '').replace('USDT', '').replace('BTC', '')
                    if 'USDC' in pair:
                        base_asset = pair.replace('USDC', '')
                    elif 'USDT' in pair:
                        base_asset = pair.replace('USDT', '')
                    
                    account_info = self.data_fetcher.binance_client.get_account()
                    balances = {b['asset']: {'free': float(b['free']), 'locked': float(b['locked'])} for b in account_info['balances']}
                    balance_info = balances.get(base_asset, {'free': 0, 'locked': 0})
                    available_balance = balance_info['free']
                    locked_balance = balance_info['locked']
                    
                    self.logger.info(f"💰 Balance {base_asset}: {available_balance} libre, {locked_balance} lockée")
                    self.logger.info(f"📊 Tentative vente quantité: {quantity}")
                    
                    # Si la balance est encore insuffisante et qu'il y a du locked, attendre un peu plus
                    if available_balance < quantity and locked_balance > 0:
                        self.logger.info(f"⏳ Balance encore lockée, attente supplémentaire...")
                        await asyncio.sleep(3)
                        
                        # Re-vérifier la balance
                        account_info = self.data_fetcher.binance_client.get_account()
                        balances = {b['asset']: {'free': float(b['free']), 'locked': float(b['locked'])} for b in account_info['balances']}
                        balance_info = balances.get(base_asset, {'free': 0, 'locked': 0})
                        available_balance = balance_info['free']
                        locked_balance = balance_info['locked']
                        self.logger.info(f"💰 Balance après attente {base_asset}: {available_balance} libre, {locked_balance} lockée")
                    
                    if available_balance < quantity:
                        self.logger.warning(f"⚠️ Balance insuffisant! Disponible: {available_balance}, Requis: {quantity}")
                        if available_balance > 0:
                            # Utiliser tout le balance disponible moins une petite marge pour les frais
                            safe_balance = available_balance * 0.999  # 0.1% de marge pour les frais
                            quantity = safe_balance
                            self.logger.info(f"🔄 Ajustement quantité à la balance disponible: {quantity}")
                        else:
                            self.logger.error(f"❌ Aucun balance disponible pour {base_asset}")
                            return {
                                'success': False,
                                'error': f'Aucun balance disponible: {available_balance} (locked: {locked_balance})',
                                'price': 0
                            }
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Erreur vérification balance: {e}")
                
                # ÉTAPE 4: Arrondir selon les règles Binance
                symbol_info = await self.data_fetcher.get_symbol_info(pair)
                if symbol_info:
                    rounded_quantity = self.data_fetcher.round_quantity(symbol_info, quantity)
                else:
                    rounded_quantity = quantity
                
                # ÉTAPE 5: Vérification de la valeur minimum (dust threshold)
                trade_value_usdc = rounded_quantity * current_price
                if trade_value_usdc < self.config.DUST_THRESHOLD_USDC:
                    self.logger.warning(f"💸 Montant trop petit (dust): {trade_value_usdc:.4f} USDC < {self.config.DUST_THRESHOLD_USDC} USDC")
                    self.logger.info(f"�️ Ignorer la vente de {rounded_quantity} {base_asset} (valeur: {trade_value_usdc:.4f} USDC)")
                    return {
                        'success': True,  # Considérer comme succès pour éviter les erreurs répétées
                        'price': current_price,
                        'quantity': 0,  # Quantité 0 pour indiquer qu'aucune vente n'a eu lieu
                        'pair': pair,
                        'reason': 'dust_threshold'
                    }
                
                self.logger.info(f"�🔄 Tentative ordre SELL {pair}: quantité {rounded_quantity} (valeur: {trade_value_usdc:.4f} USDC)")
                
                # Exécuter directement l'ordre de vente sur Binance
                order = await self.data_fetcher.place_order(
                    symbol=pair,
                    side="SELL",
                    order_type="MARKET",
                    quantity=rounded_quantity
                )
                
                self.logger.info(f"✅ Ordre de vente direct exécuté pour {pair}: {order}")
                
                return {
                    'success': True,
                    'price': current_price,
                    'quantity': rounded_quantity,
                    'pair': pair,
                    'order_id': order.get('orderId')
                }
            
            # Si le trade existe dans active_trades, utiliser la méthode normale
            ticker = await self.data_fetcher.get_ticker_price(pair)
            current_price = float(ticker['price'])
            
            # Fermer le trade
            await self._close_trade(trade, current_price, ExitReason.MANUAL)
            
            return {
                'success': True,
                'price': current_price,
                'quantity': quantity,
                'pair': pair
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur execution ordre vente {pair}: {e}")
            return {
                'success': False,
                'error': str(e),
                'price': 0
            }
    
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
                    analysis_data=trade.signal_data or {}
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
                await self.firebase_logger.log_error(
                    error_type=component,
                    error_message=message,
                    context=details
                )
            
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
