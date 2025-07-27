#!/usr/bin/env python3
"""
📋 PAGE LOGS - DONNÉES RÉELLES FIREBASE UNIQUEMENT
Logs système - AUCUNE DONNÉE TEST
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Logs - Satochi Bot",
    page_icon="📋",
    layout="wide"
)

# Import depuis le répertoire parent (racine)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from firebase_config import StreamlitFirebaseConfig
except ImportError as e:
    st.error(f"❌ Erreur import firebase_config: {e}")
    st.error(f"Tentative d'import depuis: {sys.path[0]}")
    st.stop()

class LogsPage:
    """Logs - 100% DONNÉES RÉELLES FIREBASE"""
    
    def __init__(self):
        self.firebase_config = StreamlitFirebaseConfig()
    
    def run(self):
        """Logs basés UNIQUEMENT sur Firebase"""
        
        st.title("📋 Logs Système (Firebase)")
        st.markdown("### 🔥 LOGS RÉELS - AUCUNE SIMULATION")
        st.markdown("---")
        
        # Filtres de logs
        self._display_log_filters()
        
        try:
            # Récupération logs RÉELS
            logs_data = self.firebase_config.get_logs_data(
                level=getattr(self, 'selected_level', 'ALL'),
                limit=getattr(self, 'logs_limit', 200)
            )
            
            if not logs_data:
                st.warning("📭 Aucun log trouvé dans Firebase")
                st.info("🔄 Vérifiez que le bot écrit des logs")
                
                # DEBUG DIRECT COLLECTIONS
                if st.button("🔍 Debug: Voir les collections Firebase"):
                    try:
                        st.info("🔍 Inspection des collections Firebase...")
                        
                        # Lister toutes les collections
                        collections = self.firebase_config.db.collections()
                        collection_names = []
                        
                        for collection in collections:
                            collection_names.append(collection.id)
                        
                        st.success(f"📋 Collections trouvées: {', '.join(collection_names)}")
                        
                        # Essayer la collection rsi_scalping_logs spécifiquement
                        try:
                            logs_ref = self.firebase_config.db.collection('rsi_scalping_logs')
                            sample_logs = logs_ref.limit(3).stream()
                            
                            sample_data = []
                            for log in sample_logs:
                                log_dict = log.to_dict()
                                sample_data.append({
                                    'id': log.id,
                                    'keys': list(log_dict.keys()),
                                    'data': log_dict
                                })
                            
                            if sample_data:
                                st.success(f"✅ Collection 'rsi_scalping_logs' trouvée avec {len(sample_data)} échantillons:")
                                st.json(sample_data)
                            else:
                                st.warning("⚠️ Collection 'rsi_scalping_logs' existe mais est vide")
                                
                        except Exception as e:
                            st.error(f"❌ Erreur accès rsi_scalping_logs: {e}")
                        
                        # Essayer d'autres collections potentielles
                        for potential_collection in ['logs', 'bot_logs', 'satochi_logs', 'trading_logs']:
                            try:
                                test_ref = self.firebase_config.db.collection(potential_collection)
                                test_docs = test_ref.limit(1).stream()
                                for doc in test_docs:
                                    st.info(f"✅ Collection '{potential_collection}' trouvée!")
                                    st.json(doc.to_dict())
                                    break
                            except:
                                continue
                                
                    except Exception as e:
                        st.error(f"❌ Erreur debug: {e}")
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
        col1, col2, col3, col4 = st.columns(4)
        
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
            self.auto_refresh = st.checkbox("Auto-refresh", value=True)
        
        with col4:
            if st.button("🔄 Actualiser"):
                st.rerun()
    
    def _display_real_log_stats(self, logs_data):
        """Statistiques logs RÉELLES"""
        st.subheader("📊 Statistiques Logs (Firebase)")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
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
            
            # Logs récents (dernière heure)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                one_hour_ago = datetime.now() - timedelta(hours=1)
                recent_logs = len(df[df['timestamp'] > one_hour_ago])
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
            
        except Exception as e:
            st.error(f"❌ Erreur stats logs: {e}")
    
    def _display_real_log_timeline(self, logs_data):
        """Timeline logs RÉELLE"""
        st.subheader("📈 Timeline des Logs (Firebase)")
        
        try:
            df = pd.DataFrame(logs_data)
            
            if 'timestamp' in df.columns and 'level' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
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
            else:
                st.warning("📊 Colonnes timestamp/level manquantes")
                
        except Exception as e:
            st.error(f"❌ Erreur timeline logs: {e}")
    
    def _display_real_logs_table(self, logs_data):
        """Table des logs RÉELS"""
        st.subheader("📋 Journal des Logs (Firebase)")
        
        try:
            df = pd.DataFrame(logs_data)
            
            if len(df) == 0:
                st.info("📭 Aucun log")
                return
            
            # Tri par timestamp décroissant (plus récents d'abord)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp', ascending=False)
            
            # Formatage pour affichage
            display_df = df.copy()
            
            # Colonnes importantes
            important_columns = ['timestamp', 'level', 'message', 'module', 'function']
            available_columns = [col for col in important_columns if col in display_df.columns]
            
            # Si pas de colonnes standards, prendre toutes les colonnes
            if not available_columns:
                available_columns = list(display_df.columns)
            
            # Formatage du timestamp
            if 'timestamp' in display_df.columns:
                display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Ajout de couleurs par niveau
            def highlight_level(row):
                if 'level' in row and isinstance(row['level'], str):
                    if row['level'] == 'ERROR':
                        return ['background-color: #ffebee'] * len(row)
                    elif row['level'] == 'WARNING':
                        return ['background-color: #fff3e0'] * len(row)
                    elif row['level'] == 'INFO':
                        return ['background-color: #e3f2fd'] * len(row)
                return [''] * len(row)
            
            # Affichage avec style
            if 'level' in display_df.columns:
                styled_df = display_df[available_columns].style.apply(highlight_level, axis=1)
                st.dataframe(styled_df, use_container_width=True, height=500)
            else:
                st.dataframe(display_df[available_columns], use_container_width=True, height=500)
            
            # Informations sur les données
            st.info(f"📊 {len(df)} logs affichés | Colonnes: {', '.join(available_columns)}")
            
            # Export
            if st.button("💾 Exporter CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Télécharger logs",
                    data=csv,
                    file_name=f"satochi_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
        except Exception as e:
            st.error(f"❌ Erreur table logs: {e}")

# Lancement de la page
if __name__ == "__main__":
    page = LogsPage()
    page.run()
