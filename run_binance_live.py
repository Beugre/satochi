#!/usr/bin/env python3
"""
Wrapper pour démarrer le service Binance Live avec les variables d'environnement
"""

import os
import sys
from dotenv import load_dotenv

def main():
    # Chargement des variables d'environnement depuis .env
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
    
    # Import et lancement du service principal
    from binance_live_service import main as binance_main
    import asyncio
    
    # Configuration pour Windows (si nécessaire)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    return asyncio.run(binance_main())

if __name__ == "__main__":
    sys.exit(main())
