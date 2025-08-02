#!/usr/bin/env python3
"""
📋 PAGE TRADES - DASHBOARD STREAMLIT
Liste détaillée des trades BUY/SELL avec timestamps
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime, timedelta
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="Trades - Satochi Bot",
    page_icon="📋",
    layout="wide"
)

# Ajout du répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from firebase_config import StreamlitFirebaseConfig
    from config import TradingConfig
except ImportError as e:
    st.error(f"❌ Erreur import modules: {e}")
    st.stop()

class TradesPage:
    """Page de gestion et visualisation des trades"""
    
    def __init__(self):
        self.firebase_config = None
        self.config = TradingConfig()
        self._init_firebase()
    
    def _init_firebase(self):
        """Initialise la connexion Firebase"""
        try:
            self.firebase_config = StreamlitFirebaseConfig()
        except Exception as e:
            st.error(f"❌ Erreur connexion Firebase: {e}")
    
    def run(self):
        """Lance la page trades"""
        
        st.title("📋 Historique des Trades")
        st.markdown("---")
        
        # Contrôles et filtres
        self._display_trade_controls()
        
        # Métriques des trades
        self._display_trade_metrics()
        
        # Graphiques de trades
        col1, col2 = st.columns(2)
        
        with col1:
            self._display_trades_timeline()
        
        with col2:
            self._display_trade_distribution()
        
        # Positions actives
        st.subheader("🔄 Positions Actuellement Ouvertes")
        self._display_active_positions()
        
        # Historique complet des trades
        st.subheader("📊 Historique Complet des Trades")
        self._display_trades_history()
        
        # Analyse détaillée d'un trade
        st.subheader("🔍 Analyse Détaillée")
        self._display_trade_detail_analysis()
    
    def _display_trade_controls(self):
        """Affiche les contrôles de filtrage"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            self.selected_period = st.selectbox(
                "Période",
                ["Aujourd'hui", "7 derniers jours", "30 derniers jours", "Tout l'historique"],
                index=2
            )
        
        with col2:
            self.selected_pairs = st.multiselect(
                "Paires",
                ["BTCUSDC", "ETHUSDC", "ADAUSDC", "SOLUSDC", "MATICUSDC", "DOTUSDC"],
                default=["BTCUSDC", "ETHUSDC", "ADAUSDC"]
            )
        
        with col3:
            self.trade_status = st.selectbox(
                "Statut",
                ["Tous", "Ouverts", "Fermés", "Annulés"],
                index=0
            )
        
        with col4:
            self.trade_type = st.selectbox(
                "Type",
                ["Tous", "Profits", "Pertes", "Break-even"],
                index=0
            )
        
        with col5:
            self.sort_by = st.selectbox(
                "Trier par",
                ["Date (récent)", "Date (ancien)", "P&L (desc)", "P&L (asc)", "Durée"],
                index=0
            )
    
    def _display_trade_metrics(self):
        """Affiche les métriques des trades"""
        try:
            metrics = self._get_trade_metrics()
            
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric(
                    label="📊 Total Trades",
                    value=metrics['total_trades'],
                    delta=f"Période: {self.selected_period}"
                )
            
            with col2:
                st.metric(
                    label="✅ Trades Gagnants",
                    value=metrics['winning_trades'],
                    delta=f"Winrate: {metrics['winrate']:.1f}%"
                )
            
            with col3:
                st.metric(
                    label="❌ Trades Perdants",
                    value=metrics['losing_trades'],
                    delta=f"Loss rate: {100-metrics['winrate']:.1f}%"
                )
            
            with col4:
                st.metric(
                    label="💰 P&L Total",
                    value=f"{metrics['total_pnl']:+.2f} USDC",
                    delta=f"Moy: {metrics['avg_pnl']:+.2f}"
                )
            
            with col5:
                st.metric(
                    label="⏱️ Durée Moyenne",
                    value=metrics['avg_duration'],
                    delta=f"Médiane: {metrics['median_duration']}"
                )
            
            with col6:
                st.metric(
                    label="🎯 Meilleur Trade",
                    value=f"+{metrics['best_trade']:.2f} USDC",
                    delta=f"Pire: {metrics['worst_trade']:+.2f}"
                )
                
        except Exception as e:
            st.error(f"❌ Erreur métriques trades: {e}")
    
    def _get_trade_metrics(self):
        """Récupère les métriques des trades"""
        try:
            # Simulation des données - à remplacer par Firebase
            return {
                'total_trades': 127,
                'winning_trades': 89,
                'losing_trades': 38,
                'winrate': 70.1,
                'total_pnl': 346.78,
                'avg_pnl': 2.73,
                'avg_duration': '1h 42m',
                'median_duration': '1h 28m',
                'best_trade': 67.89,
                'worst_trade': -23.45
            }
        except:
            return {
                'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0,
                'winrate': 0, 'total_pnl': 0, 'avg_pnl': 0,
                'avg_duration': 'N/A', 'median_duration': 'N/A',
                'best_trade': 0, 'worst_trade': 0
            }
    
    def _display_trades_timeline(self):
        """Affiche la timeline des trades"""
        st.subheader("📈 Timeline des Trades")
        
        try:
            # Génération de données simulées
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=50, freq='15H')
            
            trades_data = []
            for i, date in enumerate(dates):
                pnl = np.random.normal(5, 20)
                trades_data.append({
                    'timestamp': date,
                    'pnl': pnl,
                    'type': 'PROFIT' if pnl > 0 else 'LOSS',
                    'pair': np.random.choice(['BTCUSDC', 'ETHUSDC', 'ADAUSDC']),
                    'size': abs(pnl)
                })
            
            df = pd.DataFrame(trades_data)
            
            # Graphique scatter avec couleurs
            fig = px.scatter(
                df,
                x='timestamp',
                y='pnl',
                color='type',
                size='size',
                hover_data=['pair'],
                color_discrete_map={'PROFIT': '#00ff88', 'LOSS': '#ff4444'},
                title="P&L des Trades dans le Temps"
            )
            
            # Ligne zéro
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            
            fig.update_layout(
                height=350,
                yaxis_title="P&L (USDC)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur timeline trades: {e}")
    
    def _display_trade_distribution(self):
        """Affiche la distribution des trades"""
        st.subheader("📊 Distribution P&L")
        
        try:
            # Génération d'histogramme P&L
            np.random.seed(42)
            pnl_data = np.random.normal(5, 15, 200)
            
            fig = px.histogram(
                x=pnl_data,
                nbins=30,
                title="Distribution des P&L",
                labels={'x': 'P&L (USDC)', 'y': 'Nombre de Trades'},
                color_discrete_sequence=['#00ff88']
            )
            
            # Ligne médiane
            median_pnl = np.median(pnl_data)
            fig.add_vline(x=median_pnl, line_dash="dash", line_color="yellow", 
                         annotation_text=f"Médiane: {median_pnl:.2f}")
            
            # Ligne zéro
            fig.add_vline(x=0, line_dash="solid", line_color="red")
            
            fig.update_layout(
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur distribution trades: {e}")
    
    def _display_active_positions(self):
        """Affiche les positions actuellement ouvertes"""
        try:
            # Données simulées des positions actives
            active_trades = [
                {
                    'Trade ID': 'BTCUSDC_1722098567',
                    'Paire': 'BTCUSDC',
                    'Entry Time': '2024-07-27 14:22:47',
                    'Entry Price': 45234.56,
                    'Current Price': 45456.78,
                    'Quantity': 0.0044,
                    'P&L Unrealized': 25.43,
                    'P&L %': 0.49,
                    'Duration': '1h 23m',
                    'Stop Loss': 44123.45,
                    'Take Profit': 46789.12,
                    'RSI Entry': 27.3,
                    'Actions': '🔄'
                },
                {
                    'Trade ID': 'ETHUSDC_1722095234',
                    'Paire': 'ETHUSDC',
                    'Entry Time': '2024-07-27 13:33:54',
                    'Entry Price': 2567.89,
                    'Current Price': 2534.12,
                    'Quantity': 0.782,
                    'P&L Unrealized': -12.34,
                    'P&L %': -1.31,
                    'Duration': '2h 12m',
                    'Stop Loss': 2456.78,
                    'Take Profit': 2678.90,
                    'RSI Entry': 26.8,
                    'Actions': '🔄'
                },
                {
                    'Trade ID': 'ADAUSDC_1722092156',
                    'Paire': 'ADAUSDC',
                    'Entry Time': '2024-07-27 12:42:36',
                    'Entry Price': 0.4523,
                    'Current Price': 0.4562,
                    'Quantity': 442.5,
                    'P&L Unrealized': 8.67,
                    'P&L %': 0.86,
                    'Duration': '2h 54m',
                    'Stop Loss': 0.4321,
                    'Take Profit': 0.4789,
                    'RSI Entry': 25.9,
                    'Actions': '🔄'
                }
            ]
            
            df = pd.DataFrame(active_trades)
            
            # Formatage conditionnel pour P&L
            def color_pnl(row):
                colors = []
                for col in df.columns:
                    if 'P&L' in col and isinstance(row[col], (int, float)):
                        if row[col] > 0:
                            colors.append('background-color: rgba(0, 255, 136, 0.2)')
                        elif row[col] < 0:
                            colors.append('background-color: rgba(255, 68, 68, 0.2)')
                        else:
                            colors.append('')
                    else:
                        colors.append('')
                return colors
            
            styled_df = df.style.apply(lambda x: color_pnl(x), axis=1)
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Boutons d'action
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💥 Fermer Toutes Positions", type="secondary"):
                    st.warning("Fermeture de toutes les positions...")
            with col2:
                if st.button("📊 Refresh Positions", type="primary"):
                    st.success("Positions mises à jour")
            with col3:
                selected_trade = st.selectbox("Fermer position:", ["Aucune"] + [t['Trade ID'] for t in active_trades])
            
        except Exception as e:
            st.error(f"❌ Erreur positions actives: {e}")
    
    def _display_trades_history(self):
        """Affiche l'historique complet des trades"""
        try:
            # Génération de données d'historique
            history_trades = []
            
            for i in range(50):
                entry_time = datetime.now() - timedelta(hours=np.random.randint(1, 720))
                duration_minutes = np.random.randint(15, 300)
                exit_time = entry_time + timedelta(minutes=duration_minutes)
                
                entry_price = np.random.uniform(1000, 50000)
                pnl = np.random.normal(8, 25)
                exit_price = entry_price + (pnl / np.random.uniform(0.001, 0.1))
                
                pair = np.random.choice(['BTCUSDC', 'ETHUSDC', 'ADAUSDC', 'SOLUSDC', 'MATICUSDC'])
                
                history_trades.append({
                    'Trade ID': f"{pair}_{int(entry_time.timestamp())}",
                    'Paire': pair,
                    'Entry Time': entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'Exit Time': exit_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'Entry Price': round(entry_price, 6),
                    'Exit Price': round(exit_price, 6),
                    'Quantity': round(np.random.uniform(0.001, 1), 6),
                    'P&L (USDC)': round(pnl, 2),
                    'P&L (%)': round((pnl / 1000) * 100, 2),  # Approximation
                    'Duration': f"{duration_minutes // 60}h {duration_minutes % 60}m",
                    'Exit Reason': np.random.choice(['TAKE_PROFIT', 'STOP_LOSS', 'TIMEOUT', 'MANUAL']),
                    'RSI Entry': round(np.random.uniform(20, 35), 1),
                    'Status': 'CLOSED'
                })
            
            df = pd.DataFrame(history_trades)
            
            # Tri selon la sélection
            if self.sort_by == "Date (récent)":
                df = df.sort_values('Entry Time', ascending=False)
            elif self.sort_by == "Date (ancien)":
                df = df.sort_values('Entry Time', ascending=True)
            elif self.sort_by == "P&L (desc)":
                df = df.sort_values('P&L (USDC)', ascending=False)
            elif self.sort_by == "P&L (asc)":
                df = df.sort_values('P&L (USDC)', ascending=True)
            
            # Filtrage par paires
            if self.selected_pairs:
                df = df[df['Paire'].isin(self.selected_pairs)]
            
            # Formatage conditionnel
            def style_trades(row):
                colors = []
                for col in df.columns:
                    if 'P&L' in col and isinstance(row[col], (int, float)):
                        if row[col] > 0:
                            colors.append('background-color: rgba(0, 255, 136, 0.1)')
                        elif row[col] < 0:
                            colors.append('background-color: rgba(255, 68, 68, 0.1)')
                        else:
                            colors.append('')
                    elif col == 'Exit Reason':
                        if row[col] == 'TAKE_PROFIT':
                            colors.append('color: green; font-weight: bold')
                        elif row[col] == 'STOP_LOSS':
                            colors.append('color: red; font-weight: bold')
                        else:
                            colors.append('')
                    else:
                        colors.append('')
                return colors
            
            styled_df = df.style.apply(lambda x: style_trades(x), axis=1)
            
            # Pagination
            page_size = 20
            total_pages = len(df) // page_size + (1 if len(df) % page_size > 0 else 0)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page = st.selectbox(f"Page (Total: {total_pages})", list(range(1, total_pages + 1)))
            
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            st.dataframe(styled_df.iloc[start_idx:end_idx], use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur historique trades: {e}")
    
    def _display_trade_detail_analysis(self):
        """Affiche l'analyse détaillée d'un trade"""
        try:
            # Sélection d'un trade pour analyse
            selected_trade_id = st.text_input(
                "ID du trade à analyser",
                placeholder="Ex: BTCUSDC_1722098567"
            )
            
            if selected_trade_id:
                # Simulation des détails du trade
                trade_details = {
                    'trade_id': selected_trade_id,
                    'pair': 'BTCUSDC',
                    'entry_time': '2024-07-27 14:22:47',
                    'exit_time': '2024-07-27 15:45:23',
                    'entry_price': 45234.56,
                    'exit_price': 45567.89,
                    'quantity': 0.0044,
                    'pnl': 25.43,
                    'duration': '1h 22m 36s',
                    'entry_conditions': {
                        'rsi': 27.3,
                        'ema_9': 45156.78,
                        'ema_21': 44987.23,
                        'macd': 0.45,
                        'volume_ratio': 1.67,
                        'breakout': True
                    },
                    'exit_reason': 'TAKE_PROFIT'
                }
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Détails du Trade")
                    st.json(trade_details)
                
                with col2:
                    st.subheader("📈 Conditions d'Entrée")
                    
                    # Radar chart des conditions
                    conditions = ['RSI < 28', 'EMA Cross', 'MACD+', 'Volume+', 'Breakout', 'Bollinger']
                    values = [100, 85, 78, 92, 100, 65]  # Simulation scores
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatterpolar(
                        r=values,
                        theta=conditions,
                        fill='toself',
                        name='Score Conditions',
                        line_color='#00ff88'
                    ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100]
                            )
                        ),
                        title="Score des Conditions d'Entrée",
                        height=300
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur analyse détaillée: {e}")

# Interface principale
def main():
    """Fonction principale de la page trades"""
    try:
        trades_page = TradesPage()
        trades_page.run()
    except Exception as e:
        st.error(f"❌ Erreur critique page trades: {e}")

if __name__ == "__main__":
    main()
