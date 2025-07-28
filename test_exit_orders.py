#!/usr/bin/env python3
"""
🧪 TEST ORDRES SL/TP - Validation du système d'ordres automatiques
Place des ordres Take Profit et Stop Loss sur les positions actuelles
"""

import asyncio
import logging
import sys
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple

# Chargement des variables d'environnement
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv non installé, utilisation variables système")

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Ajout du répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import TradingConfig, APIConfig, RiskManagementConfig
from data_fetcher import DataFetcher
from trade_executor import TradeExecutor
from indicators import TechnicalIndicators


class ExitOrderTester:
    """Testeur d'ordres de sortie pour positions existantes"""
    
    def __init__(self):
        self.config = TradingConfig()
        self.api_config = APIConfig()
        self.risk_config = RiskManagementConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialisation du data fetcher
        self.data_fetcher = DataFetcher(
            api_key=self.api_config.BINANCE_API_KEY,
            secret_key=self.api_config.BINANCE_SECRET_KEY,
            testnet=self.api_config.BINANCE_TESTNET
        )
        
        # Initialisation du trade executor pour utiliser ses méthodes de formatage
        # Nous n'avons besoin que des méthodes de formatage, pas des autres services
        self.trade_executor = TradeExecutor(
            data_fetcher=self.data_fetcher,
            config=self.config,
            risk_config=self.risk_config,
            firebase_logger=None,
            telegram_notifier=None
        )
        
        # Initialisation des indicateurs techniques
        self.indicators = TechnicalIndicators(config=self.config)
        
        self.logger.info("🧪 Test Exit Orders initialisé")
    
    async def cancel_existing_orders(self, symbol: str):
        """Annule tous les ordres existants pour un symbole pour libérer le solde"""
        try:
            # Récupération de tous les ordres via l'historique récent
            import time
            current_time = int(time.time() * 1000)
            start_time = current_time - (24 * 60 * 60 * 1000)  # 24h en arrière
            
            # Utilisation de la méthode get_orders du data_fetcher
            orders = await self.data_fetcher.get_orders(symbol, start_time)
            
            open_orders = [o for o in orders if o['status'] in ['NEW', 'PARTIALLY_FILLED']]
            
            if open_orders:
                self.logger.info(f"🗑️ Annulation de {len(open_orders)} ordre(s) existant(s) pour {symbol}")
                for order in open_orders:
                    try:
                        result = await self.data_fetcher.cancel_order(symbol, str(order['orderId']))
                        self.logger.info(f"✅ Ordre {order['orderId']} annulé ({order['type']} {order['side']})")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Erreur annulation ordre {order['orderId']}: {e}")
            else:
                self.logger.info(f"✅ Aucun ordre ouvert trouvé pour {symbol}")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur recherche ordres existants {symbol}: {e}")

    async def get_current_positions(self) -> List[Dict]:
        """Récupère les positions actuelles avec solde > 0"""
        try:
            balances = await self.data_fetcher.get_account_balance()
            positions = []
            
            for asset, balance_info in balances.items():
                free_balance = float(balance_info['free'])
                locked_balance = float(balance_info['locked'])
                total_balance = free_balance + locked_balance
                
                # Ignorer USDC et les petits soldes
                if (asset != 'USDC' and 
                    total_balance > 0.001 and  # Seuil minimum
                    free_balance > 0):  # Doit avoir du solde libre pour vendre
                    
                    # Construire le symbole de trading
                    symbol = f"{asset}USDC"
                    
                    # Vérifier que la paire existe
                    try:
                        ticker = await self.data_fetcher.get_ticker_price(symbol)
                        current_price = float(ticker['price'])
                        
                        positions.append({
                            'asset': asset,
                            'symbol': symbol,
                            'quantity': free_balance,
                            'current_price': current_price,
                            'value_usdc': free_balance * current_price
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️ Paire {symbol} non trouvée: {e}")
            
            return positions
        
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération positions: {e}")
            return []
    
    async def format_quantity(self, symbol: str, quantity: float) -> float:
        """Utilise la méthode de formatage du TradeExecutor"""
        return await self.trade_executor._format_quantity(symbol, quantity)
    
    async def format_price(self, symbol: str, price: float) -> float:
        """Utilise la méthode de formatage du TradeExecutor"""
        return await self.trade_executor._format_price(symbol, price)
    
    async def get_rsi_distribution_strategy(self, symbol: str) -> Tuple[float, float, str]:
        """
        Calcule le RSI et retourne la stratégie de répartition optimale
        Returns: (sl_percentage, tp_percentage, strategy_name)
        """
        try:
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
    
    async def place_exit_orders_for_position(self, position: Dict) -> Dict:
        """Place les ordres SL/TP pour une position - VERSION AMÉLIORÉE pour fiabilité maximale"""
        symbol = position['symbol']
        current_price = position['current_price']
        quantity = position['quantity']
        
        # 🔍 Vérification du solde réel disponible - RAFRAÎCHI AVANT CHAQUE ORDRE
        try:
            balances = await self.data_fetcher.get_account_balance()
            asset = position['asset']
            available_balance = float(balances[asset]['free'])
            
            # Utiliser 99% du solde disponible pour éviter les erreurs de précision
            safe_quantity = min(quantity, available_balance * 0.99)
            
            if safe_quantity < quantity:
                self.logger.warning(f"⚠️ Ajustement quantité {symbol}: {quantity:.6f} → {safe_quantity:.6f} (99% du solde libre)")
            
            quantity = safe_quantity
            
            # Vérification minimum - si trop petit, skip
            if quantity < 0.000001:
                self.logger.warning(f"⚠️ Quantité {symbol} trop petite: {quantity:.8f} - Position ignorée")
                return {
                    'symbol': symbol,
                    'tp_order_placed': False,
                    'sl_order_placed': False,
                    'tp_order_id': None,
                    'sl_order_id': None,
                    'errors': ['Quantité trop petite']
                }
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur vérification solde pour {symbol}: {e}")
        
        # 🚀 NOUVELLE STRATÉGIE ADAPTATIVE RSI : Répartition intelligente basée sur les conditions de marché
        # Calcul de la stratégie optimale selon le RSI
        sl_percentage, tp_percentage, strategy_name = await self.get_rsi_distribution_strategy(symbol)
        
        # Calcul des quantités optimales pour garantir SL avec valeur NOTIONAL suffisante
        
        # Calcul du prix SL pour estimer la valeur NOTIONAL
        stop_loss_price_estimate = current_price * (1 - self.config.STOP_LOSS_PERCENT / 100)
        
        # Quantité minimale pour SL (5 USDC / prix SL + marge)
        min_sl_quantity_for_notional = (6.0 / stop_loss_price_estimate) * 1.1  # +10% de marge
        
        # Formatage de la quantité totale - AVEC VÉRIFICATION SUPPLÉMENTAIRE
        try:
            formatted_quantity = await self.format_quantity(symbol, quantity)
            
            # Double vérification - si formatage donne 0, on essaie une approche différente
            if formatted_quantity <= 0:
                # Récupération manuelle des règles de formatage
                symbol_info = await self.data_fetcher.get_symbol_info(symbol)
                if symbol_info and 'filters' in symbol_info:
                    lot_size_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
                    if lot_size_filter:
                        step_size = float(lot_size_filter['stepSize'])
                        # Arrondir à la step_size inférieure
                        formatted_quantity = (quantity // step_size) * step_size
                        self.logger.info(f"🔧 Formatage manuel quantité {symbol}: {quantity:.8f} → {formatted_quantity:.8f}")
                
            if formatted_quantity <= 0:
                self.logger.warning(f"⚠️ Formatage quantité {symbol} impossible: {quantity:.8f} → {formatted_quantity:.8f}")
                return {
                    'symbol': symbol,
                    'tp_order_placed': False,
                    'sl_order_placed': False,
                    'tp_order_id': None,
                    'sl_order_id': None,
                    'errors': ['Formatage quantité impossible']
                }
            
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
                reserved_sl_quantity = await self.format_quantity(symbol, sl_target_quantity)
                tp_quantity = await self.format_quantity(symbol, tp_target_quantity)
                
                # Vérifier que les quantités formatées sont valides
                if reserved_sl_quantity > 0 and tp_quantity > 0:
                    # Vérifier que la valeur NOTIONAL SL est suffisante
                    estimated_notional = reserved_sl_quantity * stop_loss_price_estimate
                    if estimated_notional >= 5.0:
                        self.logger.info(f"🧠 Stratégie RSI {strategy_name} pour {symbol}:")
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
                        self.logger.info(f"⚠️ Quantité SL RSI {symbol} trop petite ({estimated_notional:.2f} USDC < 5 USDC) - Mode standard")
                else:
                    # Formatage échoué, mode standard
                    tp_order_quantity = formatted_quantity
                    sl_reserved_quantity = None
                    self.logger.info(f"⚠️ Formatage quantités RSI {symbol} impossible - Mode standard")
            else:
                # Si quantité insuffisante pour diviser selon RSI, utiliser toute la quantité pour TP
                tp_order_quantity = formatted_quantity
                sl_reserved_quantity = None
                self.logger.info(f"⚠️ Quantité {symbol} insuffisante pour répartition RSI - Mode standard")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur formatage quantité {symbol}: {e}")
            return {
                'symbol': symbol,
                'tp_order_placed': False,
                'sl_order_placed': False,
                'tp_order_id': None,
                'sl_order_id': None,
                'errors': [f'Erreur formatage: {e}']
            }
        
        # Calcul des prix SL/TP - MÊME LOGIQUE que TradeExecutor
        take_profit_price = current_price * (1 + self.config.TAKE_PROFIT_PERCENT / 100)
        stop_loss_price = current_price * (1 - self.config.STOP_LOSS_PERCENT / 100)
        
        # Formatage des prix - MÊME MÉTHODE que TradeExecutor
        take_profit_price = await self.format_price(symbol, take_profit_price)
        stop_loss_price = await self.format_price(symbol, stop_loss_price)
        
        self.logger.info(f"\n📊 Position {symbol} - Stratégie: {strategy_name}")
        self.logger.info(f"   💰 Prix actuel: {current_price:.6f} USDC")
        self.logger.info(f"   📏 Quantité totale: {quantity:.6f}")
        if sl_reserved_quantity:
            self.logger.info(f"   🎯 TP ({tp_percentage:.0f}%): {tp_order_quantity:.6f}")
            self.logger.info(f"   🛡️ SL ({sl_percentage:.0f}%): {sl_reserved_quantity:.6f}")
        else:
            self.logger.info(f"   📏 Quantité formatée: {tp_order_quantity:.6f}")
        self.logger.info(f"   🎯 Take Profit: {take_profit_price:.6f} USDC (+{self.config.TAKE_PROFIT_PERCENT}%)")
        self.logger.info(f"   🛡️ Stop Loss: {stop_loss_price:.6f} USDC (-{self.config.STOP_LOSS_PERCENT}%)")
        
        result = {
            'symbol': symbol,
            'tp_order_placed': False,
            'sl_order_placed': False,
            'tp_order_id': None,
            'sl_order_id': None,
            'errors': []
        }
        
        # 🔥 RÉPLICATION EXACTE DE _setup_exit_orders
        try:
            # Vérification des types d'ordres supportés - MÊME CODE
            symbol_info = await self.data_fetcher.get_symbol_info(symbol)
            supported_order_types = symbol_info.get('orderTypes', []) if symbol_info else []
            
            self.logger.info(f"📋 Types d'ordres supportés pour {symbol}: {supported_order_types}")
            
            # 1. Ordre Take Profit - STRATÉGIE ROBUSTE AVEC RETRY
            tp_order_placed = False
            
            # Rafraîchir le solde avant chaque ordre pour éviter les conflicts
            try:
                fresh_balances = await self.data_fetcher.get_account_balance()
                fresh_available = float(fresh_balances[position['asset']]['free'])
                if fresh_available < tp_order_quantity:
                    # Re-calculer avec le solde le plus récent
                    tp_order_quantity = await self.format_quantity(symbol, fresh_available * 0.99)
                    self.logger.info(f"🔄 Quantité TP re-ajustée {symbol}: → {tp_order_quantity:.8f} (solde frais)")
            except Exception as e:
                self.logger.warning(f"⚠️ Erreur rafraîchissement solde: {e}")
            
            # Essai TAKE_PROFIT_LIMIT d'abord (recommandé pour Spot)
            if 'TAKE_PROFIT_LIMIT' in supported_order_types and tp_order_quantity > 0:
                try:
                    tp_order = await self.data_fetcher.place_order(
                        symbol=symbol,
                        side="SELL",
                        order_type="TAKE_PROFIT_LIMIT",
                        quantity=tp_order_quantity,
                        price=take_profit_price,
                        stopPrice=take_profit_price,
                        timeInForce="GTC"
                    )
                    result['tp_order_id'] = tp_order['orderId']
                    self.logger.info(f"✅ TP automatique (TAKE_PROFIT_LIMIT) placé: {take_profit_price:.6f} USDC (ID: {tp_order['orderId']})")
                    tp_order_placed = True
                except Exception as e:
                    error_msg = f"TAKE_PROFIT_LIMIT: {e}"
                    result['errors'].append(error_msg)
                    self.logger.error(f"❌ Erreur {error_msg}")
            
            # Fallback: TAKE_PROFIT (SANS timeInForce - pas supporté)
            if not tp_order_placed and 'TAKE_PROFIT' in supported_order_types and tp_order_quantity > 0:
                try:
                    tp_order = await self.data_fetcher.place_order(
                        symbol=symbol,
                        side="SELL",
                        order_type="TAKE_PROFIT",
                        quantity=tp_order_quantity,
                        stopPrice=take_profit_price
                        # timeInForce pas supporté pour TAKE_PROFIT
                    )
                    result['tp_order_id'] = tp_order['orderId']
                    self.logger.info(f"✅ TP automatique (TAKE_PROFIT) placé: {take_profit_price:.6f} USDC (ID: {tp_order['orderId']})")
                    tp_order_placed = True
                except Exception as e:
                    error_msg = f"TAKE_PROFIT: {e}"
                    result['errors'].append(error_msg)
                    self.logger.error(f"❌ Erreur {error_msg}")
            
            # Fallback final: LIMIT classique
            if not tp_order_placed and 'LIMIT' in supported_order_types and tp_order_quantity > 0:
                try:
                    tp_order = await self.data_fetcher.place_order(
                        symbol=symbol,
                        side="SELL",
                        order_type="LIMIT",
                        quantity=tp_order_quantity,
                        price=take_profit_price,
                        timeInForce="GTC"
                    )
                    result['tp_order_id'] = tp_order['orderId']
                    self.logger.info(f"✅ TP automatique (LIMIT) placé: {take_profit_price:.6f} USDC (ID: {tp_order['orderId']})")
                    tp_order_placed = True
                except Exception as e:
                    error_msg = f"LIMIT TP: {e}"
                    result['errors'].append(error_msg)
                    self.logger.error(f"❌ Erreur ordre TP LIMIT: {e}")
            
            if not tp_order_placed:
                self.logger.warning(f"⚠️ Impossible de placer TP automatique pour {symbol}")
            
            result['tp_order_placed'] = tp_order_placed
            
            # 2. Ordre Stop Loss avec Trailing Stop - STRATÉGIE SUPER ROBUSTE
            sl_order_placed = False
            
            # Conversion du pourcentage en BIPS pour trailing stop (ex: 0.3% -> 30 BIPS)
            trailing_delta_bips = int(self.config.TRAILING_STOP_DISTANCE * 100) if self.config.TRAILING_STOP_ENABLED else None
            
            # 🎯 NOUVELLE LOGIQUE: Utiliser la quantité réservée si disponible
            sl_quantity_to_use = sl_reserved_quantity
            
            # Si pas de réservation, utiliser l'ancienne méthode (solde restant)
            if sl_reserved_quantity is None:
                # Rafraîchir le solde pour le SL (après TP)
                if tp_order_placed:
                    try:
                        # Attendre un peu pour que l'ordre TP soit pris en compte
                        import asyncio
                        await asyncio.sleep(0.5)
                        
                        fresh_balances = await self.data_fetcher.get_account_balance()
                        fresh_available = float(fresh_balances[position['asset']]['free'])
                        
                        # Pour le SL, utiliser le minimum entre la quantité originale et ce qui reste
                        # Mais éviter les quantités trop petites qui causent des erreurs
                        if fresh_available < tp_order_quantity:
                            sl_quantity_to_use = await self.format_quantity(symbol, fresh_available * 0.95)
                            
                            # Vérifier que la nouvelle quantité est suffisante
                            if sl_quantity_to_use > 0:
                                # Vérifier la valeur NOTIONAL minimale (environ 5 USDC pour la plupart des paires)
                                notional_value = sl_quantity_to_use * stop_loss_price
                                if notional_value < 5.0:
                                    self.logger.warning(f"⚠️ Valeur SL trop petite {symbol}: {notional_value:.2f} USDC < 5 USDC - Skip SL")
                                    sl_quantity_to_use = 0  # Force skip du SL
                                else:
                                    self.logger.info(f"🔄 Quantité SL re-ajustée {symbol}: → {sl_quantity_to_use:.8f}")
                            else:
                                self.logger.warning(f"⚠️ Solde restant {symbol} insuffisant pour SL - Skip")
                                sl_quantity_to_use = 0
                        else:
                            # Assez de solde restant, utiliser la quantité TP
                            sl_quantity_to_use = tp_order_quantity
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️ Erreur rafraîchissement pour SL: {e}")
                        sl_quantity_to_use = 0
                else:
                    # Pas de TP placé, utiliser la quantité originale
                    sl_quantity_to_use = tp_order_quantity
            else:
                self.logger.info(f"🎯 Utilisation quantité SL réservée: {sl_quantity_to_use:.8f}")
                # Vérifier NOTIONAL pour la quantité réservée
                notional_value = sl_quantity_to_use * stop_loss_price
                if notional_value < 5.0:
                    self.logger.warning(f"⚠️ Valeur SL réservée trop petite {symbol}: {notional_value:.2f} USDC < 5 USDC")
                    sl_quantity_to_use = 0
            
            # Essai STOP_LOSS_LIMIT avec trailing stop d'abord (recommandé pour Spot)
            if 'STOP_LOSS_LIMIT' in supported_order_types and sl_quantity_to_use > 0:
                try:
                    order_params = {
                        'symbol': symbol,
                        'side': "SELL",
                        'order_type': "STOP_LOSS_LIMIT",
                        'quantity': sl_quantity_to_use,
                        'price': stop_loss_price,
                        'timeInForce': 'GTC'
                    }
                    
                    # Ajout du trailing stop si activé
                    if self.config.TRAILING_STOP_ENABLED and trailing_delta_bips:
                        order_params['trailingDelta'] = trailing_delta_bips
                        # Pour un trailing stop, stopPrice est optionnel - omis pour démarrage immédiat
                        self.logger.info(f"📈 Trailing Stop activé: {self.config.TRAILING_STOP_DISTANCE}% ({trailing_delta_bips} BIPS)")
                    else:
                        order_params['stopPrice'] = stop_loss_price
                    
                    sl_order = await self.data_fetcher.place_order(**order_params)
                    result['sl_order_id'] = sl_order['orderId']
                    
                    if self.config.TRAILING_STOP_ENABLED and trailing_delta_bips:
                        self.logger.info(f"✅ SL automatique avec Trailing Stop (STOP_LOSS_LIMIT) placé: {self.config.TRAILING_STOP_DISTANCE}% trailing (ID: {sl_order['orderId']})")
                    else:
                        self.logger.info(f"✅ SL automatique (STOP_LOSS_LIMIT) placé: {stop_loss_price:.6f} USDC (ID: {sl_order['orderId']})")
                    
                    sl_order_placed = True
                except Exception as e:
                    error_msg = f"STOP_LOSS_LIMIT: {e}"
                    result['errors'].append(error_msg)
                    self.logger.error(f"❌ Erreur {error_msg}")
            
            # Fallback: Essai STOP_LOSS si STOP_LOSS_LIMIT échoue (SANS timeInForce)
            if not sl_order_placed and 'STOP_LOSS' in supported_order_types and sl_quantity_to_use > 0:
                try:
                    order_params = {
                        'symbol': symbol,
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
                        order_params['stopPrice'] = stop_loss_price
                    
                    sl_order = await self.data_fetcher.place_order(**order_params)
                    result['sl_order_id'] = sl_order['orderId']
                    
                    if self.config.TRAILING_STOP_ENABLED and trailing_delta_bips:
                        self.logger.info(f"✅ SL automatique avec Trailing Stop (STOP_LOSS) placé: {self.config.TRAILING_STOP_DISTANCE}% trailing (ID: {sl_order['orderId']})")
                    else:
                        self.logger.info(f"✅ SL automatique (STOP_LOSS) placé: {stop_loss_price:.6f} USDC (ID: {sl_order['orderId']})")
                    
                    sl_order_placed = True
                except Exception as e:
                    error_msg = f"STOP_LOSS: {e}"
                    result['errors'].append(error_msg)
                    self.logger.error(f"❌ Erreur {error_msg}")
            
            if not sl_order_placed:
                self.logger.warning(f"⚠️ Impossible de placer SL automatique pour {symbol} - Gestion manuelle activée")
            
            result['sl_order_placed'] = sl_order_placed
            
            # 3. Logging des résultats - MÊME LOGIQUE
            if tp_order_placed and sl_order_placed:
                self.logger.info(f"📊 Ordres automatiques TP et SL configurés pour {symbol}")
            elif tp_order_placed:
                self.logger.info(f"📊 Ordre TP automatique configuré pour {symbol} - SL en gestion manuelle")
            elif sl_order_placed:
                self.logger.info(f"📊 Ordre SL automatique configuré pour {symbol} - TP en gestion manuelle")
            else:
                self.logger.warning(f"⚠️ Aucun ordre automatique pour {symbol} - Surveillance manuelle requise")
            
        except Exception as e:
            error_msg = f"Erreur setup ordres automatiques {symbol}: {e}"
            result['errors'].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
            self.logger.warning("⚠️ Passage en gestion manuelle des SL/TP")
        
        return result
    
    async def run_test(self, dry_run: bool = True):
        """Lance le test des ordres SL/TP"""
        try:
            self.logger.info("🚀 Démarrage du test d'ordres SL/TP")
            self.logger.info(f"🧪 Mode: {'DRY RUN (simulation)' if dry_run else 'RÉEL (ordres placés)'}")
            
            # Test de connexion
            await self.data_fetcher.test_connection()
            self.logger.info("✅ Connexion Binance OK")
            
            # Récupération des positions
            positions = await self.get_current_positions()
            
            if not positions:
                self.logger.warning("⚠️ Aucune position trouvée avec solde suffisant")
                return
            
            self.logger.info(f"📊 {len(positions)} position(s) trouvée(s):")
            for pos in positions:
                self.logger.info(f"   💰 {pos['symbol']}: {pos['quantity']:.6f} ({pos['value_usdc']:.2f} USDC)")
            
            # Annulation des ordres existants pour libérer les soldes
            if not dry_run:
                self.logger.info("\n🗑️ Annulation des ordres existants...")
                for pos in positions:
                    await self.cancel_existing_orders(pos['symbol'])
            
            if dry_run:
                self.logger.info("\n🔍 MODE SIMULATION - Aucun ordre ne sera réellement placé")
                self.logger.info("Pour placer les ordres réellement, utilisez: --real")
                return
            
            # Demande de confirmation
            self.logger.info(f"\n⚠️ ATTENTION: Vous allez placer des ordres RÉELS sur {len(positions)} position(s)")
            self.logger.info("📋 Configuration:")
            self.logger.info(f"   🎯 Take Profit: +{self.config.TAKE_PROFIT_PERCENT}%")
            self.logger.info(f"   🛡️ Stop Loss: -{self.config.STOP_LOSS_PERCENT}%")
            if self.config.TRAILING_STOP_ENABLED:
                self.logger.info(f"   📈 Trailing Stop: {self.config.TRAILING_STOP_DISTANCE}% (30 BIPS)")
            
            response = input("\n🤔 Confirmez-vous le placement de ces ordres ? (oui/non): ")
            if response.lower() not in ['oui', 'yes', 'y', 'o']:
                self.logger.info("❌ Test annulé par l'utilisateur")
                return
            
            # Placement des ordres
            results = []
            for position in positions:
                self.logger.info(f"\n{'='*60}")
                result = await self.place_exit_orders_for_position(position)
                results.append(result)
            
            # Résumé
            self.logger.info(f"\n{'='*60}")
            self.logger.info("📊 RÉSUMÉ DU TEST:")
            
            total_positions = len(results)
            successful_tp = sum(1 for r in results if r['tp_order_placed'])
            successful_sl = sum(1 for r in results if r['sl_order_placed'])
            
            self.logger.info(f"   📈 Positions testées: {total_positions}")
            self.logger.info(f"   🎯 Take Profit placés: {successful_tp}/{total_positions}")
            self.logger.info(f"   🛡️ Stop Loss placés: {successful_sl}/{total_positions}")
            
            # Détails des erreurs
            for result in results:
                if result['errors']:
                    self.logger.info(f"\n❌ Erreurs {result['symbol']}:")
                    for error in result['errors']:
                        self.logger.info(f"   • {error}")
            
            if successful_tp == total_positions and successful_sl == total_positions:
                self.logger.info("✅ TOUS LES ORDRES ONT ÉTÉ PLACÉS AVEC SUCCÈS!")
            else:
                self.logger.info("⚠️ Certains ordres ont échoué - vérifiez les logs ci-dessus")
        
        except Exception as e:
            self.logger.error(f"❌ Erreur durant le test: {e}")
        
        finally:
            await self.data_fetcher.close()


async def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test des ordres SL/TP sur positions existantes')
    parser.add_argument('--real', action='store_true', help='Placer les ordres réellement (sinon simulation)')
    args = parser.parse_args()
    
    tester = ExitOrderTester()
    await tester.run_test(dry_run=not args.real)


if __name__ == "__main__":
    asyncio.run(main())
