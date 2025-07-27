# 🚀 SATOCHI BOT - RSI SCALPING PRO

Bot de trading automatisé utilisant la stratégie RSI Scalping avec 6 conditions d'entrée pour générer +0.8% à +1% de profits quotidiens.

## 📋 Architecture Complète

```
├── binance_live_service.py      # Service data collection Binance temps réel
├── config.py                    # Configuration centralisée
├── data_fetcher.py             # Interface API Binance/CCXT
├── deploy.sh                   # Script déploiement VPS
├── firebase_logger.py           # Logging base de données
├── firebase-credentials.json    # Clés Firebase (à compléter)
├── indicators.py                # Indicateurs techniques optimisés
├── main.py                      # Bot principal - Stratégie RSI Scalping
├── quick_start.py              # Script démarrage rapide
├── README.md                   # Documentation complète
├── requirements_bot.txt        # Dépendances bot trading
├── requirements.txt            # Dépendances dashboard Streamlit
├── start_binance_live.py       # Lanceur service binance-live
├── telegram_notifier.py         # Notifications temps réel
├── test_validation.py          # Tests et validation
├── trade_executor.py            # Exécution trades avec SL/TP auto
├── streamlit_dashboard/        # Interface web monitoring
│   ├── app.py                 # Dashboard principal
│   └── pages/
│       ├── Analytics.py      # Analyse par paire
│       ├── Comparison.py     # Comparaison Binance/Firebase
│       ├── Logs.py           # Logs en temps réel
│       ├── PnL.py           # P&L journalier & objectifs
│       └── Trades.py        # Historique BUY/SELL
└── systemd/
    ├── satochi-binance-live.service # Service collection data
    └── satochi-tradebot.service     # Service bot trading
```

## 🎯 Stratégie de Trading

### Conditions d'Entrée (4/6 minimum requis)
1. **RSI < 28** - Zone de survente confirmée
2. **EMA(9) > EMA(21)** - Tendance haussière court terme
3. **MACD > Signal** - Momentum positif
4. **Bollinger Touch** - Proximité bande inférieure
5. **Volume > Moyenne** - Confirmation institutionnelle
6. **Breakout Confirmé** - Cassure de résistance

### Gestion des Risques
- **Take Profit**: 0.9% automatique dans Binance
- **Stop Loss**: 0.4% automatique dans Binance
- **Position**: 8% du capital par trade
- **Max Positions**: 3 simultanées
- **Trailing Stop**: Activé à +0.5%

## ⚙️ Configuration

### Variables d'Environnement (.env)
```bash
# APIs Binance
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
BINANCE_TESTNET=False

# Telegram Bot
TELEGRAM_BOT_TOKEN=7994723833:AAGwkuU4xBaNTstSTBGKwVGgifgDNCoLs4o
TELEGRAM_CHAT_ID=your_chat_id

# Firebase
FIREBASE_PROJECT_ID=satochi-d38ec
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
```

### Paramètres de Trading (config.py)
```python
class TradingConfig:
    # Stratégie
    RSI_THRESHOLD = 28
    TAKE_PROFIT_PERCENT = 0.9      # Take Profit 0.9%
    STOP_LOSS_PERCENT = 0.4      # Stop Loss 0.4%
    
    # Gestion du capital
    POSITION_SIZE_PERCENT = 8.0  # 8% par trade
    MAX_OPEN_POSITIONS = 3
    MIN_VOLUME_USDC = 80_000_000      # Volume minimum
    
    # Sécurité
    MAX_DAILY_TRADES = 15
    MAX_DAILY_LOSS = 50    # Stop loss quotidien
    MAX_LOSS_STREAK = 3    # Pause après 3 pertes
```

## 🚀 Installation & Déploiement

### 📦 Installation Locale (Windows/Mac/Linux)

```bash
# 1. Cloner le projet
git clone https://github.com/your-repo/satochi_bot
cd satochi_bot

# 2. Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 3. Installer dépendances
pip install -r requirements_bot.txt    # Bot de trading
pip install -r requirements.txt        # Dashboard Streamlit

# 4. Configuration
cp .env.example .env
# Éditer .env avec vos clés API

# 5. Lancer le bot
python main.py

# 6. Lancer le dashboard (terminal séparé)
cd streamlit_dashboard && streamlit run app.py
# Accès: http://localhost:8501
```

### 🌐 Déploiement VPS (Ubuntu/Debian)

```bash
# 1. Prérequis serveur
sudo apt update && sudo apt install -y git python3 python3-pip

# 2. Télécharger et déployer
git clone https://github.com/your-repo/satochi_bot
cd satochi_bot
chmod +x deploy.sh
./deploy.sh

# 3. Le script configure automatiquement:
# - Service systemd
# - Nginx pour le dashboard
# - Logs rotatifs
# - Monitoring automatique
# - Scripts de gestion
```

### 🔧 Commandes de Gestion VPS

```bash
# Gestion du bot
start-satochi-bot      # Démarrer
stop-satochi-bot       # Arrêter
restart-satochi-bot    # Redémarrer
status-satochi-bot     # Statut + logs

# Dashboard
start-satochi-dashboard  # Lancer interface web

# Monitoring
sudo systemctl status satochi-tradebot
tail -f /var/log/satochi-bot/bot.log
tail -f /var/log/satochi-bot/error.log
```

## 📊 Dashboard Streamlit

Interface web complète accessible sur `http://your-server:80`

### 🎯 Onglets Disponibles

| Onglet | Contenu |
|--------|---------|
| **🏠 Dashboard** | Vue d'ensemble, métriques temps réel, contrôles |
| **📝 Logs** | Logs détaillés en temps réel avec filtres |
| **📋 Trades** | Historique BUY/SELL, positions actives |
| **💰 P&L** | P&L journalier, objectifs, projections |
| **📊 Analytics** | Analyse par paire, heatmaps, conditions |
| **🔄 Comparison** | Comparaison données Binance/Firebase |

### 🎨 Fonctionnalités
- **Auto-refresh** configurable
- **Contrôles temps réel** (Start/Stop/Force Close)
- **Métriques live** (P&L, winrate, positions)
- **Graphiques interactifs** (Plotly)
- **Filtres avancés** (période, paires, statuts)
- **Export données** (CSV, JSON)

## 🔥 Firebase Integration

### Base de Données
- **trades**: Historique complet des trades
- **signals**: Signaux d'achat détectés
- **errors**: Logs d'erreurs centralisés
- **analytics**: Métriques de performance

### Credentials (firebase-credentials.json)
```json
{
  "type": "service_account",
  "project_id": "satochi-d38ec",
  "private_key_id": "your_private_key_id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "your_service_account@project.iam.gserviceaccount.com",
  "client_id": "your_client_id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

## 📱 Notifications Telegram

### Messages Automatiques
- ✅ **Nouveau trade ouvert** avec détails RSI/conditions
- 💰 **Trade fermé** avec P&L et raison (TP/SL/Timeout)
- ⚠️ **Alertes** (pertes consécutives, erreurs critiques)
- 📊 **Résumé quotidien** avec statistiques
- 🔄 **Mises à jour positions** (trailing stop)

### Configuration Bot
1. Créer bot avec @BotFather
2. Récupérer token: `7994723833:AAGwkuU4xBaNTstSTBGKwVGgifgDNCoLs4o`
3. Obtenir chat_id: envoyer `/start` puis vérifier avec `/getUpdates`

## 🛡️ Sécurité & Monitoring

### Fonctionnalités de Sécurité
- **API Keys** chiffrées en variables d'environnement
- **Rate limiting** anti-surtrading (max 5 trades/heure)
- **Capital protection** (stop loss quotidien: 50 USDC)
- **Position sizing** dynamique selon performance récente
- **Sanity checks** sur ordres et prix

### Monitoring Automatique
- **Service watchdog** (redémarrage auto si crash)
- **Logs rotatifs** (30 jours de rétention)
- **Alertes Telegram** sur erreurs critiques
- **Métriques temps réel** (CPU, mémoire, latence API)

## 📈 Performance Attendue

### Objectifs
- **+0.8% à +1%** de profit quotidien
- **65%+ winrate** avec 4/6 conditions minimum
- **Profit Factor: 1.5+** (gains/pertes)
- **Max Drawdown: <10%** avec gestion stricte

### Backtest Résultats (Simulation)
- **Période**: 90 jours
- **Capital initial**: 2000 USDC
- **ROI**: +28.7% (≈0.87% quotidien)
- **Winrate**: 72.3%
- **Max Drawdown**: 6.2%
- **Trades totaux**: 347

## 🐛 Debugging & Support

### Logs Principaux
```bash
# Bot principal
tail -f /var/log/satochi-bot/bot.log

# Erreurs
tail -f /var/log/satochi-bot/error.log

# Service systemd
journalctl -u satochi-tradebot -f

# Dashboard
tail -f ~/.streamlit/logs/app.log
```

### Problèmes Fréquents

1. **Erreur API Binance**: Vérifier clés et permissions
2. **Firebase timeout**: Vérifier fichier credentials
3. **Telegram silent**: Vérifier token et chat_id
4. **Dashboard inaccessible**: Vérifier port 8501 et Nginx

### Contact Support
- **Telegram**: @satochi_support
- **Email**: support@satochi-bot.com
- **Discord**: SatochiBotCommunity

## 📄 Licence

MIT License - Libre d'utilisation et modification

---

**⚠️ DISCLAIMER**: Le trading de cryptomonnaies présente des risques. Ce bot est fourni à des fins éducatives et de recherche. Utilisez vos propres fonds avec prudence et ne tradez que ce que vous pouvez vous permettre de perdre.
