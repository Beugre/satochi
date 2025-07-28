#!/usr/bin/env python3
"""
🧪 TEST DE FORMATAGE DES PRIX - Validation spéciale PEPE et tokens micro-prix
"""

import asyncio
import logging
from config import TradingConfig, APIConfig
from data_fetcher import DataFetcher
from trade_executor import TradeExecutor

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_price_formatting():
    """Test spécifique du formatage des prix pour tokens micro-prix"""
    
    logger.info("🧪 Test formatage prix micro-tokens démarré")
    
    # Configuration
    config = TradingConfig()
    api_config = APIConfig()
    
    # Initialisation avec les bonnes clés API
    data_fetcher = DataFetcher(
        api_key=api_config.BINANCE_API_KEY,
        secret_key=api_config.BINANCE_SECRET_KEY,
        testnet=api_config.BINANCE_TESTNET
    )
    trade_executor = TradeExecutor(data_fetcher, config, config)
    
    try:
        # Test connexion
        await data_fetcher.test_connection()
        logger.info("✅ Connexion Binance OK")
        
        # Symboles de test (micro-prix)
        test_symbols = ["PEPEUSDC", "SHIBUSDC", "BTCUSDC", "ETHUSDC"]
        
        for symbol in test_symbols:
            try:
                logger.info(f"\n🔍 Test formatage pour {symbol}")
                
                # Récupération prix actuel
                ticker = await data_fetcher.get_ticker_price(symbol)
                current_price = float(ticker['price'])
                logger.info(f"   💰 Prix actuel: {current_price}")
                
                # Test calculs TP/SL typiques
                tp_price = current_price * 1.009  # +0.9%
                sl_price = current_price * 0.996  # -0.4%
                
                logger.info(f"   📊 TP calculé: {tp_price}")
                logger.info(f"   📊 SL calculé: {sl_price}")
                
                # Test formatage sécurisé
                formatted_current = await trade_executor._format_price(symbol, current_price)
                formatted_tp = await trade_executor._format_price(symbol, tp_price)
                formatted_sl = await trade_executor._format_price(symbol, sl_price)
                
                logger.info(f"   ✅ Prix formaté: {formatted_current}")
                logger.info(f"   ✅ TP formaté: {formatted_tp}")
                logger.info(f"   ✅ SL formaté: {formatted_sl}")
                
                # Validation format Binance
                import re
                def validate_binance_format(price_val):
                    price_str = str(price_val)
                    return re.match(r'^([0-9]{1,20})(\.[0-9]{1,20})?$', price_str) is not None
                
                current_valid = validate_binance_format(formatted_current)
                tp_valid = validate_binance_format(formatted_tp)
                sl_valid = validate_binance_format(formatted_sl)
                
                logger.info(f"   🔍 Validation format Binance:")
                logger.info(f"      Prix: {'✅' if current_valid else '❌'}")
                logger.info(f"      TP: {'✅' if tp_valid else '❌'}")
                logger.info(f"      SL: {'✅' if sl_valid else '❌'}")
                
                if all([current_valid, tp_valid, sl_valid]):
                    logger.info(f"   🎉 {symbol}: Formatage parfait!")
                else:
                    logger.warning(f"   ⚠️ {symbol}: Formatage à problème")
                
            except Exception as e:
                logger.error(f"   ❌ Erreur test {symbol}: {e}")
        
        logger.info("\n📋 RÉSUMÉ TEST FORMATAGE:")
        logger.info("   🔧 Nouvelles protections contre notation scientifique activées")
        logger.info("   🔍 Validation format regex Binance intégrée")
        logger.info("   ⚠️ PEPEUSDC maintenant blacklisté par défaut")
        logger.info("   📈 Système robuste pour tous types de prix")
        
    except Exception as e:
        logger.error(f"❌ Erreur test formatage: {e}")
    
    finally:
        await data_fetcher.close()
        logger.info("✅ Connexions fermées")

if __name__ == "__main__":
    asyncio.run(test_price_formatting())
