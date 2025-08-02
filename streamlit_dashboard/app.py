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
import tempfile
import json
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
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
    from firebase_config import StreamlitFirebaseConfig
except ImportError as e:
    st.error(f"❌ Erreur import modules: {e}")
    st.stop()

class SatochiDashboard:
    """Dashboard principal du bot Satochi"""
    
    def __init__(self):
        self.config = TradingConfig()
        self.api_config = APIConfig()
        self.firebase_config = None
        self.db = None
        
        # Initialisation des connexions
        self._init_connections()
    
    def _init_connections(self):
        """Initialise les connexions Firebase"""
        try:
            # Utiliser la configuration Firebase existante qui fonctionne
            self.firebase_config = StreamlitFirebaseConfig()
            self.db = self.firebase_config.db
            
        except Exception as e:
            st.error(f"❌ Erreur initialisation connexions: {e}")
            self.firebase_config = None
            self.db = None
    
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
            if not self.firebase_config:
                return {'is_running': False, 'uptime': "N/A", 'last_update': None}
            
            # Utiliser la méthode existante de firebase_config
            health_data = self.firebase_config.get_bot_health()
            
            if health_data.get('is_running', False):
                return {
                    'is_running': True,
                    'uptime': health_data.get('uptime', '0h 0m'),
                    'last_update': health_data.get('last_update'),
                    'cycle_count': health_data.get('cycle_count', 0),
                    'monitored_pairs': health_data.get('monitored_pairs', 0)
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
                    delta=f"Max: {getattr(self.config, 'MAX_DAILY_TRADES', 20)}"
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
                    delta=f"Max: {getattr(self.config, 'MAX_OPEN_POSITIONS', 2)}"
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
            if not self.firebase_config:
                return self._get_default_stats()
            
            # Utiliser les méthodes existantes de firebase_config
            trades_data = self.firebase_config.get_trades_data(limit=50)
            positions_data = self.firebase_config.get_positions_data()
            
            # Filtrer les trades d'aujourd'hui
            today = datetime.now().strftime('%Y-%m-%d')
            today_trades = []
            
            for trade in trades_data:
                # Vérifier différents champs de date
                trade_date = None
                for date_field in ['date', 'timestamp', 'entry_time']:
                    if date_field in trade and trade[date_field]:
                        try:
                            if isinstance(trade[date_field], str):
                                if trade[date_field].startswith(today):
                                    trade_date = today
                                    break
                                # Essayer de parser la date ISO
                                try:
                                    parsed_date = datetime.fromisoformat(trade[date_field].replace('Z', '+00:00'))
                                    if parsed_date.strftime('%Y-%m-%d') == today:
                                        trade_date = today
                                        break
                                except:
                                    pass
                        except:
                            pass
                
                if trade_date == today:
                    today_trades.append(trade)
            
            # Calculer les statistiques
            daily_pnl = 0
            winning_trades = 0
            total_trades = len(today_trades)
            
            for trade in today_trades:
                pnl = trade.get('pnl_usdc', trade.get('pnl', 0))
                if isinstance(pnl, (int, float)):
                    daily_pnl += pnl
                    if pnl > 0:
                        winning_trades += 1
            
            winrate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Capital et positions
            total_capital = 1000  # Valeur par défaut
            active_positions = len(positions_data)
            daily_pnl_percent = (daily_pnl / total_capital * 100) if total_capital > 0 else 0
            
            return {
                'daily_pnl': round(daily_pnl, 2),
                'daily_pnl_percent': round(daily_pnl_percent, 2),
                'daily_trades': total_trades,
                'winrate': round(winrate, 1),
                'active_positions': active_positions,
                'free_capital': round(total_capital * 0.8, 2),
                'total_capital': round(total_capital, 2)
            }
            
        except Exception as e:
            st.error(f"Erreur récupération stats: {e}")
            return self._get_default_stats()
    
    def _get_default_stats(self):
        """Retourne des statistiques par défaut"""
        return {
            'daily_pnl': 0, 'daily_pnl_percent': 0, 'daily_trades': 0,
            'winrate': 0, 'active_positions': 0, 'free_capital': 0, 'total_capital': 1000
        }
    
    def _display_pnl_chart(self):
        """Affiche le graphique P&L"""
        st.subheader("📈 P&L Évolution")
        
        try:
            if not self.firebase_config:
                st.warning("⚠️ Firebase non connecté")
                return
            
            # Récupérer les vraies données de trades
            trades_data = self.firebase_config.get_trades_data(limit=100)
            
            if not trades_data:
                st.info("📭 Aucun trade trouvé pour le graphique")
                return
            
            # Organiser les données par date
            daily_pnl = {}
            for trade in trades_data:
                pnl = trade.get('pnl_usdc', trade.get('pnl', 0))
                if not isinstance(pnl, (int, float)):
                    continue
                    
                # Extraire la date du trade
                trade_date = None
                for date_field in ['date', 'timestamp', 'entry_time']:
                    if date_field in trade and trade[date_field]:
                        try:
                            if isinstance(trade[date_field], str):
                                # Parser la date ISO
                                parsed_date = datetime.fromisoformat(trade[date_field].replace('Z', '+00:00'))
                                trade_date = parsed_date.strftime('%Y-%m-%d')
                                break
                        except:
                            pass
                
                if trade_date:
                    if trade_date not in daily_pnl:
                        daily_pnl[trade_date] = 0
                    daily_pnl[trade_date] += pnl
            
            if not daily_pnl:
                st.info("📭 Aucune donnée P&L trouvée")
                return
            
            # Convertir en DataFrame et calculer P&L cumulé
            dates = sorted(daily_pnl.keys())
            daily_values = [daily_pnl[date] for date in dates]
            cumul_values = []
            cumul = 0
            for val in daily_values:
                cumul += val
                cumul_values.append(cumul)
            
            pnl_data = pd.DataFrame({
                'date': pd.to_datetime(dates),
                'pnl_cumul': cumul_values,
                'daily_pnl': daily_values
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
            if not self.firebase_config:
                st.warning("⚠️ Firebase non connecté")
                return
            
            # Récupérer les vraies données de positions
            positions_data = self.firebase_config.get_positions_data()
            
            if not positions_data:
                st.info("📭 Aucune position active pour l'aperçu")
                return
            
            # Organiser les données pour le graphique
            pairs = []
            pnl_values = []
            durations = []
            
            for position in positions_data:
                pair = position.get('pair', position.get('symbol', 'N/A'))
                pnl = position.get('pnl_usdc', position.get('unrealized_pnl', 0))
                duration = position.get('duration', 'N/A')
                
                if isinstance(pnl, (int, float)) and pnl != 0:
                    pairs.append(pair)
                    pnl_values.append(abs(pnl))  # Valeur absolue pour le graphique
                    durations.append(duration)
            
            if not pairs:
                st.info("📭 Aucune donnée P&L trouvée pour les positions")
                return
            
            # Graphique en secteurs
            fig = px.pie(
                values=pnl_values,
                names=pairs,
                title="Exposition par paire",
                color_discrete_sequence=['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#6c5ce7', '#fd79a8']
            )
            
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau résumé des positions
            if len(pairs) > 0:
                summary_df = pd.DataFrame({
                    'Paire': pairs,
                    'P&L': [position.get('pnl_usdc', position.get('unrealized_pnl', 0)) for position in positions_data[:len(pairs)]],
                    'Duration': durations
                })
                st.dataframe(summary_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur aperçu positions: {e}")
    
    def _display_active_positions(self):
        """Affiche les positions actives"""
        try:
            if not self.firebase_config:
                st.warning("⚠️ Firebase non connecté")
                return
            
            # Récupérer les vraies données de positions
            positions_data = self.firebase_config.get_positions_data()
            
            if not positions_data:
                st.info("📭 Aucune position active")
                return
            
            # Convertir en DataFrame
            df_data = []
            for position in positions_data:
                df_data.append({
                    'Paire': position.get('pair', position.get('symbol', 'N/A')),
                    'Entry Price': position.get('entry_price', position.get('price', 0)),
                    'Current Price': position.get('current_price', position.get('mark_price', 0)),
                    'Quantity': position.get('quantity', position.get('amount', 0)),
                    'P&L USDC': position.get('pnl_usdc', position.get('unrealized_pnl', 0)),
                    'P&L %': position.get('pnl_percent', position.get('pnl_pct', 0)),
                    'Duration': position.get('duration', 'N/A'),
                    'SL': position.get('stop_loss', position.get('sl_price', 0)),
                    'TP': position.get('take_profit', position.get('tp_price', 0))
                })
            
            positions_df = pd.DataFrame(df_data)
            
            # Colorisation des P&L
            def color_pnl(val):
                if isinstance(val, (int, float)):
                    color = 'color: green' if val > 0 else 'color: red' if val < 0 else 'color: gray'
                    return color
                return ''
            
            styled_df = positions_df.style.applymap(color_pnl, subset=['P&L USDC', 'P&L %'])
            st.dataframe(styled_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur positions actives: {e}")
    
    def _display_recent_trades(self):
        """Affiche les derniers trades"""
        try:
            if not self.firebase_config:
                st.warning("⚠️ Firebase non connecté")
                return
            
            # Récupérer les vraies données de trades
            trades_data = self.firebase_config.get_trades_data(limit=20)
            
            if not trades_data:
                st.info("📭 Aucun trade trouvé")
                return
            
            # Convertir en DataFrame
            df_data = []
            for trade in trades_data:
                df_data.append({
                    'Timestamp': trade.get('timestamp', 'N/A'),
                    'Paire': trade.get('pair', trade.get('symbol', 'N/A')),
                    'Type': trade.get('side', trade.get('type', 'N/A')),
                    'Entry': trade.get('entry_price', trade.get('price', 0)),
                    'Exit': trade.get('exit_price', '-'),
                    'P&L USDC': trade.get('pnl_usdc', trade.get('pnl', 0)),
                    'P&L %': trade.get('pnl_percent', trade.get('pnl_pct', 0)),
                    'Duration': trade.get('duration', '-'),
                    'Exit Reason': trade.get('exit_reason', trade.get('reason', '-'))
                })
            
            trades_df = pd.DataFrame(df_data)
            
            # Colorisation
            def color_trades(row):
                if row['Type'] == 'BUY':
                    return ['background-color: rgba(0,255,136,0.1)'] * len(row)
                elif row['P&L USDC'] != '-' and row['P&L USDC'] != 0:
                    try:
                        pnl = float(row['P&L USDC']) if row['P&L USDC'] != '-' else 0
                        if pnl > 0:
                            return ['background-color: rgba(0,255,136,0.1)'] * len(row)
                        else:
                            return ['background-color: rgba(255,68,68,0.1)'] * len(row)
                    except:
                        pass
                return [''] * len(row)
            
            styled_trades = trades_df.style.apply(color_trades, axis=1)
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
