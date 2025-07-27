#!/usr/bin/env python3
"""
🔄 PAGE COMPARISON - DONNÉES RÉELLES FIREBASE UNIQUEMENT
Comparaison de performances - AUCUNE DONNÉE TEST
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(
    page_title="Comparison - Satochi Bot",
    page_icon="🔄",
    layout="wide"
)

try:
    from firebase_config import StreamlitFirebaseConfig
except ImportError as e:
    st.error(f"❌ Erreur import firebase_config: {e}")
    st.stop()

class ComparisonPage:
    """Comparison - 100% DONNÉES RÉELLES FIREBASE"""
    
    def __init__(self):
        self.firebase_config = StreamlitFirebaseConfig()
    
    def run(self):
        """Comparaisons basées UNIQUEMENT sur Firebase"""
        
        st.title("🔄 Comparaison de Performances (Firebase)")
        st.markdown("### 🔥 COMPARAISONS RÉELLES - AUCUNE SIMULATION")
        st.markdown("---")
        
        try:
            # Récupération données RÉELLES
            trades_data = self.firebase_config.get_trades_data(limit=1000)
            
            if not trades_data:
                st.warning("📭 Aucune donnée pour comparaison dans Firebase")
                st.info("🔄 Attendez que le bot génère plus de données")
                return
            
            # Sélection des périodes de comparaison
            self._display_comparison_controls()
            
            # Comparaison par paires RÉELLES
            self._display_real_pairs_comparison(trades_data)
            
            # Comparaison temporelle RÉELLE
            self._display_real_time_comparison(trades_data)
            
            # Comparaison stratégies RÉELLE (si disponible)
            self._display_real_strategy_comparison(trades_data)
            
        except Exception as e:
            st.error(f"❌ Erreur comparaison Firebase: {e}")
    
    def _display_comparison_controls(self):
        """Contrôles de comparaison"""
        st.subheader("⚙️ Paramètres de Comparaison")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self.comparison_type = st.selectbox(
                "Type de comparaison",
                ["Par Paire", "Par Période", "Par Stratégie"],
                index=0
            )
        
        with col2:
            self.metric_type = st.selectbox(
                "Métrique principale",
                ["P&L Total", "Winrate", "Profit Factor", "Sharpe Ratio"],
                index=0
            )
        
        with col3:
            self.time_period = st.selectbox(
                "Période d'analyse",
                ["7 derniers jours", "30 derniers jours", "Tout l'historique"],
                index=1
            )
    
    def _display_real_pairs_comparison(self, trades_data):
        """Comparaison par paires RÉELLES"""
        st.subheader("📊 Comparaison par Paire (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            if 'symbol' not in df.columns or 'pnl' not in df.columns:
                st.warning("📊 Données symbol/pnl manquantes")
                return
            
            # Groupement par paire
            pair_stats = df.groupby('symbol').agg({
                'pnl': ['sum', 'mean', 'count', 'std'],
                'symbol': 'count'
            }).round(4)
            
            pair_stats.columns = ['PnL Total', 'PnL Moyen', 'Nb Trades', 'Volatilité', 'Total']
            pair_stats = pair_stats.drop('Total', axis=1)
            
            # Calcul Winrate par paire
            winrates = df.groupby('symbol').apply(
                lambda x: (x['pnl'] > 0).sum() / len(x) * 100
            ).round(1)
            pair_stats['Winrate %'] = winrates
            
            # Calcul Profit Factor par paire
            def calculate_profit_factor(group):
                wins = group[group['pnl'] > 0]['pnl'].sum()
                losses = abs(group[group['pnl'] < 0]['pnl'].sum())
                return wins / losses if losses > 0 else float('inf')
            
            profit_factors = df.groupby('symbol').apply(calculate_profit_factor).round(2)
            pair_stats['Profit Factor'] = profit_factors
            
            # Tri par métrique sélectionnée
            sort_column_map = {
                "P&L Total": "PnL Total",
                "Winrate": "Winrate %",
                "Profit Factor": "Profit Factor",
                "Sharpe Ratio": "PnL Moyen"  # Approximation
            }
            sort_column = sort_column_map.get(self.metric_type, "PnL Total")
            pair_stats = pair_stats.sort_values(sort_column, ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(pair_stats, use_container_width=True)
            
            with col2:
                # Graphique de comparaison
                fig = px.bar(
                    x=pair_stats.index,
                    y=pair_stats[sort_column],
                    title=f"{self.metric_type} par Paire (Firebase)",
                    labels={'y': self.metric_type, 'x': 'Paire'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur comparaison paires: {e}")
    
    def _display_real_time_comparison(self, trades_data):
        """Comparaison temporelle RÉELLE"""
        st.subheader("⏰ Comparaison Temporelle (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            if 'timestamp' not in df.columns or 'pnl' not in df.columns:
                st.warning("📊 Données timestamp/pnl manquantes")
                return
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filtrage par période
            if self.time_period == "7 derniers jours":
                cutoff = datetime.now() - timedelta(days=7)
                df = df[df['timestamp'] > cutoff]
            elif self.time_period == "30 derniers jours":
                cutoff = datetime.now() - timedelta(days=30)
                df = df[df['timestamp'] > cutoff]
            
            if len(df) == 0:
                st.info("📭 Aucune donnée dans la période sélectionnée")
                return
            
            # Comparaison par jour
            df['date'] = df['timestamp'].dt.date
            daily_stats = df.groupby('date').agg({
                'pnl': ['sum', 'mean', 'count']
            }).round(2)
            
            daily_stats.columns = ['PnL Total', 'PnL Moyen', 'Nb Trades']
            daily_stats['Winrate %'] = df.groupby('date').apply(
                lambda x: (x['pnl'] > 0).sum() / len(x) * 100
            ).round(1)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique évolution journalière
                fig = px.bar(
                    x=daily_stats.index,
                    y=daily_stats['PnL Total'],
                    title="P&L Journalier (Firebase)",
                    color=daily_stats['PnL Total'],
                    color_continuous_scale=['red', 'gray', 'green']
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Graphique winrate journalier
                fig = px.line(
                    x=daily_stats.index,
                    y=daily_stats['Winrate %'],
                    title="Winrate Journalier (Firebase)",
                    markers=True
                )
                fig.add_hline(y=50, line_dash="dash", line_color="gray")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Table des stats journalières
            st.dataframe(daily_stats.sort_index(ascending=False), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur comparaison temporelle: {e}")
    
    def _display_real_strategy_comparison(self, trades_data):
        """Comparaison stratégies RÉELLE"""
        st.subheader("🎯 Comparaison Stratégies (Firebase)")
        
        try:
            df = pd.DataFrame(trades_data)
            
            # Vérifier si on a des données de stratégie
            if 'strategy' in df.columns:
                strategy_stats = df.groupby('strategy').agg({
                    'pnl': ['sum', 'mean', 'count', 'std']
                }).round(4)
                
                strategy_stats.columns = ['PnL Total', 'PnL Moyen', 'Nb Trades', 'Volatilité']
                
                # Calculs additionnels
                winrates = df.groupby('strategy').apply(
                    lambda x: (x['pnl'] > 0).sum() / len(x) * 100
                ).round(1)
                strategy_stats['Winrate %'] = winrates
                
                st.dataframe(strategy_stats, use_container_width=True)
                
                # Graphique comparaison stratégies
                fig = px.bar(
                    x=strategy_stats.index,
                    y=strategy_stats['PnL Total'],
                    title="P&L par Stratégie (Firebase)"
                )
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                # Analyse par type de trade (BUY/SELL)
                if 'side' in df.columns:
                    side_stats = df.groupby('side').agg({
                        'pnl': ['sum', 'mean', 'count']
                    }).round(4)
                    
                    side_stats.columns = ['PnL Total', 'PnL Moyen', 'Nb Trades']
                    
                    winrates = df.groupby('side').apply(
                        lambda x: (x['pnl'] > 0).sum() / len(x) * 100
                    ).round(1)
                    side_stats['Winrate %'] = winrates
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.dataframe(side_stats, use_container_width=True)
                    
                    with col2:
                        fig = px.pie(
                            values=side_stats['PnL Total'],
                            names=side_stats.index,
                            title="Répartition P&L par Type (Firebase)"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📊 Pas de données de stratégie ou de side disponibles")
            
        except Exception as e:
            st.error(f"❌ Erreur comparaison stratégies: {e}")

# Lancement de la page
if __name__ == "__main__":
    page = ComparisonPage()
    page.run()
