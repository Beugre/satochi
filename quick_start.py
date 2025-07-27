#!/usr/bin/env python3
"""
🚀 QUICK START - SATOCHI BOT
Script de démarrage rapide et de vérification
"""

import sys
import os
import subprocess
import time
import platform
from pathlib import Path

def print_banner():
    """Affiche la bannière du bot"""
    banner = """
    ███████╗ █████╗ ████████╗ ██████╗  ██████╗██╗  ██╗██╗    ██████╗  ██████╗ ████████╗
    ██╔════╝██╔══██╗╚══██╔══╝██╔═══██╗██╔════╝██║  ██║██║    ██╔══██╗██╔═══██╗╚══██╔══╝
    ███████╗███████║   ██║   ██║   ██║██║     ███████║██║    ██████╔╝██║   ██║   ██║   
    ╚════██║██╔══██║   ██║   ██║   ██║██║     ██╔══██║██║    ██╔══██╗██║   ██║   ██║   
    ███████║██║  ██║   ██║   ╚██████╔╝╚██████╗██║  ██║██║    ██████╔╝╚██████╔╝   ██║   
    ╚══════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝    ╚═════╝  ╚═════╝    ╚═╝   
    
    🚀 RSI SCALPING PRO - Trading Bot Automatisé
    💰 Objectif: +0.8% à +1% de profit quotidien
    📊 Dashboard Streamlit intégré
    """
    print(banner)

def check_python_version():
    """Vérifie la version de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ requis. Version actuelle:", platform.python_version())
        return False
    print(f"✅ Python {platform.python_version()} détecté")
    return True

def check_environment():
    """Vérifie l'environnement"""
    project_root = Path(__file__).parent
    
    # Vérification des fichiers essentiels
    essential_files = [
        'main.py',
        'config.py', 
        'requirements_bot.txt',
        'streamlit_dashboard/app.py'
    ]
    
    missing_files = []
    for file in essential_files:
        if not (project_root / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Fichiers manquants: {', '.join(missing_files)}")
        return False
    
    print("✅ Fichiers essentiels présents")
    return True

def install_dependencies():
    """Installe les dépendances"""
    print("📦 Installation des dépendances...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements_bot.txt"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Dépendances installées avec succès")
            return True
        else:
            print("❌ Erreur installation dépendances:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout lors de l'installation des dépendances")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def check_config():
    """Vérifie la configuration"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️ Fichier .env manquant")
            print("💡 Copiez .env.example vers .env et configurez vos clés API")
            
            response = input("Voulez-vous copier .env.example vers .env maintenant? (y/n): ")
            if response.lower() in ['y', 'yes', 'o', 'oui']:
                try:
                    import shutil
                    shutil.copy(env_example, env_file)
                    print("✅ Fichier .env créé")
                    print("📝 Éditez .env avec vos vraies clés API avant de continuer")
                    return False  # Nécessite configuration manuelle
                except Exception as e:
                    print(f"❌ Erreur copie fichier: {e}")
                    return False
            else:
                return False
        else:
            print("❌ Fichier .env.example manquant")
            return False
    
    print("✅ Fichier .env présent")
    return True

def run_validation():
    """Lance la validation du système"""
    print("🧪 Validation du système...")
    
    try:
        result = subprocess.run([
            sys.executable, "test_validation.py"
        ], capture_output=True, text=True, timeout=60)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0
        
    except FileNotFoundError:
        print("⚠️ Script de validation non trouvé (optionnel)")
        return True
    except Exception as e:
        print(f"⚠️ Erreur validation: {e}")
        return True  # Continue même si validation échoue

def show_menu():
    """Affiche le menu principal"""
    print("\n" + "="*50)
    print("🎯 QUE VOULEZ-VOUS FAIRE ?")
    print("="*50)
    print("1. 🚀 Lancer le bot de trading")
    print("2. 📊 Lancer le dashboard Streamlit")
    print("3. 🧪 Valider l'installation")
    print("4. 📋 Afficher la configuration")
    print("5. 🆘 Aide et documentation")
    print("6. ❌ Quitter")
    print("="*50)
    
    while True:
        try:
            choice = input("\nVotre choix (1-6): ").strip()
            if choice in ['1', '2', '3', '4', '5', '6']:
                return int(choice)
            else:
                print("⚠️ Veuillez entrer un chiffre entre 1 et 6")
        except KeyboardInterrupt:
            print("\n👋 Au revoir !")
            sys.exit(0)

def launch_trading_bot():
    """Lance le bot de trading"""
    print("🚀 Lancement du bot de trading...")
    print("⏹️ Ctrl+C pour arrêter")
    print("-" * 40)
    
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n⏹️ Bot arrêté par l'utilisateur")
    except FileNotFoundError:
        print("❌ Fichier main.py non trouvé")
    except Exception as e:
        print(f"❌ Erreur lancement bot: {e}")

def launch_dashboard():
    """Lance le dashboard"""
    print("📊 Lancement du dashboard...")
    print("🌐 Le dashboard sera accessible sur http://localhost:8501")
    print("⏹️ Ctrl+C pour arrêter")
    print("-" * 40)
    
    try:
        # Changer vers le répertoire du dashboard et lancer streamlit
        import os
        os.chdir("streamlit_dashboard")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n⏹️ Dashboard arrêté par l'utilisateur")
    except FileNotFoundError:
        print("❌ Dashboard non trouvé dans streamlit_dashboard/app.py")
    except Exception as e:
        print(f"❌ Erreur lancement dashboard: {e}")
    finally:
        # Revenir au répertoire parent
        os.chdir("..")

def show_config():
    """Affiche la configuration actuelle"""
    print("📋 CONFIGURATION ACTUELLE")
    print("=" * 30)
    
    try:
        from config import TradingConfig, APIConfig
        
        trading_config = TradingConfig()
        api_config = APIConfig()
        
        print(f"RSI Threshold: {trading_config.RSI_THRESHOLD}")
        print(f"Take Profit: {trading_config.TAKE_PROFIT_PERCENT}%")
        print(f"Stop Loss: {trading_config.STOP_LOSS_PERCENT}%")
        print(f"Position Size: {trading_config.POSITION_SIZE_PERCENT}%")
        print(f"Max Positions: {trading_config.MAX_OPEN_POSITIONS}")
        print(f"Timeframe: {trading_config.TIMEFRAME}")
        
        # Vérification clés API (sans les afficher)
        env_file = Path(".env")
        if env_file.exists():
            content = env_file.read_text()
            has_binance = "BINANCE_API_KEY=" in content and "your_" not in content
            has_telegram = "TELEGRAM_BOT_TOKEN=" in content and "your_" not in content
            
            print(f"\nClés API configurées:")
            print(f"• Binance: {'✅' if has_binance else '❌'}")
            print(f"• Telegram: {'✅' if has_telegram else '❌'}")
        else:
            print("\n❌ Fichier .env non trouvé")
            
    except Exception as e:
        print(f"❌ Erreur lecture configuration: {e}")

def show_help():
    """Affiche l'aide"""
    help_text = """
    📚 AIDE - SATOCHI BOT
    =====================
    
    🎯 OBJECTIF:
    Ce bot utilise la stratégie RSI Scalping pour générer des profits
    quotidiens de 0.8% à 1% avec une gestion stricte des risques.
    
    ⚙️ CONFIGURATION REQUISE:
    1. Créer un compte Binance et générer des clés API
    2. Créer un bot Telegram avec @BotFather
    3. Configurer Firebase (optionnel mais recommandé)
    4. Éditer le fichier .env avec vos clés
    
    🚀 DÉMARRAGE RAPIDE:
    1. Exécuter ce script: python quick_start.py
    2. Choisir option 3 pour valider l'installation
    3. Configurer le fichier .env
    4. Lancer le bot (option 1) ou dashboard (option 2)
    
    📊 DASHBOARD:
    Interface web accessible sur http://localhost:8501
    - Monitoring en temps réel
    - Contrôle du bot
    - Analyse des performances
    - Historique des trades
    
    🆘 SUPPORT:
    - Documentation: README_COMPLETE.md
    - Tests: python test_validation.py
    - Logs: Vérifiez les fichiers de logs pour diagnostics
    
    📈 STRATÉGIE:
    Le bot utilise 6 conditions d'entrée (minimum 4 requises):
    1. RSI < 28 (survente)
    2. EMA(9) > EMA(21) (tendance haussière)
    3. MACD > Signal (momentum)
    4. Bollinger Touch (proximité bande inférieure)
    5. Volume élevé (confirmation)
    6. Breakout détecté (cassure résistance)
    
    ⚠️ RISQUES:
    Le trading comporte des risques. Ne tradez que ce que vous
    pouvez vous permettre de perdre. Testez d'abord en mode paper trading.
    """
    print(help_text)

def main():
    """Fonction principale"""
    print_banner()
    
    # Vérifications préliminaires
    if not check_python_version():
        sys.exit(1)
    
    if not check_environment():
        sys.exit(1)
    
    # Demander si installer les dépendances
    response = input("\n📦 Installer/Mettre à jour les dépendances? (y/n): ")
    if response.lower() in ['y', 'yes', 'o', 'oui']:
        if not install_dependencies():
            print("❌ Échec installation dépendances")
            sys.exit(1)
    
    # Vérifier la configuration
    if not check_config():
        print("\n⚠️ Configuration incomplète. Configurez .env avant de continuer.")
        input("Appuyez sur Entrée une fois la configuration terminée...")
    
    # Validation optionnelle
    response = input("\n🧪 Lancer la validation du système? (y/n): ")
    if response.lower() in ['y', 'yes', 'o', 'oui']:
        if not run_validation():
            print("⚠️ Validation échouée. Vous pouvez continuer mais des erreurs sont possibles.")
    
    # Menu principal
    while True:
        try:
            choice = show_menu()
            
            if choice == 1:
                launch_trading_bot()
            elif choice == 2:
                launch_dashboard()
            elif choice == 3:
                run_validation()
            elif choice == 4:
                show_config()
            elif choice == 5:
                show_help()
            elif choice == 6:
                print("👋 Au revoir !")
                break
            
            input("\nAppuyez sur Entrée pour continuer...")
            
        except KeyboardInterrupt:
            print("\n👋 Au revoir !")
            break

if __name__ == "__main__":
    main()
