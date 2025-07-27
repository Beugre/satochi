#!/usr/bin/env python3
"""
💰 PAGE P&L - DONNÉES RÉELLES FIREBASE UNIQUEMENT
Suivi profit/loss - AUCUNE DONNÉE TEST
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(
    page_title="P&L - Satochi Bot",
    page_icon="💰",
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

class PnLPage:
    """P&L - 100% DONNÉES RÉELLES FIREBASE"""
    
    def __init__(self):
        self.firebase_config = StreamlitFirebaseConfig()
    
    def run(self):
        """P&L basé UNIQUEMENT sur Firebase"""
        
        st.title("💰 Profit & Loss (Données Firebase)")
        st.markdown("### 🔥 P&L RÉEL - AUCUNE SIMULATION")
        st.markdown("---")
        
        try:
            # Récupération données RÉELLES
            trades_data = self.firebase_config.get_trades_data(limit=1000)
            
            if not trades_data:
                st.warning("📭 Aucune donnée P&L dans Firebase")
                st.info("🔄 Attendez que le bot effectue des trades")
                return
            
            # Vue d'ensemble P&L RÉEL
            self._display_real_pnl_overview(trades_data)
            
            # Graphiques P&L RÉELS
            col1, col2 = st.columns(2)
            with col1:
                self._display_real_cumulative_pnl(trades_data)
            with col2:
                self._display_real_daily_pnl(trades_data)
            
            # Détails P&L RÉELS
            self._display_real_pnl_details(trades_data)
            
            # Analyse risque RÉELLE
            self._display_real_risk_analysis(trades_data)
            
        except Exception as e:
            st.error(f"❌ Erreur P&L Firebase: {e}")
    
    def _display_real_pnl_overview(self, trades_data):
        """Vue d'ensemble P&L RÉEL"""
        st.subheader("💰 Vue d'ensemble P&L (Firebase)")
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        try:
            df = pd.DataFrame(trades_data)
            
            if 'pnl' not in df.columns:
                st.warning("📊 Colonne 'pnl' manquante dans les données")
                return
            
            # Calculs RÉELS
            total_pnl = df['pnl'].sum()
            positive_trades = df[df['pnl'] > 0]
            negative_trades = df[df['pnl'] < 0]
            
            total_profit = positive_trades['pnl'].sum() if len(positive_trades) > 0 else 0
            total_loss = negative_trades['pnl'].sum() if len(negative_trades) > 0 else 0
            
            avg_win = positive_trades['pnl'].mean() if len(positive_trades) > 0 else 0
            avg_loss = negative_trades['pnl'].mean() if len(negative_trades) > 0 else 0
            
            profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
            
            with col1:
                color = "normal" if total_pnl >= 0 else "inverse"
                st.metric("💰 P&L Total", f"{total_pnl:+.2f} USDC", delta="Réel", delta_color=color)
            
            with col2:
                st.metric("📈 Profits", f"+{total_profit:.2f} USDC", delta=f"{len(positive_trades)} trades")
            
            with col3:
                st.metric("📉 Pertes", f"{total_loss:.2f} USDC", delta=f"{len(negative_trades)} trades")
            
            with col4:
                st.metric("🎯 Win Moyen", f"+{avg_win:.2f} USDC", delta="Par trade gagnant")
            
            with col5:
                st.metric("💥 Loss Moyen", f"{avg_loss:.2f} USDC", delta="Par trade perdant")
            
            with col6:
                pf_color = "normal" if profit_factor >= 1 else "inverse"
                st.metric("⚖️ Profit Factor", f"{profit_factor:.2f}", delta="Ratio", delta_color=pf_color)
                
        except Exception as e:
            st.error(f"❌ Erreur vue d'ensemble: {e}")
    
    def _display_real_cumulative_pnl(self, trades_data):
        """P&L cumulé RÉEL"""
        st.subheader("📈 P&L Cumulé (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            if 'pnl' in df.columns and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                df['cumulative_pnl'] = df['pnl'].cumsum()
                
                fig = go.Figure()
                
                # Ligne principale
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['cumulative_pnl'],
                    mode='lines+markers',
                    name='P&L Cumulé',
                    line=dict(width=3),
                    marker=dict(size=5)
                ))
                
                # Zone positive/négative
                fig.add_hline(y=0, line_dash="dash", line_color="gray")
                
                fig.update_layout(
                    title="Évolution P&L Cumulé (Firebase)",
                    xaxis_title="Date",
                    yaxis_title="P&L Cumulé (USDC)",
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("📊 Données pnl/timestamp manquantes")
                
        except Exception as e:
            st.error(f"❌ Erreur P&L cumulé: {e}")
    
    def _display_real_daily_pnl(self, trades_data):
        """P&L journalier RÉEL"""
        st.subheader("📊 P&L Journalier (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            if 'pnl' in df.columns and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['date'] = df['timestamp'].dt.date
                
                daily_pnl = df.groupby('date')['pnl'].sum().reset_index()
                daily_pnl['color'] = daily_pnl['pnl'].apply(lambda x: 'green' if x >= 0 else 'red')
                
                fig = px.bar(
                    daily_pnl,
                    x='date',
                    y='pnl',
                    color='color',
                    color_discrete_map={'green': 'green', 'red': 'red'},
                    title="P&L par Jour (Firebase)"
                )
                
                fig.update_layout(
                    height=400,
                    showlegend=False,
                    xaxis_title="Date",
                    yaxis_title="P&L Journalier (USDC)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("📊 Données pnl/timestamp manquantes")
                
        except Exception as e:
            st.error(f"❌ Erreur P&L journalier: {e}")
    
    def _display_real_pnl_details(self, trades_data):
        """Détails P&L RÉELS"""
        st.subheader("🔍 Détails P&L par Trade (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            if len(df) == 0:
                st.info("📭 Aucun trade")
                return
            
            # Tri par timestamp décroissant
            if 'timestamp' in df.columns:
                df = df.sort_values('timestamp', ascending=False)
            
            # Formatage pour affichage
            display_df = df.copy()
            
            # Colonnes importantes pour P&L
            pnl_columns = ['timestamp', 'symbol', 'side', 'quantity', 'price', 'pnl']
            available_columns = [col for col in pnl_columns if col in display_df.columns]
            
            if available_columns:
                # Formatage des nombres
                if 'pnl' in display_df.columns:
                    display_df['pnl'] = display_df['pnl'].round(4)
                if 'price' in display_df.columns:
                    display_df['price'] = display_df['price'].round(6)
                if 'quantity' in display_df.columns:
                    display_df['quantity'] = display_df['quantity'].round(6)
                
                st.dataframe(
                    display_df[available_columns],
                    use_container_width=True,
                    height=400
                )
            else:
                st.warning("📊 Colonnes P&L attendues non trouvées")
                st.dataframe(display_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur détails P&L: {e}")
    
    def _display_real_risk_analysis(self, trades_data):
        """Analyse de risque RÉELLE"""
        st.subheader("⚠️ Analyse de Risque (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            if 'pnl' not in df.columns:
                st.warning("📊 Données PnL manquantes")
                return
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribution des P&L
                fig = px.histogram(
                    df,
                    x='pnl',
                    title="Distribution des P&L (Firebase)",
                    nbins=30,
                    marginal="box"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Métriques de risque
                pnl_values = df['pnl'].values
                
                # VaR (Value at Risk) 95%
                var_95 = np.percentile(pnl_values, 5)
                
                # Expected Shortfall (moyenne des 5% pires)
                worst_5_percent = pnl_values[pnl_values <= var_95]
                expected_shortfall = np.mean(worst_5_percent) if len(worst_5_percent) > 0 else 0
                
                # Volatilité
                volatility = np.std(pnl_values)
                
                # Max drawdown
                cumulative = np.cumsum(pnl_values)
                running_max = np.maximum.accumulate(cumulative)
                drawdown = cumulative - running_max
                max_drawdown = np.min(drawdown)
                
                st.metric("📉 VaR 95%", f"{var_95:.2f} USDC", delta="Risque quotidien")
                st.metric("💥 Expected Shortfall", f"{expected_shortfall:.2f} USDC", delta="Perte moyenne pire 5%")
                st.metric("🌊 Volatilité", f"{volatility:.2f} USDC", delta="Écart-type")
                st.metric("⬇️ Max Drawdown", f"{max_drawdown:.2f} USDC", delta="Perte maximale")
            
        except Exception as e:
            st.error(f"❌ Erreur analyse risque: {e}")

# Lancement de la page
if __name__ == "__main__":
    page = PnLPage()
    page.run()
