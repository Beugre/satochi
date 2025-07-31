#!/usr/bin/env python3
"""
📊 DATA FETCHER - Récupération des données de marché Binance
Gestion des API calls, cache et optimisations
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException
    import ccxt.async_support as ccxt
except ImportError:
    print("⚠️ Modules Binance manquants. Installez avec: pip install python-binance ccxt")
    Client = None
    ccxt = None


class DataFetcher:
    """Gestionnaire de récupération des données de marché"""
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        self.logger = logging.getLogger(__name__)
        
        # Cache pour optimiser les requêtes
        self.cache = {}
        self.cache_ttl = {}
        
        # Initialisation des clients
        self.binance_client = None
        self.ccxt_client = None
        
        if Client and api_key and secret_key:
            try:
                self.binance_client = Client(
                    api_key=api_key,
                    api_secret=secret_key,
                    testnet=testnet
                )
                self.logger.info(f"📊 Client Binance initialisé (Testnet: {testnet})")
            except Exception as e:
                self.logger.error(f"❌ Erreur initialisation Binance: {e}")
        
        if ccxt:
            try:
                self.ccxt_client = ccxt.binance({
                    'apiKey': api_key,
                    'secret': secret_key,
                    'sandbox': testnet,
                    'enableRateLimit': True,
                })
                self.logger.info("📊 Client CCXT initialisé")
            except Exception as e:
                self.logger.error(f"❌ Erreur initialisation CCXT: {e}")
    
    async def test_connection(self) -> bool:
        """Test la connexion à l'API Binance"""
        if not self.binance_client:
            raise Exception("Client Binance non initialisé")
        
        try:
            # Test avec l'endpoint de statut du serveur
            status = self.binance_client.get_system_status()
            
            if status['status'] == 0:
                self.logger.info("✅ Connexion Binance testée avec succès")
                return True
            else:
                raise Exception(f"Statut serveur Binance: {status}")
                
        except Exception as e:
            self.logger.error(f"❌ Test connexion Binance échoué: {e}")
            raise
    
    async def get_symbol_info(self, symbol: str) -> Dict:
        """Récupère les informations de trading d'un symbole"""
        cache_key = f"symbol_info_{symbol}"
        
        # Vérifier le cache (valide 1 heure)
        if self._is_cache_valid(cache_key, 3600):
            return self.cache[cache_key]
        
        try:
            if self.binance_client:
                exchange_info = self.binance_client.get_exchange_info()
                
                for symbol_info in exchange_info['symbols']:
                    if symbol_info['symbol'] == symbol:
                        # Extraire les informations importantes
                        filters = {}
                        for filter_info in symbol_info['filters']:
                            filters[filter_info['filterType']] = filter_info
                        
                        info = {
                            'symbol': symbol,
                            'status': symbol_info['status'],
                            'baseAsset': symbol_info['baseAsset'],
                            'quoteAsset': symbol_info['quoteAsset'],
                            'quotePrecision': symbol_info['quotePrecision'],
                            'baseAssetPrecision': symbol_info['baseAssetPrecision'],
                            'filters': filters
                        }
                        
                        # Mettre en cache et retourner
                        self._set_cache(cache_key, info)
                        return info
                
                raise Exception(f"Symbole {symbol} non trouvé")
            
            else:
                raise Exception("Client Binance non disponible")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération info symbole {symbol}: {e}")
            raise
    
    def round_quantity(self, symbol_info: Dict, quantity: float) -> float:
        """Arrondit une quantité selon les règles du symbole"""
        try:
            self.logger.debug(f"🔍 Debug round_quantity pour {symbol_info.get('symbol', 'N/A')}")
            self.logger.debug(f"🔍 Type symbol_info: {type(symbol_info)}")
            self.logger.debug(f"🔍 Clés symbol_info: {list(symbol_info.keys()) if isinstance(symbol_info, dict) else 'N/A'}")
            
            # Vérifier que symbol_info est bien un dictionnaire
            if not isinstance(symbol_info, dict):
                self.logger.warning(f"⚠️ symbol_info n'est pas un dict: {type(symbol_info)}")
                return quantity
            
            # Récupérer les filtres LOT_SIZE
            filters = symbol_info.get('filters', {})
            self.logger.debug(f"🔍 Type filters: {type(filters)}")
            
            # Si filters est une liste (format Binance brut), on la convertit en dict
            if isinstance(filters, list):
                self.logger.debug(f"🔍 Conversion des filtres de liste vers dict")
                filters_dict = {}
                for filter_info in filters:
                    if isinstance(filter_info, dict) and 'filterType' in filter_info:
                        filters_dict[filter_info['filterType']] = filter_info
                filters = filters_dict
                self.logger.debug(f"🔍 Filtres convertis: {list(filters.keys())}")
            
            if not isinstance(filters, dict):
                self.logger.warning(f"⚠️ filters n'est pas un dict après conversion: {type(filters)}")
                precision = symbol_info.get('baseAssetPrecision', 8)
                self.logger.info(f"📏 Utilisation précision par défaut: {precision}")
                return round(quantity, precision)
            
            lot_size_filter = filters.get('LOT_SIZE')
            self.logger.debug(f"🔍 LOT_SIZE filter: {lot_size_filter}")
            
            if not lot_size_filter:
                # Utiliser la précision de base si pas de filtre
                precision = symbol_info.get('baseAssetPrecision', 8)
                self.logger.info(f"📏 Pas de LOT_SIZE, utilisation précision base: {precision}")
                return round(quantity, precision)
            
            step_size = float(lot_size_filter['stepSize'])
            min_qty = float(lot_size_filter['minQty'])
            
            self.logger.debug(f"🔍 stepSize: {step_size}, minQty: {min_qty}")
            
            # Arrondir à la step_size la plus proche
            if step_size == 0:
                return quantity
            
            # Calculer le nombre de décimales dans step_size
            step_str = f"{step_size:.10f}".rstrip('0')
            if '.' in step_str:
                decimals = len(step_str.split('.')[1])
            else:
                decimals = 0
            
            # Arrondir vers le bas à la step_size
            rounded = (quantity // step_size) * step_size
            rounded = round(rounded, decimals)
            
            # Vérifier la quantité minimum
            if rounded < min_qty:
                rounded = min_qty
            
            self.logger.info(f"📏 Quantité arrondie: {quantity} -> {rounded} (decimals: {decimals})")
            return rounded
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur arrondi quantité: {e}, utilisation quantité originale")
            import traceback
            self.logger.debug(f"🔍 Traceback: {traceback.format_exc()}")
            return quantity
    
    def round_price(self, symbol_info: Dict, price: float) -> float:
        """Arrondit un prix selon les règles du symbole"""
        try:
            # Récupérer les filtres PRICE_FILTER
            price_filter = symbol_info['filters'].get('PRICE_FILTER')
            if not price_filter:
                # Utiliser la précision de quote si pas de filtre
                precision = symbol_info.get('quotePrecision', 8)
                return round(price, precision)
            
            tick_size = float(price_filter['tickSize'])
            
            if tick_size == 0:
                return price
            
            # Calculer le nombre de décimales dans tick_size
            tick_str = f"{tick_size:.10f}".rstrip('0')
            if '.' in tick_str:
                decimals = len(tick_str.split('.')[1])
            else:
                decimals = 0
            
            # Arrondir à la tick_size la plus proche
            rounded = round(price / tick_size) * tick_size
            return round(rounded, decimals)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur arrondi prix: {e}, utilisation prix original")
            return price
    
    def _is_cache_valid(self, key: str, ttl_seconds: int) -> bool:
        """Vérifie si le cache est encore valide"""
        if key not in self.cache:
            return False
        
        if key not in self.cache_ttl:
            return False
        
        return time.time() - self.cache_ttl[key] < ttl_seconds
    
    def _set_cache(self, key: str, data: Any):
        """Met en cache des données"""
        self.cache[key] = data
        self.cache_ttl[key] = time.time()
    
    async def get_klines(self, symbol: str, interval: str, limit: int = 100, start_time: Optional[int] = None) -> List[List]:
        """
        Récupère les données de chandelier (klines)
        
        Returns:
            List de [open_time, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_volume, taker_buy_quote_volume, ignore]
        """
        cache_key = f"klines_{symbol}_{interval}_{limit}"
        
        # Vérification du cache (30 secondes pour les klines)
        if self._is_cache_valid(cache_key, 30):
            return self.cache[cache_key]
        
        try:
            if self.binance_client:
                # Utilisation du client Binance officiel
                klines = self.binance_client.get_klines(
                    symbol=symbol,
                    interval=interval,
                    limit=limit,
                    startTime=start_time
                )
                
                # Conversion en format numérique
                processed_klines = []
                for kline in klines:
                    processed_klines.append([
                        int(kline[0]),      # Open time
                        float(kline[1]),    # Open
                        float(kline[2]),    # High
                        float(kline[3]),    # Low
                        float(kline[4]),    # Close
                        float(kline[5]),    # Volume
                        int(kline[6]),      # Close time
                        float(kline[7]),    # Quote asset volume
                        int(kline[8]),      # Number of trades
                        float(kline[9]),    # Taker buy base asset volume
                        float(kline[10]),   # Taker buy quote asset volume
                        kline[11]           # Ignore
                    ])
                
                self._set_cache(cache_key, processed_klines)
                return processed_klines
                
            elif self.ccxt_client:
                # Fallback sur CCXT
                ohlcv = await self.ccxt_client.fetch_ohlcv(
                    symbol.replace('USDC', '/USDC'),
                    timeframe=interval,
                    limit=limit
                )
                
                # Conversion au format Binance
                processed_klines = []
                for i, candle in enumerate(ohlcv):
                    processed_klines.append([
                        int(candle[0]),     # timestamp
                        float(candle[1]),   # open
                        float(candle[2]),   # high
                        float(candle[3]),   # low
                        float(candle[4]),   # close
                        float(candle[5]),   # volume
                        int(candle[0]) + 60000,  # close time (approximation)
                        0,  # quote volume (non disponible)
                        0,  # count
                        0,  # taker buy volume
                        0,  # taker buy quote volume
                        ""  # ignore
                    ])
                
                self._set_cache(cache_key, processed_klines)
                return processed_klines
            
            else:
                raise Exception("Aucun client API disponible")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération klines {symbol}: {e}")
            raise
    
    async def get_ticker_price(self, symbol: str) -> Dict[str, str]:
        """Récupère le prix actuel d'une paire"""
        cache_key = f"ticker_{symbol}"
        
        # Cache de 5 secondes pour les prix
        if self._is_cache_valid(cache_key, 5):
            return self.cache[cache_key]
        
        try:
            if self.binance_client:
                ticker = self.binance_client.get_symbol_ticker(symbol=symbol)
                self._set_cache(cache_key, ticker)
                return ticker
            
            elif self.ccxt_client:
                ticker = await self.ccxt_client.fetch_ticker(symbol.replace('USDC', '/USDC'))
                result = {
                    'symbol': symbol,
                    'price': str(ticker['last'])
                }
                self._set_cache(cache_key, result)
                return result
            
            else:
                raise Exception("Aucun client API disponible")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération prix {symbol}: {e}")
            raise
    
    async def get_24hr_ticker_stats(self) -> List[Dict]:
        """Récupère les statistiques 24h de toutes les paires"""
        cache_key = "24hr_tickers"
        
        # Cache de 60 secondes pour les stats 24h
        if self._is_cache_valid(cache_key, 60):
            return self.cache[cache_key]
        
        try:
            if self.binance_client:
                tickers = self.binance_client.get_ticker()
                
                # Filtrage pour USDC uniquement
                usdc_tickers = [
                    ticker for ticker in tickers 
                    if ticker['symbol'].endswith('USDC')
                ]
                
                self._set_cache(cache_key, usdc_tickers)
                return usdc_tickers
            
            elif self.ccxt_client:
                tickers = await self.ccxt_client.fetch_tickers()
                
                # Conversion au format Binance et filtrage USDC
                converted_tickers = []
                for symbol, ticker in tickers.items():
                    if '/USDC' in symbol:
                        binance_symbol = symbol.replace('/', '')
                        converted_ticker = {
                            'symbol': binance_symbol,
                            'priceChange': str(ticker['change'] or 0),
                            'priceChangePercent': str(ticker['percentage'] or 0),
                            'weightedAvgPrice': str(ticker['vwap'] or ticker['last']),
                            'prevClosePrice': str(ticker['close'] or ticker['last']),
                            'lastPrice': str(ticker['last']),
                            'lastQty': '0',
                            'bidPrice': str(ticker['bid'] or ticker['last']),
                            'askPrice': str(ticker['ask'] or ticker['last']),
                            'openPrice': str(ticker['open'] or ticker['last']),
                            'highPrice': str(ticker['high'] or ticker['last']),
                            'lowPrice': str(ticker['low'] or ticker['last']),
                            'volume': str(ticker['baseVolume'] or 0),
                            'quoteVolume': str(ticker['quoteVolume'] or 0),
                            'openTime': int((ticker['timestamp'] or time.time() * 1000) - 86400000),
                            'closeTime': int(ticker['timestamp'] or time.time() * 1000),
                            'firstId': 0,
                            'lastId': 0,
                            'count': 0
                        }
                        converted_tickers.append(converted_ticker)
                
                self._set_cache(cache_key, converted_tickers)
                return converted_tickers
            
            else:
                raise Exception("Aucun client API disponible")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération tickers 24h: {e}")
            raise
    
    async def get_all_pairs(self) -> List[str]:
        """Récupère la liste de toutes les paires de trading disponibles"""
        cache_key = "all_pairs"
        
        # Cache de 300 secondes (5 minutes) pour les paires
        if self._is_cache_valid(cache_key, 300):
            return self.cache[cache_key]
        
        try:
            if self.binance_client:
                exchange_info = self.binance_client.get_exchange_info()
                
                # Extraction des paires actives
                pairs = []
                for symbol_info in exchange_info['symbols']:
                    if symbol_info['status'] == 'TRADING':
                        pairs.append(symbol_info['symbol'])
                
                self._set_cache(cache_key, pairs)
                return pairs
            
            elif self.ccxt_client:
                markets = await self.ccxt_client.fetch_markets()
                
                # Conversion au format Binance
                pairs = []
                for market in markets:
                    if market['active']:
                        binance_symbol = market['symbol'].replace('/', '')
                        pairs.append(binance_symbol)
                
                self._set_cache(cache_key, pairs)
                return pairs
            
            else:
                raise Exception("Aucun client API disponible")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération paires: {e}")
            raise
    
    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Récupère les statistiques 24h d'une paire spécifique"""
        try:
            if self.binance_client:
                ticker = self.binance_client.get_ticker(symbol=symbol)
                return ticker
            
            elif self.ccxt_client:
                ticker = await self.ccxt_client.fetch_ticker(symbol.replace('USDC', '/USDC'))
                
                # Conversion au format Binance
                return {
                    'symbol': symbol,
                    'priceChange': str(ticker['change'] or 0),
                    'priceChangePercent': str(ticker['percentage'] or 0),
                    'weightedAvgPrice': str(ticker['vwap'] or ticker['last']),
                    'prevClosePrice': str(ticker['close'] or ticker['last']),
                    'lastPrice': str(ticker['last']),
                    'lastQty': '0',
                    'bidPrice': str(ticker['bid'] or ticker['last']),
                    'askPrice': str(ticker['ask'] or ticker['last']),
                    'openPrice': str(ticker['open'] or ticker['last']),
                    'highPrice': str(ticker['high'] or ticker['last']),
                    'lowPrice': str(ticker['low'] or ticker['last']),
                    'volume': str(ticker['baseVolume'] or 0),
                    'quoteVolume': str(ticker['quoteVolume'] or 0),
                    'openTime': int((ticker['timestamp'] or time.time() * 1000) - 86400000),
                    'closeTime': int(ticker['timestamp'] or time.time() * 1000),
                    'firstId': 0,
                    'lastId': 0,
                    'count': 0
                }
            
            else:
                raise Exception("Aucun client API disponible")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération ticker {symbol}: {e}")
            return None
    
    async def get_account_balance(self) -> Dict[str, Dict[str, str]]:
        """Récupère le solde du compte"""
        try:
            if self.binance_client:
                account = self.binance_client.get_account()
                
                # Formatage du solde
                balances = {}
                for balance in account['balances']:
                    asset = balance['asset']
                    if float(balance['free']) > 0 or float(balance['locked']) > 0:
                        balances[asset] = {
                            'free': balance['free'],
                            'locked': balance['locked'],
                            'total': str(float(balance['free']) + float(balance['locked']))
                        }
                
                return balances
            
            elif self.ccxt_client:
                balance = await self.ccxt_client.fetch_balance()
                
                # Conversion au format Binance
                formatted_balances = {}
                for asset, amounts in balance.items():
                    if asset not in ['info', 'timestamp', 'datetime', 'free', 'used', 'total']:
                        if amounts['total'] > 0:
                            formatted_balances[asset] = {
                                'free': str(amounts['free']),
                                'locked': str(amounts['used']),
                                'total': str(amounts['total'])
                            }
                
                return formatted_balances
            
            else:
                raise Exception("Aucun client API disponible")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération solde: {e}")
            raise
    
    async def get_order_book(self, symbol: str, limit: int = 10) -> Dict:
        """Récupère le carnet d'ordres"""
        try:
            if self.binance_client:
                depth = self.binance_client.get_order_book(symbol=symbol, limit=limit)
                return depth
            
            elif self.ccxt_client:
                order_book = await self.ccxt_client.fetch_order_book(
                    symbol.replace('USDC', '/USDC'), 
                    limit=limit
                )
                
                # Conversion au format Binance
                return {
                    'lastUpdateId': int(time.time() * 1000),
                    'bids': [[str(price), str(amount)] for price, amount in order_book['bids']],
                    'asks': [[str(price), str(amount)] for price, amount in order_book['asks']]
                }
            
            else:
                raise Exception("Aucun client API disponible")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération order book {symbol}: {e}")
            raise
    
    async def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None, **kwargs) -> Dict:
        """Place un ordre sur Binance avec gestion de la précision"""
        try:
            # Version simplifiée : récupérer directement la précision depuis Binance
            try:
                # Utiliser les informations d'échange Binance directement
                if self.binance_client:
                    exchange_info = self.binance_client.get_exchange_info()
                    
                    # Trouver le symbole
                    symbol_info = None
                    for s in exchange_info['symbols']:
                        if s['symbol'] == symbol:
                            symbol_info = s
                            break
                    
                    if symbol_info:
                        # Extraire les informations de précision
                        lot_size_filter = None
                        for filter_info in symbol_info['filters']:
                            if filter_info['filterType'] == 'LOT_SIZE':
                                lot_size_filter = filter_info
                                break
                        
                        if lot_size_filter:
                            step_size = float(lot_size_filter['stepSize'])
                            min_qty = float(lot_size_filter['minQty'])
                            
                            # Calculer les décimales depuis step_size
                            if step_size == 1:
                                decimals = 0
                            elif step_size == 0.1:
                                decimals = 1
                            elif step_size == 0.01:
                                decimals = 2
                            elif step_size == 0.001:
                                decimals = 3
                            elif step_size == 0.0001:
                                decimals = 4
                            elif step_size == 0.00001:
                                decimals = 5
                            elif step_size == 0.000001:
                                decimals = 6
                            else:
                                # Méthode générale pour calculer les décimales
                                step_str = f"{step_size:.10f}".rstrip('0')
                                decimals = len(step_str.split('.')[1]) if '.' in step_str else 0
                            
                            # Arrondir la quantité
                            rounded_quantity = round(quantity, decimals)
                            
                            # Vérifier quantité minimum
                            if rounded_quantity < min_qty:
                                rounded_quantity = min_qty
                            
                            self.logger.info(f"📏 Précision {symbol}: {quantity} -> {rounded_quantity} (decimals: {decimals}, stepSize: {step_size})")
                            quantity = rounded_quantity
                        else:
                            # Pas de filtre LOT_SIZE, utiliser précision par défaut
                            precision = symbol_info.get('baseAssetPrecision', 6)
                            quantity = round(quantity, precision)
                            self.logger.info(f"📏 Précision par défaut {symbol}: {quantity} (precision: {precision})")
                    else:
                        self.logger.warning(f"⚠️ Symbole {symbol} non trouvé dans exchange_info")
                else:
                    self.logger.warning(f"⚠️ Client Binance non disponible pour précision")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Erreur récupération précision {symbol}: {e}")
            
            # Arrondir le prix si fourni
            if price is not None:
                price = round(price, 8)  # Prix généralement 8 décimales max
            
            if self.binance_client:
                if order_type.upper() == 'MARKET':
                    if side.upper() == 'BUY':
                        order = self.binance_client.order_market_buy(
                            symbol=symbol,
                            quantity=quantity
                        )
                    else:
                        order = self.binance_client.order_market_sell(
                            symbol=symbol,
                            quantity=quantity
                        )
                elif order_type.upper() == 'TRAILING_STOP_MARKET':
                    # Ordre trailing stop spécifique Binance
                    order = self.binance_client.create_order(
                        symbol=symbol,
                        side=side,
                        type='TRAILING_STOP_MARKET',
                        quantity=quantity,
                        callbackRate=kwargs.get('callbackRate', 1.0),  # Callback rate en %
                        timeInForce='GTC'
                    )
                else:
                    order = self.binance_client.create_order(
                        symbol=symbol,
                        side=side,
                        type=order_type,
                        quantity=quantity,
                        price=price,
                        **kwargs
                    )
                
                return order
            
            elif self.ccxt_client:
                order = await self.ccxt_client.create_order(
                    symbol.replace('USDC', '/USDC'),
                    type=order_type.lower(),
                    side=side.lower(),
                    amount=quantity,
                    price=price,
                    params=kwargs
                )
                
                # Conversion au format Binance
                return {
                    'symbol': symbol,
                    'orderId': order['id'],
                    'orderListId': -1,
                    'clientOrderId': order.get('clientOrderId', ''),
                    'transactTime': int(order['timestamp']),
                    'price': str(order['price'] or 0),
                    'origQty': str(order['amount']),
                    'executedQty': str(order['filled']),
                    'cummulativeQuoteQty': str(order['cost']),
                    'status': order['status'].upper(),
                    'timeInForce': 'GTC',
                    'type': order['type'].upper(),
                    'side': order['side'].upper(),
                    'fills': []
                }
            
            else:
                raise Exception("Aucun client API disponible")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur placement ordre {symbol}: {e}")
            raise
    
    async def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """Annule un ordre"""
        try:
            if self.binance_client:
                result = self.binance_client.cancel_order(
                    symbol=symbol,
                    orderId=order_id
                )
                return result
            
            elif self.ccxt_client:
                result = await self.ccxt_client.cancel_order(
                    order_id,
                    symbol.replace('USDC', '/USDC')
                )
                
                # Conversion au format Binance
                return {
                    'symbol': symbol,
                    'orderId': result['id'],
                    'orderListId': -1,
                    'clientOrderId': result.get('clientOrderId', ''),
                    'price': str(result.get('price', 0)),
                    'origQty': str(result.get('amount', 0)),
                    'executedQty': str(result.get('filled', 0)),
                    'cummulativeQuoteQty': str(result.get('cost', 0)),
                    'status': 'CANCELED',
                    'timeInForce': 'GTC',
                    'type': result.get('type', '').upper(),
                    'side': result.get('side', '').upper()
                }
            
            else:
                raise Exception("Aucun client API disponible")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur annulation ordre {symbol}: {e}")
            raise
    
    async def get_order_status(self, symbol: str, order_id: str) -> Dict:
        """Récupère le statut d'un ordre"""
        try:
            if self.binance_client:
                order = self.binance_client.get_order(
                    symbol=symbol,
                    orderId=order_id
                )
                return order
            
            elif self.ccxt_client:
                order = await self.ccxt_client.fetch_order(
                    order_id,
                    symbol.replace('USDC', '/USDC')
                )
                
                # Conversion au format Binance
                return {
                    'symbol': symbol,
                    'orderId': order['id'],
                    'orderListId': -1,
                    'clientOrderId': order.get('clientOrderId', ''),
                    'price': str(order['price'] or 0),
                    'origQty': str(order['amount']),
                    'executedQty': str(order['filled']),
                    'cummulativeQuoteQty': str(order['cost']),
                    'status': order['status'].upper(),
                    'timeInForce': 'GTC',
                    'type': order['type'].upper(),
                    'side': order['side'].upper(),
                    'stopPrice': str(order.get('stopPrice', 0)),
                    'icebergQty': '0',
                    'time': int(order['timestamp']),
                    'updateTime': int(order['timestamp']),
                    'isWorking': order['status'] in ['open', 'partial'],
                    'origQuoteOrderQty': '0'
                }
            
            else:
                raise Exception("Aucun client API disponible")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération statut ordre {symbol}: {e}")
            raise
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Récupère les informations d'une paire"""
        try:
            if self.binance_client:
                exchange_info = self.binance_client.get_exchange_info()
                
                for symbol_info in exchange_info['symbols']:
                    if symbol_info['symbol'] == symbol:
                        return symbol_info
                
                return None
            
            elif self.ccxt_client:
                markets = await self.ccxt_client.fetch_markets()
                
                for market in markets:
                    if market['symbol'] == symbol.replace('USDC', '/USDC'):
                        # Conversion au format Binance
                        return {
                            'symbol': symbol,
                            'status': 'TRADING' if market['active'] else 'HALT',
                            'baseAsset': market['base'],
                            'baseAssetPrecision': market['precision']['base'],
                            'quoteAsset': market['quote'],
                            'quotePrecision': market['precision']['quote'],
                            'quoteAssetPrecision': market['precision']['quote'],
                            'orderTypes': ['LIMIT', 'MARKET'],
                            'icebergAllowed': False,
                            'ocoAllowed': False,
                            'isSpotTradingAllowed': True,
                            'isMarginTradingAllowed': False,
                            'filters': []
                        }
                
                return None
            
            else:
                raise Exception("Aucun client API disponible")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération info symbol {symbol}: {e}")
            return None
    
    async def close(self):
        """Ferme les connexions"""
        try:
            if self.ccxt_client:
                await self.ccxt_client.close()
                self.logger.info("✅ Connexions fermées")
        except Exception as e:
            self.logger.error(f"❌ Erreur fermeture connexions: {e}")
    
    def __del__(self):
        """Destructeur pour fermer les connexions"""
        try:
            if self.ccxt_client and hasattr(self.ccxt_client, 'close'):
                # Ne pas utiliser asyncio.create_task dans __del__ pour éviter les warnings
                pass
        except:
            pass


# Exemple d'utilisation
async def main():
    """Test du data fetcher"""
    import os
    
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")
    
    if not api_key or not secret_key:
        print("❌ Clés API manquantes")
        return
    
    fetcher = DataFetcher(api_key, secret_key, testnet=True)
    
    try:
        # Test de connexion
        await fetcher.test_connection()
        
        # Test récupération klines
        klines = await fetcher.get_klines("BTCUSDC", "1m", 10)
        print(f"✅ Klines BTC: {len(klines)} bougies")
        
        # Test prix
        ticker = await fetcher.get_ticker_price("BTCUSDC")
        print(f"✅ Prix BTC: {ticker['price']}")
        
        # Test solde
        balance = await fetcher.get_account_balance()
        print(f"✅ Solde: {len(balance)} assets")
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
    
    finally:
        await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
