#!/usr/bin/env python3
"""
<<<<<<< HEAD
💰 PAGE P&L - DONNÉES RÉELLES FIREBASE UNIQUEMENT
Suivi profit/loss - AUCUNE DONNÉE TEST
=======
💰 PAGE P&L - DASHBOARD STREAMLIT
Suivi du P&L journalier et objectifs
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
    page_title="P&L - Satochi Bot",
    page_icon="💰",
    layout="wide"
)

<<<<<<< HEAD
try:
    from firebase_config import StreamlitFirebaseConfig
except ImportError as e:
    st.error(f"❌ Erreur import firebase_config: {e}")
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
        
        # Auto-refresh automatique toutes les 20 secondes pour P&L
        count = st_autorefresh(interval=20000, key="pnl_autorefresh")
        st.success(f"🔄 Auto-refresh P&L - Actualisation #{count} (toutes les 20s)")
        
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
=======
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
>>>>>>> feature/clean-config
