#!/usr/bin/env python3
"""
💰 PAGE P&L - DASHBOARD STREAMLIT
Suivi du P&L journalier et objectifs
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Configuration de la page
st.set_page_config(
    page_title="P&L - Satochi Bot",
    page_icon="💰",
    layout="wide"
)

# Ajout du répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from firebase_logger import FirebaseLogger
    from config import TradingConfig
except ImportError as e:
    st.error(f"❌ Erreur import modules: {e}")
    st.stop()

class PnLPage:
    """Page de suivi P&L et objectifs"""
    
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
        """Lance la page P&L"""
        
        st.title("💰 P&L Journalier & Objectifs")
        st.markdown("---")
        
        # Contrôles
        col1, col2, col3 = st.columns(3)
        
        with col1:
            target_daily = st.number_input(
                "Objectif quotidien (%)",
                min_value=0.1,
                max_value=5.0,
                value=0.8,
                step=0.1
            )
        
        with col2:
            target_monthly = st.number_input(
                "Objectif mensuel (%)",
                min_value=5.0,
                max_value=50.0,
                value=20.0,
                step=1.0
            )
        
        with col3:
            initial_capital = st.number_input(
                "Capital initial (USDC)",
                min_value=100,
                max_value=100000,
                value=2000,
                step=100
            )
        
        # Métriques P&L actuelles
        self._display_pnl_metrics(target_daily, target_monthly, initial_capital)
        
        # Graphiques P&L
        col1, col2 = st.columns(2)
        
        with col1:
            self._display_daily_pnl_chart(target_daily, initial_capital)
        
        with col2:
            self._display_cumulative_pnl_chart(target_monthly, initial_capital)
        
        # Tableau détaillé P&L quotidien
        st.subheader("📊 P&L Quotidien Détaillé")
        self._display_daily_pnl_table()
        
        # Analyse des objectifs
        st.subheader("🎯 Analyse des Objectifs")
        self._display_targets_analysis(target_daily, target_monthly, initial_capital)
        
        # Projection P&L
        st.subheader("🔮 Projection P&L")
        self._display_pnl_projection(target_daily, initial_capital)
    
    def _display_pnl_metrics(self, target_daily, target_monthly, initial_capital):
        """Affiche les métriques P&L principales"""
        try:
            metrics = self._get_pnl_metrics(target_daily, target_monthly, initial_capital)
            
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric(
                    label="💵 P&L Aujourd'hui",
                    value=f"{metrics['today_pnl']:+.2f} USDC",
                    delta=f"{metrics['today_percent']:+.2f}%"
                )
            
            with col2:
                st.metric(
                    label="🎯 Objectif Quotidien",
                    value=f"{metrics['daily_target']:.2f} USDC",
                    delta=f"Atteint: {metrics['daily_progress']:.1f}%"
                )
            
            with col3:
                st.metric(
                    label="📅 P&L Mensuel",
                    value=f"{metrics['monthly_pnl']:+.2f} USDC",
                    delta=f"{metrics['monthly_percent']:+.2f}%"
                )
            
            with col4:
                st.metric(
                    label="🏆 Objectif Mensuel",
                    value=f"{metrics['monthly_target']:.2f} USDC",
                    delta=f"Atteint: {metrics['monthly_progress']:.1f}%"
                )
            
            with col5:
                st.metric(
                    label="📈 Capital Actuel",
                    value=f"{metrics['current_capital']:.0f} USDC",
                    delta=f"ROI: {metrics['total_roi']:+.1f}%"
                )
            
            with col6:
                st.metric(
                    label="🔥 Streak",
                    value=f"{metrics['winning_streak']} jours",
                    delta=f"Record: {metrics['best_streak']}"
                )
                
        except Exception as e:
            st.error(f"❌ Erreur métriques P&L: {e}")
    
    def _get_pnl_metrics(self, target_daily, target_monthly, initial_capital):
        """Récupère les métriques P&L"""
        try:
            # Simulation des données - à remplacer par Firebase
            today_pnl = 16.45
            monthly_pnl = 178.32
            current_capital = initial_capital + monthly_pnl
            
            daily_target = initial_capital * (target_daily / 100)
            monthly_target = initial_capital * (target_monthly / 100)
            
            return {
                'today_pnl': today_pnl,
                'today_percent': (today_pnl / current_capital) * 100,
                'daily_target': daily_target,
                'daily_progress': (today_pnl / daily_target) * 100,
                'monthly_pnl': monthly_pnl,
                'monthly_percent': (monthly_pnl / initial_capital) * 100,
                'monthly_target': monthly_target,
                'monthly_progress': (monthly_pnl / monthly_target) * 100,
                'current_capital': current_capital,
                'total_roi': (monthly_pnl / initial_capital) * 100,
                'winning_streak': 5,
                'best_streak': 8
            }
        except:
            return {
                'today_pnl': 0, 'today_percent': 0, 'daily_target': 0, 'daily_progress': 0,
                'monthly_pnl': 0, 'monthly_percent': 0, 'monthly_target': 0, 'monthly_progress': 0,
                'current_capital': initial_capital, 'total_roi': 0, 'winning_streak': 0, 'best_streak': 0
            }
    
    def _display_daily_pnl_chart(self, target_daily, initial_capital):
        """Affiche le graphique P&L quotidien"""
        st.subheader("📊 P&L Quotidien (30 derniers jours)")
        
        try:
            # Génération de données simulées
            dates = pd.date_range(start=datetime.now() - timedelta(days=29), periods=30, freq='D')
            daily_target = initial_capital * (target_daily / 100)
            
            # Simulation de P&L quotidiens avec tendance positive
            np.random.seed(42)
            daily_pnl = []
            cumul = 0
            
            for i in range(30):
                # P&L avec biais positif et volatilité
                base_pnl = np.random.normal(daily_target * 0.8, daily_target * 0.6)
                # Ajout de quelques jours exceptionnels
                if np.random.random() < 0.1:
                    base_pnl *= 2.5
                # Quelques jours de pertes
                if np.random.random() < 0.25:
                    base_pnl *= -0.7
                
                daily_pnl.append(base_pnl)
                cumul += base_pnl
            
            df = pd.DataFrame({
                'Date': dates,
                'P&L': daily_pnl,
                'Target': [daily_target] * 30,
                'Cumulative': np.cumsum(daily_pnl)
            })
            
            # Graphique avec barres et ligne d'objectif
            fig = go.Figure()
            
            # Barres P&L quotidien
            colors = ['#00ff88' if x > 0 else '#ff4444' for x in daily_pnl]
            fig.add_trace(go.Bar(
                x=df['Date'],
                y=df['P&L'],
                name='P&L Quotidien',
                marker_color=colors,
                opacity=0.8
            ))
            
            # Ligne objectif
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['Target'],
                mode='lines',
                name=f'Objectif ({target_daily}%)',
                line=dict(color='yellow', dash='dash', width=2)
            ))
            
            fig.update_layout(
                height=350,
                yaxis_title="P&L (USDC)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur graphique P&L quotidien: {e}")
    
    def _display_cumulative_pnl_chart(self, target_monthly, initial_capital):
        """Affiche le graphique P&L cumulé"""
        st.subheader("📈 P&L Cumulé & Capital")
        
        try:
            # Données simulées pour le mois en cours
            dates = pd.date_range(start=datetime.now().replace(day=1), periods=30, freq='D')
            
            # Simulation d'évolution du capital
            np.random.seed(123)
            capital_evolution = [initial_capital]
            monthly_target_line = []
            
            for i in range(1, 30):
                # Évolution quotidienne du capital
                daily_change = np.random.normal(8, 15)
                new_capital = capital_evolution[-1] + daily_change
                capital_evolution.append(max(new_capital, initial_capital * 0.8))  # Limite de perte
                
                # Ligne d'objectif mensuel proportionnelle
                monthly_target_line.append(initial_capital + (initial_capital * target_monthly / 100) * (i / 30))
            
            monthly_target_line.insert(0, initial_capital)
            
            df = pd.DataFrame({
                'Date': dates,
                'Capital': capital_evolution,
                'Target': monthly_target_line
            })
            
            fig = go.Figure()
            
            # Capital réel
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['Capital'],
                mode='lines+markers',
                name='Capital Réel',
                line=dict(color='#00ff88', width=3),
                fill='tonexty'
            ))
            
            # Objectif mensuel
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['Target'],
                mode='lines',
                name=f'Objectif Mensuel ({target_monthly}%)',
                line=dict(color='orange', dash='dot', width=2)
            ))
            
            # Capital initial
            fig.add_hline(
                y=initial_capital,
                line_dash="dash",
                line_color="gray",
                annotation_text="Capital Initial"
            )
            
            fig.update_layout(
                height=350,
                yaxis_title="Capital (USDC)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur graphique P&L cumulé: {e}")
    
    def _display_daily_pnl_table(self):
        """Affiche le tableau P&L quotidien"""
        try:
            # Données simulées pour les 15 derniers jours
            dates = pd.date_range(start=datetime.now() - timedelta(days=14), periods=15, freq='D')
            
            np.random.seed(42)
            table_data = []
            
            for i, date in enumerate(dates):
                daily_pnl = np.random.normal(15, 20)
                trades_count = np.random.randint(3, 12)
                winning_trades = int(trades_count * np.random.uniform(0.5, 0.8))
                
                table_data.append({
                    'Date': date.strftime('%Y-%m-%d'),
                    'Jour': date.strftime('%A'),
                    'P&L (USDC)': round(daily_pnl, 2),
                    'P&L (%)': round((daily_pnl / 2000) * 100, 2),
                    'Trades': trades_count,
                    'Wins': winning_trades,
                    'Losses': trades_count - winning_trades,
                    'Winrate (%)': round((winning_trades / trades_count) * 100, 1),
                    'Objectif Atteint': '✅' if daily_pnl > 16 else '❌'
                })
            
            df = pd.DataFrame(table_data)
            
            # Formatage conditionnel
            def color_pnl(val):
                if isinstance(val, (int, float)):
                    if val > 0:
                        return 'background-color: rgba(0, 255, 136, 0.2)'
                    elif val < 0:
                        return 'background-color: rgba(255, 68, 68, 0.2)'
                return ''
            
            styled_df = df.style.applymap(color_pnl, subset=['P&L (USDC)', 'P&L (%)'])
            
            st.dataframe(styled_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur tableau P&L: {e}")
    
    def _display_targets_analysis(self, target_daily, target_monthly, initial_capital):
        """Affiche l'analyse des objectifs"""
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique en gauge pour objectif quotidien
                daily_progress = 103.1  # Simulation
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = daily_progress,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Objectif Quotidien (%)"},
                    delta = {'reference': 100},
                    gauge = {
                        'axis': {'range': [None, 200]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 100], 'color': "yellow"},
                            {'range': [100, 200], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 100
                        }
                    }
                ))
                
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Graphique en gauge pour objectif mensuel
                monthly_progress = 89.2  # Simulation
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = monthly_progress,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Objectif Mensuel (%)"},
                    delta = {'reference': 100},
                    gauge = {
                        'axis': {'range': [None, 150]},
                        'bar': {'color': "darkgreen"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 100], 'color': "yellow"},
                            {'range': [100, 150], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 100
                        }
                    }
                ))
                
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur analyse objectifs: {e}")
    
    def _display_pnl_projection(self, target_daily, initial_capital):
        """Affiche la projection P&L"""
        try:
            # Calculs de projection
            current_capital = initial_capital + 178.32  # Simulation
            daily_target_amount = current_capital * (target_daily / 100)
            
            projections = {
                '7 jours': current_capital * ((1 + target_daily/100) ** 7) - current_capital,
                '30 jours': current_capital * ((1 + target_daily/100) ** 30) - current_capital,
                '90 jours': current_capital * ((1 + target_daily/100) ** 90) - current_capital,
                '365 jours': current_capital * ((1 + target_daily/100) ** 365) - current_capital
            }
            
            # Graphique de projection
            periods = list(projections.keys())
            profits = list(projections.values())
            
            fig = px.bar(
                x=periods,
                y=profits,
                title=f"Projection P&L (Objectif {target_daily}% quotidien)",
                labels={'x': 'Période', 'y': 'Profit Projeté (USDC)'},
                color=profits,
                color_continuous_scale='Viridis'
            )
            
            fig.update_layout(
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau des projections
            proj_df = pd.DataFrame({
                'Période': periods,
                'Profit Projeté (USDC)': [f"{p:.2f}" for p in profits],
                'Capital Final (USDC)': [f"{current_capital + p:.2f}" for p in profits],
                'ROI (%)': [f"{(p/initial_capital)*100:.1f}" for p in profits]
            })
            
            st.dataframe(proj_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erreur projection P&L: {e}")

# Interface principale
def main():
    """Fonction principale de la page P&L"""
    try:
        pnl_page = PnLPage()
        pnl_page.run()
    except Exception as e:
        st.error(f"❌ Erreur critique page P&L: {e}")

if __name__ == "__main__":
    main()
