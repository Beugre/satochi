#!/usr/bin/env python3
"""
🔧 CONFIGURATION CENTRALISÉE - RSI SCALPING PRO
Tous les paramètres du bot configurables à volonté
"""

import os
from dataclasses import dataclass, field
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
    POSITION_SIZE_PERCENT: float = 5.0          # % du capital par position
    MAX_POSITIONS: int = 2                      # Max positions simultanées
    MAX_OPEN_POSITIONS: int = 2                 # Alias pour compatibilité (telegram_notifier)
    MIN_POSITION_SIZE_USDC: float = 50.0        # Taille min position
    MAX_POSITION_SIZE_USDC: float = 500.0       # Taille max position

    # 🎯 TAKE PROFIT / STOP LOSS
    TAKE_PROFIT_PERCENT: float = 0.9            # TP: +0.9%
    STOP_LOSS_PERCENT: float = 0.4              # SL: -0.4%
    DAILY_STOP_LOSS_PERCENT: float = 2.0        # Max -2% perte journalière
    DAILY_TARGET_PERCENT: float = 1.0           # Objectif +1% quotidien
    
    # ⏱️ TIMEOUTS
    POSITION_TIMEOUT_MINUTES: int = 45          # Timeout position (45min)
    TIMEOUT_ENABLED: bool = True                # Activation timeout
    TIMEOUT_MINUTES: int = 45                   # Durée timeout position
    TIMEOUT_PNL_MIN: float = -0.1               # Seuil PnL min timeout
    TIMEOUT_PNL_MAX: float = 0.2                # Seuil PnL max timeout
    STAGNATION_THRESHOLD_LOW: float = -0.1      # Seuil stagnation bas
    STAGNATION_THRESHOLD_HIGH: float = 0.2      # Seuil stagnation haut
    STAGNATION_TIME_MINUTES: int = 15           # Temps stagnation max
    
    # 🚪 SORTIE ANTICIPÉE
    EARLY_EXIT_ENABLED: bool = True             # Sortie anticipée activée
    EARLY_EXIT_DURATION_MIN: int = 15           # Durée minimum avant sortie anticipée
    
    # 🚫 ANTI-SURTRADING
    MIN_TIME_BETWEEN_BUYS: int = 300            # 300s entre achats
    MAX_LOSS_STREAK: int = 3                    # Max pertes consécutives
    LOSS_PAUSE_MINUTES: int = 60                # Pause après pertes consécutives
    MAX_TRADES_PER_PAIR_HOUR: int = 2           # Max 2 trades par paire par heure
    MAX_TRADES_PER_HOUR: int = 2                # Max 2 trades par heure toutes paires

    # 📋 CONDITIONS ENTRÉE
    MIN_CONDITIONS_MET: int = 4                 # Min 4/5 conditions
    
    # 🏷️ TRADING
    TIMEFRAME: str = "1m"                       # Timeframe (1min)
    SCAN_ALL_PAIRS: bool = True                 # Scanner toutes les paires USDC
    
    # 💱 SLIPPAGE ET FRAIS
    SLIPPAGE_TOLERANCE: float = 0.1             # 0.1% slippage max
    TRADING_FEE: float = 0.1                    # 0.1% frais
    
    # 🔄 TRAILING STOP
    TRAILING_STOP_ENABLED: bool = True          # Activation trailing stop
    TRAILING_STOP_TRIGGER: float = 0.5          # Déclenchement à +0.5%
    TRAILING_STOP_DISTANCE: float = 0.3         # Distance 0.3%
    TRAILING_START_PERCENT: float = 0.5         # Pourcentage de déclenchement
    TRAILING_STEP_PERCENT: float = 0.1          # Pas de trailing
    
    # ⏰ HORAIRES
    TRADING_HOURS_ENABLED: bool = False         # Horaires de trading
    TRADING_START_HOUR: int = 6                 # Début trading (6h UTC)
    TRADING_END_HOUR: int = 22                  # Fin trading (22h UTC)
    WEEKEND_TRADING_ENABLED: bool = True        # Trading week-end
    
    # 🧠 SORTIE INTELLIGENTE RSI + TEMPS
    INTELLIGENT_EXIT_ENABLED: bool = True       # Activation sortie intelligente
    INTELLIGENT_EXIT_PHASE1_DURATION: int = 15  # Phase 1: 0-15 minutes (protection)
    INTELLIGENT_EXIT_PHASE2_DURATION: int = 45  # Phase 2: 15-45 minutes (rentabilité)
    INTELLIGENT_EXIT_PHASE3_DURATION: int = 120 # Phase 3: 45-120 minutes (conservateur)
    INTELLIGENT_EXIT_PHASE4_TIMEOUT: int = 120  # Phase 4: timeout obligatoire (minutes)
    
    # Seuils P&L pour sortie intelligente
    INTELLIGENT_EXIT_PROTECTION_LOSS: float = -0.8    # Phase 1: protection -0.8%
    INTELLIGENT_EXIT_PROFIT_THRESHOLD: float = 0.6    # Phase 2: seuil +0.6%
    INTELLIGENT_EXIT_SMALL_PROFIT: float = 0.3        # Phase 3: petit profit +0.3%
    
    # Seuils RSI pour sortie intelligente
    INTELLIGENT_EXIT_RSI_EXTREME_HIGH: float = 75.0   # RSI très haut (sortie)
    INTELLIGENT_EXIT_RSI_EXTREME_LOW: float = 25.0    # RSI très bas (sortie)
    INTELLIGENT_EXIT_RSI_HIGH: float = 70.0           # RSI haut (sortie conservateur)
    INTELLIGENT_EXIT_RSI_LOW: float = 30.0            # RSI bas (sortie conservateur)

    # 🚫 FILTRES
    BLACKLISTED_SYMBOLS: List[str] = field(default_factory=lambda: ["XRPUSDC", "DOGEUSDC", "PEPEUSDC"])  # Symboles interdits (PEPE ajouté pour problèmes formatage prix)
    BLACKLISTED_PAIRS: List[str] = field(default_factory=list)                                          # Paires interdites (alias)
    PRIORITY_PAIRS: List[str] = field(default_factory=lambda: ["BTCUSDC", "ETHUSDC", "SOLUSDC", "ADAUSDC", "DOTUSDC"])  # Paires prioritaires
    MAX_PAIRS_PER_SCAN: int = 7                             # Limite à 7 paires par scan
    MIN_VOLUME_USDC: float = 40000000.0                     # Volume min USDC
    MAX_SPREAD_PERCENT: float = 0.15                        # Spread max 0.15%
    MIN_VOLATILITY_PERCENT: float = 0.7                     # Volatilité min 0.7%
    
    # 🔧 GESTION TOKENS MICRO-PRIX (MEME COINS)
    MIN_PRICE_USDC: float = 0.00001                        # Prix minimum 0.00001 USDC (évite tokens trop volatils)
    MAX_PRICE_PRECISION: int = 20                           # Précision maximale autorisée (évite erreurs formatage)
    MICRO_PRICE_SYMBOLS: List[str] = field(default_factory=lambda: ["PEPEUSDC", "SHIBUSDC", "FLOKIUSDC"])  # Symboles micro-prix à surveiller

    def __post_init__(self):
        # Plus besoin de __post_init__ car les listes sont gérées par default_factory
        pass


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
    MAX_DAILY_LOSS: float = 200.0               # Max perte quotidienne en USDC
    MAX_WEEKLY_LOSS_PERCENT: float = 5.0        # Max -5% perte hebdomadaire
    MIN_ACCOUNT_BALANCE: float = 100.0          # Solde minimum USDC
    MIN_CAPITAL_TO_TRADE: float = 100.0         # Capital minimum pour trader
    
    # 📊 POSITIONS ET TRADES
    MAX_TOTAL_EXPOSURE_PERCENT: float = 50.0    # Max 50% capital exposé
    MAX_DAILY_TRADES: int = 20                  # Max trades par jour
    
    # 🔥 PROTECTION DRAWDOWN
    MAX_CONSECUTIVE_LOSSES: int = 5             # Max 5 pertes consécutives
    COOLING_PERIOD_MINUTES: int = 60            # 60min pause après 5 pertes
    
    # 🎯 POSITION SIZING DYNAMIQUE
    DYNAMIC_SIZING: bool = True                 # Sizing dynamique activé
    SIZE_REDUCTION_FACTOR: float = 0.8          # Réduction 20% après perte
    
    # 📈 VOLATILITÉ
    MAX_VOLATILITY_THRESHOLD: float = 3.0       # Max 3% volatilité 1h
    MIN_VOLATILITY_THRESHOLD: float = 0.1       # Min 0.1% volatilité 1h
    
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
    print(f"📊 Scanner: Toutes les paires USDC")
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
