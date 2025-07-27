#!/usr/bin/env python3
"""
📊 PAGE ANALYTICS - DONNÉES RÉELLES FIREBASE UNIQUEMENT
Analyses de performance - AUCUNE DONNÉE TEST
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(
    page_title="Analytics - Satochi Bot",
    page_icon="📊",
    layout="wide"
)

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
