#!/usr/bin/env python3
"""
Test des notifications Telegram pour vérifier les signatures
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from telegram_notifier import TelegramNotifier, NotificationConfig

async def test_telegram_notifications():
    """Test des signatures des méthodes de notification"""
    
    print("🧪 Test des signatures Telegram...")
    
    # Mock configuration
    config = NotificationConfig()
    config.send_trade_open = True
    config.send_trade_close = True
    config.send_errors = True
    
    # Mock telegram notifier
    notifier = TelegramNotifier(config, "fake_token", "fake_chat_id")
    notifier.bot = AsyncMock()  # Mock du bot
    
    # Test données trade ouverture
    trade_open_data = {
        'pair': 'BTCUSDC',
        'entry_price': 50000.0,
        'quantity': 0.002,
        'capital_engaged': 100.0,
        'stop_loss': 49500.0,
        'take_profit': 50500.0,
        'timestamp': '2025-07-28T17:00:00'
    }
    
    # Test données trade fermeture
    trade_close_data = {
        'pair': 'BTCUSDC',
        'exit_price': 50300.0,
        'exit_reason': 'TAKE_PROFIT',
        'duration_formatted': '15m30s',
        'pnl_amount': 0.6,
        'pnl_percent': 0.6,
        'daily_pnl': 5.2
    }
    
    # Test données erreur
    error_data = {
        'message': 'Test erreur',
        'component': 'Test Component',
        'pair': 'BTCUSDC',
        'action': 'BUY'
    }
    
    try:
        # Test notification ouverture
        await notifier.send_trade_open_notification(trade_open_data)
        print("✅ send_trade_open_notification: OK")
        
        # Test notification fermeture
        await notifier.send_trade_close_notification(trade_close_data)
        print("✅ send_trade_close_notification: OK")
        
        # Test notification erreur
        await notifier.send_error_notification(error_data)
        print("✅ send_error_notification: OK")
        
        # Test notification start
        await notifier.send_start_notification(1000.0)
        print("✅ send_start_notification: OK")
        
        print("\n🎉 Tous les tests passés - Signatures correctes!")
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_telegram_notifications())
