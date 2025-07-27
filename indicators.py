#!/usr/bin/env python3
"""
📊 INDICATORS - Indicateurs techniques pour RSI Scalping
Calculs optimisés avec TA-Lib et pandas
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("⚠️ TA-Lib non disponible. Utilisation des calculs manuels.")


class TechnicalIndicators:
    """Classe pour calculer les indicateurs techniques"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def calculate_rsi(self, prices, period: int = 14):
        """Calcule le RSI (Relative Strength Index)"""
        try:
            # Convertir en numpy array si c'est une Series pandas
            if hasattr(prices, 'values'):
                prices_array = prices.values
            else:
                prices_array = np.array(prices, dtype=np.float64)
            
            if TALIB_AVAILABLE and len(prices_array) >= period:
                rsi = talib.RSI(prices_array, timeperiod=period)
                # Retourner une Series pandas pour compatibilité avec .iloc
                if hasattr(prices, 'index'):
                    return pd.Series(rsi, index=prices.index)
                else:
                    return pd.Series(rsi)
            else:
                # Calcul manuel du RSI
                if len(prices_array) < period + 1:
                    result = np.full(len(prices_array), 50.0)
                    if hasattr(prices, 'index'):
                        return pd.Series(result, index=prices.index)
                    else:
                        return pd.Series(result)
                
                # Calcul RSI avec fenêtre glissante
                rsi_values = []
                for i in range(len(prices_array)):
                    if i < period:
                        rsi_values.append(50.0)
                    else:
                        window_prices = prices_array[i-period:i+1]
                        deltas = np.diff(window_prices)
                        gains = np.where(deltas > 0, deltas, 0)
                        losses = np.where(deltas < 0, -deltas, 0)
                        
                        avg_gain = np.mean(gains)
                        avg_loss = np.mean(losses)
                        
                        if avg_loss == 0:
                            rsi_values.append(100.0)
                        else:
                            rs = avg_gain / avg_loss
                            rsi = 100 - (100 / (1 + rs))
                            rsi_values.append(rsi)
                
                if hasattr(prices, 'index'):
                    return pd.Series(rsi_values, index=prices.index)
                else:
                    return pd.Series(rsi_values)
                
                return float(rsi)
                
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul RSI: {e}")
            return 50.0
    
    def calculate_ema(self, prices, period: int):
        """Calcule l'EMA (Exponential Moving Average)"""
        try:
            # Convertir en numpy array si c'est une Series pandas
            if hasattr(prices, 'values'):
                prices_array = prices.values
            else:
                prices_array = np.array(prices, dtype=np.float64)
            
            if TALIB_AVAILABLE and len(prices_array) >= period:
                ema = talib.EMA(prices_array, timeperiod=period)
                # Retourner une Series pandas pour compatibilité avec .iloc
                if hasattr(prices, 'index'):
                    return pd.Series(ema, index=prices.index)
                else:
                    return pd.Series(ema)
            else:
                # Calcul manuel de l'EMA
                if len(prices_array) < period:
                    result = np.full(len(prices_array), prices_array[-1] if len(prices_array) > 0 else 0.0)
                    if hasattr(prices, 'index'):
                        return pd.Series(result, index=prices.index)
                    else:
                        return pd.Series(result)
                
                multiplier = 2 / (period + 1)
                ema_values = []
                ema = prices_array[0]
                ema_values.append(ema)
                
                for price in prices_array[1:]:
                    ema = (price * multiplier) + (ema * (1 - multiplier))
                    ema_values.append(ema)
                
                if hasattr(prices, 'index'):
                    return pd.Series(ema_values, index=prices.index)
                else:
                    return pd.Series(ema_values)
                
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul EMA: {e}")
            return prices[-1] if prices else 0.0
    
    def calculate_macd(self, prices, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calcule le MACD"""
        try:
            # Convertir en numpy array si c'est une Series pandas
            if hasattr(prices, 'values'):
                prices_array = prices.values
            else:
                prices_array = np.array(prices, dtype=np.float64)
            
            if TALIB_AVAILABLE and len(prices_array) >= slow:
                macd, signal_line, histogram = talib.MACD(prices_array, fastperiod=fast, slowperiod=slow, signalperiod=signal)
                
                # Retourner des Series pandas pour compatibilité avec .iloc
                if hasattr(prices, 'index'):
                    return {
                        'macd': pd.Series(macd, index=prices.index),
                        'signal': pd.Series(signal_line, index=prices.index),
                        'histogram': pd.Series(histogram, index=prices.index)
                    }
                else:
                    return {
                        'macd': pd.Series(macd),
                        'signal': pd.Series(signal_line),
                        'histogram': pd.Series(histogram)
                    }
            else:
                # Calcul manuel du MACD
                if len(prices_array) < slow:
                    result = np.zeros(len(prices_array))
                    if hasattr(prices, 'index'):
                        return {
                            'macd': pd.Series(result, index=prices.index),
                            'signal': pd.Series(result, index=prices.index),
                            'histogram': pd.Series(result, index=prices.index)
                        }
                    else:
                        return {
                            'macd': pd.Series(result),
                            'signal': pd.Series(result),
                            'histogram': pd.Series(result)
                        }
                
                ema_fast = self.calculate_ema(prices, fast)
                ema_slow = self.calculate_ema(prices, slow)
                macd = ema_fast - ema_slow
                
                # Pour le signal, simplification: signal = macd * 0.9
                signal_line = macd * 0.9
                histogram = macd - signal_line
                
                return {
                    'macd': macd,
                    'signal': signal_line,
                    'histogram': histogram
                }
                
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul MACD: {e}")
            return {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0}
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        """Calcule les bandes de Bollinger"""
        try:
            if TALIB_AVAILABLE and len(prices) >= period:
                prices_array = np.array(prices, dtype=np.float64)
                upper, middle, lower = talib.BBANDS(prices_array, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
                
                return {
                    'upper': float(upper[-1]) if not np.isnan(upper[-1]) else prices[-1],
                    'middle': float(middle[-1]) if not np.isnan(middle[-1]) else prices[-1],
                    'lower': float(lower[-1]) if not np.isnan(lower[-1]) else prices[-1]
                }
            else:
                # Calcul manuel des bandes de Bollinger
                if len(prices) < period:
                    price = prices[-1] if prices else 0.0
                    return {'upper': price, 'middle': price, 'lower': price}
                
                recent_prices = prices[-period:]
                middle = np.mean(recent_prices)
                std = np.std(recent_prices)
                
                upper = middle + (std_dev * std)
                lower = middle - (std_dev * std)
                
                return {
                    'upper': float(upper),
                    'middle': float(middle),
                    'lower': float(lower)
                }
                
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul Bollinger: {e}")
            price = prices[-1] if prices else 0.0
            return {'upper': price, 'middle': price, 'lower': price}
    
    def calculate_volume_sma(self, volumes: List[float], period: int = 20) -> float:
        """Calcule la moyenne mobile simple du volume"""
        try:
            if len(volumes) < period:
                return volumes[-1] if volumes else 0.0
            
            return float(np.mean(volumes[-period:]))
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul Volume SMA: {e}")
            return volumes[-1] if volumes else 0.0
    
    def detect_breakout(self, prices: List[float], volumes: List[float], threshold: float = 0.02) -> bool:
        """Détecte un breakout basé sur le prix et le volume"""
        try:
            if len(prices) < 3 or len(volumes) < 3:
                return False
            
            # Vérifier la hausse de prix
            price_change = (prices[-1] - prices[-2]) / prices[-2]
            
            # Vérifier l'augmentation du volume
            avg_volume = np.mean(volumes[-10:]) if len(volumes) >= 10 else volumes[-1]
            volume_spike = volumes[-1] > (avg_volume * 1.5)
            
            return price_change > threshold and volume_spike
            
        except Exception as e:
            self.logger.error(f"❌ Erreur détection breakout: {e}")
            return False
    
    def analyze_market_conditions(self, klines_data: List[List]) -> Dict[str, any]:
        """Analyse complète des conditions de marché"""
        try:
            if not klines_data or len(klines_data) < 30:
                return {
                    'rsi': 50.0,
                    'ema_9': 0.0,
                    'ema_21': 0.0,
                    'macd': {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0},
                    'bollinger': {'upper': 0.0, 'middle': 0.0, 'lower': 0.0},
                    'volume_avg': 0.0,
                    'breakout_detected': False,
                    'conditions_met': 0
                }
            
            # Extraction des données
            closes = [float(kline[4]) for kline in klines_data]  # Prix de clôture
            volumes = [float(kline[5]) for kline in klines_data]  # Volume
            
            # Calcul des indicateurs
            rsi = self.calculate_rsi(closes)
            ema_9 = self.calculate_ema(closes, 9)
            ema_21 = self.calculate_ema(closes, 21)
            macd = self.calculate_macd(closes)
            bollinger = self.calculate_bollinger_bands(closes)
            volume_avg = self.calculate_volume_sma(volumes)
            breakout = self.detect_breakout(closes, volumes)
            
            # Vérification des conditions d'entrée
            conditions_met = 0
            current_price = closes[-1]
            
            # 1. RSI < 28 (survente)
            if rsi < 28:
                conditions_met += 1
            
            # 2. EMA(9) > EMA(21) (tendance haussière)
            if ema_9 > ema_21:
                conditions_met += 1
            
            # 3. MACD > Signal (momentum positif)
            if macd['macd'] > macd['signal']:
                conditions_met += 1
            
            # 4. Prix proche de la bande inférieure de Bollinger
            if current_price <= bollinger['lower'] * 1.02:  # 2% de marge
                conditions_met += 1
            
            # 5. Volume supérieur à la moyenne
            if volumes[-1] > volume_avg:
                conditions_met += 1
            
            # 6. Breakout détecté
            if breakout:
                conditions_met += 1
            
            return {
                'rsi': rsi,
                'ema_9': ema_9,
                'ema_21': ema_21,
                'macd': macd,
                'bollinger': bollinger,
                'volume_avg': volume_avg,
                'current_volume': volumes[-1],
                'breakout_detected': breakout,
                'conditions_met': conditions_met,
                'current_price': current_price
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse conditions marché: {e}")
            return {
                'rsi': 50.0,
                'ema_9': 0.0,
                'ema_21': 0.0,
                'macd': {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0},
                'bollinger': {'upper': 0.0, 'middle': 0.0, 'lower': 0.0},
                'volume_avg': 0.0,
                'current_volume': 0.0,
                'breakout_detected': False,
                'conditions_met': 0,
                'current_price': 0.0
            }


# Instance globale pour utilisation facile
indicators = TechnicalIndicators()

# Fonctions d'accès rapide
def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calcule le RSI"""
    return indicators.calculate_rsi(prices, period)

def calculate_ema(prices: List[float], period: int) -> float:
    """Calcule l'EMA"""
    return indicators.calculate_ema(prices, period)

def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    """Calcule le MACD"""
    return indicators.calculate_macd(prices, fast, slow, signal)

def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
    """Calcule les bandes de Bollinger"""
    return indicators.calculate_bollinger_bands(prices, period, std_dev)

def analyze_market_conditions(klines_data: List[List]) -> Dict[str, any]:
    """Analyse complète des conditions de marché"""
    return indicators.analyze_market_conditions(klines_data)
