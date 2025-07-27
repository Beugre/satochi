#!/usr/bin/env python3
"""
🚀 Script de lancement du RSI Scalping Pro Bot
Point d'entrée principal qui charge la configuration et lance le bot
"""

import asyncio
import os
import sys
from pathlib import Path

# Ajout du répertoire racine au path
sys.path.append(str(Path(__file__).parent))

# Charger les variables d'environnement depuis .env
from dotenv import load_dotenv
load_dotenv()

from config import validate_config, print_config_summary
from main import RSIScalpingBot


def main():
    """Point d'entrée principal"""
    
    print("🔍 Vérification de la configuration...")
    
    # Validation de la configuration
    try:
        errors = validate_config()
        if errors:
            print("❌ ERREURS DE CONFIGURATION:")
            for error in errors:
                print(f"  {error}")
            print("💡 Vérifiez votre fichier .env et les clés API")
            return 1
        
        print("✅ Configuration validée")
        print_config_summary()
        
    except Exception as e:
        print(f"❌ Erreur de configuration: {e}")
        print("💡 Vérifiez votre fichier .env et les clés API")
        return 1
    
    # Création et lancement du bot
    bot = RSIScalpingBot()
    
    try:
        print("🚀 Lancement du RSI Scalping Pro Bot...")
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du bot demandé par l'utilisateur")
        # Le bot gère déjà l'arrêt proprement dans sa méthode run()
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
