#!/usr/bin/env python3
"""
🚀 SATOCHI BOT - DASHBOARD STREAMLIT CLOUD
Interface de monitoring en temps réel - DONNÉES RÉELLES FIREBASE UNIQUEMENT
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# Configuration de la page
st.set_page_config(
    page_title="Satochi Bot Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import de la configuration Firebase
try:
    from firebase_config import StreamlitFirebaseConfig
except ImportError as e:
    st.error(f"❌ Erreur import firebase_config: {e}")
    st.stop()

class SatochiDashboard:
    """Dashboard principal du bot Satochi - 100% DONNÉES RÉELLES"""
    
    def __init__(self):
        # Initialisation Firebase uniquement
        self.firebase_config = StreamlitFirebaseConfig()
        self.db = self.firebase_config.db
    
    def run(self):
        """Lance l'interface dashboard avec DONNÉES RÉELLES FIREBASE"""
        
        # Auto-refresh contrôlé par l'utilisateur
        with st.sidebar:
            enable_auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=False, key="main_auto_refresh")
        
        if enable_auto_refresh:
            # Auto-refresh toutes les 30 secondes
            st_autorefresh(interval=30000, key="dashboard_refresh")
            st.info("🔄 Auto-refresh activé - Page actualisée toutes les 30 secondes")
        
        # Sidebar avec contrôles
        with st.sidebar:
            st.title("🚀 Satochi Bot")
            st.markdown("---")
            
            # Statut du bot RÉEL depuis Firebase
            bot_health = self.firebase_config.get_bot_health()
            if bot_health['status'] == 'RUNNING':
                st.success("🟢 Bot actif")
                if 'last_update' in bot_health and bot_health['last_update']:
                    try:
                        last_update = datetime.fromisoformat(bot_health['last_update'].replace('Z', ''))
                        uptime = datetime.now() - last_update
                        st.metric("⏱️ Dernière activité", f"{uptime.seconds//60}min")
                    except:
                        st.metric("⏱️ Status", "Actif")
            else:
                st.error("🔴 Bot arrêté")
                st.text(bot_health.get('message', 'Status inconnu'))
            
            # Métriques temps réel
            positions_data = self.firebase_config.get_positions_data()
            st.metric("📊 Positions Ouvertes", len(positions_data))
            
            # Auto-refresh
            st.markdown("---")
            st.subheader("🔄 Actualisation")
            auto_refresh = st.checkbox("Auto-refresh (30s)", value=True)
        
        # Corps principal
        st.title("🚀 Satochi Bot - RSI Scalping Pro Dashboard")
        st.markdown("### 📊 DONNÉES EN TEMPS RÉEL - FIREBASE")
        
        # Métriques principales RÉELLES
        self._display_real_metrics()
        
        # Graphiques RÉELS
        col1, col2 = st.columns(2)
        
        with col1:
            self._display_real_pnl_chart()
        
        with col2:
            self._display_real_positions()
        
        # Tableau des positions actives RÉELLES
        st.subheader("📈 Positions Actives (Firebase)")
        self._display_real_active_positions()
        
        # Derniers trades RÉELS
        st.subheader("📋 Derniers Trades (Firebase)")
        self._display_real_recent_trades()
    
    def _display_real_metrics(self):
        """Affiche les métriques RÉELLES depuis Firebase"""
        col1, col2, col3, col4 = st.columns(4)
        
        try:
            # Récupération des données RÉELLES
            trades_data = self.firebase_config.get_trades_data(limit=50)
            positions_data = self.firebase_config.get_positions_data()
            
            # Calculs RÉELS
            total_trades = len(trades_data)
            total_pnl = sum([trade.get('pnl', 0) for trade in trades_data if 'pnl' in trade])
            winning_trades = len([t for t in trades_data if t.get('pnl', 0) > 0])
            winrate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            with col1:
                st.metric(
                    label="💰 P&L Total",
                    value=f"{total_pnl:.2f} USDC",
                    delta=f"Trades: {total_trades}"
                )
            
            with col2:
                st.metric(
                    label="🎯 Winrate",
                    value=f"{winrate:.1f}%",
                    delta=f"{winning_trades}/{total_trades}"
                )
            
            with col3:
                st.metric(
                    label="📊 Positions",
                    value=len(positions_data),
                    delta="Ouvertes"
                )
            
            with col4:
                avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
                st.metric(
                    label="📈 PnL Moyen",
                    value=f"{avg_pnl:.2f} USDC",
                    delta="Par trade"
                )
                
        except Exception as e:
            st.error(f"❌ Erreur métriques réelles: {e}")
            st.info("🔄 Vérifiez la connexion Firebase")
    
    def _display_real_pnl_chart(self):
        """Graphique P&L RÉEL depuis Firebase"""
        st.subheader("📈 Évolution P&L (Données Firebase)")
        
        try:
            trades_data = self.firebase_config.get_trades_data(limit=100)
            
            if not trades_data:
                st.warning("📭 Aucune donnée de trade disponible")
                return
            
            # Conversion en DataFrame RÉEL
            df = pd.DataFrame(trades_data)
            
            if 'timestamp' in df.columns and 'pnl' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['cumulative_pnl'] = df['pnl'].cumsum()
                
                fig = px.line(
                    df, 
                    x='timestamp', 
                    y='cumulative_pnl',
                    title="P&L Cumulé (Firebase)",
                    labels={'cumulative_pnl': 'P&L Cumulé (USDC)', 'timestamp': 'Date'}
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("📊 Colonnes timestamp/pnl manquantes dans les données")
                
        except Exception as e:
            st.error(f"❌ Erreur graphique P&L: {e}")
    
    def _display_real_positions(self):
        """Affiche les positions RÉELLES depuis Firebase"""
        st.subheader("📊 Positions Ouvertes (Firebase)")
        
        try:
            positions_data = self.firebase_config.get_positions_data()
            
            if not positions_data:
                st.info("📭 Aucune position ouverte")
                return
            
            # DataFrame RÉEL
            df = pd.DataFrame(positions_data)
            
            if 'symbol' in df.columns:
                # Graphique des positions par paire
                fig = px.pie(
                    df, 
                    names='symbol', 
                    title="Répartition par Paire (Firebase)",
                    hole=0.4
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("📊 Colonne 'symbol' manquante")
                
        except Exception as e:
            st.error(f"❌ Erreur positions: {e}")
    
    def _display_real_active_positions(self):
        """Tableau des positions actives RÉELLES"""
        try:
            positions_data = self.firebase_config.get_positions_data()
            
            if not positions_data:
                st.info("📭 Aucune position active")
                return
            
            # DataFrame RÉEL
            df = pd.DataFrame(positions_data)
            
            # Colonnes à afficher
            display_columns = ['symbol', 'side', 'size', 'entry_price', 'current_price', 'pnl', 'timestamp']
            available_columns = [col for col in display_columns if col in df.columns]
            
            if available_columns:
                st.dataframe(df[available_columns], use_container_width=True)
            else:
                st.warning("📊 Colonnes attendues non trouvées dans les données")
                st.json(positions_data[0] if positions_data else {})
                
        except Exception as e:
            st.error(f"❌ Erreur tableau positions: {e}")
    
    def _display_real_recent_trades(self):
        """Affiche les derniers trades RÉELS"""
        try:
            trades_data = self.firebase_config.get_trades_data(limit=20)
            
            if not trades_data:
                st.info("📭 Aucun trade disponible")
                return
            
            # DataFrame RÉEL
            df = pd.DataFrame(trades_data)
            
            # Colonnes à afficher
            display_columns = ['symbol', 'side', 'quantity', 'price', 'pnl', 'timestamp']
            available_columns = [col for col in display_columns if col in df.columns]
            
            if available_columns:
                st.dataframe(df[available_columns], use_container_width=True)
            else:
                st.warning("📊 Colonnes attendues non trouvées dans les données")
                st.json(trades_data[0] if trades_data else {})
                
        except Exception as e:
            st.error(f"❌ Erreur tableau trades: {e}")

# Lancement de l'application
if __name__ == "__main__":
    dashboard = SatochiDashboard()
    dashboard.run()
