#!/usr/bin/env python3
"""
🔧 CONFIGURATION CENTRALISÉE - RSI SCALPING PRO
Tous les paramètres du bot configurables à volonté
"""

import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TradingConfig:
    """⚙️ Configuration principale du trading"""
    
    # 🎯 STRATÉGIE RSI SCALPING
    RSI_PERIOD: int = 14                        # Période RSI
    RSI_OVERSOLD: float = 28.0                  # Seuil survente (entrée)
    RSI_OVERBOUGHT: float = 70.0                # Seuil surachat (sortie)
    
    # 📈 MOYENNES MOBILES
    EMA_FAST: int = 9                           # EMA rapide
    EMA_SLOW: int = 21                          # EMA lente
    
    # 📊 MACD
    MACD_FAST: int = 12                         # MACD rapide
    MACD_SLOW: int = 26                         # MACD lent
    MACD_SIGNAL: int = 9                        # Signal MACD
    
    # 🎈 BOLLINGER BANDS
    BB_PERIOD: int = 20                         # Période BB
    BB_STD: float = 2.0                         # Écart type BB
    
    # 📊 VOLUME
    VOLUME_MA_PERIOD: int = 20                  # Moyenne mobile volume
    VOLUME_SPIKE_THRESHOLD: float = 1.5         # Seuil spike volume
    
    # 🎯 DÉTECTION BREAKOUT
    BREAKOUT_THRESHOLD: float = 0.0007          # 0.07% breakout
    LOOKBACK_CANDLES: int = 5                   # Nombre bougies lookback
    
    # 💰 GESTION POSITION
    POSITION_SIZE_PERCENT: float = 22.0         # % du capital par position
    MAX_POSITIONS: int = 2                      # Max positions simultanées
    
    # 🎯 TAKE PROFIT / STOP LOSS
    TAKE_PROFIT_PERCENT: float = 0.9            # TP: +0.9%
    STOP_LOSS_PERCENT: float = 0.4              # SL: -0.4%
    
    # ⏱️ TIMEOUTS
    POSITION_TIMEOUT_MINUTES: int = 45          # Timeout position (45min)
    STAGNATION_THRESHOLD_LOW: float = -0.1      # Seuil stagnation bas
    STAGNATION_THRESHOLD_HIGH: float = 0.2      # Seuil stagnation haut
    STAGNATION_TIME_MINUTES: int = 15           # Temps stagnation max
    
    # 🚫 ANTI-SURTRADING
    MAX_TRADES_PER_HOUR: int = 2                # Max 2 trades/heure
    MIN_TIME_BETWEEN_BUYS: int = 300            # 300s entre achats
    
    # 📋 CONDITIONS ENTRÉE
    MIN_CONDITIONS_MET: int = 4                 # Min 4/5 conditions
    
    # 🏷️ TRADING
    SYMBOL: str = "BTCUSDC"                     # Paire de trading
    TIMEFRAME: str = "3m"                       # Timeframe (3min)
    
    # 💱 SLIPPAGE ET FRAIS
    SLIPPAGE_TOLERANCE: float = 0.1             # 0.1% slippage max
    TRADING_FEE: float = 0.1                    # 0.1% frais
    
    # 🔄 TRAILING STOP
    TRAILING_STOP_ENABLED: bool = True          # Activation trailing stop
    TRAILING_STOP_TRIGGER: float = 0.5          # Déclenchement à +0.5%
    TRAILING_STOP_DISTANCE: float = 0.3         # Distance 0.3%


@dataclass
class APIConfig:
    """🔐 Configuration API et services externes"""
    
    # 🏦 BINANCE
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY: str = os.getenv("BINANCE_SECRET_KEY", "")
    BINANCE_TESTNET: bool = os.getenv("BINANCE_TESTNET", "false").lower() == "true"
    
    # 📱 TELEGRAM
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # 🔥 FIREBASE
    FIREBASE_CREDENTIALS: str = os.getenv("FIREBASE_CREDENTIALS", "")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_DATABASE_URL: str = os.getenv("FIREBASE_DATABASE_URL", "")
    
    # 📊 GOOGLE SHEETS
    GOOGLE_SHEETS_CREDENTIALS: str = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "")
    GOOGLE_SHEETS_SPREADSHEET_ID: str = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")


@dataclass
class LoggingConfig:
    """Configuration du logging"""
    
    # 📝 NIVEAUX
    CONSOLE_LEVEL: str = "INFO"                 # DEBUG, INFO, WARNING, ERROR
    FILE_LEVEL: str = "DEBUG"                   # Niveau fichier
    
    # 📄 FORMAT ET CHEMIN
    FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    FILE_PATH: str = "logs/scalping_bot.log"
    
    # 📁 FICHIERS
    LOG_DIR: str = "logs"                       # Répertoire logs
    LOG_FILE: str = "scalping_bot.log"          # Fichier principal
    LOG_MAX_SIZE: int = 10 * 1024 * 1024        # 10MB max par fichier
    LOG_BACKUP_COUNT: int = 5                   # 5 fichiers de sauvegarde
    
    # 📋 LOGS SPÉCIALISÉS
    TRADES_LOG_FILE: str = "trades.log"         # Log des trades
    SIGNALS_LOG_FILE: str = "signals.log"       # Log des signaux
    ERRORS_LOG_FILE: str = "errors.log"         # Log des erreurs
    
    # 🔄 ROTATION
    ROTATION_ENABLED: bool = True               # Activation rotation
    ROTATION_WHEN: str = "midnight"             # Rotation à minuit
    ROTATION_INTERVAL: int = 1                  # Chaque jour


@dataclass
class NotificationConfig:
    """Configuration des notifications"""
    
    # 📱 TELEGRAM
    SEND_START_STOP: bool = True                # Démarrage/arrêt
    SEND_TRADE_OPEN: bool = True                # Ouverture trade
    SEND_TRADE_CLOSE: bool = True               # Fermeture trade
    SEND_SIGNALS: bool = False                  # Signaux techniques
    SEND_ERRORS: bool = True                    # Erreurs importantes
    
    # 🎯 FILTRES
    MIN_PROFIT_NOTIFICATION: float = 0.5        # Min +0.5% pour notif profit
    MIN_LOSS_NOTIFICATION: float = -0.2         # Min -0.2% pour notif perte
    
    # ⏰ TIMING
    QUIET_HOURS_START: int = 0                  # Début heures silencieuses (0h)
    QUIET_HOURS_END: int = 7                    # Fin heures silencieuses (7h)
    RATE_LIMIT_MINUTES: int = 5                 # Max 1 notif / 5min même type


@dataclass
class RiskManagementConfig:
    """⚠️ Configuration gestion des risques"""
    
    # 💰 CAPITAL
    MAX_DAILY_LOSS_PERCENT: float = 2.0         # Max -2% perte journalière
    MAX_WEEKLY_LOSS_PERCENT: float = 5.0        # Max -5% perte hebdomadaire
    MIN_ACCOUNT_BALANCE: float = 100.0          # Solde minimum USDC
    
    # 📊 POSITIONS
    MAX_POSITION_SIZE_USDC: float = 500.0       # Taille max position (500 USDC)
    MAX_TOTAL_EXPOSURE_PERCENT: float = 50.0    # Max 50% capital exposé
    
    # 🔥 PROTECTION DRAWDOWN
    MAX_CONSECUTIVE_LOSSES: int = 5             # Max 5 pertes consécutives
    COOLING_PERIOD_MINUTES: int = 60            # 60min pause après 5 pertes
    
    # 📈 VOLATILITÉ
    MAX_VOLATILITY_THRESHOLD: float = 3.0       # Max 3% volatilité 1h
    MIN_VOLATILITY_THRESHOLD: float = 0.1       # Min 0.1% volatilité 1h
    
    # ⏰ HORAIRES
    TRADING_START_HOUR: int = 6                 # Début trading (6h UTC)
    TRADING_END_HOUR: int = 22                  # Fin trading (22h UTC)
    
    # 🚨 ARRÊT D'URGENCE
    EMERGENCY_STOP_LOSS_PERCENT: float = 5.0    # Arrêt si -5% journalier
    AUTO_STOP_ENABLED: bool = True              # Arrêt auto activé


@dataclass
class DatabaseConfig:
    """🗄️ Configuration base de données et stockage"""
    
    # 📁 FICHIERS LOCAUX
    TRADES_DB_FILE: str = "data/trades.db"      # Base trades SQLite
    SIGNALS_DB_FILE: str = "data/signals.db"    # Base signaux SQLite
    BACKUP_ENABLED: bool = True                 # Sauvegarde auto
    BACKUP_INTERVAL_HOURS: int = 6              # Sauvegarde toutes les 6h
    
    # 🔄 RETENTION
    TRADES_RETENTION_DAYS: int = 365            # Garder trades 1 an
    SIGNALS_RETENTION_DAYS: int = 90            # Garder signaux 3 mois
    LOGS_RETENTION_DAYS: int = 30               # Garder logs 1 mois
    
    # 📊 EXPORT
    EXPORT_FORMAT: str = "CSV"                  # Format export (CSV/JSON)
    AUTO_EXPORT_ENABLED: bool = True            # Export auto quotidien
    EXPORT_PATH: str = "exports/"               # Dossier exports


@dataclass
class MonitoringConfig:
    """📊 Configuration monitoring et alertes"""
    
    # 📈 MÉTRIQUES
    TRACK_PERFORMANCE: bool = True              # Suivi performance
    TRACK_SIGNALS: bool = True                  # Suivi signaux
    TRACK_LATENCY: bool = True                  # Suivi latence
    
    # ⚡ ALERTES PERFORMANCE
    MAX_ORDER_LATENCY_MS: int = 5000           # Max 5s latence ordre
    MAX_API_RESPONSE_MS: int = 3000            # Max 3s réponse API
    MIN_SUCCESS_RATE: float = 95.0             # Min 95% réussite trades
    
    # 🔔 NOTIFICATIONS SYSTÈME
    SEND_DAILY_REPORT: bool = True             # Rapport quotidien
    SEND_WEEKLY_SUMMARY: bool = True           # Résumé hebdomadaire
    ALERT_ON_HIGH_LATENCY: bool = True         # Alerte latence
    
    # 📊 DASHBOARD
    STREAMLIT_ENABLED: bool = True             # Dashboard Streamlit
    STREAMLIT_PORT: int = 8501                 # Port dashboard
    STREAMLIT_HOST: str = "0.0.0.0"           # Host dashboard
    
    # 🔍 DEBUG
    DEBUG_SIGNALS: bool = False                # Debug signaux détaillé
    DEBUG_ORDERS: bool = False                 # Debug ordres détaillé
    SAVE_MARKET_DATA: bool = True              # Sauvegarder données marché


# 🌍 INSTANCES GLOBALES
trading_config = TradingConfig()
api_config = APIConfig()
logging_config = LoggingConfig()
notification_config = NotificationConfig()
risk_config = RiskManagementConfig()
db_config = DatabaseConfig()
monitoring_config = MonitoringConfig()


# 📋 VALIDATION CONFIG
def validate_config():
    """Valide la configuration au démarrage"""
    errors = []
    
    # Vérification API Binance
    if not api_config.BINANCE_API_KEY:
        errors.append("❌ BINANCE_API_KEY manquante")
    if not api_config.BINANCE_SECRET_KEY:
        errors.append("❌ BINANCE_SECRET_KEY manquante")
        
    # Vérification Telegram
    if not api_config.TELEGRAM_BOT_TOKEN:
        errors.append("⚠️ TELEGRAM_BOT_TOKEN manquant (notifications désactivées)")
    if not api_config.TELEGRAM_CHAT_ID:
        errors.append("⚠️ TELEGRAM_CHAT_ID manquant (notifications désactivées)")
        
    # Vérification paramètres trading
    if trading_config.TAKE_PROFIT_PERCENT <= 0:
        errors.append("❌ TAKE_PROFIT_PERCENT doit être > 0")
    if trading_config.STOP_LOSS_PERCENT <= 0:
        errors.append("❌ STOP_LOSS_PERCENT doit être > 0")
    if trading_config.POSITION_SIZE_PERCENT <= 0 or trading_config.POSITION_SIZE_PERCENT > 100:
        errors.append("❌ POSITION_SIZE_PERCENT doit être entre 0 et 100")
        
    return errors


def print_config_summary():
    """Affiche un résumé de la configuration"""
    print("\n" + "="*60)
    print("🔧 CONFIGURATION RSI SCALPING PRO")
    print("="*60)
    print(f"📊 Symbole: {trading_config.SYMBOL}")
    print(f"⏰ Timeframe: {trading_config.TIMEFRAME}")
    print(f"🎯 TP/SL: +{trading_config.TAKE_PROFIT_PERCENT}% / -{trading_config.STOP_LOSS_PERCENT}%")
    print(f"💰 Taille position: {trading_config.POSITION_SIZE_PERCENT}%")
    print(f"📈 RSI: {trading_config.RSI_PERIOD} (survente: {trading_config.RSI_OVERSOLD})")
    print(f"🌊 EMA: {trading_config.EMA_FAST}/{trading_config.EMA_SLOW}")
    print(f"🔄 Trailing Stop: {'✅' if trading_config.TRAILING_STOP_ENABLED else '❌'}")
    print(f"🏦 Testnet: {'✅' if api_config.BINANCE_TESTNET else '❌'}")
    print(f"📱 Telegram: {'✅' if api_config.TELEGRAM_BOT_TOKEN else '❌'}")
    print(f"🔥 Firebase: {'✅' if api_config.FIREBASE_CREDENTIALS else '❌'}")
    print("="*60)


if __name__ == "__main__":
    # Test de la configuration
    errors = validate_config()
    if errors:
        print("❌ ERREURS DE CONFIGURATION:")
        for error in errors:
            print(f"  {error}")
    else:
        print("✅ Configuration valide!")
        
    print_config_summary()
