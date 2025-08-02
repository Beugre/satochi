#!/usr/bin/env python3
"""
📝 PAGE LOGS - DASHBOARD STREAMLIT
Monitoring des logs en temps réel depuis Firebase
"""

import streamlit as st
import pandas as pd
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
