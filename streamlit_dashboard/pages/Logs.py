#!/usr/bin/env python3
"""
📋 PAGE LOGS - DONNÉES RÉELLES FIREBASE UNIQUEMENT
Logs système - AUCUNE DONNÉE TEST
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, timezone
import pytz

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
        
        # Auto-refresh simple (optionnel - utilisateur peut actualiser manuellement)
        if getattr(self, 'auto_refresh', False):
            st.info("🔄 Mode auto-refresh activé - Utilisez F5 ou le bouton 🔄 Actualiser pour rafraîchir")
        
        try:
            # RÉCUPÉRATION LOGS DIRECTE DANS LA PAGE
            st.info("🔍 Récupération directe des logs...")
            
            # Au lieu d'utiliser get_logs_data(), faisons directement dans la page
            logs_ref = self.firebase_config.db.collection('rsi_scalping_logs')
            selected_level = getattr(self, 'selected_level', 'ALL')
            logs_limit = getattr(self, 'logs_limit', 200)
            
            direct_logs = logs_ref.limit(logs_limit).stream()
            
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
                if i >= 30:  # Afficher maximum 30 logs
                    break
            
            # Informations sur les données
            st.success(f"📊 {len(sorted_logs)} logs trouvés | Affichage des 30 plus récents | 🕐 Tri: Plus récents en premier")
            
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
