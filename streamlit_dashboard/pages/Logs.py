#!/usr/bin/env python3
"""
<<<<<<< HEAD
📋 PAGE LOGS - DONNÉES RÉELLES FIREBASE UNIQUEMENT
Logs système - AUCUNE DONNÉE TEST
=======
📝 PAGE LOGS - DASHBOARD STREAMLIT
Monitoring des logs en temps réel depuis Firebase
>>>>>>> feature/clean-config
"""

import streamlit as st
import pandas as pd
<<<<<<< HEAD
import plotly.express as px
from datetime import datetime, timedelta, timezone
import pytz
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Logs - Satochi Bot",
    page_icon="📋",
    layout="wide"
)

try:
    from firebase_config import StreamlitFirebaseConfig
except ImportError as e:
    st.error(f"❌ Erreur import firebase_config: {e}")
    st.stop()

class LogsPage:
    """Logs - 100% DONNÉES RÉELLES FIREBASE"""
    
    def __init__(self):
        self.firebase_config = StreamlitFirebaseConfig()
        self.paris_tz = pytz.timezone('Europe/Paris')
    
    def _convert_to_paris_time(self, timestamp):
        """Convertit un timestamp Firebase vers l'heure de Paris"""
        try:
            # Si c'est un DatetimeWithNanoseconds Firebase
            if str(type(timestamp)).find('DatetimeWithNanoseconds') != -1:
                # Firebase timestamps sont en UTC
                utc_dt = timestamp.replace(tzinfo=pytz.UTC)
                paris_dt = utc_dt.astimezone(self.paris_tz)
                return f"{paris_dt.hour:02d}:{paris_dt.minute:02d}:{paris_dt.second:02d}"
            
            # Si c'est une string ISO
            elif isinstance(timestamp, str) and 'T' in timestamp:
                # Parser la string ISO
                if timestamp.endswith('Z'):
                    utc_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                elif '+' in timestamp:
                    utc_dt = datetime.fromisoformat(timestamp)
                else:
                    utc_dt = datetime.fromisoformat(timestamp).replace(tzinfo=pytz.UTC)
                
                # Convertir vers Paris
                paris_dt = utc_dt.astimezone(self.paris_tz)
                return f"{paris_dt.hour:02d}:{paris_dt.minute:02d}:{paris_dt.second:02d}"
            
            # Fallback
            else:
                return str(timestamp)[:19]
                
        except Exception as e:
            # En cas d'erreur, retourner timestamp brut
            return str(timestamp)[:19]
    
    def run(self):
        """Logs basés UNIQUEMENT sur Firebase"""
        
        st.title("📋 Logs Système (Firebase)")
        st.markdown("### 🔥 LOGS RÉELS - VERSION CORRIGÉE - AUCUNE SIMULATION")
        st.markdown("---")
        
        # Filtres de logs
        self._display_log_filters()
        
        # Auto-refresh automatique TOUJOURS ACTIF
        # Récupération en temps réel toutes les 5 secondes
        count = st_autorefresh(interval=5000, key="logs_autorefresh")
        
        # Afficher le statut de l'auto-refresh
        status_col1, status_col2 = st.columns([3, 1])
        with status_col1:
            st.success(f"🔄 AUTO-REFRESH TEMPS RÉEL - Actualisation #{count} - Toutes les 5 secondes")
        with status_col2:
            current_time = datetime.now(self.paris_tz).strftime("%H:%M:%S")
            st.info(f"🕐 {current_time} Paris")
        
        try:
            # RÉCUPÉRATION LOGS EN TEMPS RÉEL - TRIÉS PAR TIMESTAMP
            st.info("🔍 Récupération logs en temps réel...")
            
            # Récupération directe avec tri par timestamp décroissant
            logs_ref = self.firebase_config.db.collection('rsi_scalping_logs')
            selected_level = getattr(self, 'selected_level', 'ALL')
            logs_limit = getattr(self, 'logs_limit', 200)
            
            # Récupération avec ordre par timestamp (plus récents en premier)
            direct_logs = logs_ref.order_by('timestamp', direction='DESCENDING').limit(logs_limit).stream()
            
            logs_data = []
            for log in direct_logs:
                log_dict = log.to_dict()
                log_dict['id'] = log.id
                
                # Filtrage par niveau si nécessaire
                if selected_level != 'ALL':
                    if log_dict.get('level', '') != selected_level:
                        continue
                
                logs_data.append(log_dict)
            
            st.success(f"✅ {len(logs_data)} logs récupérés directement!")
            
            if not logs_data:
                st.warning("📭 Aucun log trouvé dans Firebase")
                st.info("🔄 Vérifiez que le bot écrit des logs")
                return
            
            # Statistiques logs RÉELLES
            self._display_real_log_stats(logs_data)
            
            # Graphique logs RÉELS
            self._display_real_log_timeline(logs_data)
            
            # Table logs RÉELS
            self._display_real_logs_table(logs_data)
            
        except Exception as e:
            st.error(f"❌ Erreur logs Firebase: {e}")
    
    def _display_log_filters(self):
        """Filtres pour les logs"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self.selected_level = st.selectbox(
                "Niveau de log",
                ["ALL", "ERROR", "WARNING", "INFO", "DEBUG"],
                index=0
            )
        
        with col2:
            self.logs_limit = st.selectbox(
                "Nombre de logs",
                [50, 100, 200, 500, 1000],
                index=2
            )
        
        with col3:
            if st.button("🔄 Actualiser maintenant"):
                st.rerun()
    
    def _display_real_log_stats(self, logs_data):
        """Statistiques logs RÉELLES"""
        st.subheader("📊 Statistiques Logs (Firebase)")
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        try:
            df = pd.DataFrame(logs_data)
            
            total_logs = len(df)
            
            # Comptage par niveau
            if 'level' in df.columns:
                level_counts = df['level'].value_counts().to_dict()
                errors = level_counts.get('ERROR', 0)
                warnings = level_counts.get('WARNING', 0)
                infos = level_counts.get('INFO', 0)
                debugs = level_counts.get('DEBUG', 0)
            else:
                errors = warnings = infos = debugs = 0
            
            # Logs récents (dernière heure en heure de Paris)
            if 'timestamp' in df.columns:
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
                    # Calculer une heure en arrière en UTC (pour Paris)
                    paris_now = datetime.now(self.paris_tz)
                    one_hour_ago_paris = paris_now - timedelta(hours=1)
                    one_hour_ago_utc = one_hour_ago_paris.astimezone(pytz.UTC)
                    recent_logs = len(df[df['timestamp'] > one_hour_ago_utc])
                except Exception as e:
                    st.warning(f"⚠️ Erreur parsing timestamp: {e}")
                    recent_logs = 0
            else:
                recent_logs = 0
            
            with col1:
                st.metric("📋 Total Logs", total_logs, delta="Firebase")
            
            with col2:
                error_color = "inverse" if errors > 0 else "normal"
                st.metric("❌ Erreurs", errors, delta_color=error_color)
            
            with col3:
                warning_color = "inverse" if warnings > 5 else "normal"
                st.metric("⚠️ Warnings", warnings, delta_color=warning_color)
            
            with col4:
                st.metric("ℹ️ Infos", infos, delta="Messages")
            
            with col5:
                st.metric("🔍 Debug", debugs, delta="Traces")
            
            with col6:
                st.metric("🕒 Récents (1h)", recent_logs, delta="Paris")
            
        except Exception as e:
            st.error(f"❌ Erreur stats logs: {e}")
    
    def _display_real_log_timeline(self, logs_data):
        """Timeline logs RÉELLE"""
        st.subheader("📈 Timeline des Logs (Firebase)")
        
        try:
            df = pd.DataFrame(logs_data)
            
            if 'timestamp' in df.columns and 'level' in df.columns:
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
                    df = df.sort_values('timestamp')
                    
                    # Graphique temporel par niveau
                    fig = px.histogram(
                        df,
                        x='timestamp',
                        color='level',
                        title="Distribution des Logs dans le Temps (Firebase)",
                        nbins=50,
                        color_discrete_map={
                            'ERROR': 'red',
                            'WARNING': 'orange',
                            'INFO': 'blue',
                            'DEBUG': 'gray'
                        }
                    )
                    
                    fig.update_layout(
                        height=400,
                        xaxis_title="Temps",
                        yaxis_title="Nombre de logs"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"⚠️ Erreur graphique timeline: {e}")
                    st.info("📊 Graphique temporel non disponible")
            else:
                st.warning("📊 Colonnes timestamp/level manquantes")
                
        except Exception as e:
            st.error(f"❌ Erreur timeline logs: {e}")
    
    def _display_real_logs_table(self, logs_data):
        """Affichage des logs RÉELS en format console"""
        st.subheader("📋 Console des Logs (Firebase)")
        
        try:
            if len(logs_data) == 0:
                st.info("📭 Aucun log")
                return
            
            # Tri par timestamp décroissant (plus récents d'abord)
            try:
                sorted_logs = sorted(logs_data, key=lambda x: x.get('timestamp', ''), reverse=True)
            except:
                sorted_logs = logs_data
            
            # Affichage en format console avec bannières colorées
            log_lines = []
            for i, log in enumerate(sorted_logs):
                # Format console: [TIMESTAMP] [LEVEL] MESSAGE
                timestamp = log.get('timestamp', 'NO_TIME')
                
                # Convertir vers l'heure de Paris
                time_display = self._convert_to_paris_time(timestamp)
                
                level = log.get('level', 'INFO')
                message = log.get('message', 'Pas de message')
                module = log.get('module', '')
                
                # Affichage avec bannière colorée selon le niveau
                if level == 'ERROR':
                    st.error(f"🔴 **[{time_display} Paris] ERROR** `{module}` {message}")
                elif level == 'WARNING':
                    st.warning(f"🟠 **[{time_display} Paris] WARNING** `{module}` {message}")
                elif level == 'INFO':
                    st.info(f"🔵 **[{time_display} Paris] INFO** `{module}` {message}")
                elif level == 'DEBUG':
                    st.write(f"⚪ **[{time_display} Paris] DEBUG** `{module}` {message}")
                else:
                    st.write(f"⚫ **[{time_display} Paris] {level}** `{module}` {message}")
                
                # Limiter l'affichage pour éviter la surcharge  
                if i >= 50:  # Afficher maximum 50 logs (augmenté de 30 à 50)
                    break
            
            # Informations sur les données avec temps de dernière actualisation
            current_time = datetime.now(self.paris_tz).strftime("%H:%M:%S")
            st.success(f"📊 {len(sorted_logs)} logs trouvés | Affichage des 50 plus récents | 🕐 Dernière actualisation: {current_time} Paris | ⚡ Tri: Plus récents en premier")
            
            # Options d'export et refresh
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Actualiser les logs"):
                    st.rerun()
            
            with col2:
                if st.button("💾 Exporter CSV"):
                    df = pd.DataFrame(sorted_logs)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Télécharger logs",
                        data=csv,
                        file_name=f"satochi_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with col3:
                if st.button("📋 Voir format tableau"):
                    st.dataframe(pd.DataFrame(sorted_logs), use_container_width=True, height=300)
            
        except Exception as e:
            st.error(f"❌ Erreur affichage logs console: {e}")
            # Fallback vers tableau simple
            try:
                st.dataframe(pd.DataFrame(logs_data), use_container_width=True)
            except:
                st.error("Impossible d'afficher les logs")

# Lancement de la page
page = LogsPage()
page.run()
=======
import sys
import os
from datetime import datetime, timedelta
import json
import time
import firebase_admin
from firebase_admin import credentials, firestore
from streamlit_autorefresh import st_autorefresh

# Configuration de la page
st.set_page_config(
    page_title="Logs - Satochi Bot",
    page_icon="📝",
    layout="wide"
)

# Auto-refresh toutes les 10 secondes pour les logs
st_autorefresh(interval=10000, key="logs_refresh")

# Ajout du répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def init_firebase():
    """Initialise Firebase si pas déjà fait"""
    try:
        app = firebase_admin.get_app()
        return firestore.client(app)
    except ValueError:
        # Initialiser Firebase
        cred_paths = [
            '/opt/satochi_bot/firebase-credentials.json',
            'firebase-credentials.json',
            '../firebase-credentials.json'
        ]
        
        for path in cred_paths:
            if os.path.exists(path):
                cred = credentials.Certificate(path)
                app = firebase_admin.initialize_app(cred)
                return firestore.client(app)
        
        st.error("❌ Fichier Firebase credentials non trouvé")
        return None

def get_recent_logs(db, limit=100):
    """Récupère les logs récents depuis Firebase"""
    try:
        # Récupérer les logs depuis la collection rsi_scalping_logs
        logs_ref = db.collection('rsi_scalping_logs')
        query = logs_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        
        logs = []
        for doc in query.stream():
            log_data = doc.to_dict()
            log_data['id'] = doc.id
            logs.append(log_data)
        
        return logs
    except Exception as e:
        st.error(f"❌ Erreur récupération logs: {e}")
        return []

def get_signals_logs(db, limit=50):
    """Récupère les signaux depuis Firebase"""
    try:
        signals_ref = db.collection('rsi_scalping_signals')
        query = signals_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        
        signals = []
        for doc in query.stream():
            signal_data = doc.to_dict()
            signal_data['id'] = doc.id
            signals.append(signal_data)
        
        return signals
    except Exception as e:
        st.error(f"❌ Erreur récupération signaux: {e}")
        return []

def get_pair_rejections(db, limit=30):
    """Récupère les paires rejetées depuis Firebase"""
    try:
        pairs_ref = db.collection('rsi_scalping_pairs_analysis')
        query = pairs_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        
        rejections = []
        for doc in query.stream():
            rejection_data = doc.to_dict()
            rejection_data['id'] = doc.id
            rejections.append(rejection_data)
        
        return rejections
    except Exception as e:
        st.error(f"❌ Erreur récupération rejets: {e}")
        return []

# Interface principale
def main():
    st.title("📝 Logs Bot RSI Scalping Pro")
    st.markdown("---")
    
    # Initialisation Firebase
    db = init_firebase()
    if not db:
        st.stop()
    
    # Onglets pour différents types de logs
    tab1, tab2, tab3, tab4 = st.tabs(["🔄 Logs Console", "📶 Signaux", "⛔ Paires Rejetées", "📊 Statistiques"])
    
    with tab1:
        st.subheader("🔄 Logs Console en Temps Réel")
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        with col1:
            level_filter = st.selectbox("Niveau", ["Tous", "INFO", "WARNING", "ERROR", "DEBUG"])
        with col2:
            module_filter = st.selectbox("Module", ["Tous", "main_scanner", "signal_detector", "trade_executor", "pair_scanner"])
        with col3:
            limit = st.slider("Nombre de logs", 10, 200, 50)
        
        # Récupération et affichage des logs
        logs = get_recent_logs(db, limit)
        if logs:
            # Filtrer selon les critères
            if level_filter != "Tous":
                logs = [log for log in logs if log.get('level') == level_filter]
            if module_filter != "Tous":
                logs = [log for log in logs if log.get('module') == module_filter]
            
            # Créer DataFrame pour affichage
            df_logs = pd.DataFrame(logs)
            if not df_logs.empty:
                df_logs['time'] = pd.to_datetime(df_logs['timestamp']).dt.strftime('%H:%M:%S')
                
                # Style selon le niveau
                def color_level(level):
                    colors = {
                        'INFO': '🔵',
                        'WARNING': '🟡', 
                        'ERROR': '🔴',
                        'DEBUG': '⚪'
                    }
                    return colors.get(level, '⚪')
                
                for _, log in df_logs.iterrows():
                    icon = color_level(log['level'])
                    st.markdown(f"{icon} **{log['time']}** `{log['module']}` {log['message']}")
            else:
                st.info("Aucun log correspondant aux filtres")
        else:
            st.warning("Aucun log trouvé")
    
    with tab2:
        st.subheader("📶 Signaux de Trading")
        
        # Récupération des signaux
        signals = get_signals_logs(db, 30)
        if signals:
            for signal in signals:
                time_str = pd.to_datetime(signal['timestamp']).strftime('%H:%M:%S')
                pair = signal.get('pair', 'N/A')
                
                if signal.get('is_valid_signal', False):
                    strength = signal.get('signal_strength', 0)
                    rsi = signal.get('rsi_value', 0)
                    st.success(f"✅ **{time_str}** - Signal VALIDE pour **{pair}** (RSI: {rsi:.1f}, Force: {strength}/6)")
                else:
                    reason = signal.get('action_taken', 'conditions insuffisantes')
                    st.warning(f"❌ **{time_str}** - Signal ignoré pour **{pair}** : {reason}")
        else:
            st.info("Aucun signal récent")
    
    with tab3:
        st.subheader("⛔ Paires Rejetées")
        
        # Récupération des rejets
        rejections = get_pair_rejections(db, 20)
        if rejections:
            for rejection in rejections:
                time_str = pd.to_datetime(rejection['timestamp']).strftime('%H:%M:%S')
                pair = rejection.get('pair', 'N/A')
                reason = rejection.get('rejection_reason', 'N/A')
                
                # Affichage avec détails
                with st.expander(f"⛔ {time_str} - {pair} : {reason}"):
                    metrics = rejection.get('metrics', {})
                    if metrics:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Spread %", f"{metrics.get('spread_percent', 0):.2f}")
                        with col2:
                            st.metric("Volume USDC", f"{metrics.get('volume_usdc', 0):,.0f}")
                        with col3:
                            st.metric("Volatilité %", f"{metrics.get('volatility_percent', 0):.1f}")
        else:
            st.info("Aucune paire rejetée récemment")
    
    with tab4:
        st.subheader("📊 Statistiques en Temps Réel")
        
        # Statistiques rapides depuis les logs
        logs = get_recent_logs(db, 100)
        if logs:
            log_counts = {}
            for log in logs:
                level = log.get('level', 'UNKNOWN')
                log_counts[level] = log_counts.get(level, 0) + 1
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🔵 INFO", log_counts.get('INFO', 0))
            with col2:
                st.metric("🟡 WARNING", log_counts.get('WARNING', 0))
            with col3:
                st.metric("🔴 ERROR", log_counts.get('ERROR', 0))
            with col4:
                st.metric("⚪ DEBUG", log_counts.get('DEBUG', 0))
        
        # Statistiques signaux
        signals = get_signals_logs(db, 50)
        if signals:
            valid_signals = sum(1 for s in signals if s.get('is_valid_signal', False))
            st.metric("📶 Signaux Valides", valid_signals, f"sur {len(signals)} analysés")
        
        # Dernière activité
        st.markdown("### ⏰ Dernière Activité")
        if logs:
            last_log = logs[0]
            last_time = pd.to_datetime(last_log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            st.success(f"Dernière activité: {last_time}")
        else:
            st.warning("Aucune activité récente détectée")

if __name__ == "__main__":
    main()
>>>>>>> feature/clean-config
