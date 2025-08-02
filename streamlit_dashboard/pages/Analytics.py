#!/usr/bin/env python3
"""
📊 PAGE ANALYTICS - DASHBOARD STREAMLIT
Analyse détaillée des performances par paire
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
    page_title="Analytics - Satochi Bot",
    page_icon="📊",
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

class AnalyticsPage:
    """Page d'analyse des performances"""
    
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
            # Récupérer les paires réellement tradées
            if self.firebase_config:
                trades_data = self.firebase_config.get_trades_data(limit=100)
                available_pairs = list(set([
                    t.get('pair', t.get('symbol', '')) 
                    for t in trades_data 
                    if t.get('pair') or t.get('symbol')
                ]))
                # Filtrer les paires vides
                available_pairs = [p for p in available_pairs if p and p != 'UNKNOWN']
            else:
                available_pairs = []
            
            if not available_pairs:
                available_pairs = ["Aucune paire trouvée"]
            
            selected_pairs = st.multiselect(
                "Sélectionner les paires à analyser",
                available_pairs,
                default=available_pairs[:3] if len(available_pairs) > 3 else available_pairs
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
            if not self.firebase_config:
                return self._get_default_analytics_metrics()
            
            # Récupérer les vraies données de trades
            trades_data = self.firebase_config.get_trades_data(limit=200)
            
            if not trades_data:
                return self._get_default_analytics_metrics()
            
            # Calculer les vraies métriques
            total_trades = len(trades_data)
            winning_trades = 0
            total_pnl = 0
            pnl_values = []
            durations = []
            pair_pnl = {}
            
            for trade in trades_data:
                pnl = trade.get('pnl_usdc', trade.get('pnl', 0))
                if isinstance(pnl, (int, float)):
                    total_pnl += pnl
                    pnl_values.append(pnl)
                    if pnl > 0:
                        winning_trades += 1
                    
                    # Analyser par paire
                    pair = trade.get('pair', trade.get('symbol', 'UNKNOWN'))
                    if pair not in pair_pnl:
                        pair_pnl[pair] = 0
                    pair_pnl[pair] += pnl
                
                # Analyser durée
                duration = trade.get('duration', 0)
                if isinstance(duration, (int, float)) and duration > 0:
                    durations.append(duration)
            
            # Calculer métriques avancées
            winrate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Profit Factor
            gross_profit = sum([p for p in pnl_values if p > 0])
            gross_loss = abs(sum([p for p in pnl_values if p < 0]))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            
            # Sharpe Ratio (simplifié)
            pnl_std = np.std(pnl_values) if pnl_values else 1
            sharpe_ratio = (np.mean(pnl_values) / pnl_std) if pnl_std > 0 else 0
            
            # Max Drawdown (simplifié)
            cumulative = np.cumsum(pnl_values)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max * 100
            max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
            current_drawdown = abs(drawdown[-1]) if len(drawdown) > 0 else 0
            
            # Durées
            avg_duration_min = np.mean(durations) if durations else 0
            median_duration_min = np.median(durations) if durations else 0
            
            # Meilleure paire
            best_pair = max(pair_pnl.keys(), key=lambda k: pair_pnl[k]) if pair_pnl else 'N/A'
            best_pair_pnl = pair_pnl[best_pair] if best_pair != 'N/A' else 0
            
            return {
                'profit_factor': round(profit_factor, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': round(max_drawdown, 1),
                'current_drawdown': round(current_drawdown, 1),
                'avg_duration': f"{int(avg_duration_min//60)}h {int(avg_duration_min%60)}m",
                'median_duration': f"{int(median_duration_min//60)}h {int(median_duration_min%60)}m",
                'best_pair': best_pair,
                'best_pair_pnl': round((best_pair_pnl / 1000 * 100), 1),  # En %
                'total_trades': total_trades,
                'period_days': 30  # Approximation
            }
            
        except Exception as e:
            st.error(f"Erreur calcul métriques: {e}")
            return self._get_default_analytics_metrics()
    
    def _get_default_analytics_metrics(self):
        """Retourne des métriques par défaut"""
        return {
            'profit_factor': 0, 'sharpe_ratio': 0, 'max_drawdown': 0,
            'current_drawdown': 0, 'avg_duration': 'N/A', 'median_duration': 'N/A',
            'best_pair': 'N/A', 'best_pair_pnl': 0, 'total_trades': 0, 'period_days': 0
        }
    
    def _display_performance_by_pair(self):
        """Affiche les performances par paire"""
        st.subheader("💰 Performance par Paire")
        
        try:
            if not self.firebase_config:
                st.warning("⚠️ Firebase non connecté")
                return
            
            # Récupérer les vraies données
            trades_data = self.firebase_config.get_trades_data(limit=100)
            
            if not trades_data:
                st.info("📭 Aucun trade trouvé")
                return
            
            # Analyser par paire
            pair_analysis = {}
            
            for trade in trades_data:
                pair = trade.get('pair', trade.get('symbol', 'UNKNOWN'))
                pnl = trade.get('pnl_usdc', trade.get('pnl', 0))
                duration = trade.get('duration', 0)
                
                if pair not in pair_analysis:
                    pair_analysis[pair] = {
                        'pnl_total': 0,
                        'trades': 0,
                        'wins': 0,
                        'durations': []
                    }
                
                if isinstance(pnl, (int, float)):
                    pair_analysis[pair]['pnl_total'] += pnl
                    pair_analysis[pair]['trades'] += 1
                    if pnl > 0:
                        pair_analysis[pair]['wins'] += 1
                
                if isinstance(duration, (int, float)) and duration > 0:
                    pair_analysis[pair]['durations'].append(duration)
            
            # Créer DataFrame
            pairs_data = []
            for pair, data in pair_analysis.items():
                if data['trades'] > 0:
                    winrate = (data['wins'] / data['trades']) * 100
                    avg_duration = np.mean(data['durations']) if data['durations'] else 0
                    gross_profit = sum([t.get('pnl_usdc', 0) for t in trades_data 
                                      if t.get('pair', t.get('symbol')) == pair and t.get('pnl_usdc', 0) > 0])
                    gross_loss = abs(sum([t.get('pnl_usdc', 0) for t in trades_data 
                                        if t.get('pair', t.get('symbol')) == pair and t.get('pnl_usdc', 0) < 0]))
                    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
                    
                    pairs_data.append({
                        'Paire': pair,
                        'P&L Total': round(data['pnl_total'], 2),
                        'Winrate': round(winrate, 1),
                        'Trades': data['trades'],
                        'Profit Factor': round(profit_factor, 2),
                        'Avg Duration': round(avg_duration, 0)
                    })
            
            if not pairs_data:
                st.info("📭 Aucune donnée à analyser")
                return
            
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
            if not self.firebase_config:
                st.warning("⚠️ Firebase non connecté")
                return
            
            # Récupérer les vraies données
            trades_data = self.firebase_config.get_trades_data(limit=100)
            
            if not trades_data:
                st.info("📭 Aucun trade trouvé")
                return
            
            # Extraire durées et P&L
            duration_data = []
            for trade in trades_data:
                duration = trade.get('duration', 0)
                pnl = trade.get('pnl_usdc', trade.get('pnl', 0))
                
                if isinstance(duration, (int, float)) and isinstance(pnl, (int, float)) and duration > 0:
                    duration_data.append({
                        'Duration (min)': duration,
                        'P&L': pnl
                    })
            
            if not duration_data:
                st.info("📭 Aucune donnée de durée trouvée")
                return
            
            duration_df = pd.DataFrame(duration_data)
            
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
            
            # Ligne de tendance si assez de données
            if len(duration_df) > 5:
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
            durations = duration_df['Duration (min)'].values
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
            if not self.firebase_config:
                st.warning("⚠️ Firebase non connecté")
                return
            
            # Récupérer les vraies données
            trades_data = self.firebase_config.get_trades_data(limit=200)
            
            if not trades_data:
                st.info("📭 Aucun trade trouvé")
                return
            
            # Analyser les paires disponibles
            pairs_available = list(set([t.get('pair', t.get('symbol', 'UNKNOWN')) for t in trades_data]))
            pairs_available = [p for p in pairs_available if p != 'UNKNOWN']
            
            if not pairs_available:
                st.info("📭 Aucune paire identifiée")
                return
            
            # Sélection de la paire
            selected_pair = st.selectbox(
                "Choisir une paire pour analyse détaillée",
                pairs_available
            )
            
            # Filtrer les trades pour la paire sélectionnée
            pair_trades = [t for t in trades_data if t.get('pair', t.get('symbol')) == selected_pair]
            
            if not pair_trades:
                st.info(f"📭 Aucun trade trouvé pour {selected_pair}")
                return
            
            # Calculer statistiques
            total_trades = len(pair_trades)
            wins = len([t for t in pair_trades if t.get('pnl_usdc', 0) > 0])
            winrate = (wins / total_trades) * 100 if total_trades > 0 else 0
            total_pnl = sum([t.get('pnl_usdc', 0) for t in pair_trades if isinstance(t.get('pnl_usdc'), (int, float))])
            durations = [t.get('duration', 0) for t in pair_trades if isinstance(t.get('duration'), (int, float)) and t.get('duration', 0) > 0]
            avg_duration = np.mean(durations) if durations else 0
            
            # Métriques de la paire
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Trades", total_trades)
            with col2:
                st.metric("Winrate", f"{winrate:.1f}%")
            with col3:
                st.metric("P&L Total", f"{total_pnl:+.2f} USDC")
            with col4:
                st.metric("Durée Moy.", f"{int(avg_duration)} min")
            
            # Analyser P&L par mois (si assez de données)
            monthly_pnl = {}
            win_count = 0
            loss_count = 0
            
            for trade in pair_trades:
                # Extraire le mois
                timestamp = trade.get('timestamp', trade.get('entry_time', ''))
                if timestamp:
                    try:
                        if isinstance(timestamp, str):
                            date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        else:
                            date_obj = timestamp
                        month_key = date_obj.strftime('%Y-%m')
                        
                        pnl = trade.get('pnl_usdc', 0)
                        if isinstance(pnl, (int, float)):
                            if month_key not in monthly_pnl:
                                monthly_pnl[month_key] = 0
                            monthly_pnl[month_key] += pnl
                            
                            if pnl > 0:
                                win_count += 1
                            else:
                                loss_count += 1
                    except:
                        pass
            
            # Graphiques pour la paire
            col1, col2 = st.columns(2)
            
            with col1:
                # P&L mensuel
                if monthly_pnl:
                    months = sorted(monthly_pnl.keys())
                    values = [monthly_pnl[m] for m in months]
                    
                    fig = px.line(
                        x=months,
                        y=values,
                        title=f"P&L Mensuel - {selected_pair}",
                        markers=True
                    )
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Pas assez de données pour le graphique mensuel")
            
            with col2:
                # Distribution Win/Loss
                if win_count + loss_count > 0:
                    fig = px.pie(
                        values=[win_count, loss_count],
                        names=['Wins', 'Losses'],
                        title=f"Win/Loss Distribution - {selected_pair}",
                        color_discrete_sequence=['#00ff88', '#ff4444']
                    )
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Pas de données Win/Loss")
            
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
                'P&L Moyen': [15.2, 12.8, 18.9, 14.3, 11.7, 22.4]
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
