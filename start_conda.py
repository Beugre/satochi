#!/usr/bin/env python3
"""
🚀 SCRIPT DE DÉMARRAGE CONDA - RSI SCALPING PRO
"""

import sys
import os

def check_conda_env():
    """Vérifier que nous sommes dans l'environnement conda"""
    if 'CONDA_DEFAULT_ENV' in os.environ:
        print(f"✅ Environnement conda actif: {os.environ['CONDA_DEFAULT_ENV']}")
        return True
    else:
        print("❌ Environnement conda non actif")
        return False

def test_imports():
    """Tester tous les imports critiques"""
    try:
        import talib
        print(f"✅ TA-Lib {talib.__version__} - OK")
        
        import ccxt
        print(f"✅ CCXT {ccxt.__version__} - OK")
        
        import pandas as pd
        print(f"✅ Pandas {pd.__version__} - OK")
        
        import numpy as np
        print(f"✅ NumPy {np.__version__} - OK")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    print("🚀 RSI SCALPING PRO - Démarrage avec CONDA")
    print("=" * 50)
    
    if not check_conda_env():
        sys.exit(1)
    
    if not test_imports():
        sys.exit(1)
    
    print("✅ Tous les tests passés ! Le bot peut maintenant démarrer.")
    print("Pour démarrer le bot, utilisez:")
    print("python main.py")

if __name__ == "__main__":
    main()
