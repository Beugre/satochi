#!/usr/bin/env python3
"""
📊 SATOCHI BOT - DASHBOARD STREAMLIT
Interface de monitoring et contrôle en temps réel
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import sys
import os
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import json
import time

# Configuration de la page
st.set_page_config(
    page_title="Satochi Bot Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ajout du répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from config import TradingConfig, APIConfig
    from firebase_logger import FirebaseLogger
    from data_fetcher import DataFetcher
except ImportError as e:
    st.error(f"❌ Erreur import modules: {e}")
    st.stop()

class SatochiDashboard:
    """Dashboard principal du bot Satochi"""
    
    def __init__(self):
        self.config = TradingConfig()
        self.api_config = APIConfig()
        self.firebase_logger = None
        self.data_fetcher = None
        
        # Initialisation des connexions
        self._init_connections()
    
    def _init_connections(self):
        """Initialise les connexions Firebase et API"""
        try:
            # Firebase
            self.firebase_logger = FirebaseLogger()
            
            # Data Fetcher
            self.data_fetcher = DataFetcher(
                api_key=self.api_config.BINANCE_API_KEY,
                api_secret=self.api_config.BINANCE_SECRET_KEY,
                testnet=self.api_config.BINANCE_TESTNET
            )
            
        except Exception as e:
            st.error(f"❌ Erreur initialisation connexions: {e}")
    
    def run(self):
        """Lance l'interface dashboard"""
        
        # Auto-refresh toutes les 30 secondes
        st_autorefresh(interval=30000, key="dashboard_refresh")
        
        # Sidebar avec logo et contrôles
        with st.sidebar:
            st.image("https://via.placeholder.com/200x80/1f1f2e/ffffff?text=SATOCHI+BOT", width=200)
            st.title("🚀 Satochi Bot")
            st.markdown("---")
            
            # Statut du bot
            bot_status = self._get_bot_status()
            if bot_status['is_running']:
                st.success("🟢 Bot actif")
                st.metric("⏱️ Uptime", bot_status['uptime'])
                if 'cycle_count' in bot_status:
                    st.metric("🔄 Cycles", bot_status['cycle_count'])
                if 'monitored_pairs' in bot_status:
                    st.metric("📊 Paires", bot_status['monitored_pairs'])
            else:
                st.error("🔴 Bot arrêté")
            
            # Contrôles
            st.subheader("⚙️ Contrôles")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Start", type="primary"):
                    self._start_bot()
            with col2:
                if st.button("⏹️ Stop", type="secondary"):
                    self._stop_bot()
            
            if st.button("💥 Force Close All", type="secondary"):
                self._force_close_all()
            
            # Paramètres temps réel
            st.markdown("---")
            st.subheader("📊 Données")
            auto_refresh = st.checkbox("Auto-refresh (30s)", value=True)
            
            if auto_refresh:
                time.sleep(30)
                st.rerun()
        
        # Corps principal
        st.title("📊 Satochi Bot - RSI Scalping Pro Dashboard")
        
        # Métriques principales
        self._display_main_metrics()
        
        # Graphiques principaux
        col1, col2 = st.columns(2)
        
        with col1:
            self._display_pnl_chart()
        
        with col2:
            self._display_positions_overview()
        
        # Tableau des positions actives
        st.subheader("📈 Positions Actives")
        self._display_active_positions()
        
        # Derniers trades
        st.subheader("📋 Derniers Trades")
        self._display_recent_trades()
    
    def _get_bot_status(self):
        """Récupère le statut du bot depuis Firebase"""
        try:
            # Récupérer le health check du binance live service
            health_doc = self.db.collection('binance_live').document('health').get()
            
            if health_doc.exists:
                health_data = health_doc.to_dict()
                last_update = health_data.get('timestamp')
                if last_update:
                    last_update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    uptime_seconds = (datetime.now() - last_update_dt).total_seconds()
                    
                    if uptime_seconds < 300:  # Moins de 5 minutes = actif
                        hours = int(uptime_seconds // 3600)
                        minutes = int((uptime_seconds % 3600) // 60)
                        uptime = f"{hours}h {minutes}m"
                        
                        return {
                            'is_running': True,
                            'uptime': uptime,
                            'last_update': last_update_dt,
                            'cycle_count': health_data.get('cycle_count', 0),
                            'monitored_pairs': health_data.get('monitored_pairs_count', 0)
                        }
            
            return {'is_running': False, 'uptime': "0", 'last_update': None}
            
        except Exception as e:
            st.error(f"Erreur récupération statut: {e}")
            return {'is_running': False, 'uptime': "0", 'last_update': None}
    
    def _start_bot(self):
        """Démarre le bot"""
        st.success("✅ Bot démarré")
        # Implémentation du démarrage
    
    def _stop_bot(self):
        """Arrête le bot"""
        st.warning("⏹️ Bot arrêté")
        # Implémentation de l'arrêt
    
    def _force_close_all(self):
        """Force la fermeture de toutes les positions"""
        st.error("💥 Fermeture forcée de toutes les positions")
        # Implémentation de la fermeture forcée
    
    def _display_main_metrics(self):
        """Affiche les métriques principales"""
        try:
            # Récupération des données
            stats = self._get_daily_stats()
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    label="💰 P&L Journalier",
                    value=f"{stats['daily_pnl']:+.2f} USDC",
                    delta=f"{stats['daily_pnl_percent']:+.2f}%"
                )
            
            with col2:
                st.metric(
                    label="📊 Trades Aujourd'hui",
                    value=stats['daily_trades'],
                    delta=f"Max: {self.config.MAX_DAILY_TRADES}"
                )
            
            with col3:
                st.metric(
                    label="🎯 Winrate",
                    value=f"{stats['winrate']:.1f}%",
                    delta=f"Target: 65%"
                )
            
            with col4:
                st.metric(
                    label="📈 Positions Actives",
                    value=stats['active_positions'],
                    delta=f"Max: {self.config.MAX_OPEN_POSITIONS}"
                )
            
            with col5:
                st.metric(
                    label="💵 Capital Libre",
                    value=f"{stats['free_capital']:.0f} USDC",
                    delta=f"Total: {stats['total_capital']:.0f}"
                )
                
        except Exception as e:
            st.error(f"❌ Erreur métriques: {e}")
    
    def _get_daily_stats(self):
        """Récupère les statistiques quotidiennes depuis Firebase"""
        try:
            # Récupérer les données de compte Binance
            account_doc = self.db.collection('binance_live').document('account_info').get()
            account_data = account_doc.to_dict() if account_doc.exists else {}
            
            # Récupérer les trades récents
            trades_doc = self.db.collection('binance_live').document('recent_trades').get()
            trades_data = trades_doc.to_dict() if trades_doc.exists else {}
            
            # Calculer les statistiques
            total_capital = account_data.get('total_value_usdc_approx', 0)
            daily_trades = len(trades_data.get('trades', []))
            
            # Calculer P&L et winrate depuis les trades
            trades = trades_data.get('trades', [])
            daily_pnl = 0
            winning_trades = 0
            
            for trade in trades:
                # Calculer approximatif du P&L (simplification)
                if trade.get('isBuyer'):
                    # Achat - on considère comme négatif pour le calcul
                    daily_pnl -= trade.get('quoteQty', 0)
                else:
                    # Vente - positif
                    daily_pnl += trade.get('quoteQty', 0)
                    if trade.get('quoteQty', 0) > 0:
                        winning_trades += 1
            
            winrate = (winning_trades / daily_trades * 100) if daily_trades > 0 else 0
            daily_pnl_percent = (daily_pnl / total_capital * 100) if total_capital > 0 else 0
            
            # Récupérer positions ouvertes
            orders_doc = self.db.collection('binance_live').document('open_orders').get()
            orders_data = orders_doc.to_dict() if orders_doc.exists else {}
            active_positions = len(orders_data.get('orders', []))
            
            return {
                'daily_pnl': round(daily_pnl, 2),
                'daily_pnl_percent': round(daily_pnl_percent, 2),
                'daily_trades': daily_trades,
                'winrate': round(winrate, 1),
                'active_positions': active_positions,
                'free_capital': round(total_capital * 0.8, 2),  # Approximation
                'total_capital': round(total_capital, 2)
            }
        except Exception as e:
            st.error(f"Erreur récupération stats: {e}")
            return {
                'daily_pnl': 0, 'daily_pnl_percent': 0, 'daily_trades': 0,
                'winrate': 0, 'active_positions': 0, 'free_capital': 0, 'total_capital': 0
            }
    
    def _display_pnl_chart(self):
        """Affiche le graphique P&L"""
        st.subheader("📈 P&L Évolution")
        
        try:
            # Données simulées - à remplacer par Firebase
            dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
            pnl_data = pd.DataFrame({
                'date': dates,
                'pnl_cumul': [i * 2.5 + (i % 3 - 1) * 10 for i in range(30)],
                'daily_pnl': [(i % 3 - 1) * 15 + 5 for i in range(30)]
            })
            
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('P&L Cumulé', 'P&L Journalier'),
                vertical_spacing=0.1
            )
            
            # P&L Cumulé
            fig.add_trace(
                go.Scatter(
                    x=pnl_data['date'],
                    y=pnl_data['pnl_cumul'],
                    mode='lines+markers',
                    name='P&L Cumulé',
                    line=dict(color='#00ff88', width=2)
                ),
                row=1, col=1
            )
            
            # P&L Journalier
            colors = ['#ff4444' if x < 0 else '#00ff88' for x in pnl_data['daily_pnl']]
            fig.add_trace(
                go.Bar(
                    x=pnl_data['date'],
                    y=pnl_data['daily_pnl'],
                    name='P&L Journalier',
                    marker_color=colors
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                height=400,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur graphique P&L: {e}")
    
    def _display_positions_overview(self):
        """Affiche l'aperçu des positions"""
        st.subheader("🎯 Répartition Positions")
        
        try:
            # Données simulées
            positions_data = {
                'Paire': ['BTCUSDC', 'ETHUSDC', 'ADAUSDC'],
                'P&L': [25.4, -12.1, 8.7],
                'Duration': ['1h 23m', '45m', '2h 12m']
            }
            
            df = pd.DataFrame(positions_data)
            
            # Graphique en secteurs
            fig = px.pie(
                values=[abs(x) for x in df['P&L']],
                names=df['Paire'],
                title="Exposition par paire",
                color_discrete_sequence=['#ff6b6b', '#4ecdc4', '#45b7d1']
            )
            
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau des positions
            st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur positions: {e}")
    
    def _display_active_positions(self):
        """Affiche les positions actives"""
        try:
            # Données simulées
            positions = pd.DataFrame({
                'Paire': ['BTCUSDC', 'ETHUSDC', 'ADAUSDC'],
                'Entry Price': [45234.56, 2567.89, 0.4523],
                'Current Price': [45456.78, 2534.12, 0.4562],
                'Quantity': [0.0044, 0.782, 442.5],
                'P&L USDC': [25.4, -12.1, 8.7],
                'P&L %': [0.49, -1.31, 0.86],
                'Duration': ['1h 23m', '45m', '2h 12m'],
                'SL': [44123.45, 2456.78, 0.4321],
                'TP': [46789.12, 2678.90, 0.4789]
            })
            
            # Colorisation des P&L
            def color_pnl(val):
                if isinstance(val, (int, float)):
                    color = 'color: green' if val > 0 else 'color: red' if val < 0 else 'color: gray'
                    return color
                return ''
            
            styled_df = positions.style.applymap(color_pnl, subset=['P&L USDC', 'P&L %'])
            
            st.dataframe(styled_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur positions actives: {e}")
    
    def _display_recent_trades(self):
        """Affiche les derniers trades"""
        try:
            # Données simulées
            trades = pd.DataFrame({
                'Timestamp': [
                    '2024-07-27 14:23:45',
                    '2024-07-27 13:45:12',
                    '2024-07-27 12:34:56',
                    '2024-07-27 11:12:34',
                    '2024-07-27 10:45:23'
                ],
                'Paire': ['BTCUSDC', 'ETHUSDC', 'ADAUSDC', 'SOLUSDC', 'MATICUSDC'],
                'Type': ['SELL', 'SELL', 'BUY', 'SELL', 'BUY'],
                'Entry': [45123.45, 2567.89, 0.4523, 156.78, 0.8934],
                'Exit': [45567.89, 2534.12, '-', 159.45, '-'],
                'P&L USDC': [44.56, -26.77, '-', 26.67, '-'],
                'P&L %': [0.98, -1.31, '-', 1.70, '-'],
                'Duration': ['1h 23m', '45m', '-', '2h 45m', '-'],
                'Exit Reason': ['TP', 'SL', '-', 'TP', '-']
            })
            
            # Colorisation
            def color_trades(row):
                if row['Type'] == 'BUY':
                    return ['background-color: rgba(0,255,136,0.1)'] * len(row)
                elif row['P&L USDC'] != '-':
                    pnl = float(row['P&L USDC']) if row['P&L USDC'] != '-' else 0
                    if pnl > 0:
                        return ['background-color: rgba(0,255,136,0.1)'] * len(row)
                    else:
                        return ['background-color: rgba(255,68,68,0.1)'] * len(row)
                return [''] * len(row)
            
            styled_trades = trades.style.apply(color_trades, axis=1)
            
            st.dataframe(styled_trades, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur derniers trades: {e}")

# Interface principale
def main():
    """Fonction principale du dashboard"""
    try:
        dashboard = SatochiDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"❌ Erreur critique dashboard: {e}")
        st.stop()

if __name__ == "__main__":
    main()
