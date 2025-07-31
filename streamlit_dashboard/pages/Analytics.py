#!/usr/bin/env python3
"""
<<<<<<< HEAD
📊 PAGE ANALYTICS - DONNÉES RÉELLES FIREBASE UNIQUEMENT
Analyses de performance - AUCUNE DONNÉE TEST
=======
📊 PAGE ANALYTICS - DASHBOARD STREAMLIT
Analyse détaillée des performances par paire
>>>>>>> feature/clean-config
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
<<<<<<< HEAD
from datetime import datetime, timedelta
import numpy as np
from streamlit_autorefresh import st_autorefresh

=======
from plotly.subplots import make_subplots
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Configuration de la page
>>>>>>> feature/clean-config
st.set_page_config(
    page_title="Analytics - Satochi Bot",
    page_icon="📊",
    layout="wide"
)

<<<<<<< HEAD
try:
    from firebase_config import StreamlitFirebaseConfig
except ImportError as e:
    st.error(f"❌ Erreur import firebase_config: {e}")
    st.stop()

class AnalyticsPage:
    """Analytics - 100% DONNÉES RÉELLES FIREBASE"""
    
    def __init__(self):
        self.firebase_config = StreamlitFirebaseConfig()
    
    def run(self):
        """Analytics basés UNIQUEMENT sur Firebase"""
        
        st.title("📊 Analytics (Données Firebase)")
        st.markdown("### 🔥 ANALYSES RÉELLES - AUCUNE SIMULATION")
        st.markdown("---")
        
        # Auto-refresh automatique toutes les 30 secondes pour Analytics
        count = st_autorefresh(interval=30000, key="analytics_autorefresh")
        st.success(f"🔄 Auto-refresh Analytics - Actualisation #{count} (toutes les 30s)")
        
        try:
            # Récupération données RÉELLES
            trades_data = self.firebase_config.get_trades_data(limit=500)
            analytics_data = self.firebase_config.get_analytics_data(period_days=30)
            
            if not trades_data:
                st.warning("📭 Aucune donnée d'analytics dans Firebase")
                st.info("🔄 Attendez que le bot génère des données")
                return
            
            # KPIs RÉELS
            self._display_real_kpis(trades_data)
            
            # Graphiques performance RÉELS
            col1, col2 = st.columns(2)
            with col1:
                self._display_real_performance_chart(trades_data)
            with col2:
                self._display_real_drawdown_chart(trades_data)
            
            # Analyses par paire RÉELLES
            self._display_real_pair_analysis(trades_data)
            
            # Analyses temporelles RÉELLES
            self._display_real_time_analysis(trades_data)
            
        except Exception as e:
            st.error(f"❌ Erreur analytics Firebase: {e}")
    
    def _display_real_kpis(self, trades_data):
        """KPIs RÉELS calculés depuis Firebase"""
        st.subheader("🎯 KPIs de Performance (Firebase)")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        try:
            df = pd.DataFrame(trades_data)
            
            # Calculs RÉELS
            total_pnl = df['pnl'].sum() if 'pnl' in df.columns else 0
            winning_trades = len(df[df['pnl'] > 0]) if 'pnl' in df.columns else 0
            total_trades = len(df)
            winrate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Sharpe ratio RÉEL
            returns = df['pnl'].pct_change().dropna() if 'pnl' in df.columns else pd.Series([])
            sharpe = np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 1 and returns.std() != 0 else 0
            
            # Max drawdown RÉEL
            cumulative = df['pnl'].cumsum() if 'pnl' in df.columns else pd.Series([])
            running_max = cumulative.expanding().max()
            drawdown = cumulative - running_max
            max_drawdown = drawdown.min() if len(drawdown) > 0 else 0
            
            with col1:
                st.metric("💰 P&L Total", f"{total_pnl:.2f} USDC", delta="Réel")
            
            with col2:
                st.metric("🎯 Winrate", f"{winrate:.1f}%", delta=f"{winning_trades}/{total_trades}")
            
            with col3:
                st.metric("📈 Sharpe Ratio", f"{sharpe:.2f}", delta="Calculé")
            
            with col4:
                st.metric("📉 Max Drawdown", f"{max_drawdown:.2f} USDC", delta="Réel")
            
            with col5:
                avg_trade = total_pnl / total_trades if total_trades > 0 else 0
                st.metric("⚡ Trade Moyen", f"{avg_trade:.2f} USDC", delta="Calculé")
                
        except Exception as e:
            st.error(f"❌ Erreur KPIs: {e}")
    
    def _display_real_performance_chart(self, trades_data):
        """Graphique performance RÉEL"""
        st.subheader("📈 Courbe de Performance (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            if 'pnl' in df.columns and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                df['cumulative_pnl'] = df['pnl'].cumsum()
                
                fig = px.line(
                    df, 
                    x='timestamp', 
                    y='cumulative_pnl',
                    title="Performance Cumulative (Firebase)"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("📊 Données insuffisantes pour le graphique")
                
        except Exception as e:
            st.error(f"❌ Erreur graphique performance: {e}")
    
    def _display_real_drawdown_chart(self, trades_data):
        """Graphique drawdown RÉEL"""
        st.subheader("📉 Analyse Drawdown (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            if 'pnl' in df.columns:
                cumulative = df['pnl'].cumsum()
                running_max = cumulative.expanding().max()
                drawdown = cumulative - running_max
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    y=drawdown,
                    mode='lines',
                    fill='tonexty',
                    name='Drawdown'
                ))
                fig.update_layout(
                    title="Drawdown (Firebase)",
                    height=400,
                    yaxis_title="Drawdown (USDC)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("📊 Données PnL manquantes")
                
        except Exception as e:
            st.error(f"❌ Erreur drawdown: {e}")
    
    def _display_real_pair_analysis(self, trades_data):
        """Analyse par paire RÉELLE"""
        st.subheader("🔍 Analyse par Paire (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            if 'symbol' in df.columns and 'pnl' in df.columns:
                pair_stats = df.groupby('symbol').agg({
                    'pnl': ['sum', 'mean', 'count'],
                    'symbol': 'count'
                }).round(2)
                
                pair_stats.columns = ['PnL Total', 'PnL Moyen', 'Nb Trades', 'Total']
                pair_stats = pair_stats.drop('Total', axis=1)
                pair_stats = pair_stats.sort_values('PnL Total', ascending=False)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.dataframe(pair_stats, use_container_width=True)
                
                with col2:
                    fig = px.bar(
                        x=pair_stats.index,
                        y=pair_stats['PnL Total'],
                        title="P&L par Paire (Firebase)"
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("📊 Données symbol/pnl manquantes")
                
        except Exception as e:
            st.error(f"❌ Erreur analyse paires: {e}")
    
    def _display_real_time_analysis(self, trades_data):
        """Analyse temporelle RÉELLE"""
        st.subheader("⏰ Analyse Temporelle (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            if 'timestamp' in df.columns and 'pnl' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['hour'] = df['timestamp'].dt.hour
                df['day_of_week'] = df['timestamp'].dt.day_name()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Performance par heure
                    hourly_pnl = df.groupby('hour')['pnl'].sum().reset_index()
                    fig = px.bar(
                        hourly_pnl,
                        x='hour',
                        y='pnl',
                        title="P&L par Heure (Firebase)"
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Performance par jour de la semaine
                    daily_pnl = df.groupby('day_of_week')['pnl'].sum().reset_index()
                    fig = px.bar(
                        daily_pnl,
                        x='day_of_week',
                        y='pnl',
                        title="P&L par Jour (Firebase)"
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("📊 Données timestamp/pnl manquantes")
                
        except Exception as e:
            st.error(f"❌ Erreur analyse temporelle: {e}")

# Lancement de la page
if __name__ == "__main__":
    page = AnalyticsPage()
    page.run()
=======
# Ajout du répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from firebase_logger import FirebaseLogger
    from config import TradingConfig
except ImportError as e:
    st.error(f"❌ Erreur import modules: {e}")
    st.stop()

class AnalyticsPage:
    """Page d'analyse des performances"""
    
    def __init__(self):
        self.firebase_logger = None
        self.config = TradingConfig()
        self._init_firebase()
    
    def _init_firebase(self):
        """Initialise la connexion Firebase"""
        try:
            self.firebase_logger = FirebaseLogger()
        except Exception as e:
            st.error(f"❌ Erreur connexion Firebase: {e}")
    
    def run(self):
        """Lance la page analytics"""
        
        st.title("📊 Analytics & Performance")
        st.markdown("---")
        
        # Contrôles de période
        col1, col2, col3 = st.columns(3)
        
        with col1:
            period = st.selectbox(
                "Période d'analyse",
                ["7 derniers jours", "30 derniers jours", "90 derniers jours", "Tout l'historique"],
                index=1
            )
        
        with col2:
            pair_filter = st.multiselect(
                "Filtrer par paires",
                ["BTCUSDC", "ETHUSDC", "ADAUSDC", "SOLUSDC", "MATICUSDC", "DOTUSDC"],
                default=["BTCUSDC", "ETHUSDC", "ADAUSDC"]
            )
        
        with col3:
            metric_focus = st.selectbox(
                "Métrique principale",
                ["P&L Total", "Winrate", "Durée Moyenne", "Profit Factor"],
                index=0
            )
        
        # Métriques globales
        self._display_global_metrics()
        
        # Graphiques d'analyse
        col1, col2 = st.columns(2)
        
        with col1:
            self._display_performance_by_pair()
        
        with col2:
            self._display_trade_duration_analysis()
        
        # Analyse détaillée par paire
        st.subheader("🎯 Analyse Détaillée par Paire")
        self._display_pair_analysis()
        
        # Heatmap des performances
        st.subheader("🔥 Heatmap Performances")
        self._display_performance_heatmap()
        
        # Analyse des conditions d'entrée
        st.subheader("🎲 Efficacité des Conditions d'Entrée")
        self._display_entry_conditions_analysis()
    
    def _display_global_metrics(self):
        """Affiche les métriques globales d'analytics"""
        try:
            metrics = self._get_analytics_metrics()
            
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric(
                    label="📈 Profit Factor",
                    value=f"{metrics['profit_factor']:.2f}",
                    delta="Target: 1.5+"
                )
            
            with col2:
                st.metric(
                    label="📊 Sharpe Ratio",
                    value=f"{metrics['sharpe_ratio']:.2f}",
                    delta="Target: 1.0+"
                )
            
            with col3:
                st.metric(
                    label="📉 Max Drawdown",
                    value=f"{metrics['max_drawdown']:.1f}%",
                    delta=f"Actuel: {metrics['current_drawdown']:.1f}%"
                )
            
            with col4:
                st.metric(
                    label="⏱️ Durée Moy.",
                    value=f"{metrics['avg_duration']}",
                    delta=f"Médiane: {metrics['median_duration']}"
                )
            
            with col5:
                st.metric(
                    label="🔥 Meilleure Paire",
                    value=metrics['best_pair'],
                    delta=f"+{metrics['best_pair_pnl']:.1f}%"
                )
            
            with col6:
                st.metric(
                    label="📊 Trades Analysés",
                    value=metrics['total_trades'],
                    delta=f"Période: {metrics['period_days']}j"
                )
                
        except Exception as e:
            st.error(f"❌ Erreur métriques analytics: {e}")
    
    def _get_analytics_metrics(self):
        """Récupère les métriques d'analytics"""
        try:
            # Simulation des données - à remplacer par Firebase
            return {
                'profit_factor': 1.73,
                'sharpe_ratio': 1.28,
                'max_drawdown': 8.5,
                'current_drawdown': 2.1,
                'avg_duration': '1h 34m',
                'median_duration': '1h 12m',
                'best_pair': 'BTCUSDC',
                'best_pair_pnl': 12.7,
                'total_trades': 247,
                'period_days': 30
            }
        except:
            return {
                'profit_factor': 0, 'sharpe_ratio': 0, 'max_drawdown': 0,
                'current_drawdown': 0, 'avg_duration': 'N/A', 'median_duration': 'N/A',
                'best_pair': 'N/A', 'best_pair_pnl': 0, 'total_trades': 0, 'period_days': 0
            }
    
    def _display_performance_by_pair(self):
        """Affiche les performances par paire"""
        st.subheader("💰 Performance par Paire")
        
        try:
            # Données simulées
            pairs_data = {
                'Paire': ['BTCUSDC', 'ETHUSDC', 'ADAUSDC', 'SOLUSDC', 'MATICUSDC'],
                'P&L Total': [234.56, -45.78, 123.45, 67.89, 89.12],
                'Winrate': [72.5, 58.3, 68.9, 75.2, 65.4],
                'Trades': [45, 32, 28, 35, 41],
                'Profit Factor': [1.85, 0.87, 1.56, 2.12, 1.43],
                'Avg Duration': [85, 92, 78, 95, 88]  # en minutes
            }
            
            df = pd.DataFrame(pairs_data)
            
            # Graphique en barres pour P&L
            fig = px.bar(
                df,
                x='Paire',
                y='P&L Total',
                color='P&L Total',
                color_continuous_scale=['red', 'yellow', 'green'],
                title="P&L Total par Paire (USDC)"
            )
            
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau détaillé
            st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur performance par paire: {e}")
    
    def _display_trade_duration_analysis(self):
        """Affiche l'analyse des durées de trades"""
        st.subheader("⏱️ Analyse Durées de Trades")
        
        try:
            # Génération de données simulées
            durations = np.random.lognormal(4.2, 0.8, 100)  # Distribution log-normale
            duration_df = pd.DataFrame({
                'Duration (min)': durations,
                'P&L': np.random.normal(15, 25, 100)  # P&L corrélé
            })
            
            # Graphique scatter
            fig = px.scatter(
                duration_df,
                x='Duration (min)',
                y='P&L',
                color='P&L',
                color_continuous_scale=['red', 'yellow', 'green'],
                title="Relation Durée vs P&L",
                opacity=0.7
            )
            
            # Ligne de tendance
            z = np.polyfit(duration_df['Duration (min)'], duration_df['P&L'], 1)
            p = np.poly1d(z)
            fig.add_trace(
                go.Scatter(
                    x=duration_df['Duration (min)'],
                    y=p(duration_df['Duration (min)']),
                    mode='lines',
                    name='Tendance',
                    line=dict(color='white', dash='dash')
                )
            )
            
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiques durées
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Durée Moyenne", f"{durations.mean():.0f} min")
            with col2:
                st.metric("Durée Médiane", f"{np.median(durations):.0f} min")
            with col3:
                st.metric("Durée Max", f"{durations.max():.0f} min")
            
        except Exception as e:
            st.error(f"❌ Erreur analyse durées: {e}")
    
    def _display_pair_analysis(self):
        """Affiche l'analyse détaillée par paire"""
        try:
            # Données détaillées par paire
            detailed_data = {
                'BTCUSDC': {
                    'stats': {'trades': 45, 'winrate': 72.5, 'pnl': 234.56, 'avg_duration': 85},
                    'monthly_pnl': [34.5, 67.8, 89.2, 42.1, -12.3, 78.9, 156.4, 89.7, 45.2, 67.8, 89.1, 123.4],
                    'win_loss_dist': {'wins': 32, 'losses': 13}
                },
                'ETHUSDC': {
                    'stats': {'trades': 32, 'winrate': 58.3, 'pnl': -45.78, 'avg_duration': 92},
                    'monthly_pnl': [12.3, -23.4, 45.6, -67.8, 34.5, -89.2, 23.4, -45.6, 67.8, -34.5, 23.4, -12.3],
                    'win_loss_dist': {'wins': 18, 'losses': 14}
                }
            }
            
            # Sélection de la paire
            selected_pair = st.selectbox(
                "Choisir une paire pour analyse détaillée",
                list(detailed_data.keys())
            )
            
            if selected_pair in detailed_data:
                pair_data = detailed_data[selected_pair]
                
                # Métriques de la paire
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Trades", pair_data['stats']['trades'])
                with col2:
                    st.metric("Winrate", f"{pair_data['stats']['winrate']:.1f}%")
                with col3:
                    st.metric("P&L Total", f"{pair_data['stats']['pnl']:+.2f} USDC")
                with col4:
                    st.metric("Durée Moy.", f"{pair_data['stats']['avg_duration']} min")
                
                # Graphiques pour la paire
                col1, col2 = st.columns(2)
                
                with col1:
                    # P&L mensuel
                    months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 
                             'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
                    fig = px.line(
                        x=months,
                        y=pair_data['monthly_pnl'],
                        title=f"P&L Mensuel - {selected_pair}",
                        markers=True
                    )
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Distribution Win/Loss
                    fig = px.pie(
                        values=[pair_data['win_loss_dist']['wins'], pair_data['win_loss_dist']['losses']],
                        names=['Wins', 'Losses'],
                        title=f"Win/Loss Distribution - {selected_pair}",
                        color_discrete_sequence=['#00ff88', '#ff4444']
                    )
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur analyse par paire: {e}")
    
    def _display_performance_heatmap(self):
        """Affiche la heatmap des performances"""
        try:
            # Données pour heatmap (heures vs jours de semaine)
            hours = list(range(24))
            days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
            
            # Génération de données simulées
            np.random.seed(42)
            performance_matrix = np.random.normal(10, 15, (7, 24))
            
            # Ajustement pour simuler des patterns réalistes
            for i in range(7):
                for j in range(24):
                    # Plus de volatilité pendant les heures de trading US/EU
                    if 8 <= j <= 16 or 20 <= j <= 23:
                        performance_matrix[i][j] *= 1.5
                    # Week-end moins actif
                    if i >= 5:
                        performance_matrix[i][j] *= 0.5
            
            fig = px.imshow(
                performance_matrix,
                x=hours,
                y=days,
                color_continuous_scale='RdYlGn',
                title="Heatmap Performance (P&L moyen par heure/jour)",
                labels={'x': 'Heure', 'y': 'Jour', 'color': 'P&L Moyen (USDC)'}
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur heatmap: {e}")
    
    def _display_entry_conditions_analysis(self):
        """Affiche l'analyse des conditions d'entrée"""
        try:
            # Données d'efficacité des conditions
            conditions_data = {
                'Condition': [
                    'RSI < 28',
                    'EMA(9) > EMA(21)',
                    'MACD > Signal',
                    'Bollinger Touch',
                    'Volume > Moyenne',
                    'Breakout Confirmé'
                ],
                'Succès Rate': [78.5, 65.2, 72.8, 69.4, 61.3, 84.7],
                'Fréquence': [45, 67, 52, 38, 71, 29],  # % d'apparition
                'P&L Moyen': [23.4, 18.7, 21.2, 19.8, 15.6, 28.9]
            }
            
            df = pd.DataFrame(conditions_data)
            
            # Graphique radar
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=df['Succès Rate'],
                theta=df['Condition'],
                fill='toself',
                name='Taux de Succès (%)',
                line_color='#00ff88'
            ))
            
            fig.add_trace(go.Scatterpolar(
                r=df['P&L Moyen'],
                theta=df['Condition'],
                fill='toself',
                name='P&L Moyen (USDC)',
                line_color='#ffaa00',
                opacity=0.6
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                title="Efficacité des Conditions d'Entrée",
                height=400
            )
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("📊 Détails Conditions")
                st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur analyse conditions: {e}")

# Interface principale
def main():
    """Fonction principale de la page analytics"""
    try:
        analytics_page = AnalyticsPage()
        analytics_page.run()
    except Exception as e:
        st.error(f"❌ Erreur critique page analytics: {e}")

if __name__ == "__main__":
    main()
>>>>>>> feature/clean-config
