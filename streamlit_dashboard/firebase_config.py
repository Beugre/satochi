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
from datetime import datetime

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
        """Récupère les données de trades depuis Firebase - VRAIES COLLECTIONS"""
        try:
            # Utilisation de la vraie collection du bot RSI Scalping Pro
            trades_ref = self.db.collection('rsi_scalping_trades')
            # Pas de tri par timestamp pour éviter les erreurs d'index
            trades = trades_ref.limit(limit).stream()
            
            trades_data = []
            for trade in trades:
                trade_dict = trade.to_dict()
                trade_dict['id'] = trade.id
                
                # Conversion des timestamps Firebase
                for timestamp_field in ['timestamp', 'entry_time', 'exit_time']:
                    if timestamp_field in trade_dict and trade_dict[timestamp_field]:
                        try:
                            firebase_timestamp = trade_dict[timestamp_field]
                            if hasattr(firebase_timestamp, 'isoformat'):
                                trade_dict[timestamp_field] = firebase_timestamp.isoformat()
                            else:
                                trade_dict[timestamp_field] = str(firebase_timestamp)
                        except:
                            trade_dict[timestamp_field] = str(trade_dict[timestamp_field])
                
                trades_data.append(trade_dict)
            
            # Tri côté client
            try:
                trades_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            except:
                pass
            
            return trades_data
            
        except Exception as e:
            st.error(f"❌ Erreur récupération trades: {e}")
            return []
    
    def get_positions_data(self) -> list:
        """Récupère les positions actives depuis Firebase - VRAIES COLLECTIONS"""
        try:
            # Le bot RSI utilise peut-être 'rsi_scalping_signals' pour les positions ouvertes
            # Essayons d'abord les trades en cours
            positions_ref = self.db.collection('rsi_scalping_trades')
            positions = positions_ref.where('status', 'in', ['OPEN', 'PENDING', 'FILLED']).stream()
            
            positions_data = []
            for position in positions:
                position_dict = position.to_dict()
                position_dict['id'] = position.id
                positions_data.append(position_dict)
            
            # Si pas de résultats, essayer la collection signals
            if not positions_data:
                signals_ref = self.db.collection('rsi_scalping_signals')
                signals = signals_ref.where('is_active', '==', True).limit(20).stream()
                
                for signal in signals:
                    signal_dict = signal.to_dict()
                    signal_dict['id'] = signal.id
                    positions_data.append(signal_dict)
            
            return positions_data
            
        except Exception as e:
            st.error(f"❌ Erreur récupération positions: {e}")
            return []
    
    def get_bot_health(self) -> dict:
        """Récupère l'état de santé du bot depuis Firebase - VRAIES COLLECTIONS"""
        try:
            # Chercher dans les vraies collections du bot
            # 1. Vérifier les logs récents (sans order_by pour éviter les erreurs d'index)
            logs_ref = self.db.collection('rsi_scalping_logs')
            recent_logs = logs_ref.limit(5).stream()
            
            recent_log_data = []
            for log in recent_logs:
                log_dict = log.to_dict()
                # Conversion du timestamp Firebase
                if 'timestamp' in log_dict and log_dict['timestamp']:
                    try:
                        firebase_timestamp = log_dict['timestamp']
                        if hasattr(firebase_timestamp, 'isoformat'):
                            log_dict['timestamp'] = firebase_timestamp.isoformat()
                        else:
                            log_dict['timestamp'] = str(firebase_timestamp)
                    except:
                        log_dict['timestamp'] = str(log_dict['timestamp'])
                recent_log_data.append(log_dict)
            
            # Tri côté client par timestamp
            try:
                recent_log_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            except:
                pass
            
            if recent_log_data:
                latest_log = recent_log_data[0]
                last_update = latest_log.get('timestamp')
                
                if last_update:
                    # Déterminer si le bot est actif (log récent)
                    if isinstance(last_update, str):
                        last_update_dt = datetime.fromisoformat(last_update.replace('Z', ''))
                    else:
                        last_update_dt = last_update
                    
                    time_diff = datetime.now() - last_update_dt.replace(tzinfo=None)
                    is_active = time_diff.total_seconds() < 300  # Moins de 5 minutes = actif
                    
                    return {
                        'status': 'RUNNING' if is_active else 'STOPPED',
                        'last_update': last_update,
                        'message': f'Dernière activité: {time_diff.seconds//60}min ago' if not is_active else 'Bot actif',
                        'recent_logs_count': len(recent_log_data)
                    }
            
            # Si aucun log, chercher dans les trades récents (sans order_by)
            trades_ref = self.db.collection('rsi_scalping_trades')
            recent_trades = trades_ref.limit(1).stream()
            
            for trade in recent_trades:
                trade_dict = trade.to_dict()
                return {
                    'status': 'RUNNING',
                    'last_update': trade_dict.get('timestamp'),
                    'message': 'Bot actif - Trading en cours'
                }
            
            return {
                'status': 'UNKNOWN',
                'last_update': None,
                'message': 'Aucune activité récente détectée'
            }
                
        except Exception as e:
            st.error(f"❌ Erreur récupération santé bot: {e}")
            return {
                'status': 'ERROR',
                'last_update': None,
                'message': f'Erreur: {e}'
            }
    
    def get_analytics_data(self, period_days: int = 30) -> dict:
        """Récupère les données d'analytics depuis Firebase - VRAIES COLLECTIONS"""
        try:
            # Récupération des stats journalières du bot RSI (sans order_by)
            analytics_ref = self.db.collection('rsi_scalping_daily_stats')
            analytics_docs = analytics_ref.limit(period_days).stream()
            
            analytics_data = []
            for doc in analytics_docs:
                data = doc.to_dict()
                # Conversion timestamp si nécessaire
                if 'date' in data and data['date']:
                    try:
                        firebase_date = data['date']
                        if hasattr(firebase_date, 'isoformat'):
                            data['date'] = firebase_date.isoformat()
                        else:
                            data['date'] = str(firebase_date)
                    except:
                        data['date'] = str(data['date'])
                analytics_data.append(data)
            
            # Tri côté client par date
            try:
                analytics_data.sort(key=lambda x: x.get('date', ''), reverse=True)
            except:
                pass
            
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
        """Récupère les logs depuis Firebase - TEST RADICAL AVEC SESSION STATE"""
        
        # TEST RADICAL: Utiliser session_state pour prouver que la méthode s'exécute
        if 'get_logs_data_called' not in st.session_state:
            st.session_state.get_logs_data_called = 0
        st.session_state.get_logs_data_called += 1
        
        # Forcer l'affichage avec session_state
        st.sidebar.error(f"🔥 get_logs_data() appelée {st.session_state.get_logs_data_called} fois")
        
        try:
            st.sidebar.success("🔍 DÉBUT get_logs_data - Version bypass")
            
            # COPIE EXACTE du code BYPASS qui fonctionne
            direct_ref = self.db.collection('rsi_scalping_logs')
            st.sidebar.info("✅ Collection référence obtenue (bypass)")
            
            direct_stream = direct_ref.limit(limit).stream()
            st.sidebar.info("✅ Stream obtenu (bypass)")
            
            bypass_data = []
            for i, doc in enumerate(direct_stream):
                st.sidebar.write(f"📄 Document #{i+1} trouvé: ID={doc.id}")
                doc_dict = doc.to_dict()
                st.sidebar.write(f"📄 Keys: {list(doc_dict.keys())}")
                bypass_data.append(doc_dict)
            
            st.sidebar.success(f"🎯 TOTAL récupéré (bypass): {len(bypass_data)} logs")
            
            # Filtrage côté client APRÈS récupération
            if level != 'ALL':
                st.sidebar.write(f"🔍 Filtrage par niveau: {level}")
                filtered_data = []
                for log in bypass_data:
                    if log.get('level', '') == level:
                        filtered_data.append(log)
                bypass_data = filtered_data
                st.sidebar.write(f"🔍 APRÈS filtrage: {len(bypass_data)} logs")
            
            st.sidebar.success(f"🎯 RETOUR FINAL (bypass): {len(bypass_data)} logs")
            return bypass_data
            
        except Exception as e:
            st.sidebar.error(f"❌ EXCEPTION dans get_logs_data: {e}")
            import traceback
            st.sidebar.error(f"🔍 TRACEBACK: {traceback.format_exc()}")
            return []
    
    def debug_collections(self) -> dict:
        """Debug: Liste toutes les collections disponibles et leurs contenus"""
        try:
            collections_info = {}
            
            # Lister toutes les collections
            collections = self.db.collections()
            
            for collection in collections:
                collection_name = collection.id
                
                # Compter les documents
                docs = collection.limit(5).stream()
                doc_count = 0
                sample_docs = []
                
                for doc in docs:
                    doc_count += 1
                    doc_data = doc.to_dict()
                    sample_docs.append({
                        'id': doc.id,
                        'keys': list(doc_data.keys()) if doc_data else [],
                        'sample_data': doc_data
                    })
                
                collections_info[collection_name] = {
                    'doc_count_sample': doc_count,
                    'sample_documents': sample_docs
                }
            
            return collections_info
            
        except Exception as e:
            st.error(f"❌ Erreur debug collections: {e}")
            return {}
