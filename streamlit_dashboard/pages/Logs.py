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

try:
    from firebase_config import StreamlitFirebaseConfig
except ImportError as e:
    st.error(f"❌ Erreur import firebase_config: {e}")
    st.stop()

class LogsPage:
    """Logs - 100% DONNÉES RÉELLES FIREBASE"""
    
    def __init__(self):
        self.firebase_config = StreamlitFirebaseConfig()
    
    def run(self):
        """Logs basés UNIQUEMENT sur Firebase"""
        
        st.title("📋 Logs Système (Firebase)")
        st.markdown("### 🔥 LOGS RÉELS - VERSION CORRIGÉE - AUCUNE SIMULATION")
        st.markdown("---")
        
        # Filtres de logs
        self._display_log_filters()
        
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
            
            # Affichage en format console
            log_lines = []
            for log in sorted_logs:
                # Format console: [TIMESTAMP] [LEVEL] MESSAGE
                timestamp = log.get('timestamp', 'NO_TIME')
                
                # Gérer DatetimeWithNanoseconds brut
                if str(type(timestamp)).find('DatetimeWithNanoseconds') != -1:
                    try:
                        # Extraire heure, minute, seconde du DatetimeWithNanoseconds
                        time_display = f"{timestamp.hour:02d}:{timestamp.minute:02d}:{timestamp.second:02d}"
                    except:
                        time_display = str(timestamp)[:19]
                elif isinstance(timestamp, str) and 'T' in timestamp:
                    # Extraire juste la partie heure:minute:seconde
                    try:
                        dt_part = timestamp.split('T')[1].split('+')[0]  # Récupérer HH:MM:SS
                        time_display = dt_part[:8]  # Garder HH:MM:SS
                    except:
                        time_display = timestamp[:19]  # Fallback
                else:
                    time_display = str(timestamp)[:19]
                
                level = log.get('level', 'INFO')
                message = log.get('message', 'Pas de message')
                module = log.get('module', '')
                
                # Couleur selon le niveau
                if level == 'ERROR':
                    level_icon = "🔴"
                elif level == 'WARNING':
                    level_icon = "🟠"
                elif level == 'INFO':
                    level_icon = "🔵"
                elif level == 'DEBUG':
                    level_icon = "⚪"
                else:
                    level_icon = "⚫"
                
                # Format ligne de log console
                if module:
                    log_line = f"`[{time_display}]` {level_icon} **{level}** `[{module}]` {message}"
                else:
                    log_line = f"`[{time_display}]` {level_icon} **{level}** {message}"
                
                log_lines.append(log_line)
            
            # Afficher dans un container scrollable
            logs_text = "\n\n".join(log_lines)
            
            # Container avec fond sombre pour effet console
            st.markdown("""
            <style>
            .console-logs {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                padding: 15px;
                border-radius: 5px;
                height: 500px;
                overflow-y: auto;
                border: 1px solid #333;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Affichage des logs en format console
            with st.container():
                st.markdown("**Console des logs en temps réel:**")
                
                # Zone de logs avec scrolling
                for log_line in log_lines[:50]:  # Limiter à 50 logs récents
                    st.markdown(log_line)
            
            # Informations sur les données
            st.info(f"📊 {len(sorted_logs)} logs affichés | 🕐 Tri: Plus récents en premier")
            
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
