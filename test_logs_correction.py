#!/usr/bin/env python3
"""
🔍 TEST RAPIDE get_logs_data
Test de la méthode corrigée
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime

def test_get_logs_data():
    """Test rapide de get_logs_data corrigée"""
    try:
        # Initialisation Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate('firebase-credentials.json')
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        
        print("🔥 Test get_logs_data corrigée...")
        
        # Simulation de la méthode corrigée
        logs_ref = db.collection('rsi_scalping_logs')
        logs = logs_ref.limit(5).stream()
        
        logs_data = []
        for log in logs:
            log_dict = log.to_dict()
            log_dict['id'] = log.id
            
            # Conversion du timestamp Firebase en string
            if 'timestamp' in log_dict and log_dict['timestamp']:
                try:
                    firebase_timestamp = log_dict['timestamp']
                    if hasattr(firebase_timestamp, 'isoformat'):
                        log_dict['timestamp'] = firebase_timestamp.isoformat()
                    else:
                        log_dict['timestamp'] = str(firebase_timestamp)
                except Exception as e:
                    log_dict['timestamp'] = str(log_dict['timestamp'])
            
            logs_data.append(log_dict)
        
        print(f"✅ Logs récupérés: {len(logs_data)}")
        
        if logs_data:
            print("📋 Premier log:")
            for key, value in logs_data[0].items():
                print(f"  {key}: {value}")
            
            print(f"\n📋 Types de timestamps:")
            for log in logs_data[:2]:
                if 'timestamp' in log:
                    print(f"  - {log['timestamp']} (type: {type(log['timestamp'])})")
        
        # Test filtrage par niveau
        print(f"\n🔍 Test filtrage niveau INFO:")
        info_logs = [log for log in logs_data if log.get('level') == 'INFO']
        print(f"  Logs INFO trouvés: {len(info_logs)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    test_get_logs_data()
