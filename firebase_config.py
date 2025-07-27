#!/usr/bin/env python3
"""
🔥 CONFIGURATION FIREBASE POUR STREAMLIT CLOUD
Configuration sécurisée utilisant les secrets Streamlit
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
from typing import Optional

class StreamlitFirebaseConfig:
    """Configuration Firebase optimisée pour Streamlit Cloud"""
    
    def __init__(self):
        self.db: Optional[firestore.Client] = None
        self._init_firebase()
    
    def _init_firebase(self):
        """Initialise Firebase avec les secrets Streamlit"""
        try:
            # Vérifier si Firebase est déjà initialisé
            if not firebase_admin._apps:
                # Récupération des secrets Streamlit Cloud
                if "firebase" not in st.secrets:
                    st.error("❌ Secrets Firebase non configurés dans Streamlit Cloud!")
                    st.info("""
                    🔧 Pour configurer les secrets Firebase:
                    1. Allez dans votre app Streamlit Cloud
                    2. Settings → Secrets
                    3. Ajoutez la configuration Firebase
                    """)
                    st.stop()
                
                # Construction des credentials depuis les secrets
                firebase_secrets = st.secrets["firebase"]
                
                # Formatage de la clé privée
                private_key = firebase_secrets["private_key"].replace("\\n", "\n")
                
                cred_dict = {
                    "type": firebase_secrets["type"],
                    "project_id": firebase_secrets["project_id"],
                    "private_key_id": firebase_secrets["private_key_id"],
                    "private_key": private_key,
                    "client_email": firebase_secrets["client_email"],
                    "client_id": firebase_secrets["client_id"],
                    "auth_uri": firebase_secrets["auth_uri"],
                    "token_uri": firebase_secrets["token_uri"],
                    "auth_provider_x509_cert_url": firebase_secrets["auth_provider_x509_cert_url"],
                    "client_x509_cert_url": firebase_secrets["client_x509_cert_url"],
                    "universe_domain": firebase_secrets["universe_domain"]
                }
                
                # Initialisation Firebase
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                
                st.success("✅ Firebase initialisé avec succès!")
            
            # Connexion Firestore
            self.db = firestore.client()
            
        except Exception as e:
            st.error(f"❌ Erreur initialisation Firebase: {e}")
            st.info("""
            🔧 Vérifiez que les secrets Firebase sont correctement configurés.
            Les clés requises: type, project_id, private_key_id, private_key, client_email, etc.
            """)
            st.stop()
    
    def get_trades_data(self, limit: int = 100) -> list:
        """Récupère les données de trades depuis Firebase"""
        try:
            trades_ref = self.db.collection('trades')
            trades = trades_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
            
            trades_data = []
            for trade in trades:
                trade_dict = trade.to_dict()
                trade_dict['id'] = trade.id
                trades_data.append(trade_dict)
            
            return trades_data
            
        except Exception as e:
            st.error(f"❌ Erreur récupération trades: {e}")
            return []
    
    def get_positions_data(self) -> list:
        """Récupère les positions actives depuis Firebase"""
        try:
            positions_ref = self.db.collection('positions')
            positions = positions_ref.where('status', '==', 'OPEN').stream()
            
            positions_data = []
            for position in positions:
                position_dict = position.to_dict()
                position_dict['id'] = position.id
                positions_data.append(position_dict)
            
            return positions_data
            
        except Exception as e:
            st.error(f"❌ Erreur récupération positions: {e}")
            return []
    
    def get_bot_health(self) -> dict:
        """Récupère l'état de santé du bot depuis Firebase"""
        try:
            health_ref = self.db.collection('bot_health').document('current')
            health_doc = health_ref.get()
            
            if health_doc.exists:
                return health_doc.to_dict()
            else:
                return {
                    'status': 'UNKNOWN',
                    'last_update': None,
                    'message': 'Aucune donnée de santé disponible'
                }
                
        except Exception as e:
            st.error(f"❌ Erreur récupération santé bot: {e}")
            return {
                'status': 'ERROR',
                'last_update': None,
                'message': f'Erreur: {e}'
            }
    
    def get_analytics_data(self, period_days: int = 30) -> dict:
        """Récupère les données d'analytics depuis Firebase"""
        try:
            # Récupération des métriques de performance
            analytics_ref = self.db.collection('analytics')
            analytics_docs = analytics_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(period_days).stream()
            
            analytics_data = []
            for doc in analytics_docs:
                data = doc.to_dict()
                analytics_data.append(data)
            
            return {
                'daily_metrics': analytics_data,
                'period_days': period_days,
                'total_records': len(analytics_data)
            }
            
        except Exception as e:
            st.error(f"❌ Erreur récupération analytics: {e}")
            return {
                'daily_metrics': [],
                'period_days': period_days,
                'total_records': 0
            }
    
    def get_logs_data(self, level: str = 'ALL', limit: int = 100) -> list:
        """Récupère les logs depuis Firebase"""
        try:
            logs_ref = self.db.collection('logs')
            
            if level != 'ALL':
                logs_query = logs_ref.where('level', '==', level)
            else:
                logs_query = logs_ref
            
            logs = logs_query.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
            
            logs_data = []
            for log in logs:
                log_dict = log.to_dict()
                log_dict['id'] = log.id
                logs_data.append(log_dict)
            
            return logs_data
            
        except Exception as e:
            st.error(f"❌ Erreur récupération logs: {e}")
            return []
